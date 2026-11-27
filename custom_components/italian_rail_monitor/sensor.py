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
    name="Ritardo stimato alla fermata di salita",
    native_unit_of_measurement=UnitOfTime.MINUTES,
    icon="mdi:train-clock",
    entity_category=EntityCategory.DIAGNOSTIC,
)

PLATFORM_DESCRIPTION = SensorEntityDescription(
    key="boarding_platform",
    name="Binario previsto fermata di salita",
    icon="mdi:train-track",
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
            TrainBoardingPlatformSensor(entry),
            TrainNextStopSensor(entry),
            TrainNextStopDelaySensor(entry),
        ]
    )


class TrainDelaySensor(CoordinatorEntity, SensorEntity):
    """Represent the current reported train delay."""

    entity_description = DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        train_number = entry.data[CONF_TRAIN_NUMBER]
        self._attr_unique_id = f"{entry.entry_id}_delay"
        self._attr_name = f"RE {train_number} Ritardo"

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
    """Estimate boarding-station delay from the latest preceding departure."""

    entity_description = BOARDING_DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        train_number = entry.data[CONF_TRAIN_NUMBER]
        self._station_code = entry.options.get(
            CONF_BOARDING_STATION_CODE,
            entry.data.get(CONF_BOARDING_STATION_CODE, DEFAULT_BOARDING_STATION_CODE),
        )
        self._attr_unique_id = f"{entry.entry_id}_boarding_delay"
        self._attr_name = (
            f"RE {train_number} Ritardo stimato alla fermata di salita"
        )

    def _boarding_index(self) -> int | None:
        """Find the selected boarding stop in the route."""
        for index, stop in enumerate(self.coordinator.data.get("fermate", [])):
            if str(stop.get("id")) == str(self._station_code):
                return index
        return None

    def _latest_preceding_departure(
        self,
    ) -> tuple[dict[str, Any], int | float] | None:
        """Return the most recent preceding stop with an actual departure."""
        stops = self.coordinator.data.get("fermate", [])
        boarding_index = self._boarding_index()
        if boarding_index is None:
            return None

        for index in range(boarding_index - 1, -1, -1):
            stop = stops[index]
            delay = stop.get("ritardoPartenza")
            if stop.get("partenzaReale") is not None and isinstance(
                delay, (int, float)
            ):
                return stop, delay
        return None

    @property
    def native_value(self) -> int | float | None:
        """Return the latest actual departure delay before the boarding stop."""
        latest = self._latest_preceding_departure()
        return latest[1] if latest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose estimate source and selected boarding stop."""
        stops = self.coordinator.data.get("fermate", [])
        boarding_index = self._boarding_index()
        if boarding_index is None:
            return {
                "boarding_station_code": self._station_code,
                "boarding_station_found": False,
                "estimate_method": "last_actual_departure_before_boarding_station",
            }

        boarding_stop = stops[boarding_index]
        latest = self._latest_preceding_departure()
        source_stop, source_delay = latest if latest else (None, None)

        return {
            "boarding_station_code": self._station_code,
            "boarding_station": boarding_stop.get("stazione"),
            "boarding_station_found": True,
            "boarding_station_reached": (
                boarding_stop.get("arrivoReale") is not None
            ),
            "scheduled_arrival": boarding_stop.get("arrivo_teorico"),
            "arrival_delay_reported_by_service": boarding_stop.get(
                "ritardoArrivo"
            ),
            "estimated_delay": source_delay,
            "estimate_method": "last_actual_departure_before_boarding_station",
            "estimate_source_station": (
                source_stop.get("stazione") if source_stop else None
            ),
            "estimate_source_station_code": (
                source_stop.get("id") if source_stop else None
            ),
            "estimate_source_departure_time": (
                source_stop.get("partenzaReale") if source_stop else None
            ),
            "estimate_source_departure_delay": source_delay,
            "scheduled_platform": boarding_stop.get(
                "binarioProgrammatoArrivoDescrizione"
            ),
            "scheduled_platform_code": boarding_stop.get(
                "binarioProgrammatoArrivoCodice"
            ),
            "actual_platform": boarding_stop.get(
                "binarioEffettivoArrivoDescrizione"
            ),
            "actual_platform_code": boarding_stop.get(
                "binarioEffettivoArrivoCodice"
            ),
            "last_detection_station": self.coordinator.data.get(
                "stazioneUltimoRilevamento"
            ),
            "train_arrived": self.coordinator.data.get("arrivato"),
        }


class TrainBoardingPlatformSensor(CoordinatorEntity, SensorEntity):
    """Expose the planned arrival platform at the selected boarding stop."""

    entity_description = PLATFORM_DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        train_number = entry.data[CONF_TRAIN_NUMBER]
        self._station_code = entry.options.get(
            CONF_BOARDING_STATION_CODE,
            entry.data.get(CONF_BOARDING_STATION_CODE, DEFAULT_BOARDING_STATION_CODE),
        )
        self._attr_unique_id = f"{entry.entry_id}_boarding_platform"
        self._attr_name = (
            f"RE {train_number} Binario previsto fermata di salita"
        )

    def _boarding_stop(self) -> dict[str, Any] | None:
        """Find the selected boarding stop in the journey."""
        for stop in self.coordinator.data.get("fermate", []):
            if str(stop.get("id")) == str(self._station_code):
                return stop
        return None

    @property
    def native_value(self) -> str | None:
        """Return the planned arrival platform."""
        stop = self._boarding_stop()
        if stop is None:
            return None
        value = stop.get("binarioProgrammatoArrivoDescrizione")
        if value in (None, ""):
            value = stop.get("binarioProgrammatoArrivoCodice")
        return str(value) if value not in (None, "") else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose planned and actual platform details."""
        stop = self._boarding_stop()
        if stop is None:
            return {"boarding_station_code": self._station_code}
        return {
            "boarding_station": stop.get("stazione"),
            "scheduled_platform": stop.get(
                "binarioProgrammatoArrivoDescrizione"
            ),
            "scheduled_platform_code": stop.get(
                "binarioProgrammatoArrivoCodice"
            ),
            "actual_platform": stop.get("binarioEffettivoArrivoDescrizione"),
            "actual_platform_code": stop.get("binarioEffettivoArrivoCodice"),
        }



def _next_stop_index(data: dict[str, Any]) -> int | None:
    """Find the index of the stop after the latest detected station."""
    stops = data.get("fermate", [])
    if not isinstance(stops, list) or not stops:
        return None

    last_station = data.get("stazioneUltimoRilevamento")
    if isinstance(last_station, str) and last_station.strip():
        normalized = " ".join(last_station.casefold().split())
        for index in range(len(stops) - 1, -1, -1):
            station = stops[index].get("stazione")
            if isinstance(station, str) and " ".join(
                station.casefold().split()
            ) == normalized:
                return index + 1 if index + 1 < len(stops) else None

    # Fallback when the service does not provide a matching detection station.
    last_departed_index = None
    for index, stop in enumerate(stops):
        if stop.get("partenzaReale") is not None:
            last_departed_index = index

    if last_departed_index is not None and last_departed_index + 1 < len(stops):
        return last_departed_index + 1
    return None


def _next_stop(data: dict[str, Any]) -> dict[str, Any] | None:
    """Return the next stop in the route."""
    stops = data.get("fermate", [])
    index = _next_stop_index(data)
    return stops[index] if index is not None else None


def _next_stop_departure_delay(
    data: dict[str, Any],
) -> tuple[dict[str, Any], int | float] | None:
    """Return the latest actual departure delay before the next stop."""
    stops = data.get("fermate", [])
    next_index = _next_stop_index(data)
    if next_index is None:
        return None

    for index in range(next_index - 1, -1, -1):
        stop = stops[index]
        delay = stop.get("ritardoPartenza")
        if stop.get("partenzaReale") is not None and isinstance(
            delay, (int, float)
        ):
            return stop, delay
    return None


NEXT_STOP_DESCRIPTION = SensorEntityDescription(
    key="next_stop",
    name="Prossima fermata",
    icon="mdi:train",
    entity_category=EntityCategory.DIAGNOSTIC,
)

NEXT_STOP_DELAY_DESCRIPTION = SensorEntityDescription(
    key="next_stop_delay",
    name="Ritardo previsto prossima fermata",
    native_unit_of_measurement=UnitOfTime.MINUTES,
    icon="mdi:train-clock",
    entity_category=EntityCategory.DIAGNOSTIC,
)


class TrainNextStopSensor(CoordinatorEntity, SensorEntity):
    """Show the next station after the latest train detection."""

    entity_description = NEXT_STOP_DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        train_number = entry.data[CONF_TRAIN_NUMBER]
        self._attr_unique_id = f"{entry.entry_id}_next_stop"
        self._attr_name = f"RE {train_number} Prossima fermata"

    @property
    def native_value(self) -> str | None:
        stop = _next_stop(self.coordinator.data)
        return stop.get("stazione") if stop else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        stop = _next_stop(self.coordinator.data)
        if stop is None:
            return {
                "last_detection_station": self.coordinator.data.get(
                    "stazioneUltimoRilevamento"
                )
            }
        return {
            "last_detection_station": self.coordinator.data.get(
                "stazioneUltimoRilevamento"
            ),
            "scheduled_arrival": stop.get("arrivo_teorico"),
            "estimated_arrival": stop.get("arrivoStimato"),
            "arrival_delay": stop.get("ritardoArrivo"),
            "scheduled_departure": stop.get("partenza_teorica"),
            "platform": stop.get("binarioProgrammatoArrivoDescrizione")
            or stop.get("binarioProgrammatoArrivoCodice"),
        }


class TrainNextStopDelaySensor(CoordinatorEntity, SensorEntity):
    """Show the estimated arrival delay at the next station."""

    entity_description = NEXT_STOP_DELAY_DESCRIPTION

    def __init__(self, entry: ItalianRailMonitorConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        train_number = entry.data[CONF_TRAIN_NUMBER]
        self._attr_unique_id = f"{entry.entry_id}_next_stop_delay"
        self._attr_name = f"RE {train_number} Ritardo previsto prossima fermata"

    @property
    def native_value(self) -> int | float | None:
        latest = _next_stop_departure_delay(self.coordinator.data)
        return latest[1] if latest else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        next_stop = _next_stop(data)
        latest = _next_stop_departure_delay(data)
        source_stop, source_delay = latest if latest else (None, None)
        return {
            "next_station": next_stop.get("stazione") if next_stop else None,
            "estimate_method": "latest_actual_departure_before_next_stop",
            "estimate_source_station": (
                source_stop.get("stazione") if source_stop else None
            ),
            "estimate_source_departure_time": (
                source_stop.get("partenzaReale") if source_stop else None
            ),
            "estimate_source_departure_delay": source_delay,
            "last_detection_station": data.get("stazioneUltimoRilevamento"),
        }
