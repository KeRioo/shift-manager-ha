"""Work Schedule integration – setup."""

from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up from YAML configuration."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN not in config:
        # No YAML config - use defaults (auto-discover add-on)
        _LOGGER.info("Work Schedule: No configuration.yaml entry found, using add-on defaults")
        hass.data[DOMAIN]["config"] = {}
    else:
        hass.data[DOMAIN]["config"] = config[DOMAIN]
        _LOGGER.info("Work Schedule: loading with config %s", config[DOMAIN])
    
    # Always load sensors (with defaults or YAML config)
    await async_load_platform(hass, Platform.SENSOR, DOMAIN, {}, config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry (UI flow – future)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = dict(entry.data)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop("config", None)
    return unload_ok
