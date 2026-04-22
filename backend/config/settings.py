"""Global configuration settings for Ticket Grabber Suite.

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Screenshot storage for debugging
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# Default Playwright settings
DEFAULT_HEADLESS = False
DEFAULT_TIMEOUT = 30000  # 30 seconds
POLL_INTERVAL = 0.5  # seconds between stock checks

# Browser user agent (Chrome on macOS)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Platform URLs
PLATFORM_URLS = {
    "damai": {
        "login": "https://www.damai.cn/",
        "base": "https://www.damai.cn",
    },
    "maoyan": {
        "login": "https://www.maoyan.com/",
        "base": "https://www.maoyan.com",
    },
    "12306": {
        "login": "https://kyfw.12306.cn/otn/resources/login.html",
        "query": "https://kyfw.12306.cn/otn/leftTicket/init",
        "base": "https://kyfw.12306.cn",
    },
}

# Anti-detection delays (seconds)
MIN_DELAY = 0.5
MAX_DELAY = 2.0

# Max retry attempts for critical operations
MAX_RETRIES = 3
