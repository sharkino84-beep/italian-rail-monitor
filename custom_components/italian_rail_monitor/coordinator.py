"""Data update coordinator for Italian Rail Monitor."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ViaggiaTrenoApiError, ViaggiaTrenoClient
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class TrainDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate updates for one monitored train."""

    def __init__(
        self,
        hass: HomeAssistant,
        train_number: str,
        origin_station_code: str,
    ) -> None:
        self.client = ViaggiaTrenoClient(async_get_clientsession(hass))
        self.train_number = train_number
        self.origin_station_code = origin_station_code

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{train_number}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest train data."""
        try:
            return await self.client.get_train_status(
                self.train_number, self.origin_station_code
            )
        except ViaggiaTrenoApiError as err:
            raise UpdateFailed(str(err)) from err
