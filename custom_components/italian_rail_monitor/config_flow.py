"""Config flow for Italian Rail Monitor."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ViaggiaTrenoApiError, ViaggiaTrenoClient
from .const import (
    CONF_BOARDING_STATION_CODE,
    CONF_ORIGIN_STATION_CODE,
    CONF_TRAIN_NUMBER,
    DEFAULT_BOARDING_STATION_CODE,
    DOMAIN,
)


def _station_options(data):
    """Build a station-code to display-name mapping from a train response."""
    options = {}
    for stop in data.get("fermate", []):
        code = stop.get("id")
        name = stop.get("stazione")
        if code and name:
            options[str(code)] = str(name)
    return options


def _station_selector(options):
    """Return a dropdown selector for the stations on the selected route."""
    choices = [
        {"value": code, "label": name}
        for code, name in options.items()
    ]
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=choices,
            mode=selector.SelectSelectorMode.DROPDOWN,
            sort=False,
        )
    )


class ItalianRailMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Italian Rail Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Configure train number and origin station."""
        errors = {}

        if user_input is not None:
            train_number = str(user_input[CONF_TRAIN_NUMBER]).strip()
            station_code = str(user_input[CONF_ORIGIN_STATION_CODE]).strip().upper()

            client = ViaggiaTrenoClient(async_get_clientsession(self.hass))
            try:
                train_data = await client.get_train_status(train_number, station_code)
            except ViaggiaTrenoApiError:
                errors["base"] = "train_not_found"
            else:
                stations = _station_options(train_data)
                if not stations:
                    errors["base"] = "stations_unavailable"
                else:
                    await self.async_set_unique_id(f"{train_number}_{station_code}")
                    self._abort_if_unique_id_configured()
                    self._train_number = train_number
                    self._origin_station_code = station_code
                    self._stations = stations
                    return await self.async_step_boarding()

        schema = vol.Schema(
            {
                vol.Required(CONF_TRAIN_NUMBER): str,
                vol.Required(CONF_ORIGIN_STATION_CODE): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_boarding(self, user_input=None):
        """Select the boarding station from the train's stops."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"RE {self._train_number}",
                data={
                    CONF_TRAIN_NUMBER: self._train_number,
                    CONF_ORIGIN_STATION_CODE: self._origin_station_code,
                    CONF_BOARDING_STATION_CODE: user_input[CONF_BOARDING_STATION_CODE],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_BOARDING_STATION_CODE): _station_selector(
                    self._stations
                )
            }
        )
        return self.async_show_form(
            step_id="boarding", data_schema=schema
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow for an existing train."""
        return ItalianRailMonitorOptionsFlow(config_entry)


class ItalianRailMonitorOptionsFlow(config_entries.OptionsFlow):
    """Configure the boarding station for an existing train."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Select the boarding station from the current train route."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_BOARDING_STATION_CODE: user_input[
                        CONF_BOARDING_STATION_CODE
                    ]
                },
            )

        train_number = self.config_entry.data[CONF_TRAIN_NUMBER]
        origin_code = self.config_entry.data[CONF_ORIGIN_STATION_CODE]
        client = ViaggiaTrenoClient(async_get_clientsession(self.hass))
        errors = {}
        try:
            train_data = await client.get_train_status(train_number, origin_code)
            stations = _station_options(train_data)
        except ViaggiaTrenoApiError:
            stations = {}

        if not stations:
            errors["base"] = "stations_unavailable"
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_BOARDING_STATION_CODE,
                        default=self.config_entry.options.get(
                            CONF_BOARDING_STATION_CODE,
                            self.config_entry.data.get(
                                CONF_BOARDING_STATION_CODE,
                                DEFAULT_BOARDING_STATION_CODE,
                            ),
                        ),
                    ): str
                }
            )
        else:
            current_code = self.config_entry.options.get(
                CONF_BOARDING_STATION_CODE,
                self.config_entry.data.get(
                    CONF_BOARDING_STATION_CODE, DEFAULT_BOARDING_STATION_CODE
                ),
            )
            if current_code not in stations:
                current_code = next(iter(stations))
            schema = vol.Schema(
                {
                    vol.Required(
                        CONF_BOARDING_STATION_CODE, default=current_code
                    ): _station_selector(stations)
                }
            )

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
