"""Sensor platform for Italian Rail Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from . import ItalianRailMonitorConfigEntry
from .const import CONF_TRAIN_NUMBER


DESCRIPTION = SensorEntityDescription(
    key="delay",
    name="Ritardo",
    native_unit_of_measurement=UnitOfTime.MINUTES,
    icon="mdi:train",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ItalianRailMonitorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up train sensors."""
    async_add_entities([TrainDelaySensor(entry)])


class TrainDelaySensor(CoordinatorEntity, SensorEntity):
    """Represent the current reported train delay."""

    entity_description = DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_delay"
        self._attr_name = f"RE {entry.data[CONF_TRAIN_NUMBER]} Ritardo"

    @property
    def native_value(self) -> int | None:
        """Return the delay in minutes, if available."""
        value = self.coordinator.data.get("ritardo")
        return value if isinstance(value, int) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose useful raw service information for automations."""
        data = self.coordinator.data
        return {
            "train_number": data.get("numeroTreno"),
            "origin": data.get("origine"),
            "destination": data.get("destinazione"),
            "last_detection_station": data.get("stazioneUltimoRilevamento"),
            "last_detection_time": data.get("oraUltimoRilevamento"),
            "running": data.get("circolante"),
            "arrived": data.get("arrivato"),
            "stops": data.get("fermate", []),
            "suppressed_stops": data.get("fermateSoppresse", []),
            "notices": data.get("provvedimenti", []),
            "anomalies": data.get("anormalita", []),
            "reports": data.get("segnalazioni", []),
        }
