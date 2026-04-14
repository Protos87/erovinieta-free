"""Coordinator pentru integrarea CNAIR eRovinieta Free."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import ErovinietaFreeAPI
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN
from .exceptions import ErovinietaAuthError, ErovinietaConnectionError
from .helpers import safe_get

_LOGGER = logging.getLogger(__name__)


class ErovinietaFreeCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator centralizat pentru datele din API-ul eRovinieta."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: ErovinietaFreeAPI,
        config_entry: ConfigEntry,
        update_interval: int = DEFAULT_UPDATE_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=update_interval),
            config_entry=config_entry,
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        try:
            return await self._fetch_all_data()
        except ErovinietaAuthError as err:
            raise ConfigEntryAuthFailed(
                f"Autentificare eșuată: {err}"
            ) from err
        except ErovinietaConnectionError as err:
            raise UpdateFailed(
                f"Eroare de conexiune: {err}"
            ) from err
        except Exception as err:
            raise UpdateFailed(
                f"Eroare neașteptată la actualizarea datelor: {err}"
            ) from err

    async def _fetch_all_data(self) -> dict:
        user_data = await self._safe_fetch(
            self.api.get_user_data, {}, "date utilizator"
        )

        paginated_data = await self._safe_fetch(
            self.api.get_paginated_data, {}, "date vehicule"
        )
        vehicule = [
            safe_get(v.get("entity"), {})
            for v in safe_get(paginated_data.get("view"), [])
        ]

        countries_data = await self._safe_fetch(
            self.api.get_countries, [], "lista de țări"
        )

        treceri_per_vehicul: dict[str, list] = {}
        for vehicul in vehicule:
            vin = safe_get(vehicul.get("vin"))
            plate_no = safe_get(vehicul.get("plateNo"))
            cert = safe_get(vehicul.get("certificateSeries"))
            if not all([vin, plate_no, cert]):
                continue

            try:
                result = await self.api.get_treceri_pod(vin, plate_no, cert)
                treceri_per_vehicul[plate_no] = safe_get(
                    result.get("detectionList"), []
                )
            except ErovinietaAuthError:
                raise
            except Exception as err:
                _LOGGER.warning(
                    "Eroare la obținerea trecerilor pentru %s: %s", plate_no, err
                )
                treceri_per_vehicul[plate_no] = []

        return {
            "user_data": user_data,
            "paginated_data": paginated_data,
            "countries_data": countries_data,
            "treceri_pod_per_vehicul": treceri_per_vehicul,
        }

    async def _safe_fetch(self, func, default, name: str):
        try:
            return await func()
        except ErovinietaAuthError:
            raise
        except Exception as err:
            _LOGGER.warning("Eroare la obținerea %s: %s", name, err)
            return default