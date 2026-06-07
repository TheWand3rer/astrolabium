"""WikimediaStar — parse Wikipedia infobox data into astropy Quantities.

This module provides a data class that mirrors WikidataStar's pattern:
it takes raw Wikipedia infobox key-value pairs (strings with units)
and converts them into astropy Quantity objects for consistent handling
across all data sources.

Usage:
    >>> raw = {"Mass": "2.063 M", "Temperature": "9845 K"}
    >>> ws = WikimediaStar.from_raw(raw)
    >>> ws.m  # astropy Quantity
    <2.063 M_sun>
"""

from __future__ import annotations

import logging
import re
from typing import Any

from astropy import units as u

logger = logging.getLogger(__name__)

# Unit aliases from Wikipedia infoboxes -> astropy units
_infobox_units: dict[str, u.Unit] = {
    "M": u.M_sun,
    "M_sun": u.M_sun,
    r"M☉": u.M_sun,  # M with solar symbol
    "L": u.L_sun,
    "L_sun": u.L_sun,
    r"L☉": u.L_sun,  # L with solar symbol
    "R": u.R_sun,
    "R_sun": u.R_sun,
    r"R☉": u.R_sun,  # R with solar symbol
    "K": u.K,
    "g": u.cm / u.s**2,
    "cm/s2": u.cm / u.s**2,
    "cm/s**2": u.cm / u.s**2,
    "Myr": u.Myr,
    "Gyr": u.Gyr,
    "yr": u.yr,
}

# Field -> default unit (fallback when no unit in value)
_field_default_unit: dict[str, u.Unit | None] = {
    "m": u.M_sun,
    "l": u.L_sun,
    "t": u.K,
    "g": u.cm / u.s**2,
    "age": u.Gyr,
    "r": u.R_sun,
    "plx": u.mas,
}

# Wikipedia infobox key -> internal field name
_key_to_field: dict[str, str] = {
    "Mass": "m",
    "Luminosity": "l",
    "Temperature": "t",
    "Radius": "r",
    "Age": "age",
    "Surface gravity": "g",
    "Parallax": "plx",
}


def normalize_field(key: str) -> str | None:
    """Map a Wikipedia infobox key to our internal field name.

    :param key: Raw key from the infobox (e.g. "Mass").
    :return: Internal field name (e.g. "m"), or None if not a PhysicalData field.
    """
    return _key_to_field.get(key)


def _parse_infobox_value(raw: str, field: str) -> u.Quantity | None:
    """Parse a Wikipedia infobox value string into an astropy Quantity.

    Handles formats like "2.063 M", "24.74 L", "5777 K", "4.6 Gyr", "4.44 cm/s2".
    Also handles uncertainty notation like "2.063+-0.023 M" (takes primary value).

    :param raw: Raw value string from the infobox.
    :param field: Internal field name (used as fallback for unit).
    :return: Parsed Quantity, or None if parsing fails.
    """
    if not raw or not isinstance(raw, str):
        return None

    raw = raw.strip()

    # Extract numeric part: take first token, handle uncertainty notation
    parts = raw.split()
    num_str = parts[0] if parts else raw

    # Handle uncertainty: "2.063+-0.023" -> "2.063", "2.063±0.023" -> "2.063"
    for sep in ["+-", "±"]:  # ± symbol
        if sep in num_str:
            num_str = num_str.split(sep)[0]

    try:
        value = float(num_str)
    except ValueError:
        logger.debug(f"Cannot parse numeric value from '{raw}' for field '{field}'")
        return None

    # Determine unit
    unit: u.Unit | None = None
    if len(parts) >= 2:
        unit_symbol = " ".join(parts[1:])
        unit = _infobox_units.get(unit_symbol)
    if unit is None:
        unit = _field_default_unit.get(field)

    if unit is None:
        logger.debug(f"No unit for field '{field}' from value '{raw}'")
        return None

    return value * unit


class WikimediaStar:
    """Parse Wikipedia infobox data into astropy Quantities.

    Mirrors the WikidataStar pattern: takes raw string values with units
    and converts them to astropy Quantity objects for consistent handling
    across all data sources.

    Attributes:
        m: Mass (M_sun)
        l: Luminosity (L_sun)
        t: Temperature (K)
        g: Surface gravity (cm/s^2)
        age: Age (Gyr)
        r: Radius (R_sun)
        plx: Parallax (mas)
    """

    def __init__(self, raw_data: dict[str, str] | None = None):
        """Initialize from raw infobox data.

        :param raw_data: Dict mapping internal field names to raw string values
                        (e.g. {"m": "2.063 M", "t": "9845 K"}).
        """
        self.m: u.Quantity | None = None
        self.l: u.Quantity | None = None
        self.t: u.Quantity | None = None
        self.g: u.Quantity | None = None
        self.age: u.Quantity | None = None
        self.r: u.Quantity | None = None
        self.plx: u.Quantity | None = None

        if raw_data:
            self._parse_raw(raw_data)

    @classmethod
    def from_raw(cls, raw_data: dict[str, str]) -> WikimediaStar:
        """Create a WikimediaStar from raw infobox data.

        Accepts data in either format:
        - Internal field names: {"m": "2.063 M", "t": "9845 K"}
        - Wikipedia infobox keys: {"Mass": "2.063 M", "Temperature": "9845 K"}

        :param raw_data: Raw infobox key-value pairs.
        :return: New WikimediaStar instance.
        """
        # Normalize keys: map infobox keys to internal field names
        normalized: dict[str, str] = {}
        for key, value in raw_data.items():
            # If key is already an internal field name, use it directly
            if key in _field_default_unit:
                normalized[key] = value
            else:
                # Try to map infobox key to internal field name
                field = normalize_field(key)
                if field is not None:
                    normalized[field] = value
                else:
                    logger.debug(f"Unknown infobox key: {key}")

        return cls(normalized if normalized else None)

    def _parse_raw(self, raw_data: dict[str, str]) -> None:
        """Parse raw data into astropy Quantities.

        :param raw_data: Dict mapping internal field names to raw string values.
        """
        field_map: dict[str, str] = {
            "m": "m",
            "l": "l",
            "t": "t",
            "g": "g",
            "age": "age",
            "r": "r",
            "plx": "plx",
        }

        for field_name, attr_name in field_map.items():
            raw_value = raw_data.get(field_name)
            if raw_value is not None:
                qty = _parse_infobox_value(raw_value, field_name)
                if qty is not None:
                    setattr(self, attr_name, qty)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict of field name -> Quantity.

        :return: Dict with only non-None fields.
        """
        result: dict[str, Any] = {}
        for field in ["m", "l", "t", "g", "age", "r", "plx"]:
            value = getattr(self, field, None)
            if value is not None:
                result[field] = value
        return result

    def get_missing_fields(self, existing: dict[str, Any] | None = None) -> list[str]:
        """Get list of fields that are None (missing).

        :param existing: Optional dict of existing values to compare against.
        :return: List of missing field names.
        """
        existing = existing or {}
        missing: list[str] = []
        for field in ["m", "l", "t", "g", "age", "r", "plx"]:
            if field not in existing and getattr(self, field, None) is None:
                missing.append(field)
        return missing

    def get_fillable_fields(self, existing: dict[str, Any] | None = None) -> dict[str, u.Quantity]:
        """Get fields that can fill missing values in existing data.

        Only returns fields that are:
        1. Present in this WikimediaStar (not None)
        2. Missing from existing data

        :param existing: Optional dict of existing values.
        :return: Dict mapping field names to Quantity values.
        """
        existing = existing or {}
        fillable: dict[str, u.Quantity] = {}
        for field in ["m", "l", "t", "g", "age", "r", "plx"]:
            value = getattr(self, field, None)
            if value is not None and field not in existing:
                fillable[field] = value
        return fillable
