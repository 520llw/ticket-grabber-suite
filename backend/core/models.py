"""Pydantic models for tasks and logs."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid

def generate_id() -> str:
    return str(uuid.uuid4())[:8]

class TaskConfig(BaseModel):
    id: str = Field(default_factory=generate_id)
    name: str = ""
    platform: Literal["damai", "maoyan", "12306", "custom"] = "damai"
    url: str = ""
    date: str = ""
    session: str = ""
    price: str = ""
    ticket_count: int = 1
    buyers: list[str] = []
    cron_time: Optional[str] = None  # ISO format datetime string
    status: Literal["idle", "running", "success", "failed", "stopped"] = "idle"
    headless: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class TaskConfigCreate(BaseModel):
    name: str
    platform: Literal["damai", "maoyan", "12306", "custom"] = "damai"
    url: str
    date: str = ""
    session: str = ""
    price: str = ""
    ticket_count: int = 1
    buyers: list[str] = []
    cron_time: Optional[str] = None
    headless: bool = False

class TaskLog(BaseModel):
    task_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    level: Literal["info", "warn", "error", "success"] = "info"
    message: str

class SystemStatus(BaseModel):
    version: str = "1.0.0"
    active_tasks: int = 0
    total_tasks: int = 0
    playwright_ready: bool = False
