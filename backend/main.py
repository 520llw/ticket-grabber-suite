"""FastAPI 主入口 — Ticket Grabber Suite v2.0"""
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

from core.manager import TaskManager, get_task_manager
from config.settings import VERSION, HOST, PORT

# ── 生命周期 ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = get_task_manager()
    await manager.initialize()
    print(f"✅ Ticket Grabber Suite v{VERSION} 已启动")
    print(f"📡 API: http://{HOST}:{PORT}/api/docs")
    yield
    await manager.shutdown()
    print("🛑 服务已关闭")


# ── 应用 ──────────────────────────────────────────────

app = FastAPI(
    title="Ticket Grabber Suite API",
    description="跨平台抢票自动化工具后端 API — 支持大麦/猫眼/12306",
    version=VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "请求参数错误", "errors": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )

# API 路由
from api.routes import router
app.include_router(router, prefix="/api")

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": VERSION, "service": "ticket-grabber-api"}

# 前端静态文件
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    # 静态资源
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # SPA 回退
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # 排除 API 路径
        if path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API 路径不存在"})
        # 尝试直接返回文件
        file_path = os.path.join(frontend_dist, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # 回退到 index.html
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"detail": "前端未构建"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False, log_level="info")
