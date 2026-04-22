"""API Routes."""
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from core.models import TaskConfig, TaskConfigCreate, SystemStatus
from core.manager import TaskManager
from main import get_task_manager

router = APIRouter()

def get_manager() -> TaskManager:
    return get_task_manager()

@router.get("/tasks")
async def list_tasks():
    manager = get_manager()
    tasks = await manager.get_all_tasks()
    return {"tasks": [t.model_dump() for t in tasks]}

@router.post("/tasks")
async def create_task(data: TaskConfigCreate):
    manager = get_manager()
    task = TaskConfig(**data.model_dump())
    await manager.create_task(task)
    return {"task": task.model_dump()}

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    manager = get_manager()
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.model_dump()}

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, data: dict):
    manager = get_manager()
    task = await manager.update_task(task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task": task.model_dump()}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    manager = get_manager()
    success = await manager.delete_task(task_id)
    return {"success": success}

@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str):
    manager = get_manager()
    success = await manager.start_task(task_id)
    return {"success": success}

@router.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    manager = get_manager()
    success = await manager.stop_task(task_id)
    return {"success": success}

@router.get("/tasks/{task_id}/logs")
async def get_logs(task_id: str, limit: int = 100):
    manager = get_manager()
    logs = await manager.get_logs(task_id, limit)
    return {"logs": [l.model_dump() for l in logs]}

@router.get("/tasks/{task_id}/logs/stream")
async def stream_logs(task_id: str):
    manager = get_manager()
    queue = asyncio.Queue()
    manager.add_listener(queue)
    
    async def event_generator():
        try:
            while True:
                data = await queue.get()
                if data.get("task_id") == task_id:
                    yield {"event": "log", "data": data}
        except asyncio.CancelledError:
            manager.remove_listener(queue)
    
    return EventSourceResponse(event_generator())

@router.get("/status")
async def system_status():
    manager = get_manager()
    all_tasks = await manager.get_all_tasks()
    running = sum(1 for t in all_tasks if t.status == "running")
    return SystemStatus(
        active_tasks=running,
        total_tasks=len(all_tasks),
        playwright_ready=True
    )
