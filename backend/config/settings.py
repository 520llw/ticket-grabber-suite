"""全局配置 — 支持环境变量覆盖与运行时调整。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
import os
from pathlib import Path

# ── 目录 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOT_DIR = DATA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "tasks.json"
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ── 服务器 ────────────────────────────────────────────
HOST = os.getenv("TGS_HOST", "0.0.0.0")
PORT = int(os.getenv("TGS_PORT", "8000"))

# ── Playwright ────────────────────────────────────────
DEFAULT_HEADLESS = os.getenv("TGS_HEADLESS", "true").lower() == "true"
DEFAULT_TIMEOUT = int(os.getenv("TGS_TIMEOUT", "30000"))
POLL_INTERVAL = float(os.getenv("TGS_POLL_INTERVAL", "0.3"))

# ── 浏览器指纹池（随机选取） ─────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

# ── 平台 URL ──────────────────────────────────────────
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

# ── 反检测 ────────────────────────────────────────────
MIN_DELAY = float(os.getenv("TGS_MIN_DELAY", "0.3"))
MAX_DELAY = float(os.getenv("TGS_MAX_DELAY", "1.5"))

# ── 重试与并发 ────────────────────────────────────────
MAX_RETRIES = int(os.getenv("TGS_MAX_RETRIES", "5"))
RETRY_INTERVAL = float(os.getenv("TGS_RETRY_INTERVAL", "1.0"))
MAX_CONCURRENT_TASKS = int(os.getenv("TGS_MAX_CONCURRENT", "3"))

# ── 通知（预留） ─────────────────────────────────────
NOTIFY_WEBHOOK = os.getenv("TGS_NOTIFY_WEBHOOK", "")
NOTIFY_EMAIL = os.getenv("TGS_NOTIFY_EMAIL", "")

# ── 版本 ──────────────────────────────────────────────
VERSION = "2.0.0"
