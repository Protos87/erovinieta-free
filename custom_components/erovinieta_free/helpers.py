"""Funcții utilitare pentru integrarea CNAIR eRovinieta Free."""

from __future__ import annotations

from typing import Any

from homeassistant.util import dt as dt_util


def format_timestamp_ms(timestamp_millis: int | float | None) -> str:
    """Formatează timestamp ms în ora locală HA."""
    if not timestamp_millis or timestamp_millis <= 0:
        return ""
    try:
        dt = dt_util.utc_from_timestamp(timestamp_millis / 1000).astimezone(
            dt_util.DEFAULT_TIME_ZONE
        )
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, ValueError, OverflowError):
        return "Dată invalidă"


def safe_get(value: Any, default: Any = None) -> Any:
    """Returnează fallback dacă valoarea e None sau goală."""
    if value is None or value == "":
        return default
    return value


def sanitize_plate_no(plate_no: str) -> str:
    """Curăță numărul de înmatriculare pentru unique_id."""
    return plate_no.replace(" ", "_").lower()


def capitalize_name(name: str) -> str:
    """Capitalizează fiecare cuvânt."""
    if not name:
        return ""
    return " ".join(word.capitalize() for word in name.split())