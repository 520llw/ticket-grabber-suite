"""任务管理器 — 持久化、调度、重试、并发控制。

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
import asyncio
import json
import time
import os
import psutil
from datetime import datetime
from typing import Dict, List, Optional

from core.models import TaskConfig, TaskLog, SystemStatus
from config.settings import (
    DB_PATH, LOG_DIR, MAX_CONCURRENT_TASKS, VERSION,
    MAX_RETRIES, RETRY_INTERVAL, NOTIFY_WEBHOOK,
)


class TaskManager:
    """任务管理器：CRUD、调度、引擎调度、持久化、SSE 广播。"""

    def __init__(self):
        self.tasks: Dict[str, TaskConfig] = {}
        self.logs: Dict[str, List[TaskLog]] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._listeners: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        self._start_time = time.time()

    # ── 生命周期 ──────────────────────────────────────

    async def initialize(self):
        """启动时从磁盘加载任务。"""
        self._load_tasks()

    async def shutdown(self):
        """关闭时取消所有运行中任务并持久化。"""
        for t in list(self._running.values()):
            t.cancel()
        self._running.clear()
        self._save_tasks()

    # ── 持久化 ────────────────────────────────────────

    def _load_tasks(self):
        if DB_PATH.exists():
            try:
                data = json.loads(DB_PATH.read_text(encoding="utf-8"))
                for item in data:
                    task = TaskConfig(**item)
                    # 恢复时将 running 状态重置为 stopped
                    if task.status == "running":
                        task.status = "stopped"
                    self.tasks[task.id] = task
                    self.logs[task.id] = self._load_task_logs(task.id)
            except Exception:
                pass

    def _save_tasks(self):
        try:
            data = [t.model_dump() for t in self.tasks.values()]
            DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_task_logs(self, task_id: str) -> List[TaskLog]:
        log_file = LOG_DIR / f"{task_id}.jsonl"
        logs = []
        if log_file.exists():
            try:
                for line in log_file.read_text(encoding="utf-8").strip().split("\n"):
                    if line:
                        logs.append(TaskLog(**json.loads(line)))
            except Exception:
                pass
        return logs[-500:]  # 最多保留最近500条

    def _append_log_file(self, task_id: str, log: TaskLog):
        log_file = LOG_DIR / f"{task_id}.jsonl"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log.model_dump(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ── CRUD ──────────────────────────────────────────

    async def create_task(self, config: TaskConfig) -> TaskConfig:
        async with self._lock:
            self.tasks[config.id] = config
            self.logs[config.id] = []
            self._save_tasks()
        return config

    async def get_task(self, task_id: str) -> Optional[TaskConfig]:
        return self.tasks.get(task_id)

    async def get_all_tasks(self) -> List[TaskConfig]:
        return list(self.tasks.values())

    async def update_task(self, task_id: str, updates: dict) -> Optional[TaskConfig]:
        async with self._lock:
            if task_id not in self.tasks:
                return None
            task = self.tasks[task_id]
            for key, value in updates.items():
                if hasattr(task, key) and value is not None:
                    setattr(task, key, value)
            task.updated_at = datetime.now().isoformat()
            self._save_tasks()
            return task

    async def delete_task(self, task_id: str) -> bool:
        async with self._lock:
            await self.stop_task(task_id)
            self.tasks.pop(task_id, None)
            self.logs.pop(task_id, None)
            # 删除日志文件
            log_file = LOG_DIR / f"{task_id}.jsonl"
            if log_file.exists():
                log_file.unlink()
            self._save_tasks()
        return True

    # ── 任务执行 ──────────────────────────────────────

    async def start_task(self, task_id: str) -> bool:
        task = await self.get_task(task_id)
        if not task or task.status == "running":
            return False

        await self.update_task(task_id, {"status": "running", "attempt_count": 0, "last_error": ""})

        async def add_task_log(level: str, message: str):
            await self.add_log(task_id, level, message)

        async def run():
            async with self._semaphore:
                from engines import ENGINE_MAP

                engine_class = ENGINE_MAP.get(task.platform)
                if not engine_class:
                    await add_task_log("error", f"未知平台: {task.platform}")
                    await self.update_task(task_id, {"status": "failed"})
                    return

                engine = engine_class(headless=task.headless, log_callback=add_task_log)
                retries = task.max_retries if task.auto_retry else 1
                attempt = 0

                try:
                    await engine.initialize()
                    await add_task_log("info", f"引擎已初始化 [{task.platform}]")

                    # 定时等待
                    if task.cron_time:
                        try:
                            target = datetime.fromisoformat(task.cron_time)
                            now = datetime.now()
                            if target > now:
                                wait = (target - now).total_seconds()
                                await self.update_task(task_id, {"status": "waiting"})
                                await add_task_log("info", f"等待 {wait:.0f} 秒到达目标时间 {task.cron_time}")
                                await asyncio.sleep(wait)
                                await self.update_task(task_id, {"status": "running"})
                            else:
                                await add_task_log("warn", "目标时间已过，立即开始")
                        except Exception as e:
                            await add_task_log("warn", f"时间解析异常: {e}")

                    # 带重试的抢票循环
                    success = False
                    while attempt < retries and not success:
                        attempt += 1
                        await self.update_task(task_id, {"attempt_count": attempt})
                        await add_task_log("info", f"第 {attempt}/{retries} 次尝试抢票...")

                        try:
                            success = await engine.grab(task)
                        except Exception as e:
                            await add_task_log("error", f"第 {attempt} 次异常: {str(e)}")
                            await self.update_task(task_id, {"last_error": str(e)})

                        if not success and attempt < retries:
                            interval = task.retry_interval
                            await add_task_log("info", f"等待 {interval}s 后重试...")
                            await asyncio.sleep(interval)

                    if success:
                        await add_task_log("success", "抢票成功！请尽快完成支付！")
                        await self.update_task(task_id, {"status": "success"})
                        await self._notify_success(task)
                    else:
                        await add_task_log("warn", f"经过 {attempt} 次尝试，抢票未成功")
                        await self.update_task(task_id, {"status": "failed"})

                except asyncio.CancelledError:
                    await add_task_log("warn", "任务被用户取消")
                    await self.update_task(task_id, {"status": "stopped"})
                    raise
                except Exception as e:
                    await add_task_log("error", f"致命异常: {str(e)}")
                    await self.update_task(task_id, {"status": "failed", "last_error": str(e)})
                finally:
                    await add_task_log("info", "引擎关闭中...")
                    await engine.close()
                    self._running.pop(task_id, None)

        self._running[task_id] = asyncio.create_task(run())
        return True

    async def stop_task(self, task_id: str) -> bool:
        if task_id in self._running:
            self._running[task_id].cancel()
            del self._running[task_id]
            await self.update_task(task_id, {"status": "stopped"})
        return True

    async def restart_task(self, task_id: str) -> bool:
        """停止后重新启动任务。"""
        await self.stop_task(task_id)
        await asyncio.sleep(0.5)
        return await self.start_task(task_id)

    # ── 日志 ──────────────────────────────────────────

    async def add_log(self, task_id: str, level: str, message: str):
        log = TaskLog(task_id=task_id, level=level, message=message)
        if task_id not in self.logs:
            self.logs[task_id] = []
        self.logs[task_id].append(log)
        # 内存日志上限
        if len(self.logs[task_id]) > 1000:
            self.logs[task_id] = self.logs[task_id][-500:]
        # 持久化
        self._append_log_file(task_id, log)
        # 广播
        for queue in self._listeners:
            try:
                queue.put_nowait({"task_id": task_id, **log.model_dump()})
            except asyncio.QueueFull:
                pass

    async def get_logs(self, task_id: str, limit: int = 100) -> List[TaskLog]:
        logs = self.logs.get(task_id, [])
        return logs[-limit:]

    async def clear_logs(self, task_id: str):
        self.logs[task_id] = []
        log_file = LOG_DIR / f"{task_id}.jsonl"
        if log_file.exists():
            log_file.unlink()

    def add_listener(self, queue: asyncio.Queue):
        self._listeners.append(queue)

    def remove_listener(self, queue: asyncio.Queue):
        if queue in self._listeners:
            self._listeners.remove(queue)

    # ── 系统状态 ──────────────────────────────────────

    async def get_system_status(self) -> SystemStatus:
        all_tasks = list(self.tasks.values())
        process = psutil.Process(os.getpid())
        return SystemStatus(
            version=VERSION,
            active_tasks=sum(1 for t in all_tasks if t.status in ("running", "waiting")),
            total_tasks=len(all_tasks),
            success_tasks=sum(1 for t in all_tasks if t.status == "success"),
            failed_tasks=sum(1 for t in all_tasks if t.status == "failed"),
            playwright_ready=True,
            uptime_seconds=time.time() - self._start_time,
            cpu_percent=process.cpu_percent(),
            memory_mb=process.memory_info().rss / 1024 / 1024,
        )

    # ── 通知 ──────────────────────────────────────────

    async def _notify_success(self, task: TaskConfig):
        """抢票成功后发送通知（Webhook）。"""
        if not task.notify_on_success or not NOTIFY_WEBHOOK:
            return
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(NOTIFY_WEBHOOK, json={
                    "event": "ticket_success",
                    "task_name": task.name,
                    "platform": task.platform,
                    "time": datetime.now().isoformat(),
                }, timeout=10)
        except Exception:
            pass


# ── 全局单例 ──────────────────────────────────────────

_task_manager_instance: TaskManager | None = None


def get_task_manager() -> TaskManager:
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance
