"""Constants for the Work Schedule integration."""

DOMAIN = "work_schedule"
# Add-on hostname in Home Assistant (slug from config.yaml)
DEFAULT_HOST = "b467121c-work-schedule"
DEFAULT_PORT = 8000
SCAN_INTERVAL_SECONDS = 300      # 5 min
CONF_HOST = "host"
CONF_PORT = "port"

# Add-on detection: try multiple possible hostnames
ADDON_HOSTNAMES = [
    "b467121c-work-schedule",  # Main hostname
    "work-schedule",            # Potential alternative
    "localhost",                # Fallback
]
