from astrolabium.parsers.data import EntryBase, Orb6Entry, WikidataStar, WikimediaStar
from astropy import units as u
from astropy.coordinates import SkyCoord, ICRS, Galactic
from tqdm import tqdm
from typing import Any, Tuple
import logging
import math

logger = logging.getLogger(__name__)


class Star(EntryBase):
    key_settings = [
        ["id", [], None, None, None],
        ["Name", [], None, None, None],
        ["ra", [], lambda v: float(v), u.rad, 6],
        ["dec", [], lambda v: float(v), u.rad, 6],
        ["sc", [], None, None, None],
        ["d", [], lambda v: float(v), u.pc, 6],
        ["a", [], lambda v: float(v), u.AU, 6],
        ["e", [], lambda v: float(v), None, 3],
        ["P", [], lambda v: float(v), u.yr, 3],
        ["i", [], lambda v: float(v), u.deg, 3],
        ["lan", [], lambda v: float(v), u.deg, 3],
        ["argp", [], lambda v: float(v), u.deg, 3],
        ["otypes", [], None, None, None]
    ]

    def __init__(
        self, catalogue_entry: EntryBase | None = None, orbit: Orb6Entry | None = None, crossref: Any | None = None, distance: u.Quantity | None = None
    ):
        self.id: str | None = None
        self.Name: str | None = None
        self.a: u.Quantity | None = None
        self.d: u.Quantity | None = None
        self.sc: str | None = None
        self.Orbiters: dict[str, Star | None] = {}

        data = {}
        if orbit is not None and isinstance(orbit, Orb6Entry):
            data = orbit.to_dict()
            d = None
            if distance is not None:
                d = distance
            elif catalogue_entry is not None:
                d = catalogue_entry.d

            data["a"] = orbit.calculate_sma_AU(d)
            # assuming lpa (Longitude of the Periastron ϖ) refers to the argument of the periastron instead (ω)
            data["argp"] = data["lpa"]
            del data["lpa"]

        if crossref is not None:
            data = data | crossref
            data["otypes"] = crossref["otypes"]
            if "st" in crossref and crossref["st"] != "":
                data["sc"] = crossref["st"]
            if catalogue_entry is None and "Name" in crossref:
                del data["Name"]

        if catalogue_entry is not None:
            # catalogue_entry is expected to be a dict with keys matching Star.key_settings.
            # Each entry class's to_star() is responsible for building this dict.
            if isinstance(catalogue_entry, dict):
                data = data | catalogue_entry

        self._parse_values(self.key_settings, data)

    def to_dict(self):
        json = {}
        json["Id"] = self.extract_value("id", None, None)
        json["Name"] = self.extract_value("Name", None, None)
        if hasattr(self,"otypes"):
            otypes = self.extract_value("otypes", None, None)
            otypes = ", ".join(otypes)
        else:
            otypes = "*"
        json["Attributes"] = {"otypes": otypes }
        json["SC"] = self.extract_value("sc", None, None)

        physicalData = {
            "l": self.extract_value("l", 6, u.L_sun),
            "m": self.extract_value("m", 6, u.M_sun),
            "t": self.extract_value("t", 6, u.K),
            "g": self.extract_value("g", 6, u.Unit("cm/s**2")),
            "age": self.extract_value("age", 6, u.Gyr),
        }
        json["PhysicalData"] = {k: v for k, v in physicalData.items() if v is not None}

        orbitalData = {
            "a": self.extract_value("a", 6, u.AU),
            "P": self.extract_value("P", 6, u.yr),
            "e": self.extract_value("e", 6, None),
            "i": self.extract_value("i", 3, u.deg),
            "lan": self.extract_value("lan", 3, u.deg),
            "argp": self.extract_value("argp", 3, u.deg),
        }
        json["OrbitalData"] = {k: v for k, v in orbitalData.items() if v is not None}

        orbiters = {}
        for key, star in self.Orbiters.items():
            if star is not None:
                orbiters[key] = star.to_dict()

        json["Orbiters"] = orbiters

        return {k: v for k, v in json.items() if v}

    def add_properties(self, data: WikidataStar, properties: list[str] = ["l", "m", "t", "g", "age"]):
        for prop in properties:
            value = getattr(data, prop, None)
            if value is not None:
                setattr(self, prop, value)

    def add_wikimedia(self, wikimedia_star: WikimediaStar) -> list[str]:
        """Fill missing physical data fields from a WikimediaStar.

        Only sets fields that are currently None on the star. If a field
        already has a value (e.g. from Wikidata), it is preserved. Large
        discrepancies between existing and new values are logged as warnings.

        :param wikimedia_star: A WikimediaStar instance containing parsed
                               infobox data as astropy Quantities.
        :return: List of field names that were actually set.
        """
        physical_fields: list[str] = ["l", "m", "t", "g", "age", "r"]
        set_fields: list[str] = []

        for field in physical_fields:
            existing_value = getattr(self, field, None)
            new_value = getattr(wikimedia_star, field, None)

            if new_value is None:
                continue

            if existing_value is not None:
                # Field already set — check for large discrepancy
                try:
                    if isinstance(new_value, u.Quantity) and isinstance(existing_value, u.Quantity):
                        # Compare in the same unit
                        try:
                            new_val = new_value.to(existing_value.unit).value
                            existing_val = existing_value.value
                            if existing_val > 0:
                                diff_pct = abs(new_val - existing_val) / abs(existing_val) * 100
                                if diff_pct > 20:
                                    logger.warning(
                                        f"{self.id}: Wikimedia value for '{field}' "
                                        f"({new_value}) differs by {diff_pct:.1f}% "
                                        f"from existing Wikidata value "
                                        f"({existing_val} {existing_value.unit})"
                                    )
                        except (u.UnitConversionError, ValueError):
                            pass
                except (ValueError, TypeError):
                    pass
                continue

            # Field is missing — set it
            setattr(self, field, new_value)
            set_fields.append(field)

        return set_fields

    def to_string(self, indent_spaces=3):
        (x, y, z) = self.xyz
        string = super().to_string(indent_spaces)
        string += f"{self._get_indent(indent_spaces)}x, y, z: {x}, {y}, {z}"
        return string

    @property
    def gc(self):
        assert hasattr(self, "ra"), "Missing ra"
        assert hasattr(self, "dec"), "Missing dec"
        gc = SkyCoord(ra=self.ra, dec=self.dec, distance=self.d if self.d > 0 else None, frame=ICRS)
        return gc.transform_to(Galactic)

    @property
    def xyz(self) -> tuple[float, float, float]:
        assert self.d is not None, f"{self.id}: missing distance"
        gc = self.gc
        l = gc.l.to(u.rad)
        b = gc.b.to(u.rad)
        d = self.d.to(u.pc)
        x = d.value * math.cos(b.value) * math.cos(l.value)
        y = d.value * math.cos(b.value) * math.sin(l.value)
        z = d.value * math.sin(b.value)
        return (x, y, z)

    def has_required_physical_data(self) -> bool:
        """Check whether this star has the minimum required physical data.

        The game requires at least one of Mass (m) or Luminosity (l),
        plus Temperature (t). A star is considered valid if it has
        temperature AND (mass OR luminosity).

        :return: True if the star has sufficient physical data,
                 False otherwise.
        """
        has_temp = getattr(self, "t", None) is not None
        has_mass = getattr(self, "m", None) is not None
        has_lum = getattr(self, "l", None) is not None
        return has_temp and (has_mass or has_lum)

    def has_required_orbital_data(self) -> bool:
        """Check whether this star component has required orbital data.

        For binary/multiple star components, the game requires separation (a),
        eccentricity (e), and period (P).

        :return: True if all three orbital parameters are present,
                 False otherwise.
        """
        return (
            getattr(self, "a", None) is not None
            and getattr(self, "e", None) is not None
            and getattr(self, "P", None) is not None
        )

    @classmethod
    def preorder_visit(cls, star: "Star"):
        yield star
        for orbiter in star.Orbiters.values():
            if orbiter is not None:
                yield from Star.preorder_visit(orbiter)
