"""大麦网抢票引擎实现。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
import asyncio
import random
from typing import Optional, Callable
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from engines.base import BaseEngine
from core.models import TaskConfig

# Default timeouts
PAGE_TIMEOUT = 30000
ACTION_TIMEOUT = 10000


class DamaiEngine(BaseEngine):
    """大麦网抢票引擎。

    流程：登录页 → 商品详情页 → 选择日期场次 → 选择票档 → 确认观演人 → 提交订单
    """

    def __init__(
        self,
        headless: bool = False,
        log_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        super().__init__(headless=headless)
        self.log_callback = log_callback
        self.platform_name = "damai"

    async def _log(self, level: str, message: str):
        """通过回调记录日志。"""
        if self.log_callback:
            await self.log_callback(level, message)

    async def _random_delay(self):
        """随机延迟，模拟人工操作防检测。"""
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

    async def login(self) -> bool:
        """打开大麦登录页，等待用户手动扫码/登录完成。

        非 headless 模式下浏览器会显示，用户需要手动完成登录。
        登录成功后跳转到首页。
        """
        await self._log("info", "[大麦] 打开登录页面...")
        try:
            await self.page.goto(
                "https://www.damai.cn/",
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()

            # 检查是否已经登录（有用户名或头像显示）
            logged_in_indicators = [
                ".user-name",
                ".dm-header-user-name",
                "[data-spm='duserinfo']",
                ".header-user-avatar",
            ]
            for selector in logged_in_indicators:
                try:
                    await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    await self._log("info", "[大麦] 检测到已登录状态")
                    return True
                except PlaywrightTimeoutError:
                    continue

            # 未登录，尝试点击登录入口
            await self._log("info", "[大麦] 未登录，请用户在浏览器中扫码或登录...")
            login_btn_selectors = [
                ".login-text",
                "a[href*='login']",
                ".dm-header-login",
                "[data-spm='dlogin']",
            ]
            for selector in login_btn_selectors:
                try:
                    btn = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if btn:
                        await btn.click()
                        await self._log("info", f"[大麦] 已点击登录入口: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            # 等待用户完成登录（最多等待 120 秒）
            await self._log("info", "[大麦] 等待用户手动登录（最多120秒）...")
            for attempt in range(60):
                await asyncio.sleep(2)
                for selector in logged_in_indicators:
                    try:
                        await self.page.wait_for_selector(
                            selector, timeout=2000, state="visible"
                        )
                        await self._log("success", "[大麦] 用户登录成功")
                        return True
                    except PlaywrightTimeoutError:
                        continue
                if attempt % 10 == 0:
                    await self._log("info", "[大麦] 仍在等待登录...")

            await self._log("warn", "[大麦] 登录等待超时，用户可能未完成登录")
            return False

        except Exception as e:
            await self._log("error", f"[大麦] 登录流程异常: {e}")
            return False

    async def check_stock(self, task: TaskConfig) -> bool:
        """检查页面是否有'缺货登记'或'已售罄'字样。

        Returns:
            True 表示有库存可抢，False 表示已售罄。
        """
        out_of_stock_keywords = [
            "缺货登记",
            "已售罄",
            "暂时缺货",
            "已售完",
            "暂无票",
            "售磬",
        ]
        page_text = await self.page.content()
        for keyword in out_of_stock_keywords:
            if keyword in page_text:
                await self._log("warn", f"[大麦] 检测到缺货关键词: {keyword}")
                return False
        return True

    async def grab(self, task: TaskConfig) -> bool:
        """执行大麦网抢票流程。

        Args:
            task: 任务配置，包含 URL、date、session、price、buyers 等。

        Returns:
            True 表示成功进入支付/订单确认页面。
        """
        await self._log("info", f"[大麦] 开始抢票任务: {task.name}")
        await self._log("info", f"[大麦] 目标URL: {task.url}")

        # 1. 先登录
        logged_in = await self.login()
        if not logged_in:
            await self._log("warn", "[大麦] 未登录，但继续尝试抢票...")

        try:
            # 2. 打开演出详情页
            await self._log("info", "[大麦] 打开演出详情页...")
            await self.page.goto(
                task.url,
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()

            # 等待页面关键元素加载
            await self.page.wait_for_load_state("networkidle")

            # 3. 检查库存状态
            has_stock = await self.check_stock(task)
            if not has_stock:
                await self._log("error", "[大麦] 当前商品已售罄或无法购买")
                return False

            # 4. 点击购买按钮（"立即购买" / "选座购买" / "购买"）
            await self._log("info", "[大麦] 寻找并点击购买按钮...")
            buy_btn_selectors = [
                ".buybtn",                    # 经典购买按钮
                ".perform__order__btn",       # 演出详情页购票按钮
                ".dm-btn-buy",                # 大麦通用购买按钮
                "[data-spm='dbuy']",          # 数据埋点购买按钮
                ".btn-buy",
                "button:has-text('立即购买')",
                "button:has-text('选座购买')",
                "button:has-text('购买')",
                "a:has-text('立即购买')",
                "a:has-text('购买')",
            ]
            buy_clicked = False
            for selector in buy_btn_selectors:
                try:
                    btn = await self.page.wait_for_selector(
                        selector, timeout=5000, state="visible"
                    )
                    if btn:
                        await self._random_delay()
                        await btn.click()
                        await self._log("info", f"[大麦] 已点击购买按钮: {selector}")
                        buy_clicked = True
                        break
                except PlaywrightTimeoutError:
                    continue
            if not buy_clicked:
                await self._log("error", "[大麦] 未找到购买按钮，页面结构可能已变更")
                return False

            await self._random_delay()
            await self.page.wait_for_load_state("domcontentloaded")

            # 5. 选择日期场次（如果有多个日期，按 task.date 匹配）
            await self._log("info", f"[大麦] 尝试选择日期/场次: {task.date} {task.session}")
            date_selected = await self._select_date_session(task.date, task.session)
            if not date_selected:
                await self._log("warn", "[大麦] 未找到匹配的日期场次，可能只有默认场次")

            # 6. 选择票档价格（按 task.price 匹配）
            await self._log("info", f"[大麦] 尝试选择票档: {task.price}")
            price_selected = await self._select_price(task.price)
            if not price_selected:
                await self._log("warn", "[大麦] 未找到匹配的票档，可能票档已变更")

            # 7. 选择购票数量
            if task.ticket_count > 1:
                await self._log("info", f"[大麦] 设置购票数量: {task.ticket_count}")
                await self._set_ticket_count(task.ticket_count)

            # 8. 确认观演人（按 task.buyers 匹配）
            if task.buyers:
                await self._log("info", f"[大麦] 选择观演人: {task.buyers}")
                await self._select_buyers(task.buyers)

            # 9. 提交订单
            await self._log("info", "[大麦] 准备提交订单...")
            submit_success = await self._submit_order()
            if submit_success:
                await self._log("success", "[大麦] 订单提交成功，已进入支付/确认页面")
                return True
            else:
                await self._log("error", "[大麦] 订单提交失败")
                return False

        except Exception as e:
            await self._log("error", f"[大麦] 抢票流程异常: {e}")
            return False

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _select_date_session(self, target_date: str, target_session: str) -> bool:
        """在弹窗或页面中选择日期和场次。

        大麦网通常在点击购买后弹出选择面板，包含日期列表和场次列表。
        """
        try:
            # 等待选择面板出现
            await self.page.wait_for_selector(
                ".select_right, .session-list, .date-list, .sku-list",
                timeout=8000,
            )
        except PlaywrightTimeoutError:
            await self._log("warn", "[大麦] 未弹出选择面板，可能页面已直接进入订单页")
            return True  # 可能没有选择面板，直接进入下一步

        # 尝试选择日期
        date_selectors = [
            f".date-list-item:has-text('{target_date}')",
            f".session-item:has-text('{target_date}')",
            f".select_right_item:has-text('{target_date}')",
            f"[data-date*='{target_date}']",
            f"div:has-text('{target_date}'):near(.date-list)",
        ]
        for selector in date_selectors:
            try:
                el = await self.page.wait_for_selector(
                    selector, timeout=3000, state="visible"
                )
                if el:
                    await el.click()
                    await self._random_delay()
                    await self._log("info", f"[大麦] 已选择日期: {target_date}")
                    break
            except PlaywrightTimeoutError:
                continue

        # 选择场次
        session_selectors = [
            f".session-item:has-text('{target_session}')",
            f".select_right_item:has-text('{target_session}')",
            f".perform__info__time:has-text('{target_session}')",
            f"div:has-text('{target_session}'):near(.session-list)",
        ]
        for selector in session_selectors:
            try:
                el = await self.page.wait_for_selector(
                    selector, timeout=3000, state="visible"
                )
                if el:
                    await el.click()
                    await self._random_delay()
                    await self._log("info", f"[大麦] 已选择场次: {target_session}")
                    return True
            except PlaywrightTimeoutError:
                continue

        return False

    async def _select_price(self, target_price: str) -> bool:
        """选择票档价格。

        大麦网票档通常在日期场次选择后出现，或通过 SKU 列表展示。
        """
        price_selectors = [
            f".price-item:has-text('{target_price}')",
            f".sku-name:has-text('{target_price}')",
            f".select_left_item:has-text('{target_price}')",
            f".ticket-item:has-text('{target_price}')",
            f"div:has-text('¥{target_price}')",
            f"div:has-text('{target_price}元')",
            f"[data-price*='{target_price}']",
        ]
        for selector in price_selectors:
            try:
                el = await self.page.wait_for_selector(
                    selector, timeout=5000, state="visible"
                )
                if el:
                    await self._random_delay()
                    await el.click()
                    await self._log("info", f"[大麦] 已选择票档: {target_price}")
                    return True
            except PlaywrightTimeoutError:
                continue

        # 备选：直接选择第一个可用票档
        fallback_selectors = [
            ".price-item:not(.disabled):not(.selected)",
            ".sku-name:not(.disabled)",
            ".ticket-item:not(.disabled)",
        ]
        for selector in fallback_selectors:
            try:
                el = await self.page.wait_for_selector(
                    selector, timeout=3000, state="visible"
                )
                if el:
                    await self._random_delay()
                    await el.click()
                    text = await el.text_content()
                    await self._log("warn", f"[大麦] 未找到目标票档，已选择第一个可用: {text}")
                    return True
            except PlaywrightTimeoutError:
                continue

        return False

    async def _set_ticket_count(self, count: int) -> bool:
        """设置购票数量（通过 + / - 按钮）。"""
        try:
            # 先尝试定位数量输入框
            count_input_selectors = [
                ".number-picker input",
                "input[type='number']",
                ".count-input",
                ".ticket-count-input",
            ]
            for selector in count_input_selectors:
                try:
                    inp = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if inp:
                        await inp.fill(str(count))
                        await self._log("info", f"[大麦] 已设置购票数量: {count}")
                        return True
                except PlaywrightTimeoutError:
                    continue

            # 尝试点击 + 按钮增加数量
            plus_btn_selectors = [
                ".number-picker .plus",
                ".plus-btn",
                ".count-plus",
                "button:has-text('+')",
            ]
            for selector in plus_btn_selectors:
                try:
                    btn = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if btn:
                        for _ in range(count - 1):
                            await self._random_delay()
                            await btn.click()
                        await self._log("info", f"[大麦] 通过+按钮设置购票数量: {count}")
                        return True
                except PlaywrightTimeoutError:
                    continue

        except Exception as e:
            await self._log("warn", f"[大麦] 设置购票数量异常: {e}")
        return False

    async def _select_buyers(self, buyers: list[str]) -> bool:
        """选择观演人（按姓名匹配）。

        大麦订单确认页通常有观演人选择列表。
        """
        try:
            # 等待观演人列表加载
            buyer_list_selectors = [
                ".buyer-list",
                ".viewer-list",
                ".contact-list",
                ".dm-buyer-list",
            ]
            list_found = False
            for selector in buyer_list_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    list_found = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not list_found:
                await self._log("warn", "[大麦] 未找到观演人选择列表，可能页面结构不同")
                return False

            # 遍历需要选择的观演人
            for buyer_name in buyers:
                buyer_selectors = [
                    f".buyer-item:has-text('{buyer_name}')",
                    f".viewer-item:has-text('{buyer_name}')",
                    f".contact-item:has-text('{buyer_name}')",
                    f"label:has-text('{buyer_name}')",
                    f"div:has-text('{buyer_name}'):near(.buyer-list)",
                ]
                selected = False
                for selector in buyer_selectors:
                    try:
                        el = await self.page.wait_for_selector(
                            selector, timeout=3000, state="visible"
                        )
                        if el:
                            # 检查是否已选中（复选框）
                            checkbox = await el.query_selector("input[type='checkbox']")
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                if not is_checked:
                                    await el.click()
                            else:
                                await el.click()
                            await self._random_delay()
                            await self._log("info", f"[大麦] 已选择观演人: {buyer_name}")
                            selected = True
                            break
                    except PlaywrightTimeoutError:
                        continue
                if not selected:
                    await self._log("warn", f"[大麦] 未找到观演人: {buyer_name}")

            return True

        except Exception as e:
            await self._log("warn", f"[大麦] 选择观演人异常: {e}")
            return False

    async def _submit_order(self) -> bool:
        """提交订单并判断是否成功进入支付/确认页面。

        成功标志：URL 中包含 pay/confirm/order，或页面出现支付相关元素。
        """
        submit_btn_selectors = [
            ".submit-btn",
            ".dm-btn-submit",
            "button:has-text('提交订单')",
            "button:has-text('确认订单')",
            "button:has-text('下一步')",
            ".next-btn",
            "a:has-text('提交订单')",
            "[data-spm='dsubmit']",
        ]
        for selector in submit_btn_selectors:
            try:
                btn = await self.page.wait_for_selector(
                    selector, timeout=8000, state="visible"
                )
                if btn:
                    await self._random_delay()
                    await btn.click()
                    await self._log("info", "[大麦] 已点击提交订单按钮")
                    break
            except PlaywrightTimeoutError:
                continue
        else:
            await self._log("error", "[大麦] 未找到提交订单按钮")
            return False

        # 等待页面跳转，判断成功标志
        await asyncio.sleep(2)
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
        except PlaywrightTimeoutError:
            pass

        current_url = self.page.url
        success_indicators = ["pay", "confirm", "order", "payment", "收银台"]
        if any(kw in current_url.lower() for kw in success_indicators):
            await self._log("success", f"[大麦] URL检测到成功跳转: {current_url}")
            return True

        # 备选：检查页面内容
        page_text = await self.page.content()
        page_success_keywords = [
            "支付",
            "收银台",
            "订单确认",
            "订单提交成功",
            "请在",
            "分钟内完成支付",
        ]
        for kw in page_success_keywords:
            if kw in page_text:
                await self._log("success", f"[大麦] 页面内容检测到成功关键词: {kw}")
                return True

        # 检查是否有错误提示
        error_keywords = ["库存不足", "已售罄", "秒杀失败", "系统繁忙", "请重试"]
        for kw in error_keywords:
            if kw in page_text:
                await self._log("error", f"[大麦] 检测到错误提示: {kw}")
                return False

        await self._log("warn", "[大麦] 无法确认订单状态，URL未跳转到支付页")
        return False
