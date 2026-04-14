"""Config flow pentru integrarea CNAIR eRovinieta Free."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ErovinietaFreeAPI
from .const import (
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    CONF_USERNAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .exceptions import ErovinietaAuthError, ErovinietaConnectionError


class ErovinietaFreeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flow de configurare pentru eRovinieta Free."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = ErovinietaFreeAPI(
                session,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                await api.authenticate()
            except ErovinietaAuthError:
                errors["base"] = "invalid_auth"
            except ErovinietaConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"eRovinieta Free ({user_input[CONF_USERNAME]})",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    options={
                        CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=DEFAULT_UPDATE_INTERVAL,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_UPDATE_INTERVAL,
                        max=MAX_UPDATE_INTERVAL,
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )