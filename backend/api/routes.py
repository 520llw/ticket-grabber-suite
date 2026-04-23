"""API 路由 — RESTful + SSE 实时日志。"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from core.models import TaskConfig, TaskConfigCreate, TaskConfigUpdate, SystemStatus
from core.manager import get_task_manager

router = APIRouter()


# ── 任务 CRUD ─────────────────────────────────────────

@router.get("/tasks")
async def list_tasks(
    status: str = Query(None, description="按状态筛选"),
    platform: str = Query(None, description="按平台筛选"),
    search: str = Query(None, description="按名称搜索"),
    sort: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", description="排序方向"),
):
    """获取任务列表，支持筛选、搜索、排序。"""
    manager = get_task_manager()
    tasks = await manager.get_all_tasks()

    # 筛选
    if status:
        tasks = [t for t in tasks if t.status == status]
    if platform:
        tasks = [t for t in tasks if t.platform == platform]
    if search:
        search_lower = search.lower()
        tasks = [t for t in tasks if search_lower in t.name.lower() or search_lower in t.url.lower()]

    # 排序
    reverse = order == "desc"
    if sort in ("created_at", "updated_at", "name", "status", "priority"):
        tasks.sort(key=lambda t: getattr(t, sort, ""), reverse=reverse)

    return {
        "tasks": [t.model_dump() for t in tasks],
        "total": len(tasks),
    }


@router.post("/tasks")
async def create_task(data: TaskConfigCreate):
    """创建新任务。"""
    manager = get_task_manager()
    task = TaskConfig(**data.model_dump())
    await manager.create_task(task)
    return {"task": task.model_dump()}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """获取单个任务详情。"""
    manager = get_task_manager()
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": task.model_dump()}


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, data: TaskConfigUpdate):
    """更新任务配置。"""
    manager = get_task_manager()
    updates = data.model_dump(exclude_none=True)
    task = await manager.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": task.model_dump()}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务。"""
    manager = get_task_manager()
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    success = await manager.delete_task(task_id)
    return {"success": success}


# ── 任务操作 ──────────────────────────────────────────

@router.post("/tasks/{task_id}/start")
async def start_task(task_id: str):
    """启动抢票任务。"""
    manager = get_task_manager()
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status == "running":
        raise HTTPException(status_code=400, detail="任务已在运行中")
    success = await manager.start_task(task_id)
    return {"success": success}


@router.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    """停止任务。"""
    manager = get_task_manager()
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    success = await manager.stop_task(task_id)
    return {"success": success}


@router.post("/tasks/{task_id}/restart")
async def restart_task(task_id: str):
    """重启任务。"""
    manager = get_task_manager()
    task = await manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    success = await manager.restart_task(task_id)
    return {"success": success}


# ── 日志 ──────────────────────────────────────────────

@router.get("/tasks/{task_id}/logs")
async def get_logs(task_id: str, limit: int = Query(200, ge=1, le=1000)):
    """获取任务日志。"""
    manager = get_task_manager()
    logs = await manager.get_logs(task_id, limit)
    return {"logs": [l.model_dump() for l in logs]}


@router.delete("/tasks/{task_id}/logs")
async def clear_logs(task_id: str):
    """清空任务日志。"""
    manager = get_task_manager()
    await manager.clear_logs(task_id)
    return {"success": True}


@router.get("/tasks/{task_id}/logs/stream")
async def stream_logs(task_id: str):
    """SSE 实时日志流。"""
    manager = get_task_manager()
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    manager.add_listener(queue)

    async def event_generator():
        try:
            while True:
                data = await asyncio.wait_for(queue.get(), timeout=30)
                if data.get("task_id") == task_id:
                    yield {"event": "log", "data": json.dumps(data, ensure_ascii=False)}
        except asyncio.TimeoutError:
            # 发送心跳保持连接
            yield {"event": "heartbeat", "data": "ping"}
        except asyncio.CancelledError:
            pass
        finally:
            manager.remove_listener(queue)

    return EventSourceResponse(event_generator())


# ── 系统 ──────────────────────────────────────────────

@router.get("/status")
async def system_status():
    """获取系统运行状态。"""
    manager = get_task_manager()
    status = await manager.get_system_status()
    return status.model_dump()


@router.get("/platforms")
async def list_platforms():
    """获取支持的平台列表。"""
    return {
        "platforms": [
            {
                "id": "damai",
                "name": "大麦网",
                "description": "演唱会、话剧、展览等演出票务",
                "icon": "ticket",
                "fields": ["url", "date", "session", "price", "ticket_count", "buyers"],
            },
            {
                "id": "maoyan",
                "name": "猫眼",
                "description": "演出、电影等票务",
                "icon": "film",
                "fields": ["url", "date", "session", "price", "ticket_count", "buyers"],
            },
            {
                "id": "12306",
                "name": "12306 铁路",
                "description": "火车票、高铁票预订",
                "icon": "train-front",
                "fields": ["from_station", "to_station", "date", "train_number", "seat_type", "ticket_count", "buyers"],
            },
        ]
    }


# ── 批量操作 ──────────────────────────────────────────

@router.post("/tasks/batch/start")
async def batch_start(task_ids: list[str]):
    """批量启动任务。"""
    manager = get_task_manager()
    results = {}
    for tid in task_ids:
        try:
            results[tid] = await manager.start_task(tid)
        except Exception as e:
            results[tid] = False
    return {"results": results}


@router.post("/tasks/batch/stop")
async def batch_stop(task_ids: list[str]):
    """批量停止任务。"""
    manager = get_task_manager()
    results = {}
    for tid in task_ids:
        try:
            results[tid] = await manager.stop_task(tid)
        except Exception as e:
            results[tid] = False
    return {"results": results}


@router.post("/tasks/batch/delete")
async def batch_delete(task_ids: list[str]):
    """批量删除任务。"""
    manager = get_task_manager()
    results = {}
    for tid in task_ids:
        try:
            results[tid] = await manager.delete_task(tid)
        except Exception as e:
            results[tid] = False
    return {"results": results}
