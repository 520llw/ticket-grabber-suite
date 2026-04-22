"""Task Manager - manages all grabbing tasks with engine integration.

免责声明：本工具仅供学习研究使用，禁止用于商业用途或黄牛行为。
用户需自行承担使用风险，不保证100%抢票成功。
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from core.models import TaskConfig, TaskLog


class TaskManager:
    """任务管理器，负责任务的CRUD、状态管理和引擎调度。"""

    def __init__(self):
        self.tasks: Dict[str, TaskConfig] = {}
        self.logs: Dict[str, List[TaskLog]] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._listeners: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化管理器，可在此加载持久化任务。"""
        pass

    async def shutdown(self):
        """关闭管理器，取消所有运行中的任务。"""
        for task in self._running.values():
            task.cancel()
        self._running.clear()

    async def create_task(self, config: TaskConfig) -> TaskConfig:
        """创建新任务。"""
        async with self._lock:
            self.tasks[config.id] = config
            self.logs[config.id] = []
        return config

    async def get_task(self, task_id: str) -> Optional[TaskConfig]:
        """获取单个任务。"""
        return self.tasks.get(task_id)

    async def get_all_tasks(self) -> List[TaskConfig]:
        """获取所有任务。"""
        return list(self.tasks.values())

    async def update_task(self, task_id: str, updates: dict) -> Optional[TaskConfig]:
        """更新任务字段。"""
        async with self._lock:
            if task_id not in self.tasks:
                return None
            task = self.tasks[task_id]
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now().isoformat()
            return task

    async def delete_task(self, task_id: str) -> bool:
        """删除任务并清理相关资源。"""
        async with self._lock:
            await self.stop_task(task_id)
            self.tasks.pop(task_id, None)
            self.logs.pop(task_id, None)
        return True

    async def start_task(self, task_id: str) -> bool:
        """启动抢票任务。

        根据任务的平台类型选择对应引擎，在后台协程中执行抢票流程。
        支持定时抢票（通过 cron_time 字段）。
        """
        task = await self.get_task(task_id)
        if not task or task.status == "running":
            return False

        await self.update_task(task_id, {"status": "running"})

        # 内部日志辅助函数，绑定 task_id
        async def add_task_log(level: str, message: str):
            await self.add_log(task_id, level, message)

        # 后台抢票协程
        async def run():
            from engines import ENGINE_MAP

            engine_class = ENGINE_MAP.get(task.platform)
            if not engine_class:
                await add_task_log("error", f"Unknown platform: {task.platform}")
                await self.update_task(task_id, {"status": "failed"})
                return

            engine = engine_class(headless=task.headless, log_callback=add_task_log)
            try:
                await engine.initialize()
                await add_task_log("info", f"Engine initialized for {task.platform}")

                # 如果需要定时，等待到目标时间点
                if task.cron_time:
                    try:
                        target = datetime.fromisoformat(task.cron_time)
                        now = datetime.now()
                        if target > now:
                            wait = (target - now).total_seconds()
                            await add_task_log(
                                "info", f"Waiting {wait:.0f}s until target time..."
                            )
                            await asyncio.sleep(wait)
                        else:
                            await add_task_log(
                                "warn", "Target time has passed, starting immediately"
                            )
                    except Exception as e:
                        await add_task_log("warn", f"Invalid cron_time: {e}")

                # 执行抢票
                success = await engine.grab(task)
                if success:
                    await add_task_log("success", "抢票成功！请尽快完成支付！")
                    await self.update_task(task_id, {"status": "success"})
                else:
                    await add_task_log("warn", "抢票未成功，可能已售罄或流程中断")
                    await self.update_task(task_id, {"status": "failed"})
            except asyncio.CancelledError:
                await add_task_log("warn", "Task was cancelled by user")
                await self.update_task(task_id, {"status": "stopped"})
                raise
            except Exception as e:
                await add_task_log("error", f"Exception: {str(e)}")
                await self.update_task(task_id, {"status": "failed"})
            finally:
                await add_task_log("info", "Engine closing...")
                await engine.close()
                # 清理运行记录
                self._running.pop(task_id, None)

        self._running[task_id] = asyncio.create_task(run())
        return True

    async def stop_task(self, task_id: str) -> bool:
        """停止运行中的任务。"""
        if task_id in self._running:
            self._running[task_id].cancel()
            del self._running[task_id]
        return True

    async def add_log(self, task_id: str, level: str, message: str):
        """添加任务日志并通知所有监听器（SSE推送）。"""
        log = TaskLog(task_id=task_id, level=level, message=message)
        if task_id not in self.logs:
            self.logs[task_id] = []
        self.logs[task_id].append(log)
        # Notify listeners
        for queue in self._listeners:
            await queue.put({"task_id": task_id, **log.model_dump()})

    async def get_logs(self, task_id: str, limit: int = 100) -> List[TaskLog]:
        """获取任务日志（最近的 limit 条）。"""
        logs = self.logs.get(task_id, [])
        return logs[-limit:]

    def add_listener(self, queue: asyncio.Queue):
        """添加SSE监听器队列。"""
        self._listeners.append(queue)

    def remove_listener(self, queue: asyncio.Queue):
        """移除SSE监听器队列。"""
        if queue in self._listeners:
            self._listeners.remove(queue)


# Global singleton instance for task manager
_task_manager_instance: TaskManager | None = None


def get_task_manager() -> TaskManager:
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance
