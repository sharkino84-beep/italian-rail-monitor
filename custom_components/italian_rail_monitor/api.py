"""Client for the ViaggiaTreno data service.

The service is not an official, guaranteed public API. Its availability and
response format may change without notice.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_BASE_URL, API_HEADERS

_LOGGER = logging.getLogger(__name__)


class ViaggiaTrenoApiError(Exception):
    """Raised when the ViaggiaTreno service cannot be queried."""


class ViaggiaTrenoClient:
    """Small asynchronous client for train status data."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def find_train(
        self, train_number: str, origin_station_code: str
    ) -> dict[str, str]:
        """Resolve a train number to its origin code and run timestamp."""
        url = f"{API_BASE_URL}/cercaNumeroTrenoTrenoAutocomplete/{train_number}"

        try:
            async with self._session.get(
                url, headers=API_HEADERS, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()
                body = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ViaggiaTrenoApiError("Unable to search for the train") from err

        for line in body.splitlines():
            if "|" not in line:
                continue
            _, identifier = line.rsplit("|", 1)
            parts = identifier.split("-")
            if (
                len(parts) >= 3
                and parts[0] == train_number
                and parts[1].upper() == origin_station_code.upper()
            ):
                return {
                    "train_number": parts[0],
                    "origin_station_code": parts[1],
                    "timestamp": parts[2],
                }

        raise ViaggiaTrenoApiError(
            "No matching train found for this number and origin station"
        )

    async def get_train_status(
        self, train_number: str, origin_station_code: str
    ) -> dict[str, Any]:
        """Fetch the current status for a train."""
        train = await self.find_train(train_number, origin_station_code)
        url = (
            f"{API_BASE_URL}/andamentoTreno/"
            f"{train['origin_station_code']}/"
            f"{train['train_number']}/"
            f"{train['timestamp']}"
        )

        try:
            async with self._session.get(
                url, headers=API_HEADERS, timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise ViaggiaTrenoApiError("Unable to retrieve train status") from err

        if not isinstance(data, dict):
            raise ViaggiaTrenoApiError("Unexpected response from train service")

        return data
