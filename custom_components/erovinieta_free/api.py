"""Manager API async pentru integrarea CNAIR eRovinieta Free."""

from __future__ import annotations

import logging
import time

import aiohttp
from yarl import URL

from .const import (
    TOKEN_VALIDITY_SECONDS,
    URL_GET_COUNTRIES,
    URL_GET_PAGINATED,
    URL_GET_USER_DATA,
    URL_LOGIN,
    URL_TRECERI_POD,
)
from .exceptions import (
    ErovinietaApiError,
    ErovinietaAuthError,
    ErovinietaConnectionError,
)

_LOGGER = logging.getLogger(__name__)


class ErovinietaFreeAPI:
    """Client API async pentru serviciul CNAIR eRovinieta."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._token_time: float = 0

    @property
    def authenticated(self) -> bool:
        return (time.monotonic() - self._token_time) < TOKEN_VALIDITY_SECONDS

    async def authenticate(self) -> None:
        """Autentifică utilizatorul și stochează cookie-ul JSESSIONID."""
        payload = {
            "username": self._username,
            "password": self._password,
            "_spring_security_remember_me": "on",
        }
        self._session.cookie_jar.clear()

        try:
            async with self._session.post(URL_LOGIN, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise ErovinietaAuthError(
                        f"Autentificare eșuată (HTTP {resp.status}): {text[:200]}"
                    )
        except aiohttp.ClientError as err:
            raise ErovinietaConnectionError(
                f"Eroare de conexiune la autentificare: {err}"
            ) from err

        cookies = self._session.cookie_jar.filter_cookies(URL(URL_LOGIN))
        if "JSESSIONID" not in cookies:
            raise ErovinietaAuthError(
                "Cookie-ul JSESSIONID nu a fost primit după autentificare."
            )

        self._token_time = time.monotonic()
        _LOGGER.debug("Autentificare reușită pentru %s", self._username)

    async def _ensure_auth(self) -> None:
        if not self.authenticated:
            await self.authenticate()

    async def _request(
        self,
        method: str,
        url: str,
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> dict | list:
        await self._ensure_auth()

        try:
            return await self._do_request(method, url, json_data, headers)
        except ErovinietaAuthError:
            await self.authenticate()
            return await self._do_request(method, url, json_data, headers)

    async def _do_request(
        self,
        method: str,
        url: str,
        json_data: dict | None = None,
        headers: dict | None = None,
    ) -> dict | list:
        kwargs: dict = {}
        if json_data is not None:
            kwargs["json"] = json_data
        if headers is not None:
            kwargs["headers"] = headers

        try:
            async with self._session.request(method, url, **kwargs) as resp:
                if resp.status in (401, 403):
                    raise ErovinietaAuthError(f"HTTP {resp.status}")
                if resp.status != 200:
                    text = await resp.text()
                    raise ErovinietaApiError(
                        f"Eroare API (HTTP {resp.status}): {text[:200]}"
                    )

                data = await resp.json(content_type=None)
                if data is None:
                    raise ErovinietaApiError("Răspuns JSON gol de la server.")
                return data
        except aiohttp.ClientError as err:
            raise ErovinietaConnectionError(
                f"Cerere eșuată către {url}: {err}"
            ) from err

    @staticmethod
    def _add_timestamp(base_url: str, first_param: bool = True) -> str:
        ts = int(time.time() * 1000)
        sep = "?" if first_param else "&"
        return f"{base_url}{sep}timestamp={ts}"

    async def get_user_data(self) -> dict:
        url = self._add_timestamp(URL_GET_USER_DATA)
        return await self._request("GET", url)

    async def get_paginated_data(self, limit: int = 20, page: int = 0) -> dict:
        base = f"{URL_GET_PAGINATED}?limit={limit}&page={page}"
        url = self._add_timestamp(base, first_param=False)
        return await self._request("GET", url)

    async def get_countries(self) -> list:
        return await self._request("GET", URL_GET_COUNTRIES)

    async def get_treceri_pod(
        self,
        vin: str,
        plate_no: str,
        certificate_series: str,
        period: int = 4,
    ) -> dict:
        payload = {
            "vin": vin,
            "plateNo": plate_no,
            "certificateSeries": certificate_series,
            "vehicleFleetEntity": {
                "certificateSeries": certificate_series,
                "plateNo": plate_no,
                "vin": vin,
            },
            "period": period,
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }
        return await self._request(
            "POST", URL_TRECERI_POD, json_data=payload, headers=headers
        )