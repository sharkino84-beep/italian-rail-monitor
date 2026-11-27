"""Config flow for Italian Rail Monitor."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ViaggiaTrenoApiError, ViaggiaTrenoClient
from .const import CONF_ORIGIN_STATION_CODE, CONF_TRAIN_NUMBER, DOMAIN


class ItalianRailMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Italian Rail Monitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Configure a train to monitor."""
        errors = {}

        if user_input is not None:
            train_number = str(user_input[CONF_TRAIN_NUMBER]).strip()
            station_code = str(user_input[CONF_ORIGIN_STATION_CODE]).strip().upper()

            client = ViaggiaTrenoClient(async_get_clientsession(self.hass))
            try:
                await client.find_train(train_number, station_code)
            except ViaggiaTrenoApiError:
                errors["base"] = "train_not_found"
            else:
                await self.async_set_unique_id(f"{train_number}_{station_code}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"RE {train_number}",
                    data={
                        CONF_TRAIN_NUMBER: train_number,
                        CONF_ORIGIN_STATION_CODE: station_code,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_TRAIN_NUMBER): str,
                vol.Required(CONF_ORIGIN_STATION_CODE): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return ItalianRailMonitorOptionsFlow()


class ItalianRailMonitorOptionsFlow(config_entries.OptionsFlow):
    """Options flow placeholder for future settings."""
