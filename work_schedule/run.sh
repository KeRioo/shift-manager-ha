#!/bin/sh
# Work Schedule – entry point
# Works both inside HA (with bashio) and standalone (plain sh).

# If MODE is not already set by env, try bashio, fallback to 'standalone'
if [ -z "$MODE" ]; then
  if command -v bashio > /dev/null 2>&1; then
    MODE=$(bashio::config 'mode' 'standalone' 2>/dev/null || echo 'standalone')
  else
    MODE="standalone"
  fi
fi
export MODE

# DB path: honour env, then default
export DB_PATH="${DB_PATH:-/data/work_schedule.db}"

# Ensure the database directory exists
mkdir -p "$(dirname "$DB_PATH")"

echo "Starting Work Schedule add-on (mode=${MODE}, db=${DB_PATH})"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
