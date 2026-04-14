"""Integrare CNAIR eRovinieta Free pentru Home Assistant."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import ErovinietaFreeAPI
from .const import (
    CONF_PASSWORD,
    CONF_UPDATE_INTERVAL,
    CONF_USERNAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import ErovinietaFreeCoordinator
from .exceptions import ErovinietaAuthError, ErovinietaConnectionError

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setează integrarea."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurează integrarea dintr-o intrare de configurare."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = ErovinietaFreeAPI(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        await api.authenticate()
    except ErovinietaAuthError as err:
        raise ConfigEntryAuthFailed(
            f"Autentificare eșuată: {err}"
        ) from err
    except (ErovinietaConnectionError, Exception) as err:
        raise ConfigEntryNotReady(
            f"Serviciul eRovinieta nu este disponibil: {err}"
        ) from err

    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
    )

    coordinator = ErovinietaFreeCoordinator(
        hass,
        api,
        config_entry=entry,
        update_interval=update_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Aplică modificările de opțiuni."""
    coordinator: ErovinietaFreeCoordinator = hass.data[DOMAIN][entry.entry_id]

    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
    )
    coordinator.update_interval = timedelta(seconds=update_interval)
    await coordinator.async_request_refresh()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Dezinstalează integrarea."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id)

    if unload_ok and not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)

    return unload_ok