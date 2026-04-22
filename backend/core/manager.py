"""Task Manager - manages all grabbing tasks."""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from core.models import TaskConfig, TaskLog

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskConfig] = {}
        self.logs: Dict[str, List[TaskLog]] = {}
        self._running: Dict[str, asyncio.Task] = {}
        self._listeners: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        # Load persisted tasks if any
        pass
    
    async def shutdown(self):
        # Cancel all running tasks
        for task in self._running.values():
            task.cancel()
        self._running.clear()
    
    async def create_task(self, config: TaskConfig) -> TaskConfig:
        async with self._lock:
            self.tasks[config.id] = config
            self.logs[config.id] = []
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
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now().isoformat()
            return task
    
    async def delete_task(self, task_id: str) -> bool:
        async with self._lock:
            await self.stop_task(task_id)
            self.tasks.pop(task_id, None)
            self.logs.pop(task_id, None)
        return True
    
    async def start_task(self, task_id: str) -> bool:
        # To be implemented with engine integration
        return True
    
    async def stop_task(self, task_id: str) -> bool:
        if task_id in self._running:
            self._running[task_id].cancel()
            del self._running[task_id]
        return True
    
    async def add_log(self, task_id: str, level: str, message: str):
        log = TaskLog(task_id=task_id, level=level, message=message)
        if task_id not in self.logs:
            self.logs[task_id] = []
        self.logs[task_id].append(log)
        # Notify listeners
        for queue in self._listeners:
            await queue.put({"task_id": task_id, **log.model_dump()})
    
    async def get_logs(self, task_id: str, limit: int = 100) -> List[TaskLog]:
        logs = self.logs.get(task_id, [])
        return logs[-limit:]
    
    def add_listener(self, queue: asyncio.Queue):
        self._listeners.append(queue)
    
    def remove_listener(self, queue: asyncio.Queue):
        if queue in self._listeners:
            self._listeners.remove(queue)
