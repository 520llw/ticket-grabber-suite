"""Pydantic 数据模型 — 任务、日志、系统状态。"""
from datetime import datetime
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())[:8]


# ── 任务配置 ──────────────────────────────────────────

class TaskConfig(BaseModel):
    """抢票任务完整配置。"""
    id: str = Field(default_factory=generate_id)
    name: str = ""
    platform: Literal["damai", "maoyan", "12306", "custom"] = "damai"
    url: str = ""

    # 通用字段
    date: str = ""
    session: str = ""
    price: str = ""
    ticket_count: int = 1
    buyers: List[str] = []

    # 12306 专用字段
    from_station: str = ""
    to_station: str = ""
    train_number: str = ""
    seat_type: str = ""

    # 调度
    cron_time: Optional[str] = None
    status: Literal["idle", "running", "success", "failed", "stopped", "waiting"] = "idle"
    headless: bool = True

    # 高级选项
    max_retries: int = 5
    retry_interval: float = 1.0
    auto_retry: bool = True
    multi_buy: bool = False          # 多账号并发（预留）
    notify_on_success: bool = True
    priority: int = 0                # 0=普通 1=高优先级

    # 统计
    attempt_count: int = 0
    last_error: str = ""

    # 时间戳
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class TaskConfigCreate(BaseModel):
    """创建任务的请求体。"""
    name: str
    platform: Literal["damai", "maoyan", "12306", "custom"] = "damai"
    url: str = ""
    date: str = ""
    session: str = ""
    price: str = ""
    ticket_count: int = 1
    buyers: List[str] = []

    # 12306 专用
    from_station: str = ""
    to_station: str = ""
    train_number: str = ""
    seat_type: str = ""

    # 调度
    cron_time: Optional[str] = None
    headless: bool = True

    # 高级
    max_retries: int = 5
    retry_interval: float = 1.0
    auto_retry: bool = True
    notify_on_success: bool = True
    priority: int = 0


class TaskConfigUpdate(BaseModel):
    """更新任务的请求体（所有字段可选）。"""
    name: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None
    session: Optional[str] = None
    price: Optional[str] = None
    ticket_count: Optional[int] = None
    buyers: Optional[List[str]] = None
    from_station: Optional[str] = None
    to_station: Optional[str] = None
    train_number: Optional[str] = None
    seat_type: Optional[str] = None
    cron_time: Optional[str] = None
    headless: Optional[bool] = None
    max_retries: Optional[int] = None
    retry_interval: Optional[float] = None
    auto_retry: Optional[bool] = None
    notify_on_success: Optional[bool] = None
    priority: Optional[int] = None


# ── 日志 ──────────────────────────────────────────────

class TaskLog(BaseModel):
    """单条任务日志。"""
    task_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    level: Literal["info", "warn", "error", "success", "debug"] = "info"
    message: str


# ── 系统状态 ──────────────────────────────────────────

class SystemStatus(BaseModel):
    """系统运行状态。"""
    version: str = "2.0.0"
    active_tasks: int = 0
    total_tasks: int = 0
    success_tasks: int = 0
    failed_tasks: int = 0
    playwright_ready: bool = False
    uptime_seconds: float = 0
    cpu_percent: float = 0
    memory_mb: float = 0


# ── 通知 ──────────────────────────────────────────────

class NotifyConfig(BaseModel):
    """通知配置。"""
    webhook_url: str = ""
    email: str = ""
    enabled: bool = False
