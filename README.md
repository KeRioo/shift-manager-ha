# Work Schedule for Home Assistant

Shift / work schedule manager with:
- 📆 **Quarterly calendar** – click to assign shifts
- 📊 **Timeline** – continuous month view
- 🕘 **History** – full audit log with **Undo (Ctrl+Z)**
- 🏠 **Home Assistant sensors** – `sensor.next_shift_time`, `sensor.next_shift_type`

## Architecture

```
Browser UI  ←→  FastAPI Backend (Add-on)  ←→  HA Integration (sensors)
                       │
                   SQLite DB
```

## Quick start (standalone, no HA)

```bash
# Option A – Docker
docker compose -f docker-compose.dev.yml up --build

# Option B – local Python
cd addon
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- **UI:** http://localhost:8000/ui
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/shifts?from=&to=` | Shifts in range |
| `GET` | `/api/shifts/{date}` | Single shift |
| `PUT` | `/api/shifts/{date}` | Create/update (`{"type":"night12"}`) |
| `DELETE` | `/api/shifts/{date}` | Remove shift |
| `POST` | `/api/undo` | Undo last change |
| `GET` | `/api/history` | Change log |
| `GET` | `/api/next_shift` | Next upcoming shift (for HA) |
| `GET` | `/api/shift_types` | Available shift definitions |

### Shift types

| Key | Start | End |
|-----|-------|-----|
| `day8` | 07:00 | 15:00 |
| `day12` | 07:00 | 19:00 |
| `night12` | 19:00 | 07:00 |

## Home Assistant integration

### Method 1: With Add-on (recommended)

1. Add this repo as a HA add-on repository
2. Install **Work Schedule** add-on
3. Start the add-on
4. Copy `custom_components/work_schedule/` to your HA `config/custom_components/` directory
5. Restart Home Assistant
6. Sensors will automatically discover the add-on (no configuration.yaml needed!)

Sensors created:
- `sensor.next_shift_time` (device_class: timestamp)
- `sensor.next_shift_type`

### Method 2: External API server

If running the API server externally (not as add-on), add to `configuration.yaml`:

```yaml
work_schedule:
  host: 192.168.1.100  # Your API server IP
  port: 8000
```

Polling interval: **5 minutes**.
