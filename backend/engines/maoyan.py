"""猫眼抢票引擎实现。

猫眼演出页面结构与大麦不同，需要适配猫眼的DOM选择器。
流程：打开演出页 → 立即购买 → 选择场次/日期 → 选择票档 → 确认购票人 → 提交订单

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
import asyncio
import random
from typing import Optional, Callable
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from engines.base import BaseEngine
from core.models import TaskConfig

PAGE_TIMEOUT = 30000
ACTION_TIMEOUT = 10000


class MaoyanEngine(BaseEngine):
    """猫眼抢票引擎。

    猫眼演出通常通过 maoyan.com/films/ 或 maoyan.com/shows/ 页面进行购票。
    支持剧场演出和电影两种模式。
    """

    def __init__(
        self,
        headless: bool = False,
        log_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        super().__init__(headless=headless)
        self.log_callback = log_callback
        self.platform_name = "maoyan"

    async def _log(self, level: str, message: str):
        """通过回调记录日志。"""
        if self.log_callback:
            await self.log_callback(level, message)

    async def _random_delay(self):
        """随机延迟防检测。"""
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

    async def login(self) -> bool:
        """打开猫眼登录页，等待用户手动登录。

        猫眼支持手机号登录和第三方登录。
        """
        await self._log("info", "[猫眼] 打开猫眼页面...")
        try:
            await self.page.goto(
                "https://www.maoyan.com/",
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()

            # 检查是否已登录
            logged_in_selectors = [
                ".user-name",
                ".header-user-name",
                ".avatar",
                ".user-info",
            ]
            for selector in logged_in_selectors:
                try:
                    await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    await self._log("info", "[猫眼] 检测到已登录状态")
                    return True
                except PlaywrightTimeoutError:
                    continue

            # 未登录，提示用户手动操作
            await self._log("info", "[猫眼] 未登录，请用户在浏览器中完成登录...")
            login_btn_selectors = [
                ".login",
                "a[href*='login']",
                ".header-login",
                "[data-login]",
            ]
            for selector in login_btn_selectors:
                try:
                    btn = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if btn:
                        await btn.click()
                        await self._log("info", f"[猫眼] 已点击登录入口: {selector}")
                        break
                except PlaywrightTimeoutError:
                    continue

            # 等待登录（最多120秒）
            await self._log("info", "[猫眼] 等待用户手动登录（最多120秒）...")
            for attempt in range(60):
                await asyncio.sleep(2)
                for selector in logged_in_selectors:
                    try:
                        await self.page.wait_for_selector(
                            selector, timeout=2000, state="visible"
                        )
                        await self._log("success", "[猫眼] 用户登录成功")
                        return True
                    except PlaywrightTimeoutError:
                        continue
                if attempt % 10 == 0:
                    await self._log("info", "[猫眼] 仍在等待登录...")

            await self._log("warn", "[猫眼] 登录等待超时")
            return False

        except Exception as e:
            await self._log("error", f"[猫眼] 登录流程异常: {e}")
            return False

    async def check_stock(self, task: TaskConfig) -> bool:
        """检查猫眼页面是否缺货。"""
        out_of_stock_keywords = [
            "缺货登记",
            "已售罄",
            "暂时缺货",
            "已售完",
            "暂无票",
            "售磬",
            "售罄",
        ]
        page_text = await self.page.content()
        for keyword in out_of_stock_keywords:
            if keyword in page_text:
                await self._log("warn", f"[猫眼] 检测到缺货关键词: {keyword}")
                return False
        return True

    async def grab(self, task: TaskConfig) -> bool:
        """执行猫眼抢票流程。"""
        await self._log("info", f"[猫眼] 开始抢票任务: {task.name}")
        await self._log("info", f"[猫眼] 目标URL: {task.url}")

        logged_in = await self.login()
        if not logged_in:
            await self._log("warn", "[猫眼] 未登录，但继续尝试抢票...")

        try:
            # 打开目标演出页
            await self._log("info", "[猫眼] 打开演出详情页...")
            await self.page.goto(
                task.url,
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()
            await self.page.wait_for_load_state("networkidle")

            # 检查库存
            has_stock = await self.check_stock(task)
            if not has_stock:
                await self._log("error", "[猫眼] 当前商品已售罄")
                return False

            # 点击购买按钮
            await self._log("info", "[猫眼] 寻找并点击购买按钮...")
            buy_btn_selectors = [
                "button:has-text('立即购买')",
                "button:has-text('选座购买')",
                "button:has-text('特惠选座')",
                "a:has-text('立即购买')",
                ".buy-btn",
                ".purchase-btn",
                ".show-btn-buy",
                "[data-click-name='buy']",
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
                        await self._log("info", f"[猫眼] 已点击购买按钮: {selector}")
                        buy_clicked = True
                        break
                except PlaywrightTimeoutError:
                    continue
            if not buy_clicked:
                await self._log("error", "[猫眼] 未找到购买按钮")
                return False

            await self._random_delay()
            await self.page.wait_for_load_state("domcontentloaded")

            # 选择场次/日期
            await self._log("info", f"[猫眼] 选择场次: {task.date} {task.session}")
            await self._select_session(task.date, task.session)

            # 选择票档
            await self._log("info", f"[猫眼] 选择票档: {task.price}")
            await self._select_price(task.price)

            # 选择数量
            if task.ticket_count > 1:
                await self._log("info", f"[猫眼] 设置购票数量: {task.ticket_count}")
                await self._set_ticket_count(task.ticket_count)

            # 确认购票人
            if task.buyers:
                await self._log("info", f"[猫眼] 选择购票人: {task.buyers}")
                await self._select_buyers(task.buyers)

            # 提交订单
            await self._log("info", "[猫眼] 准备提交订单...")
            success = await self._submit_order()
            if success:
                await self._log("success", "[猫眼] 订单提交成功！")
                return True
            else:
                await self._log("error", "[猫眼] 订单提交失败")
                return False

        except Exception as e:
            await self._log("error", f"[猫眼] 抢票流程异常: {e}")
            return False

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _select_session(self, target_date: str, target_session: str) -> bool:
        """选择日期和场次。猫眼通常在同一面板中展示日期和场次。"""
        try:
            # 等待场次选择面板
            await self.page.wait_for_selector(
                ".show-list, .schedule-list, .session-list, .date-list",
                timeout=8000,
            )
        except PlaywrightTimeoutError:
            await self._log("warn", "[猫眼] 未弹出场次选择面板")
            return True

        # 先选择日期
        date_selectors = [
            f".date-item:has-text('{target_date}')",
            f".schedule-date:has-text('{target_date}')",
            f".time-item:has-text('{target_date}')",
            f"[data-date*='{target_date}']",
        ]
        for selector in date_selectors:
            try:
                el = await self.page.wait_for_selector(
                    selector, timeout=3000, state="visible"
                )
                if el:
                    await el.click()
                    await self._random_delay()
                    await self._log("info", f"[猫眼] 已选择日期: {target_date}")
                    break
            except PlaywrightTimeoutError:
                continue

        # 选择场次
        session_selectors = [
            f".session-item:has-text('{target_session}')",
            f".show-time:has-text('{target_session}')",
            f".time-session:has-text('{target_session}')",
            f".schedule-item:has-text('{target_session}')",
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
                    await self._log("info", f"[猫眼] 已选择场次: {target_session}")
                    return True
            except PlaywrightTimeoutError:
                continue

        return False

    async def _select_price(self, target_price: str) -> bool:
        """选择票档价格。"""
        price_selectors = [
            f".price-item:has-text('{target_price}')",
            f".ticket-type:has-text('{target_price}')",
            f".price-tag:has-text('{target_price}')",
            f"div:has-text('¥{target_price}')",
            f"div:has-text('{target_price}元')",
            f".seat-price:has-text('{target_price}')",
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
                    await self._log("info", f"[猫眼] 已选择票档: {target_price}")
                    return True
            except PlaywrightTimeoutError:
                continue

        # 备选：选第一个可用的
        fallback_selectors = [
            ".price-item:not(.disabled):not(.selected)",
            ".ticket-type:not(.disabled)",
            ".seat-price:not(.disabled)",
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
                    await self._log("warn", f"[猫眼] 未找到目标票档，已选择第一个可用: {text}")
                    return True
            except PlaywrightTimeoutError:
                continue

        return False

    async def _set_ticket_count(self, count: int) -> bool:
        """设置购票数量。"""
        try:
            # 尝试 + 按钮
            plus_selectors = [
                ".num-plus",
                ".count-plus",
                ".add-btn",
                "button:has-text('+')",
            ]
            for selector in plus_selectors:
                try:
                    btn = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if btn:
                        for _ in range(count - 1):
                            await self._random_delay()
                            await btn.click()
                        await self._log("info", f"[猫眼] 已设置购票数量: {count}")
                        return True
                except PlaywrightTimeoutError:
                    continue

            # 尝试输入框
            input_selectors = [
                ".num-input",
                "input[type='number']",
                ".ticket-count",
            ]
            for selector in input_selectors:
                try:
                    inp = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if inp:
                        await inp.fill(str(count))
                        await self._log("info", f"[猫眼] 已设置购票数量: {count}")
                        return True
                except PlaywrightTimeoutError:
                    continue

        except Exception as e:
            await self._log("warn", f"[猫眼] 设置购票数量异常: {e}")
        return False

    async def _select_buyers(self, buyers: list[str]) -> bool:
        """选择购票人。"""
        try:
            buyer_list_selectors = [
                ".buyer-list",
                ".viewer-list",
                ".contact-list",
                ".ticket-buyer-list",
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
                await self._log("warn", "[猫眼] 未找到购票人选择列表")
                return False

            for buyer_name in buyers:
                buyer_selectors = [
                    f".buyer-item:has-text('{buyer_name}')",
                    f".viewer-item:has-text('{buyer_name}')",
                    f".contact-item:has-text('{buyer_name}')",
                    f"label:has-text('{buyer_name}')",
                ]
                selected = False
                for selector in buyer_selectors:
                    try:
                        el = await self.page.wait_for_selector(
                            selector, timeout=3000, state="visible"
                        )
                        if el:
                            checkbox = await el.query_selector("input[type='checkbox']")
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                if not is_checked:
                                    await el.click()
                            else:
                                await el.click()
                            await self._random_delay()
                            await self._log("info", f"[猫眼] 已选择购票人: {buyer_name}")
                            selected = True
                            break
                    except PlaywrightTimeoutError:
                        continue
                if not selected:
                    await self._log("warn", f"[猫眼] 未找到购票人: {buyer_name}")

            return True

        except Exception as e:
            await self._log("warn", f"[猫眼] 选择购票人异常: {e}")
            return False

    async def _submit_order(self) -> bool:
        """提交订单并判断是否成功。"""
        submit_selectors = [
            "button:has-text('提交订单')",
            "button:has-text('确认支付')",
            "button:has-text('去支付')",
            "button:has-text('下一步')",
            ".submit-btn",
            ".pay-btn",
            ".order-submit",
        ]
        for selector in submit_selectors:
            try:
                btn = await self.page.wait_for_selector(
                    selector, timeout=8000, state="visible"
                )
                if btn:
                    await self._random_delay()
                    await btn.click()
                    await self._log("info", "[猫眼] 已点击提交订单")
                    break
            except PlaywrightTimeoutError:
                continue
        else:
            await self._log("error", "[猫眼] 未找到提交订单按钮")
            return False

        await asyncio.sleep(2)
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
        except PlaywrightTimeoutError:
            pass

        current_url = self.page.url
        success_url_keywords = ["pay", "confirm", "order", "payment", "收银台"]
        if any(kw in current_url.lower() for kw in success_url_keywords):
            await self._log("success", f"[猫眼] URL检测到成功: {current_url}")
            return True

        page_text = await self.page.content()
        success_keywords = [
            "支付",
            "收银台",
            "订单确认",
            "订单提交成功",
            "请在",
            "分钟内完成",
        ]
        for kw in success_keywords:
            if kw in page_text:
                await self._log("success", f"[猫眼] 页面内容检测到成功: {kw}")
                return True

        error_keywords = ["库存不足", "已售罄", "秒杀失败", "系统繁忙", "请重试", "失败"]
        for kw in error_keywords:
            if kw in page_text:
                await self._log("error", f"[猫眼] 检测到错误: {kw}")
                return False

        await self._log("warn", "[猫眼] 无法确认订单状态")
        return False
