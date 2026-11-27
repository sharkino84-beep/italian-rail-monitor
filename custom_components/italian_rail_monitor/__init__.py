"""Italian Rail Monitor integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ORIGIN_STATION_CODE, CONF_TRAIN_NUMBER, PLATFORMS
from .coordinator import TrainDataCoordinator

type ItalianRailMonitorConfigEntry = ConfigEntry[TrainDataCoordinator]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML (not supported)."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ItalianRailMonitorConfigEntry
) -> bool:
    """Set up a configured train."""
    coordinator = TrainDataCoordinator(
        hass,
        entry.data[CONF_TRAIN_NUMBER],
        entry.data[CONF_ORIGIN_STATION_CODE],
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ItalianRailMonitorConfigEntry
) -> bool:
    """Unload a configured train."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
