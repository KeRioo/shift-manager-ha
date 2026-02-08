# Changelog

## [1.0.3] - 2026-02-08

### Fixed
- Migrated from s6-overlay v2 (`/etc/services.d/`) to v3 (`/etc/s6-overlay/s6-rc.d/`) structure
- Added proper `type` (longrun), `run`, `finish` service files and `user/contents.d/` registration
- Fixed shebang to `#!/command/with-contenv bashio` (v3 syntax)

## [1.0.2] - 2026-02-08

### Fixed
- Fixed s6-overlay PID 1 issue: `run.sh` moved to `/etc/services.d/work-schedule/run` for proper s6 service management

## [1.0.1] - 2026-02-08

### Fixed
- Restructured repo for HA add-on discovery (`addon/` → `work_schedule/`)
- Added `repository.yaml` and `build.yaml` for valid HA add-on repository
- Added `image` field in `config.yaml` for pre-built Docker images
- Added GitHub Actions builder workflow for automatic image builds
- Removed unsupported architectures (armv7, i386)
- Fixed `s6-overlay-suexec: can only run as pid 1` with separate `Dockerfile.dev`

## [1.0.0] - 2026-02-08

### Added
- Quarterly calendar view with click-to-assign shifts
- Horizontal 3-row timeline view
- Full history log with snapshot-based undo (Ctrl+Z)
- Paint toolbar – click-to-paint shift mode (day8, day12, night12, eraser)
- Real-time sync across devices via SSE (Server-Sent Events)
- Home Assistant sensors: `sensor.next_shift_time`, `sensor.next_shift_type`
- REST API with full CRUD + undo
- Responsive dark theme UI
