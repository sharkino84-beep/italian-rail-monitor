"""Sensor platform for Italian Rail Monitor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ItalianRailMonitorConfigEntry
from .const import (
    CONF_BOARDING_STATION_CODE,
    CONF_TRAIN_NUMBER,
    DEFAULT_BOARDING_STATION_CODE,
)


DESCRIPTION = SensorEntityDescription(
    key="delay",
    name="Ritardo",
    native_unit_of_measurement=UnitOfTime.MINUTES,
    icon="mdi:train",
    entity_category=EntityCategory.DIAGNOSTIC,
)

BOARDING_DESCRIPTION = SensorEntityDescription(
    key="boarding_delay",
    name="Ritardo fermata di salita",
    native_unit_of_measurement=UnitOfTime.MINUTES,
    icon="mdi:train-clock",
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass,
    entry: ItalianRailMonitorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up train sensors."""
    async_add_entities(
        [
            TrainDelaySensor(entry),
            TrainBoardingDelaySensor(entry),
        ]
    )


class TrainDelaySensor(CoordinatorEntity, SensorEntity):
    """Represent the current reported train delay."""

    entity_description = DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        self._attr_unique_id = f"{entry.entry_id}_delay"
        self._attr_name = f"RE {entry.data[CONF_TRAIN_NUMBER]} Ritardo"

    @property
    def native_value(self) -> int | float | None:
        """Return the delay in minutes, if available."""
        value = self.coordinator.data.get("ritardo")
        return value if isinstance(value, (int, float)) else None

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


class TrainBoardingDelaySensor(CoordinatorEntity, SensorEntity):
    """Report the delay currently forecast for the selected boarding stop."""

    entity_description = BOARDING_DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        self._entry = entry
        self._station_code = entry.options.get(
            CONF_BOARDING_STATION_CODE, DEFAULT_BOARDING_STATION_CODE
        )
        self._attr_unique_id = f"{entry.entry_id}_boarding_delay"

    def _boarding_stop(self) -> dict[str, Any] | None:
        """Find the configured boarding stop in the journey."""
        for stop in self.coordinator.data.get("fermate", []):
            if stop.get("id") == self._station_code:
                return stop
        return None

    @property
    def native_value(self) -> int | float | None:
        """Return ViaggiaTreno's current arrival-delay estimate for the stop."""
        stop = self._boarding_stop()
        if stop is None:
            return None

        value = stop.get("ritardoArrivo")
        if not isinstance(value, (int, float)):
            value = stop.get("ritardo")
        return value if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the selected stop and whether its arrival is already recorded."""
        stop = self._boarding_stop()
        if stop is None:
            return {
                "boarding_station_code": self._station_code,
                "boarding_station_found": False,
            }

        return {
            "boarding_station_code": self._station_code,
            "boarding_station": stop.get("stazione"),
            "boarding_station_found": True,
            "boarding_station_reached": stop.get("arrivoReale") is not None,
            "scheduled_arrival": stop.get("arrivo_teorico"),
            "estimated_arrival": stop.get("effettiva"),
            "arrival_delay": stop.get("ritardoArrivo"),
            "departure_delay": stop.get("ritardoPartenza"),
            "last_detection_station": self.coordinator.data.get(
                "stazioneUltimoRilevamento"
            ),
            "train_arrived": self.coordinator.data.get("arrivato"),
        }
