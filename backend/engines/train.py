"""12306抢票引擎实现。

流程：登录页 → 查询车次 → 选择车次和席别 → 选择乘车人 → 提交订单 → 处理验证码

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。

验证码处理说明：
- 12306有严格的验证码机制（包括图片验证码和滑块验证）
- 本引擎预留验证码接口，实际运行时如遇到验证码需要人工在浏览器中处理
- 未来可集成第三方打码平台（如2Captcha、超级鹰等）
"""
import asyncio
import random
from typing import Optional, Callable
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from engines.base import BaseEngine
from core.models import TaskConfig

PAGE_TIMEOUT = 30000
ACTION_TIMEOUT = 10000


class Train12306Engine(BaseEngine):
    """12306火车票抢票引擎。

    参考 testerSunshine/12306 的设计思路，适配新版 12306 页面结构。

    task.session 格式建议："出发站-到达站" 或仅作为备注使用。
    task.price 用于匹配席别（如 "二等座", "硬卧" 等）。
    """

    def __init__(
        self,
        headless: bool = False,
        log_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        super().__init__(headless=headless)
        self.log_callback = log_callback
        self.platform_name = "12306"

    async def _log(self, level: str, message: str):
        """通过回调记录日志。"""
        if self.log_callback:
            await self.log_callback(level, message)

    async def _random_delay(self):
        """随机延迟防检测。"""
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

    async def login(self) -> bool:
        """打开12306登录页，等待用户完成登录。

        12306支持：账号密码登录、扫码登录、指纹/人脸登录。
        非 headless 模式下推荐扫码登录（最稳定）。
        """
        await self._log("info", "[12306] 打开12306登录页面...")
        try:
            await self.page.goto(
                "https://kyfw.12306.cn/otn/resources/login.html",
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()

            # 检查是否已经登录（登录后通常跳转到个人中心或余票查询页）
            logged_in_url_keywords = ["index", "query", "passport?redirect", "otn/index"]
            current_url = self.page.url
            if any(kw in current_url for kw in logged_in_url_keywords) and "login" not in current_url:
                await self._log("info", "[12306] 检测到已登录状态")
                return True

            # 未登录，提示用户手动扫码/登录
            await self._log("info", "[12306] 未登录，请用户在浏览器中扫码或输入账号密码登录...")
            await self._log("info", "[12306] 建议使用手机12306 APP扫码登录，成功率最高")

            # 等待登录完成（最多180秒，12306扫码可能需要更久）
            await self._log("info", "[12306] 等待登录完成（最多180秒）...")
            for attempt in range(90):
                await asyncio.sleep(2)
                current_url = self.page.url
                if "login" not in current_url and any(
                    kw in current_url for kw in logged_in_url_keywords
                ):
                    await self._log("success", "[12306] 用户登录成功")
                    return True
                if attempt % 15 == 0:
                    await self._log("info", "[12306] 仍在等待登录...")

            await self._log("warn", "[12306] 登录等待超时")
            return False

        except Exception as e:
            await self._log("error", f"[12306] 登录流程异常: {e}")
            return False

    async def check_stock(self, task: TaskConfig) -> bool:
        """检查12306车次是否有余票。

        12306余票查询页面会显示各席别的余票状态，"有" 或数字表示有余票，"--" 表示无此席别，"无" 表示售罄。
        """
        page_text = await self.page.content()
        # 如果是余票查询结果页，检查目标席别
        seat_type = task.price  # 使用 price 字段匹配席别
        
        if "无票" in page_text and "有" not in page_text:
            await self._log("warn", "[12306] 查询结果中无余票")
            return False
        
        # 更精确的判断需要在具体车次行中检查，交给 grab 流程处理
        return True

    async def grab(self, task: TaskConfig) -> bool:
        """执行12306抢票流程。

        Args:
            task: 任务配置
                - task.url: 可以是余票查询页URL，或包含出发/到达/日期的参数
                - task.date: 出发日期 (YYYY-MM-DD)
                - task.session: 建议格式 "出发站-到达站"，如 "北京南-上海虹桥"
                - task.price: 席别名称，如 "二等座", "一等座", "硬卧", "软卧"
                - task.buyers: 乘车人姓名列表
                - task.ticket_count: 购票数量
        """
        await self._log("info", f"[12306] 开始抢票任务: {task.name}")
        await self._log("info", f"[12306] 日期: {task.date}, 席别: {task.price}, 乘车人: {task.buyers}")

        # 1. 登录
        logged_in = await self.login()
        if not logged_in:
            await self._log("warn", "[12306] 未登录，但继续尝试...")

        try:
            # 2. 进入余票查询页面
            await self._log("info", "[12306] 进入余票查询页面...")
            
            # 如果 task.url 提供了直接的查询页URL，使用它；否则构造默认查询页
            query_url = task.url if task.url else "https://kyfw.12306.cn/otn/leftTicket/init"
            await self.page.goto(
                query_url,
                timeout=PAGE_TIMEOUT,
                wait_until="domcontentloaded",
            )
            await self._random_delay()
            await self.page.wait_for_load_state("networkidle")

            # 3. 填写查询条件（出发站、到达站、日期）
            await self._fill_query_params(task)

            # 4. 点击查询按钮并等待结果
            await self._log("info", "[12306] 点击查询按钮...")
            query_clicked = False
            query_btn_selectors = [
                "#query_ticket",
                ".btn-primary",
                "#search_one",
                "button:has-text('查询')",
                "a:has-text('查询')",
            ]
            for selector in query_btn_selectors:
                try:
                    btn = await self.page.wait_for_selector(
                        selector, timeout=5000, state="visible"
                    )
                    if btn:
                        await self._random_delay()
                        await btn.click()
                        await self._log("info", "[12306] 已点击查询")
                        query_clicked = True
                        break
                except PlaywrightTimeoutError:
                    continue

            if not query_clicked:
                await self._log("error", "[12306] 未找到查询按钮")
                return False

            # 等待查询结果加载
            await self._log("info", "[12306] 等待查询结果...")
            await asyncio.sleep(2)
            try:
                await self.page.wait_for_selector(
                    "#queryLeftTable, .ticket-list, .train-list, tbody tr",
                    timeout=15000,
                )
            except PlaywrightTimeoutError:
                await self._log("error", "[12306] 查询结果加载超时")
                return False

            # 5. 选择车次（优先按 task.session 匹配车次号，如 G1, D123 等）
            await self._log("info", f"[12306] 尝试选择车次: {task.session}")
            train_selected = await self._select_train(task.session, task.price)
            if not train_selected:
                await self._log("error", "[12306] 未找到符合条件的车次或席别无票")
                return False

            # 6. 处理登录态确认（预订按钮点击后可能弹出登录框）
            await self._random_delay()
            await asyncio.sleep(1)
            
            # 检查是否有登录弹窗
            login_popup = await self._handle_login_popup()
            if login_popup:
                await self._log("info", "[12306] 处理登录弹窗后，重新尝试预订...")
                # 重新选择车次
                train_selected = await self._select_train(task.session, task.price)
                if not train_selected:
                    return False

            # 7. 进入订单确认页面，选择乘车人
            await self._log("info", "[12306] 进入订单确认页面...")
            await self.page.wait_for_load_state("domcontentloaded", timeout=15000)
            
            # 检查是否进入了乘客选择/订单确认页
            try:
                await self.page.wait_for_selector(
                    "#passengerList, .passenger-list, .order-confirm, #normal_passenger_id",
                    timeout=15000,
                )
            except PlaywrightTimeoutError:
                await self._log("warn", "[12306] 未进入订单确认页，检查页面状态...")
                # 可能是被拦截或需要验证码
                captcha_result = await self._handle_captcha()
                if not captcha_result:
                    await self._log("error", "[12306] 验证码处理失败或被拦截")
                    return False

            # 8. 选择乘车人
            if task.buyers:
                await self._log("info", f"[12306] 选择乘车人: {task.buyers}")
                await self._select_passengers(task.buyers)

            # 9. 选择席别（订单确认页可能再次需要确认）
            if task.price:
                await self._log("info", f"[12306] 确认席别: {task.price}")
                await self._confirm_seat_type(task.price)

            # 10. 提交订单
            await self._log("info", "[12306] 准备提交订单...")
            success = await self._submit_order()
            if success:
                await self._log("success", "[12306] 订单提交成功！请尽快完成支付！")
                return True
            else:
                await self._log("error", "[12306] 订单提交失败")
                return False

        except Exception as e:
            await self._log("error", f"[12306] 抢票流程异常: {e}")
            return False

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _fill_query_params(self, task: TaskConfig) -> bool:
        """填写12306余票查询参数（出发站、到达站、日期）。

        task.session 建议格式: "出发站-到达站"，如 "北京南-上海虹桥"
        """
        try:
            # 解析出发站和到达站
            from_station = ""
            to_station = ""
            if task.session and "-" in task.session:
                parts = task.session.split("-", 1)
                from_station = parts[0].strip()
                to_station = parts[1].strip()
            else:
                # 如果没有提供，尝试从 URL 或其他方式获取，或记录警告
                await self._log("warn", "[12306] task.session 未提供出发-到达站信息，请在任务中设置如 '北京南-上海虹桥'")

            # 填写出发站
            if from_station:
                from_selectors = [
                    "#fromStationText",
                    "input[name='leftTicketDTO.from_station_name']",
                    ".from-station-input",
                ]
                for selector in from_selectors:
                    try:
                        inp = await self.page.wait_for_selector(
                            selector, timeout=5000, state="visible"
                        )
                        if inp:
                            await inp.fill("")
                            await inp.fill(from_station)
                            await self._random_delay()
                            # 12306 输入站名后会弹出下拉选择，尝试点击第一个
                            try:
                                dropdown_item = await self.page.wait_for_selector(
                                    ".city-box .city-item, .panel li, .combobox-item",
                                    timeout=3000,
                                )
                                if dropdown_item:
                                    await dropdown_item.click()
                            except PlaywrightTimeoutError:
                                pass
                            await self._log("info", f"[12306] 已填写出发站: {from_station}")
                            break
                    except PlaywrightTimeoutError:
                        continue

            # 填写到达站
            if to_station:
                to_selectors = [
                    "#toStationText",
                    "input[name='leftTicketDTO.to_station_name']",
                    ".to-station-input",
                ]
                for selector in to_selectors:
                    try:
                        inp = await self.page.wait_for_selector(
                            selector, timeout=5000, state="visible"
                        )
                        if inp:
                            await inp.fill("")
                            await inp.fill(to_station)
                            await self._random_delay()
                            try:
                                dropdown_item = await self.page.wait_for_selector(
                                    ".city-box .city-item, .panel li, .combobox-item",
                                    timeout=3000,
                                )
                                if dropdown_item:
                                    await dropdown_item.click()
                            except PlaywrightTimeoutError:
                                pass
                            await self._log("info", f"[12306] 已填写到达站: {to_station}")
                            break
                    except PlaywrightTimeoutError:
                        continue

            # 填写日期
            if task.date:
                date_selectors = [
                    "#train_date",
                    "input[name='leftTicketDTO.train_date']",
                    ".date-input",
                    "#query_ticket_date",
                ]
                for selector in date_selectors:
                    try:
                        inp = await self.page.wait_for_selector(
                            selector, timeout=5000, state="visible"
                        )
                        if inp:
                            await inp.fill(task.date)
                            await self._random_delay()
                            await self._log("info", f"[12306] 已填写日期: {task.date}")
                            break
                    except PlaywrightTimeoutError:
                        continue

            return True

        except Exception as e:
            await self._log("warn", f"[12306] 填写查询参数异常: {e}")
            return False

    async def _select_train(self, train_code: str, seat_type: str) -> bool:
        """在查询结果中选择指定车次和席别。

        Args:
            train_code: 车次号，如 G1, D123
            seat_type: 席别名称，如 "二等座", "一等座", "硬卧"

        Returns:
            True 如果成功点击了预订按钮。
        """
        try:
            # 等待查询结果表格加载
            await self.page.wait_for_selector(
                "#queryLeftTable tbody tr, .train-item, .ticket-list-item",
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            await self._log("error", "[12306] 查询结果未加载")
            return False

        # 如果指定了车次号，先定位到该车次行
        if train_code:
            train_row_selectors = [
                f"tr:has-text('{train_code}')",
                f".train-item:has-text('{train_code}')",
                f".ticket-list-item:has-text('{train_code}')",
                f"div:has-text('{train_code}'):near(#queryLeftTable)",
            ]
            target_row = None
            for selector in train_row_selectors:
                try:
                    target_row = await self.page.wait_for_selector(
                        selector, timeout=5000, state="visible"
                    )
                    if target_row:
                        await self._log("info", f"[12306] 找到车次: {train_code}")
                        break
                except PlaywrightTimeoutError:
                    continue

            if not target_row:
                await self._log("warn", f"[12306] 未找到车次 {train_code}，将选择第一个有余票的车次")

        # 检查目标席别是否有票，并点击预订按钮
        # 12306 预订按钮通常在每行最后一个 td 中
        book_btn_selectors = [
            f"tr:has-text('{train_code}') .btn72, tr:has-text('{train_code}') .btn130",
            f"tr:has-text('{train_code}') a:has-text('预订')",
            f"tr:has-text('{train_code}') button:has-text('预订')",
            f".train-item:has-text('{train_code}') .book-btn",
            ".btn72",
            ".btn130",
            "a:has-text('预订')",
            "button:has-text('预订')",
        ]

        for selector in book_btn_selectors:
            try:
                btn = await self.page.wait_for_selector(
                    selector, timeout=5000, state="visible"
                )
                if btn:
                    # 检查按钮是否可点击（非灰色/禁用状态）
                    is_disabled = await btn.is_disabled()
                    if is_disabled:
                        await self._log("warn", "[12306] 预订按钮被禁用，该车次可能无票")
                        continue
                    
                    # 检查对应行中是否有目标席别的余票
                    row_text = ""
                    try:
                        row = await btn.evaluate("el => el.closest('tr')?.textContent || el.closest('.train-item')?.textContent || ''")
                        row_text = row or ""
                    except Exception:
                        pass

                    if seat_type and seat_type not in row_text:
                        # 席别可能在行中没有完整名称，尝试简化匹配
                        seat_keywords = {
                            "二等座": ["二等", "2等"],
                            "一等座": ["一等", "1等"],
                            "商务座": ["商务", "商"],
                            "硬座": ["硬座"],
                            "软座": ["软座"],
                            "硬卧": ["硬卧"],
                            "软卧": ["软卧"],
                            "无座": ["无座"],
                            "高级软卧": ["高级软卧"],
                        }
                        matched = False
                        for keyword in seat_keywords.get(seat_type, [seat_type]):
                            if keyword in row_text:
                                matched = True
                                break
                        if not matched and row_text:
                            await self._log("warn", f"[12306] 目标行中未找到席别 '{seat_type}'，但仍尝试预订")

                    await self._random_delay()
                    await btn.click()
                    await self._log("info", f"[12306] 已点击车次 {train_code or '第一个可用车次'} 的预订按钮")
                    return True
            except PlaywrightTimeoutError:
                continue

        await self._log("error", "[12306] 未找到可预订的车次")
        return False

    async def _handle_login_popup(self) -> bool:
        """处理点击预订后弹出的登录窗口。

        12306未登录时点击预订会弹出登录框。
        """
        popup_selectors = [
            ".login-panel",
            ".modal-login",
            "#loginModal",
            ".login-box",
            "#j-login",
        ]
        for selector in popup_selectors:
            try:
                popup = await self.page.wait_for_selector(
                    selector, timeout=5000, state="visible"
                )
                if popup:
                    await self._log("info", "[12306] 检测到登录弹窗，请用户手动完成登录...")
                    # 等待用户完成登录（最多120秒）
                    for attempt in range(60):
                        await asyncio.sleep(2)
                        try:
                            still_visible = await popup.is_visible()
                            if not still_visible:
                                await self._log("info", "[12306] 登录弹窗已关闭")
                                return True
                        except Exception:
                            return True
                        if attempt % 10 == 0:
                            await self._log("info", "[12306] 等待用户完成登录弹窗...")
                    return False
            except PlaywrightTimeoutError:
                continue
        return False

    async def _handle_captcha(self) -> bool:
        """处理12306验证码。

        预留接口：目前遇到验证码时提示用户人工处理。
        未来可集成第三方打码平台实现全自动。

        Returns:
            True 如果验证码处理成功或无需处理。
        """
        captcha_indicators = [
            ".captcha-image",
            "#captcha",
            ".slide-verify",
            ".verify-code",
            "验证码",
            "请点击",
            "滑动验证",
        ]
        
        page_text = await self.page.content()
        has_captcha = any(kw in page_text for kw in captcha_indicators)
        
        if not has_captcha:
            # 检查是否有验证码元素
            for selector in captcha_indicators[:4]:
                try:
                    el = await self.page.wait_for_selector(selector, timeout=3000)
                    if el:
                        has_captcha = True
                        break
                except PlaywrightTimeoutError:
                    continue

        if has_captcha:
            await self._log("warn", "[12306] 检测到验证码/滑块验证，请用户在浏览器中手动处理...")
            await self._log("info", "[12306] 验证码处理中（最多等待120秒）...")
            
            # 等待验证码消失（用户处理完毕）
            for attempt in range(60):
                await asyncio.sleep(2)
                page_text = await self.page.content()
                if not any(kw in page_text for kw in captcha_indicators):
                    await self._log("success", "[12306] 验证码已处理完毕")
                    return True
                if attempt % 10 == 0:
                    await self._log("info", "[12306] 等待验证码处理...")
            
            await self._log("error", "[12306] 验证码处理超时")
            return False

        return True

    async def _select_passengers(self, passengers: list[str]) -> bool:
        """在订单确认页选择乘车人。"""
        try:
            # 等待乘车人列表加载
            await self.page.wait_for_selector(
                "#passengerList, #normal_passenger_id, .passenger-list, .passenger-item",
                timeout=10000,
            )
        except PlaywrightTimeoutError:
            await self._log("warn", "[12306] 未找到乘车人列表")
            return False

        for passenger_name in passengers:
            passenger_selectors = [
                f"#passengerList label:has-text('{passenger_name}')",
                f"#normal_passenger_id label:has-text('{passenger_name}')",
                f".passenger-item:has-text('{passenger_name}')",
                f"label:has-text('{passenger_name}')",
                f"tr:has-text('{passenger_name}') input[type='checkbox']",
                f"div:has-text('{passenger_name}'):near(#passengerList)",
            ]
            selected = False
            for selector in passenger_selectors:
                try:
                    el = await self.page.wait_for_selector(
                        selector, timeout=3000, state="visible"
                    )
                    if el:
                        # 如果是 checkbox 容器，找到其中的 input
                        checkbox = await el.query_selector("input[type='checkbox']")
                        if checkbox:
                            is_checked = await checkbox.is_checked()
                            if not is_checked:
                                await el.click()
                        else:
                            await el.click()
                        await self._random_delay()
                        await self._log("info", f"[12306] 已选择乘车人: {passenger_name}")
                        selected = True
                        break
                except PlaywrightTimeoutError:
                    continue
            if not selected:
                await self._log("warn", f"[12306] 未找到乘车人: {passenger_name}")

        return True

    async def _confirm_seat_type(self, seat_type: str) -> bool:
        """在订单确认页确认或选择席别。"""
        seat_selectors = [
            f"select option:has-text('{seat_type}')",
            f".seat-type:has-text('{seat_type}')",
            f"label:has-text('{seat_type}')",
            f"div:has-text('{seat_type}'):near(.seat-list)",
        ]
        for selector in seat_selectors:
            try:
                el = await self.page.wait_for_selector(
                    selector, timeout=5000, state="visible"
                )
                if el:
                    tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == "option":
                        parent = await el.evaluate("el => el.closest('select')")
                        if parent:
                            await el.click()
                    else:
                        await el.click()
                    await self._random_delay()
                    await self._log("info", f"[12306] 已确认席别: {seat_type}")
                    return True
            except PlaywrightTimeoutError:
                continue
        return False

    async def _submit_order(self) -> bool:
        """提交12306订单。"""
        submit_selectors = [
            "#submitOrder_id",
            "#qr_submit",
            "button:has-text('提交订单')",
            "button:has-text('确认')",
            ".submit-btn",
            "#submit-order",
        ]
        for selector in submit_selectors:
            try:
                btn = await self.page.wait_for_selector(
                    selector, timeout=10000, state="visible"
                )
                if btn:
                    await self._random_delay()
                    await btn.click()
                    await self._log("info", "[12306] 已点击提交订单")
                    break
            except PlaywrightTimeoutError:
                continue
        else:
            await self._log("error", "[12306] 未找到提交订单按钮")
            return False

        # 等待提交结果
        await asyncio.sleep(3)
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        current_url = self.page.url
        success_url_keywords = ["pay", "confirm", "order", "payment", "noComplete", "myOrder"]
        if any(kw in current_url.lower() for kw in success_url_keywords):
            await self._log("success", f"[12306] URL检测到成功: {current_url}")
            return True

        page_text = await self.page.content()
        success_keywords = [
            "订单提交成功",
            "等待支付",
            "支付",
            "订单确认",
            "请在",
            "分钟内完成",
            "未完成订单",
        ]
        for kw in success_keywords:
            if kw in page_text:
                await self._log("success", f"[12306] 页面内容检测到成功: {kw}")
                return True

        # 12306 特殊的排队/处理中提示
        processing_keywords = ["正在处理", "排队中", "请稍后"]
        for kw in processing_keywords:
            if kw in page_text:
                await self._log("info", f"[12306] 订单正在处理中: {kw}，等待5秒再检测...")
                await asyncio.sleep(5)
                # 再次检测
                page_text = await self.page.content()
                for kw2 in success_keywords:
                    if kw2 in page_text:
                        await self._log("success", f"[12306] 处理后检测到成功: {kw2}")
                        return True

        error_keywords = ["失败", "无余票", "已售完", "系统繁忙", "请重试", "无法提交"]
        for kw in error_keywords:
            if kw in page_text:
                await self._log("error", f"[12306] 检测到错误: {kw}")
                return False

        await self._log("warn", "[12306] 无法确认订单状态")
        return False
