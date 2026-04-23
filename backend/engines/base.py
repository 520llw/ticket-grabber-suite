"""抢票引擎抽象基类 — 统一浏览器管理、反检测、日志、截图。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
"""
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional, Callable, Awaitable
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from core.models import TaskConfig
from config.settings import (
    USER_AGENTS, MIN_DELAY, MAX_DELAY,
    DEFAULT_TIMEOUT, SCREENSHOT_DIR, MAX_RETRIES,
)


class BaseEngine(ABC):
    """所有抢票引擎的抽象基类。"""

    def __init__(
        self,
        headless: bool = True,
        log_callback: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        self.headless = headless
        self.log_callback = log_callback
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        self.platform_name = "base"

    # ── 日志 ──────────────────────────────────────────

    async def _log(self, level: str, message: str):
        if self.log_callback:
            await self.log_callback(level, message)

    # ── 反检测延迟 ────────────────────────────────────

    async def _random_delay(self, min_s: float = None, max_s: float = None):
        delay = random.uniform(min_s or MIN_DELAY, max_s or MAX_DELAY)
        await asyncio.sleep(delay)

    # ── 浏览器生命周期 ────────────────────────────────

    async def initialize(self):
        """启动 Playwright 浏览器，注入反检测脚本。"""
        self._playwright = await async_playwright().start()

        ua = random.choice(USER_AGENTS)
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-popup-blocking",
            "--disable-translate",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
        ]

        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=ua,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            color_scheme="light",
        )

        self.page = await self.context.new_page()

        # 全面反检测注入
        await self.page.add_init_script("""
            // 隐藏 webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            // 伪造 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // 伪造 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });

            // 伪造 chrome 对象
            window.chrome = { runtime: {} };

            // 隐藏 Permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);

            // 伪造 WebGL 渲染器
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.call(this, parameter);
            };
        """)

        await self._log("info", f"浏览器已启动 (headless={self.headless})")

    async def close(self):
        """安全关闭浏览器。"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass

    # ── 通用辅助 ──────────────────────────────────────

    async def screenshot(self, name: str = "debug"):
        """调试截图。"""
        if self.page:
            path = str(SCREENSHOT_DIR / f"{self.platform_name}_{name}.png")
            await self.page.screenshot(path=path, full_page=True)
            await self._log("debug", f"截图已保存: {path}")

    async def safe_click(self, selectors: list[str], timeout: int = 5000, desc: str = "元素") -> bool:
        """安全点击：遍历选择器列表，找到第一个可见元素并点击。"""
        for selector in selectors:
            try:
                el = await self.page.wait_for_selector(selector, timeout=timeout, state="visible")
                if el:
                    await self._random_delay()
                    await el.click()
                    await self._log("info", f"已点击{desc}: {selector}")
                    return True
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        await self._log("warn", f"未找到{desc}")
        return False

    async def safe_fill(self, selectors: list[str], value: str, timeout: int = 5000, desc: str = "输入框") -> bool:
        """安全填写：遍历选择器列表，找到第一个可见输入框并填写。"""
        for selector in selectors:
            try:
                el = await self.page.wait_for_selector(selector, timeout=timeout, state="visible")
                if el:
                    await el.fill("")
                    await self._random_delay(0.1, 0.3)
                    await el.type(value, delay=random.randint(50, 150))
                    await self._log("info", f"已填写{desc}: {value}")
                    return True
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue
        await self._log("warn", f"未找到{desc}")
        return False

    async def wait_for_navigation(self, keywords: list[str] = None, timeout: int = 10000) -> bool:
        """等待页面跳转并检查 URL 关键词。"""
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            if keywords:
                url = self.page.url.lower()
                return any(kw in url for kw in keywords)
            return True
        except PlaywrightTimeoutError:
            return False

    # ── 抽象方法 ──────────────────────────────────────

    @abstractmethod
    async def login(self) -> bool:
        """执行登录流程。"""
        pass

    @abstractmethod
    async def grab(self, task: TaskConfig) -> bool:
        """执行抢票流程。"""
        pass

    @abstractmethod
    async def check_stock(self, task: TaskConfig) -> bool:
        """检查库存。"""
        pass
