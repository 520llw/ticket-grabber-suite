# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ticket Grabber Suite** is a full-stack educational toolkit for automated ticket acquisition, featuring a FastAPI backend with Playwright browser automation and a React frontend. It supports three platforms: Damai (大麦), Maoyan (猫眼), and 12306 (Chinese railway).

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
python -m uvicorn main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev        # Dev server at http://localhost:5173
npm run build      # tsc && vite build
npm run preview    # Preview production build
```

The Vite dev server proxies `/api` requests to `http://localhost:8000/api`.

There are no test suites currently in this project.

## Architecture

### Data Flow
```
React UI (Zustand store) → Axios/EventSource
  → FastAPI routes (/api/tasks, /api/logs/stream)
    → TaskManager (in-memory, async locks)
      → Engine selection (ENGINE_MAP)
        → Playwright Chromium automation
          → Target platform (damai.cn / maoyan.com / kyfw.12306.cn)
```

### Backend Structure

- **`backend/main.py`** — FastAPI app entry point; CORS, lifespan, static file serving, mounts routes at `/api`
- **`backend/api/routes.py`** — All REST endpoints (task CRUD, start/stop, logs, SSE stream, system status)
- **`backend/core/manager.py`** — `TaskManager` singleton; owns all in-memory task/log state, async execution lifecycle, scheduling via `cron_time`, and SSE event listener queues
- **`backend/core/models.py`** — Pydantic models: `TaskConfig`, `TaskConfigCreate`, `TaskLog`, `SystemStatus`
- **`backend/config/settings.py`** — Centralized config (timeouts, anti-detection delays, platform URLs, user agent, headless default)
- **`backend/engines/`** — `BaseEngine` (abstract; Playwright init with anti-detection, screenshot), plus `DamaiEngine`, `MaoyanEngine`, `Train12306Engine`; registered in `ENGINE_MAP` in `__init__.py`

**Storage**: Fully in-memory—no database. Tasks and logs are lost on server restart.

**Real-time logs**: SSE via `sse-starlette`; the `TaskManager` maintains per-task async queues that feed the `/api/logs/{id}/stream` endpoint.

### Frontend Structure

- **`frontend/src/App.tsx`** — React Router v6 routes (`/`, `/tasks`, `/tasks/new`, `/tasks/:id`, `/settings`)
- **`frontend/src/store/useStore.ts`** — Zustand store; holds `tasks[]`, `logs{}`, `systemStatus`, `currentTask`
- **`frontend/src/services/api.ts`** — Axios client + `EventSource` wrapper; all HTTP calls go through `taskApi` / `systemApi`
- **`frontend/src/pages/`** — Dashboard, TaskList, TaskNew, TaskDetail (live log view via SSE), Settings
- **`frontend/src/components/`** — Layout, Sidebar, TaskCard, TaskForm, LogViewer, StatusBadge, CountdownTimer, PlatformIcon

**Styling**: Tailwind CSS dark theme (`#0f172a` base), emerald/teal accent palette, Framer Motion animations. Path alias `@` maps to `./src`.

### Adding a New Platform Engine

1. Create `backend/engines/<platform>.py` subclassing `BaseEngine` and implement `login()`, `grab()`, `check_stock()`
2. Register it in `backend/engines/__init__.py` → `ENGINE_MAP`
3. Add the platform URL to `backend/config/settings.py`
4. Add the platform option to the frontend `TaskForm` component
