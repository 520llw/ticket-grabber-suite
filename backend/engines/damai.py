"""大麦网抢票引擎 v2.0 — 完整抢票流程。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
import asyncio
import random
from typing import Optional, Callable, Awaitable
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from engines.base import BaseEngine
from core.models import TaskConfig

PAGE_TIMEOUT = 30000
ACTION_TIMEOUT = 10000


class DamaiEngine(BaseEngine):
    """大麦网抢票引擎。

    流程：登录 → 商品详情 → 选日期场次 → 选票档 → 选数量 → 选观演人 → 提交订单
    """

    def __init__(
        self,
        headless: bool = True,
        log_callback: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        super().__init__(headless=headless, log_callback=log_callback)
        self.platform_name = "damai"

    # ── 登录 ──────────────────────────────────────────

    async def login(self) -> bool:
        await self._log("info", "[大麦] 打开登录页面...")
        try:
            await self.page.goto(
                "https://www.damai.cn/",
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()

            # 检查是否已登录
            logged_in_selectors = [
                ".user-name", ".dm-header-user-name",
                "[data-spm='duserinfo']", ".header-user-avatar",
            ]
            for sel in logged_in_selectors:
                try:
                    await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                    await self._log("info", "[大麦] 已检测到登录状态")
                    return True
                except PlaywrightTimeoutError:
                    continue

            # 点击登录入口
            await self._log("info", "[大麦] 未登录，请在浏览器中完成登录...")
            login_selectors = [
                ".login-text", "a[href*='login']",
                ".dm-header-login", "[data-spm='dlogin']",
            ]
            await self.safe_click(login_selectors, timeout=3000, desc="登录入口")

            # 等待用户手动登录（最多180秒）
            await self._log("info", "[大麦] 等待用户手动登录（最多180秒）...")
            for attempt in range(90):
                await asyncio.sleep(2)
                for sel in logged_in_selectors:
                    try:
                        await self.page.wait_for_selector(sel, timeout=2000, state="visible")
                        await self._log("success", "[大麦] 登录成功！")
                        return True
                    except PlaywrightTimeoutError:
                        continue
                if attempt % 15 == 0 and attempt > 0:
                    await self._log("info", f"[大麦] 仍在等待登录... ({attempt * 2}秒)")

            await self._log("warn", "[大麦] 登录等待超时")
            return False

        except Exception as e:
            await self._log("error", f"[大麦] 登录异常: {e}")
            return False

    # ── 库存检查 ──────────────────────────────────────

    async def check_stock(self, task: TaskConfig) -> bool:
        out_of_stock = ["缺货登记", "已售罄", "暂时缺货", "已售完", "暂无票", "售磬", "暂不可售"]
        try:
            page_text = await self.page.content()
            for kw in out_of_stock:
                if kw in page_text:
                    await self._log("warn", f"[大麦] 检测到缺货: {kw}")
                    return False
        except Exception:
            pass
        return True

    # ── 抢票主流程 ────────────────────────────────────

    async def grab(self, task: TaskConfig) -> bool:
        await self._log("info", f"[大麦] 开始抢票: {task.name}")
        await self._log("info", f"[大麦] 目标: {task.url}")

        # 1. 登录
        logged_in = await self.login()
        if not logged_in:
            await self._log("warn", "[大麦] 未登录，继续尝试...")

        try:
            # 2. 打开详情页
            await self._log("info", "[大麦] 打开演出详情页...")
            await self.page.goto(task.url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            await self._random_delay()
            await self.page.wait_for_load_state("networkidle")

            # 3. 检查库存
            if not await self.check_stock(task):
                await self._log("error", "[大麦] 当前已售罄")
                return False

            # 4. 点击购买
            await self._log("info", "[大麦] 点击购买按钮...")
            buy_selectors = [
                ".buybtn", ".perform__order__btn", ".dm-btn-buy",
                "[data-spm='dbuy']", ".btn-buy",
                "button:has-text('立即购买')", "button:has-text('选座购买')",
                "button:has-text('购买')", "a:has-text('立即购买')",
                "a:has-text('购买')", "button:has-text('立即预订')",
                "button:has-text('确定')",
            ]
            if not await self.safe_click(buy_selectors, timeout=8000, desc="购买按钮"):
                await self.screenshot("no_buy_btn")
                return False

            await self._random_delay()
            await self.page.wait_for_load_state("domcontentloaded")

            # 5. 选择日期场次
            if task.date or task.session:
                await self._log("info", f"[大麦] 选择日期/场次: {task.date} {task.session}")
                await self._select_date_session(task.date, task.session)

            # 6. 选择票档
            if task.price:
                await self._log("info", f"[大麦] 选择票档: {task.price}")
                await self._select_price(task.price)

            # 7. 设置数量
            if task.ticket_count > 1:
                await self._log("info", f"[大麦] 设置数量: {task.ticket_count}")
                await self._set_ticket_count(task.ticket_count)

            # 8. 选择观演人
            if task.buyers:
                await self._log("info", f"[大麦] 选择观演人: {', '.join(task.buyers)}")
                await self._select_buyers(task.buyers)

            # 9. 提交订单
            await self._log("info", "[大麦] 提交订单...")
            if await self._submit_order():
                await self._log("success", "[大麦] 订单提交成功！")
                await self.screenshot("success")
                return True
            else:
                await self.screenshot("submit_failed")
                return False

        except Exception as e:
            await self._log("error", f"[大麦] 抢票异常: {e}")
            await self.screenshot("error")
            return False

    # ── 辅助方法 ──────────────────────────────────────

    async def _select_date_session(self, target_date: str, target_session: str) -> bool:
        try:
            await self.page.wait_for_selector(
                ".select_right, .session-list, .date-list, .sku-list, .perform__order__select",
                timeout=8000,
            )
        except PlaywrightTimeoutError:
            await self._log("warn", "[大麦] 未弹出选择面板，可能已默认选中")
            return True

        # 选日期
        if target_date:
            date_sels = [
                f".date-list-item:has-text('{target_date}')",
                f".session-item:has-text('{target_date}')",
                f".select_right_item:has-text('{target_date}')",
                f"[data-date*='{target_date}']",
                f".perform__order__select__item:has-text('{target_date}')",
            ]
            await self.safe_click(date_sels, timeout=3000, desc=f"日期 {target_date}")
            await self._random_delay(0.3, 0.8)

        # 选场次
        if target_session:
            session_sels = [
                f".session-item:has-text('{target_session}')",
                f".select_right_item:has-text('{target_session}')",
                f".perform__info__time:has-text('{target_session}')",
                f".perform__order__select__item:has-text('{target_session}')",
            ]
            await self.safe_click(session_sels, timeout=3000, desc=f"场次 {target_session}")

        return True

    async def _select_price(self, target_price: str) -> bool:
        price_sels = [
            f".price-item:has-text('{target_price}')",
            f".sku-name:has-text('{target_price}')",
            f".select_left_item:has-text('{target_price}')",
            f".ticket-item:has-text('{target_price}')",
            f"div:has-text('¥{target_price}')",
            f"div:has-text('{target_price}元')",
            f"[data-price*='{target_price}']",
            f".perform__order__select__item:has-text('{target_price}')",
        ]
        if await self.safe_click(price_sels, timeout=5000, desc=f"票档 {target_price}"):
            return True

        # 回退：选第一个可用票档
        fallback = [
            ".price-item:not(.disabled):not(.selected)",
            ".sku-name:not(.disabled)",
            ".ticket-item:not(.disabled)",
        ]
        if await self.safe_click(fallback, timeout=3000, desc="第一个可用票档"):
            return True

        return False

    async def _set_ticket_count(self, count: int) -> bool:
        # 尝试直接输入
        input_sels = [".number-picker input", "input[type='number']", ".count-input"]
        for sel in input_sels:
            try:
                inp = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if inp:
                    await inp.fill(str(count))
                    await self._log("info", f"[大麦] 已设置数量: {count}")
                    return True
            except PlaywrightTimeoutError:
                continue

        # 点击 + 按钮
        plus_sels = [".number-picker .plus", ".plus-btn", ".count-plus", "button:has-text('+')"]
        for sel in plus_sels:
            try:
                btn = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if btn:
                    for _ in range(count - 1):
                        await self._random_delay(0.1, 0.3)
                        await btn.click()
                    await self._log("info", f"[大麦] 通过+按钮设置数量: {count}")
                    return True
            except PlaywrightTimeoutError:
                continue

        return False

    async def _select_buyers(self, buyers: list[str]) -> bool:
        try:
            buyer_list_sels = [".buyer-list", ".viewer-list", ".contact-list", ".dm-buyer-list"]
            list_found = False
            for sel in buyer_list_sels:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    list_found = True
                    break
                except PlaywrightTimeoutError:
                    continue

            if not list_found:
                await self._log("warn", "[大麦] 未找到观演人列表")
                return False

            for name in buyers:
                buyer_sels = [
                    f".buyer-item:has-text('{name}')",
                    f".viewer-item:has-text('{name}')",
                    f".contact-item:has-text('{name}')",
                    f"label:has-text('{name}')",
                ]
                clicked = False
                for sel in buyer_sels:
                    try:
                        el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                        if el:
                            checkbox = await el.query_selector("input[type='checkbox']")
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                if not is_checked:
                                    await el.click()
                            else:
                                await el.click()
                            await self._random_delay(0.2, 0.5)
                            await self._log("info", f"[大麦] 已选择观演人: {name}")
                            clicked = True
                            break
                    except PlaywrightTimeoutError:
                        continue
                if not clicked:
                    await self._log("warn", f"[大麦] 未找到观演人: {name}")

            return True
        except Exception as e:
            await self._log("warn", f"[大麦] 选择观演人异常: {e}")
            return False

    async def _submit_order(self) -> bool:
        submit_sels = [
            ".submit-btn", ".dm-btn-submit",
            "button:has-text('提交订单')", "button:has-text('确认订单')",
            "button:has-text('下一步')", ".next-btn",
            "a:has-text('提交订单')", "[data-spm='dsubmit']",
            "button:has-text('立即支付')", "button:has-text('去支付')",
        ]
        if not await self.safe_click(submit_sels, timeout=8000, desc="提交订单按钮"):
            return False

        await asyncio.sleep(2)
        await self.wait_for_navigation()

        # 检查 URL
        url = self.page.url.lower()
        success_urls = ["pay", "confirm", "order", "payment", "cashier"]
        if any(kw in url for kw in success_urls):
            await self._log("success", f"[大麦] 成功跳转: {self.page.url}")
            return True

        # 检查页面内容
        try:
            content = await self.page.content()
            success_kws = ["支付", "收银台", "订单确认", "订单提交成功", "请在", "分钟内完成支付"]
            for kw in success_kws:
                if kw in content:
                    await self._log("success", f"[大麦] 页面检测到: {kw}")
                    return True

            error_kws = ["库存不足", "已售罄", "秒杀失败", "系统繁忙", "请重试", "下单失败"]
            for kw in error_kws:
                if kw in content:
                    await self._log("error", f"[大麦] 检测到错误: {kw}")
                    return False
        except Exception:
            pass

        await self._log("warn", "[大麦] 无法确认订单状态")
        return False
