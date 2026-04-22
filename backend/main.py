"""FastAPI main entry point."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from api.routes import router
from core.manager import TaskManager

# Global task manager instance
_task_manager: TaskManager | None = None

def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    manager = get_task_manager()
    await manager.initialize()
    yield
    # Shutdown
    await manager.shutdown()

app = FastAPI(
    title="Ticket Grabber Suite API",
    description="跨平台抢票自动化工具后端API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")

# Serve frontend static files if built
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"detail": "Frontend not built"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "ticket-grabber-api"}
