"""
Work Schedule – FastAPI entry point.

Run standalone:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.shifts import router as shifts_router
from .api.history import router as history_router
from .api.ha import router as ha_router
from .events import router as events_router

MODE = os.environ.get("MODE", "standalone")

app = FastAPI(
    title="Work Schedule",
    version="1.0.0",
    description="Shift manager with undo, diff history, and HA integration",
)

# ── CORS (allow everything in dev / standalone) ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routers ─────────────────────────────────────────────
app.include_router(shifts_router)
app.include_router(history_router)
app.include_router(ha_router)
app.include_router(events_router)

# ── Static UI files ─────────────────────────────────────────
UI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")

if os.path.isdir(UI_DIR):
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

    @app.get("/", include_in_schema=False)
    def root():
        return FileResponse(os.path.join(UI_DIR, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "Work Schedule API", "docs": "/docs", "mode": MODE}


@app.get("/health")
def health():
    return {"status": "ok", "mode": MODE}
