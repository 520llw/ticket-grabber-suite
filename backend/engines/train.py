"""12306 铁路抢票引擎 v2.0 — 完整抢票流程。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
"""
import asyncio
from typing import Optional, Callable, Awaitable
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from engines.base import BaseEngine
from core.models import TaskConfig

PAGE_TIMEOUT = 30000


class Train12306Engine(BaseEngine):
    """12306 铁路抢票引擎。

    流程：登录 → 余票查询 → 填写出发/到达/日期 → 查询 → 选车次 → 选乘车人 → 选席别 → 提交
    """

    def __init__(
        self,
        headless: bool = True,
        log_callback: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        super().__init__(headless=headless, log_callback=log_callback)
        self.platform_name = "12306"

    # ── 登录 ──────────────────────────────────────────

    async def login(self) -> bool:
        await self._log("info", "[12306] 打开登录页面...")
        try:
            await self.page.goto(
                "https://kyfw.12306.cn/otn/resources/login.html",
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()

            # 检查是否已登录
            logged_in_sels = [
                ".welcome-name", "#J-userName",
                ".login-hd-account", "[class*='user-name']",
            ]
            for sel in logged_in_sels:
                try:
                    await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                    await self._log("info", "[12306] 已登录")
                    return True
                except PlaywrightTimeoutError:
                    continue

            # 尝试点击账号登录
            await self._log("info", "[12306] 未登录，请在浏览器中完成登录...")
            login_sels = [
                "a:has-text('账号登录')", ".login-hd-code a",
                "#J-login", "a:has-text('登录')",
            ]
            await self.safe_click(login_sels, timeout=3000, desc="登录入口")

            # 等待用户手动登录（最多180秒）
            await self._log("info", "[12306] 等待用户手动登录（最多180秒）...")
            for attempt in range(90):
                await asyncio.sleep(2)
                # 检查 URL 是否跳转到已登录页面
                if "init" in self.page.url or "index" in self.page.url:
                    await self._log("success", "[12306] 登录成功！")
                    return True
                for sel in logged_in_sels:
                    try:
                        await self.page.wait_for_selector(sel, timeout=2000, state="visible")
                        await self._log("success", "[12306] 登录成功！")
                        return True
                    except PlaywrightTimeoutError:
                        continue
                if attempt % 15 == 0 and attempt > 0:
                    await self._log("info", f"[12306] 仍在等待登录... ({attempt * 2}秒)")

            await self._log("warn", "[12306] 登录等待超时")
            return False

        except Exception as e:
            await self._log("error", f"[12306] 登录异常: {e}")
            return False

    # ── 库存检查 ──────────────────────────────────────

    async def check_stock(self, task: TaskConfig) -> bool:
        try:
            content = await self.page.content()
            for kw in ["无票", "候补", "暂无"]:
                if kw in content:
                    await self._log("warn", f"[12306] 检测到: {kw}")
                    return False
        except Exception:
            pass
        return True

    # ── 抢票主流程 ────────────────────────────────────

    async def grab(self, task: TaskConfig) -> bool:
        await self._log("info", f"[12306] 开始抢票: {task.name}")

        # 解析站点信息
        from_station = task.from_station
        to_station = task.to_station
        train_number = task.train_number
        seat_type = task.seat_type or task.price  # 兼容旧字段

        # 兼容旧的 session 字段格式 "出发站-到达站"
        if not from_station and task.session and "-" in task.session:
            parts = task.session.split("-")
            from_station = parts[0].strip()
            to_station = parts[1].strip() if len(parts) > 1 else ""

        if not from_station or not to_station:
            await self._log("error", "[12306] 缺少出发站或到达站信息")
            return False

        await self._log("info", f"[12306] 路线: {from_station} → {to_station}, 日期: {task.date}")
        if train_number:
            await self._log("info", f"[12306] 目标车次: {train_number}")
        if seat_type:
            await self._log("info", f"[12306] 目标席别: {seat_type}")

        # 1. 登录
        logged_in = await self.login()
        if not logged_in:
            await self._log("warn", "[12306] 未登录，继续尝试...")

        try:
            # 2. 打开余票查询页
            await self._log("info", "[12306] 打开余票查询页...")
            await self.page.goto(
                "https://kyfw.12306.cn/otn/leftTicket/init",
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()
            await self.page.wait_for_load_state("networkidle")

            # 3. 填写查询参数
            await self._log("info", "[12306] 填写查询参数...")
            await self._fill_query_params(from_station, to_station, task.date)

            # 4. 点击查询
            await self._log("info", "[12306] 点击查询...")
            query_sels = [
                "#query_ticket", "a:has-text('查询')",
                "button:has-text('查询')", ".btn-query",
            ]
            if not await self.safe_click(query_sels, timeout=5000, desc="查询按钮"):
                await self.screenshot("no_query_btn")
                return False

            await self._random_delay()
            await asyncio.sleep(2)

            # 5. 选择车次并点击预订
            await self._log("info", "[12306] 选择车次...")
            if not await self._select_train(train_number, seat_type):
                await self.screenshot("no_train")
                return False

            await self._random_delay()
            await self.page.wait_for_load_state("domcontentloaded")

            # 6. 处理登录弹窗
            await self._handle_login_popup()

            # 7. 选择乘车人
            if task.buyers:
                await self._log("info", f"[12306] 选择乘车人: {', '.join(task.buyers)}")
                await self._select_passengers(task.buyers)

            # 8. 选择席别
            if seat_type:
                await self._confirm_seat_type(seat_type)

            # 9. 提交订单
            await self._log("info", "[12306] 提交订单...")
            if await self._submit_order():
                await self._log("success", "[12306] 订单提交成功！")
                await self.screenshot("success")
                return True
            else:
                await self.screenshot("submit_failed")
                return False

        except Exception as e:
            await self._log("error", f"[12306] 抢票异常: {e}")
            await self.screenshot("error")
            return False

    # ── 辅助方法 ──────────────────────────────────────

    async def _fill_query_params(self, from_station: str, to_station: str, date: str):
        """填写出发站、到达站、日期。"""
        # 出发站
        from_sels = ["#fromStationText", "#fromStation", "input[id*='from']"]
        for sel in from_sels:
            try:
                el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if el:
                    await el.click()
                    await el.fill("")
                    await el.type(from_station, delay=100)
                    await asyncio.sleep(0.5)
                    # 选择下拉建议
                    try:
                        suggestion = await self.page.wait_for_selector(
                            f".cname:has-text('{from_station}')", timeout=3000
                        )
                        if suggestion:
                            await suggestion.click()
                    except PlaywrightTimeoutError:
                        await self.page.keyboard.press("Enter")
                    await self._log("info", f"[12306] 已填写出发站: {from_station}")
                    break
            except PlaywrightTimeoutError:
                continue

        await self._random_delay(0.3, 0.8)

        # 到达站
        to_sels = ["#toStationText", "#toStation", "input[id*='to']"]
        for sel in to_sels:
            try:
                el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if el:
                    await el.click()
                    await el.fill("")
                    await el.type(to_station, delay=100)
                    await asyncio.sleep(0.5)
                    try:
                        suggestion = await self.page.wait_for_selector(
                            f".cname:has-text('{to_station}')", timeout=3000
                        )
                        if suggestion:
                            await suggestion.click()
                    except PlaywrightTimeoutError:
                        await self.page.keyboard.press("Enter")
                    await self._log("info", f"[12306] 已填写到达站: {to_station}")
                    break
            except PlaywrightTimeoutError:
                continue

        await self._random_delay(0.3, 0.8)

        # 日期
        if date:
            date_sels = ["#train_date", "input[id*='date']"]
            for sel in date_sels:
                try:
                    el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                    if el:
                        await el.click(click_count=3)
                        await el.fill(date)
                        await self.page.keyboard.press("Escape")
                        await self._log("info", f"[12306] 已填写日期: {date}")
                        break
                except PlaywrightTimeoutError:
                    continue

    async def _select_train(self, train_number: str, seat_type: str) -> bool:
        """在查询结果中选择车次并点击预订。"""
        try:
            await self.page.wait_for_selector("#queryLeftTable tr, .train-list", timeout=10000)
        except PlaywrightTimeoutError:
            await self._log("error", "[12306] 未加载到车次列表")
            return False

        await asyncio.sleep(1)

        if train_number:
            # 精确匹配车次号
            train_sels = [
                f"tr:has-text('{train_number}') .btn72, tr:has-text('{train_number}') a:has-text('预订')",
                f"tr:has-text('{train_number}') .no-br a",
                f"a.btn72:near(:text('{train_number}'))",
            ]
            for sel in train_sels:
                try:
                    btn = await self.page.wait_for_selector(sel, timeout=5000, state="visible")
                    if btn:
                        await btn.click()
                        await self._log("info", f"[12306] 已选择车次: {train_number}")
                        return True
                except PlaywrightTimeoutError:
                    continue

        # 回退：选择第一个可预订的车次
        fallback_sels = [
            "#queryLeftTable .btn72", "a:has-text('预订')",
            ".btn72:not(.btn-disabled)",
        ]
        for sel in fallback_sels:
            try:
                btn = await self.page.wait_for_selector(sel, timeout=5000, state="visible")
                if btn:
                    await btn.click()
                    await self._log("warn", "[12306] 未找到目标车次，已选择第一个可预订车次")
                    return True
            except PlaywrightTimeoutError:
                continue

        await self._log("error", "[12306] 无可预订车次")
        return False

    async def _handle_login_popup(self):
        """处理可能弹出的登录确认框。"""
        try:
            confirm_sels = [
                "#login_box a:has-text('确认')",
                ".modal-confirm", "button:has-text('确认')",
            ]
            await self.safe_click(confirm_sels, timeout=3000, desc="登录确认框")
        except Exception:
            pass

    async def _select_passengers(self, passengers: list[str]) -> bool:
        """选择乘车人。"""
        try:
            await self.page.wait_for_selector("#normal_passenger_id, .passenger-list", timeout=8000)
            await asyncio.sleep(1)

            for name in passengers:
                passenger_sels = [
                    f"label:has-text('{name}')",
                    f"#normal_passenger_id li:has-text('{name}')",
                    f".passenger-item:has-text('{name}')",
                ]
                clicked = False
                for sel in passenger_sels:
                    try:
                        el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                        if el:
                            await el.click()
                            await self._random_delay(0.2, 0.5)
                            await self._log("info", f"[12306] 已选择乘车人: {name}")
                            clicked = True
                            break
                    except PlaywrightTimeoutError:
                        continue
                if not clicked:
                    await self._log("warn", f"[12306] 未找到乘车人: {name}")

            return True
        except Exception as e:
            await self._log("warn", f"[12306] 选择乘车人异常: {e}")
            return False

    async def _confirm_seat_type(self, seat_type: str) -> bool:
        """确认席别选择。"""
        seat_sels = [
            f"select option:has-text('{seat_type}')",
            f"[class*='seat']:has-text('{seat_type}')",
        ]
        for sel in seat_sels:
            try:
                el = await self.page.wait_for_selector(sel, timeout=3000, state="visible")
                if el:
                    await el.click()
                    await self._log("info", f"[12306] 已选择席别: {seat_type}")
                    return True
            except PlaywrightTimeoutError:
                continue
        return False

    async def _submit_order(self) -> bool:
        """提交订单。"""
        submit_sels = [
            "#submitOrder_id", "button:has-text('提交订单')",
            "a:has-text('提交订单')", "#submit_order",
        ]
        if not await self.safe_click(submit_sels, timeout=8000, desc="提交订单按钮"):
            return False

        await asyncio.sleep(2)

        # 处理确认弹窗
        confirm_sels = [
            "#qr_submit_id", "button:has-text('确认')",
            "#qr_submit_id a", ".modal-confirm",
        ]
        await self.safe_click(confirm_sels, timeout=5000, desc="确认按钮")

        await asyncio.sleep(3)

        # 检查是否成功
        try:
            content = await self.page.content()
            success_kws = ["订单已提交", "排队等候", "购票成功", "订单号", "支付"]
            for kw in success_kws:
                if kw in content:
                    await self._log("success", f"[12306] 检测到: {kw}")
                    return True

            error_kws = ["出票失败", "系统繁忙", "余票不足", "占座失败"]
            for kw in error_kws:
                if kw in content:
                    await self._log("error", f"[12306] 错误: {kw}")
                    return False
        except Exception:
            pass

        url = self.page.url.lower()
        if any(kw in url for kw in ["order", "pay", "success", "queue"]):
            return True

        await self._log("warn", "[12306] 无法确认订单状态")
        return False
