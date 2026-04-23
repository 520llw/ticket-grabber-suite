"""猫眼抢票引擎 v2.0 — 完整抢票流程。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
"""
import asyncio
from typing import Optional, Callable, Awaitable
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from engines.base import BaseEngine
from core.models import TaskConfig

PAGE_TIMEOUT = 30000


class MaoyanEngine(BaseEngine):
    """猫眼抢票引擎。"""

    def __init__(
        self,
        headless: bool = True,
        log_callback: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        super().__init__(headless=headless, log_callback=log_callback)
        self.platform_name = "maoyan"

    async def login(self) -> bool:
        await self._log("info", "[猫眼] 打开首页...")
        try:
            await self.page.goto("https://www.maoyan.com/", timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            await self._random_delay()

            logged_in_sels = [".header-user-name", ".user-name", ".header-avatar", "[class*='user-info']"]
            for sel in logged_in_sels:
                try:
                    await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                    await self._log("info", "[猫眼] 已登录")
                    return True
                except PlaywrightTimeoutError:
                    continue

            await self._log("info", "[猫眼] 未登录，请在浏览器中完成登录...")
            await self.safe_click([".header-login", "a:has-text('登录')", ".login-btn"], timeout=3000, desc="登录入口")

            await self._log("info", "[猫眼] 等待用户手动登录（最多180秒）...")
            for attempt in range(90):
                await asyncio.sleep(2)
                for sel in logged_in_sels:
                    try:
                        await self.page.wait_for_selector(sel, timeout=2000, state="visible")
                        await self._log("success", "[猫眼] 登录成功！")
                        return True
                    except PlaywrightTimeoutError:
                        continue
                if attempt % 15 == 0 and attempt > 0:
                    await self._log("info", f"[猫眼] 仍在等待登录... ({attempt * 2}秒)")

            await self._log("warn", "[猫眼] 登录等待超时")
            return False
        except Exception as e:
            await self._log("error", f"[猫眼] 登录异常: {e}")
            return False

    async def check_stock(self, task: TaskConfig) -> bool:
        out_of_stock = ["已售罄", "暂时缺货", "已售完", "暂无票", "缺货", "售罄"]
        try:
            content = await self.page.content()
            for kw in out_of_stock:
                if kw in content:
                    await self._log("warn", f"[猫眼] 检测到缺货: {kw}")
                    return False
        except Exception:
            pass
        return True

    async def grab(self, task: TaskConfig) -> bool:
        await self._log("info", f"[猫眼] 开始抢票: {task.name}")

        logged_in = await self.login()
        if not logged_in:
            await self._log("warn", "[猫眼] 未登录，继续尝试...")

        try:
            await self._log("info", "[猫眼] 打开演出详情页...")
            await self.page.goto(task.url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            await self._random_delay()
            await self.page.wait_for_load_state("networkidle")

            if not await self.check_stock(task):
                return False

            buy_sels = [
                ".buy-btn", ".btn-buy", ".purchase-btn",
                "button:has-text('立即购买')", "button:has-text('购买')",
                "a:has-text('立即购买')", "a:has-text('购买')",
                "button:has-text('立即预订')", "button:has-text('选座购买')",
                ".show-buy-btn", ".show-btn-buy",
            ]
            if not await self.safe_click(buy_sels, timeout=8000, desc="购买按钮"):
                await self.screenshot("no_buy_btn")
                return False

            await self._random_delay()
            await self.page.wait_for_load_state("domcontentloaded")

            if task.date or task.session:
                await self._select_session(task.date, task.session)
            if task.price:
                await self._select_price(task.price)
            if task.ticket_count > 1:
                await self._set_ticket_count(task.ticket_count)
            if task.buyers:
                await self._select_buyers(task.buyers)

            if await self._submit_order():
                await self._log("success", "[猫眼] 订单提交成功！")
                await self.screenshot("success")
                return True
            else:
                await self.screenshot("submit_failed")
                return False

        except Exception as e:
            await self._log("error", f"[猫眼] 抢票异常: {e}")
            await self.screenshot("error")
            return False

    async def _select_session(self, target_date: str, target_session: str) -> bool:
        try:
            await self.page.wait_for_selector(
                ".session-list, .date-list, .show-session, .show-list, .schedule-list",
                timeout=8000,
            )
        except PlaywrightTimeoutError:
            await self._log("warn", "[猫眼] 未弹出选择面板")
            return True

        if target_date:
            date_sels = [
                f".date-item:has-text('{target_date}')",
                f".schedule-date:has-text('{target_date}')",
                f".time-item:has-text('{target_date}')",
                f"[data-date*='{target_date}']",
            ]
            await self.safe_click(date_sels, timeout=3000, desc=f"日期 {target_date}")
            await self._random_delay(0.3, 0.8)

        if target_session:
            session_sels = [
                f".session-item:has-text('{target_session}')",
                f".show-time:has-text('{target_session}')",
                f".schedule-item:has-text('{target_session}')",
            ]
            await self.safe_click(session_sels, timeout=3000, desc=f"场次 {target_session}")
        return True

    async def _select_price(self, target_price: str) -> bool:
        price_sels = [
            f".price-item:has-text('{target_price}')",
            f".ticket-type:has-text('{target_price}')",
            f"div:has-text('¥{target_price}')",
            f"div:has-text('{target_price}元')",
            f".seat-price:has-text('{target_price}')",
        ]
        if await self.safe_click(price_sels, timeout=5000, desc=f"票档 {target_price}"):
            return True
        fallback = [".price-item:not(.disabled)", ".ticket-type:not(.disabled)"]
        return await self.safe_click(fallback, timeout=3000, desc="第一个可用票档")

    async def _set_ticket_count(self, count: int) -> bool:
        input_sels = [".num-input", "input[type='number']", ".count-input"]
        for sel in input_sels:
            try:
                inp = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if inp:
                    await inp.fill(str(count))
                    return True
            except PlaywrightTimeoutError:
                continue

        plus_sels = [".num-plus", ".count-plus", "button:has-text('+')"]
        for sel in plus_sels:
            try:
                btn = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if btn:
                    for _ in range(count - 1):
                        await self._random_delay(0.1, 0.3)
                        await btn.click()
                    return True
            except PlaywrightTimeoutError:
                continue
        return False

    async def _select_buyers(self, buyers: list[str]) -> bool:
        try:
            for sel in [".buyer-list", ".viewer-list", ".contact-list", ".ticket-buyer-list"]:
                try:
                    await self.page.wait_for_selector(sel, timeout=5000)
                    break
                except PlaywrightTimeoutError:
                    continue

            for name in buyers:
                buyer_sels = [
                    f".buyer-item:has-text('{name}')",
                    f".contact-item:has-text('{name}')",
                    f"label:has-text('{name}')",
                ]
                clicked = False
                for sel in buyer_sels:
                    try:
                        el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                        if el:
                            checkbox = await el.query_selector("input[type='checkbox']")
                            if checkbox and not await checkbox.is_checked():
                                await el.click()
                            elif not checkbox:
                                await el.click()
                            await self._random_delay(0.2, 0.5)
                            await self._log("info", f"[猫眼] 已选择观演人: {name}")
                            clicked = True
                            break
                    except PlaywrightTimeoutError:
                        continue
                if not clicked:
                    await self._log("warn", f"[猫眼] 未找到观演人: {name}")
            return True
        except Exception as e:
            await self._log("warn", f"[猫眼] 选择观演人异常: {e}")
            return False

    async def _submit_order(self) -> bool:
        submit_sels = [
            ".submit-btn", "button:has-text('提交订单')",
            "button:has-text('确认订单')", "button:has-text('去支付')",
            ".order-submit", ".pay-btn",
        ]
        if not await self.safe_click(submit_sels, timeout=8000, desc="提交订单按钮"):
            return False

        await asyncio.sleep(2)
        await self.wait_for_navigation()

        url = self.page.url.lower()
        if any(kw in url for kw in ["pay", "confirm", "order", "payment", "cashier"]):
            return True

        try:
            content = await self.page.content()
            for kw in ["支付", "收银台", "订单确认", "订单提交成功"]:
                if kw in content:
                    return True
            for kw in ["库存不足", "已售罄", "系统繁忙"]:
                if kw in content:
                    await self._log("error", f"[猫眼] 错误: {kw}")
                    return False
        except Exception:
            pass

        await self._log("warn", "[猫眼] 无法确认订单状态")
        return False
