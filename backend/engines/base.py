"""Base engine interface for all ticket platforms."""
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from core.models import TaskConfig

class BaseEngine(ABC):
    """Abstract base class for all ticket grabbing engines."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    async def initialize(self):
        """Initialize Playwright browser instance."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        # Inject script to hide webdriver property
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
    
    async def close(self):
        """Close browser and cleanup."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    @abstractmethod
    async def login(self) -> bool:
        """Perform login. Return True if successful."""
        pass
    
    @abstractmethod
    async def grab(self, task: TaskConfig) -> bool:
        """Execute the grabbing flow. Return True if successful."""
        pass
    
    @abstractmethod
    async def check_stock(self, task: TaskConfig) -> bool:
        """Check if tickets are available."""
        pass
    
    async def screenshot(self, path: str):
        """Take a screenshot for debugging."""
        if self.page:
            await self.page.screenshot(path=path)
