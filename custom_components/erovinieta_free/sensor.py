"""Platforma sensor pentru integrarea CNAIR eRovinieta Free."""

from __future__ import annotations

import time

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant

from .const import ATTRIBUTION, DOMAIN, VERSION
from .coordinator import ErovinietaFreeCoordinator
from .helpers import capitalize_name, format_timestamp_ms, sanitize_plate_no

MAX_ATTR_TRECERI = 20


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ErovinietaFreeCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors: list[SensorEntity] = []

    sensors.append(DateUtilizatorSensor(coordinator, config_entry))

    paginated = coordinator.data.get("paginated_data", {}).get("view", [])

    for vehicul in paginated:
        entity = vehicul.get("entity", {})
        plate_no = entity.get("plateNo")
        vin = entity.get("vin")
        cert = entity.get("certificateSeries")

        if not all([plate_no, vin, cert]):
            continue

        sensors.extend(
            [
                VehiculSensor(coordinator, config_entry, plate_no),
                PlataTreceriPodSensor(coordinator, config_entry, vin, plate_no, cert),
                TreceriPodSensor(coordinator, config_entry, vin, plate_no, cert),
                SoldSensor(coordinator, config_entry, plate_no),
            ]
        )

    if sensors:
        async_add_entities(sensors)


class ErovinietaFreeBaseSensor(
    CoordinatorEntity[ErovinietaFreeCoordinator], SensorEntity
):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: ErovinietaFreeCoordinator,
        config_entry: ConfigEntry,
        name: str,
        unique_id: str,
        icon: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name="CNAIR eRovinieta Free",
            manufacturer="CNAIR",
            model="eRovinieta",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )


class DateUtilizatorSensor(ErovinietaFreeBaseSensor):
    def __init__(
        self, coordinator: ErovinietaFreeCoordinator, config_entry: ConfigEntry
    ) -> None:
        user_data = coordinator.data.get("user_data", {})
        utilizator = user_data.get("utilizator", {})
        user_id = utilizator.get("nume", "necunoscut").replace(" ", "_").lower()

        super().__init__(
            coordinator=coordinator,
            config_entry=config_entry,
            name="Date utilizator",
            unique_id=f"{DOMAIN}_date_utilizator_{user_id}_{config_entry.entry_id}",
            icon="mdi:account-details",
        )

    @property
    def native_value(self) -> str:
        if not self.coordinator.data or "user_data" not in self.coordinator.data:
            return "nespecificat"
        user_data = self.coordinator.data["user_data"]
        user_id = user_data.get("id")
        return str(user_id) if user_id is not None else "nespecificat"

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data or "user_data" not in self.coordinator.data:
            return {}

        user_data = self.coordinator.data["user_data"]
        utilizator = user_data.get("utilizator", {})
        tara_data = user_data.get("tara", {})
        denumire_tara = tara_data.get("denumire", "nespecificat")

        if denumire_tara.lower() == "romania":
            judet = user_data.get("judet", {}).get("nume", "nespecificat")
            localitate = user_data.get("localitate", {}).get("nume", "nespecificat")
        else:
            judet = user_data.get("judetText", "nespecificat")
            localitate = user_data.get("localitateText", "nespecificat")

        return {
            "Numele și prenumele": str(utilizator.get("nume", "")).title(),
            "CNP": user_data.get("cnpCui", "nespecificat"),
            "Telefon de contact": utilizator.get("telefon", "nespecificat"),
            "Persoană fizică": "Da" if user_data.get("pf") else "Nu",
            "Email utilizator": utilizator.get("email", "nespecificat"),
            "Acceptă corespondența": "Da" if user_data.get("acceptaCorespondenta") else "Nu",
            "Adresa": user_data.get("adresa", "nespecificat"),
            "Localitate": localitate,
            "Județ": judet,
            "Țară": capitalize_name(denumire_tara),
        }


class VehiculSensor(ErovinietaFreeBaseSensor):
    def __init__(
        self,
        coordinator: ErovinietaFreeCoordinator,
        config_entry: ConfigEntry,
        plate_no: str,
    ) -> None:
        sanitized = sanitize_plate_no(plate_no)
        super().__init__(
            coordinator=coordinator,
            config_entry=config_entry,
            name=f"Rovinietă activă ({plate_no})",
            unique_id=f"{DOMAIN}_vehicul_{sanitized}_{config_entry.entry_id}",
            icon="mdi:car",
        )
        self._plate_no = plate_no

    def _get_vehicle_data(self) -> dict:
        if not self.coordinator.data:
            return {}
        for item in self.coordinator.data.get("paginated_data", {}).get("view", []):
            if item.get("entity", {}).get("plateNo") == self._plate_no:
                return item
        return {}

    @staticmethod
    def _get_country_name(country_id, countries_data: list) -> str:
        if not country_id or not countries_data:
            return "Necunoscut"
        for country in countries_data:
            if country.get("id") == country_id:
                return capitalize_name(country.get("denumire", "Necunoscut"))
        return "Necunoscut"

    @property
    def native_value(self) -> str:
        vehicle = self._get_vehicle_data()
        vignettes = vehicle.get("userDetailsVignettes", [])
        if not vignettes:
            return "Nu"

        stop_ts = vignettes[0].get("vignetteStopDate")
        if not stop_ts:
            return "Nu"

        now_ms = int(time.time() * 1000)
        return "Da" if stop_ts > now_ms else "Nu"

    @property
    def extra_state_attributes(self) -> dict:
        vehicle = self._get_vehicle_data()
        entity = vehicle.get("entity", {})
        vignettes = vehicle.get("userDetailsVignettes", [])
        countries = self.coordinator.data.get("countries_data", [])

        attrs = {
            "Număr de înmatriculare": entity.get("plateNo", "Necunoscut"),
            "VIN": entity.get("vin", "Necunoscut"),
            "Seria certificatului": entity.get("certificateSeries", "Necunoscut"),
            "Țara": self._get_country_name(entity.get("tara"), countries),
        }

        if not vignettes:
            attrs["Rovinietă"] = "Nu există rovinietă"
        else:
            v = vignettes[0]
            start_ts = v.get("vignetteStartDate")
            stop_ts = v.get("vignetteStopDate")

            attrs["Categorie vignietă"] = v.get("vignetteCategory", "Necunoscut")
            attrs["Data început vignietă"] = format_timestamp_ms(start_ts)
            attrs["Data sfârșit vignietă"] = format_timestamp_ms(stop_ts)

            if stop_ts and stop_ts > 0:
                now_s = int(time.time())
                days_left = (stop_ts // 1000 - now_s) // 86400
                attrs["Expiră peste (zile)"] = days_left
            else:
                attrs["Expiră peste (zile)"] = "N/A"

        return attrs


class PlataTreceriPodSensor(ErovinietaFreeBaseSensor):
    def __init__(
        self,
        coordinator: ErovinietaFreeCoordinator,
        config_entry: ConfigEntry,
        vin: str,
        plate_no: str,
        certificate_series: str,
    ) -> None:
        sanitized = sanitize_plate_no(plate_no)
        super().__init__(
            coordinator=coordinator,
            config_entry=config_entry,
            name=f"Restanțe treceri pod ({plate_no})",
            unique_id=f"{DOMAIN}_plata_treceri_pod_{sanitized}_{config_entry.entry_id}",
            icon="mdi:invoice-text-remove",
        )
        self._vin = vin
        self._plate_no = plate_no
        self._certificate_series = certificate_series

    def _get_vehicle_detections(self) -> list:
        if not self.coordinator.data:
            return []
        per_vehicul = self.coordinator.data.get("treceri_pod_per_vehicul", {})
        return per_vehicul.get(self._plate_no, [])

    def _get_unpaid_detections(self) -> list:
        detections = self._get_vehicle_detections()
        now_ms = int(time.time() * 1000)
        interval_ms = 24 * 60 * 60 * 1000

        return [
            d
            for d in detections
            if d.get("paymentStatus") is None
            and now_ms - d.get("detectionTimestamp", 0) <= interval_ms
        ]

    @property
    def native_value(self) -> str:
        return "Da" if self._get_unpaid_detections() else "Nu"

    @property
    def extra_state_attributes(self) -> dict:
        neplatite = self._get_unpaid_detections()
        total = len(neplatite)

        neplatite_sorted = sorted(
            neplatite,
            key=lambda d: d.get("detectionTimestamp", 0),
            reverse=True,
        )
        limited = neplatite_sorted[:MAX_ATTR_TRECERI]

        attrs: dict = {
            "Număr treceri neplătite": total,
            "Număr de înmatriculare": self._plate_no,
            "VIN": self._vin,
            "Seria certificatului": self._certificate_series,
        }

        if total > MAX_ATTR_TRECERI:
            attrs["Avertisment"] = (
                f"Se afișează doar cele mai recente {MAX_ATTR_TRECERI} din {total} restanțe."
            )

        for idx, detection in enumerate(limited, start=1):
            ts = detection.get("detectionTimestamp")
            attrs[f"--- Restanță #{idx}"] = ""
            attrs[f"Trecere {idx} - Categorie"] = detection.get("detectionCategory", "")
            attrs[f"Trecere {idx} - Timp detectare"] = format_timestamp_ms(ts)
            attrs[f"Trecere {idx} - Direcție"] = detection.get("direction", "")
            attrs[f"Trecere {idx} - Bandă"] = detection.get("lane", "")
            attrs[f"Trecere {idx} - Valoare (RON)"] = detection.get("value", "")
            attrs[f"Trecere {idx} - Partener"] = detection.get("partner", "")
            attrs[f"Trecere {idx} - Metodă plată"] = detection.get("paymentMethod", "")
            attrs[f"Trecere {idx} - Vehicul"] = detection.get("paymentPlateNo", "")

        return attrs


class TreceriPodSensor(ErovinietaFreeBaseSensor):
    def __init__(
        self,
        coordinator: ErovinietaFreeCoordinator,
        config_entry: ConfigEntry,
        vin: str,
        plate_no: str,
        certificate_series: str,
    ) -> None:
        sanitized = sanitize_plate_no(plate_no)
        super().__init__(
            coordinator=coordinator,
            config_entry=config_entry,
            name=f"Treceri pod ({plate_no})",
            unique_id=f"{DOMAIN}_treceri_pod_{sanitized}_{config_entry.entry_id}",
            icon="mdi:bridge",
        )
        self._vin = vin
        self._plate_no = plate_no
        self._certificate_series = certificate_series

    def _get_vehicle_detections(self) -> list:
        if not self.coordinator.data:
            return []
        per_vehicul = self.coordinator.data.get("treceri_pod_per_vehicul", {})
        return per_vehicul.get(self._plate_no, [])

    @property
    def native_value(self) -> int:
        return len(self._get_vehicle_detections())

    @property
    def extra_state_attributes(self) -> dict:
        detection_list = self._get_vehicle_detections()
        total = len(detection_list)

        sorted_detections = sorted(
            detection_list,
            key=lambda d: d.get("detectionTimestamp", 0),
            reverse=True,
        )
        limited = sorted_detections[:MAX_ATTR_TRECERI]

        attrs: dict = {
            "Număr total treceri": total,
            "Treceri afișate": len(limited),
            "Număr de înmatriculare": self._plate_no,
            "VIN": self._vin,
            "Seria certificatului": self._certificate_series,
        }

        if total > MAX_ATTR_TRECERI:
            attrs["Avertisment"] = (
                f"Se afișează doar cele mai recente {MAX_ATTR_TRECERI} din {total} treceri."
            )

        for idx, detection in enumerate(limited, start=1):
            ts = detection.get("detectionTimestamp")
            valid_until = detection.get("validUntilTimestamp")

            attrs[f"--- Trecere #{idx}"] = ""
            attrs[f"Trecere {idx} - Categorie"] = detection.get("detectionCategory", "")
            attrs[f"Trecere {idx} - Timp detectare"] = format_timestamp_ms(ts)
            attrs[f"Trecere {idx} - Direcție"] = detection.get("direction", "")
            attrs[f"Trecere {idx} - Bandă"] = detection.get("lane", "")
            attrs[f"Trecere {idx} - Valoare (RON)"] = detection.get("value", "")
            attrs[f"Trecere {idx} - Partener"] = detection.get("partner", "")
            attrs[f"Trecere {idx} - Metodă plată"] = detection.get("paymentMethod", "")
            attrs[f"Trecere {idx} - Vehicul"] = detection.get("paymentPlateNo", "")
            attrs[f"Trecere {idx} - Treceri achiziționate"] = detection.get("taxName", "")
            attrs[f"Trecere {idx} - Status plată"] = detection.get("paymentStatus", "")
            attrs[f"Trecere {idx} - Valabilitate până la"] = format_timestamp_ms(valid_until)

        return attrs


class SoldSensor(ErovinietaFreeBaseSensor):
    def __init__(
        self,
        coordinator: ErovinietaFreeCoordinator,
        config_entry: ConfigEntry,
        plate_no: str,
    ) -> None:
        sanitized = sanitize_plate_no(plate_no)
        super().__init__(
            coordinator=coordinator,
            config_entry=config_entry,
            name=f"Sold peaje neexpirate ({plate_no})",
            unique_id=f"{DOMAIN}_sold_peaje_neexpirate_{sanitized}_{config_entry.entry_id}",
            icon="mdi:boom-gate",
        )
        self._plate_no = plate_no

    def _get_sold(self) -> int | float:
        if not self.coordinator.data:
            return 0
        for item in self.coordinator.data.get("paginated_data", {}).get("view", []):
            entity = item.get("entity", {})
            if entity.get("plateNo") == self._plate_no:
                payment_sum = item.get("detectionPaymentSum", {})
                if payment_sum:
                    return payment_sum.get("soldPeajeNeexpirate", 0)
        return 0

    @property
    def native_value(self) -> int | float:
        return self._get_sold()

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "Sold peaje neexpirate": self._get_sold(),
        }