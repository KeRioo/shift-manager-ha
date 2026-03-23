# Copilot Instructions for shift-manager-ha

## Repository Overview

This repository contains a **shift/work schedule manager** built as a Home Assistant add-on. It consists of two main components:

1. **`work_schedule/` – HA Add-on (FastAPI backend + Web UI)**
   - Python FastAPI backend serving a REST API and static HTML/JS UI
   - SQLite database (via SQLAlchemy + aiosqlite) for storing shift data
   - Supports undo/redo, full history log, and SSE events for live UI updates
   - Runs inside Home Assistant as an ingress add-on (port 8000)

2. **`custom_components/work_schedule/` – HA Custom Integration**
   - Home Assistant custom component (YAML-configured)
   - Polls the add-on's `/api/next_shift` endpoint every 5 minutes
   - Exposes two sensors: `sensor.next_shift_time` (timestamp) and `sensor.next_shift_type`
   - Auto-discovers the add-on via well-known hostnames; falls back to configured `host`/`port`

## Architecture

```
Browser UI  ←→  FastAPI Backend (work_schedule add-on)  ←→  HA Integration (sensors)
                       │
                   SQLite DB
```

## Key Files

| Path | Purpose |
|------|---------|
| `work_schedule/app/main.py` | FastAPI app entry point, mounts routers and static UI |
| `work_schedule/app/api/shifts.py` | CRUD endpoints for shifts |
| `work_schedule/app/api/ha.py` | `/api/next_shift` endpoint consumed by the HA integration |
| `work_schedule/app/api/history.py` | Audit log and undo endpoints |
| `work_schedule/app/models.py` | SQLAlchemy ORM models |
| `work_schedule/app/schemas.py` | Pydantic request/response schemas |
| `work_schedule/app/storage.py` | Database engine/session factory |
| `work_schedule/app/shifts.py` | Business logic for shift operations |
| `work_schedule/app/undo.py` | Undo stack implementation |
| `work_schedule/config.yaml` | Home Assistant add-on manifest |
| `work_schedule/requirements.txt` | Python dependencies |
| `custom_components/work_schedule/sensor.py` | HA sensor entities |
| `custom_components/work_schedule/const.py` | Constants (domain, default host/port, scan interval) |
| `custom_components/work_schedule/manifest.json` | HA integration manifest |

## Shift Types

| Key | Start | End |
|-----|-------|-----|
| `day8` | 07:00 | 15:00 |
| `day12` | 07:00 | 19:00 |
| `night12` | 19:00 | 07:00 |

## Development

### Running the add-on locally (standalone)

```bash
# Docker
docker compose up --build

# Local Python (from work_schedule/)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- **UI:** http://localhost:8000/ui
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

### Running tests

Tests are in `work_schedule/tests/` and use **pytest** with **FastAPI TestClient**.

```bash
cd work_schedule
pip install -r requirements.txt
pip install pytest httpx
pytest
```

Each test gets an isolated **in-memory SQLite** database (see `conftest.py`). No external services are required.

Test configuration lives in `work_schedule/pytest.ini`.

### CI

The GitHub Actions workflow (`.github/workflows/builder.yaml`) builds the add-on Docker image for `amd64` and `aarch64`. It uses `home-assistant/builder` and runs on push/PR to `main`.

## Code Conventions

- **Python style:** `from __future__ import annotations`, type hints throughout, `_LOGGER = logging.getLogger(__name__)` for logging
- **FastAPI routers:** each API module exports a `router = APIRouter()` included in `main.py`
- **Pydantic schemas** for all request/response bodies; ORM models are SQLAlchemy
- **HA integration** follows standard Home Assistant patterns: `async_setup`, `async_setup_entry`, `async_unload_entry` in `__init__.py`; sensor entities extend `SensorEntity`
- **Constants** live in `custom_components/work_schedule/const.py`
- **No config flow** – the HA integration is YAML-only (`config_flow: false` in `manifest.json`)
- Version is kept in sync across `manifest.json`, `work_schedule/config.yaml`, and `CHANGELOG.md`
