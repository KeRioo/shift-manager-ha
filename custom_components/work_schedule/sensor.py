"""Work Schedule sensors – next shift time & type."""

from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_HOST,
    DEFAULT_PORT,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_SECONDS)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up sensors from YAML platform config."""
    conf = hass.data.get(DOMAIN, {}).get("config", {})
    host = conf.get(CONF_HOST, DEFAULT_HOST)
    port = conf.get(CONF_PORT, DEFAULT_PORT)
    base_url = f"http://{host}:{port}"

    _LOGGER.info("Setting up Work Schedule sensors with base_url: %s", base_url)

    async_add_entities(
        [
            NextShiftTimeSensor(base_url),
            NextShiftTypeSensor(base_url),
        ],
        update_before_add=True,
    )


# ── Shared fetch ───────────────────────────────────────────────

async def _fetch_next_shift(base_url: str) -> dict | None:
    """GET /api/next_shift from the add-on."""
    url = f"{base_url}/api/next_shift"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.warning("Work Schedule API returned %s", resp.status)
    except Exception:
        _LOGGER.exception("Failed to reach Work Schedule API at %s", url)
    return None


# ── Sensor: next_shift_time ────────────────────────────────────

class NextShiftTimeSensor(SensorEntity):
    """Shows the datetime of the next shift."""

    _attr_name = "Next Shift Time"
    _attr_unique_id = "work_schedule_next_shift_time"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._attr_native_value = None
        self._extra: dict = {}

    async def async_update(self) -> None:
        _LOGGER.debug("Updating NextShiftTimeSensor from %s", self._base_url)
        data = await _fetch_next_shift(self._base_url)
        if data:
            # value like "2026-02-09T07:00"
            self._attr_native_value = data.get("datetime")
            _LOGGER.debug("NextShiftTimeSensor updated: %s", self._attr_native_value)
        else:
            _LOGGER.warning("NextShiftTimeSensor: no data from API")
            self._extra = data
        else:
            self._attr_native_value = None

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "shift_type": self._extra.get("type"),
            "start": self._extra.get("start"),
            "end": self._extra.get("end"),
        }


# ── Sensor: next_shift_type ───────────────────────────────────

class NextShiftTypeSensor(SensorEntity):
    """Shows the type of the next shift (day8 / day12 / night12)."""

    _attr_name = "Next Shift Type"
    _attr_unique_id = "work_schedule_next_shift_type"
    _attr_icon = "mdi:briefcase-outline"

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url
        self._attr_native_value = None
        self._extra: dict = {}

    async def async_update(self) -> None:
        _LOGGER.debug("Updating NextShiftTypeSensor from %s", self._base_url)
        data = await _fetch_next_shift(self._base_url)
        if data:
            self._attr_native_value = data.get("type")
            self._extra = data
            _LOGGER.debug("NextShiftTypeSensor updated: %s", self._attr_native_value)
        else:
            self._attr_native_value = None
            _LOGGER.warning("NextShiftTypeSensor: no data from API")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "datetime": self._extra.get("datetime"),
            "start": self._extra.get("start"),
            "end": self._extra.get("end"),
        }
