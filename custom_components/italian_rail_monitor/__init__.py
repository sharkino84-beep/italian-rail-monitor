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
        entry.data.get(CONF_ORIGIN_STATION_CODE),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ItalianRailMonitorConfigEntry
) -> bool:
    """Unload the integration platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant, entry: ItalianRailMonitorConfigEntry
) -> None:
    """Reload the integration when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
