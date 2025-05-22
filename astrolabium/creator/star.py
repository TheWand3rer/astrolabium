from astrolabium.parsers.data import EntryBase, HipparcosEntry, Orb6Entry, WikidataStar
from astropy import units as u
from astropy.coordinates import SkyCoord, ICRS, Galactic
from tqdm import tqdm
from typing import Any, Tuple
import math


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
    ]

    def __init__(self, catalogue_entry: EntryBase | None = None, orbit: Orb6Entry | None = None, crossref: Any | None = None):
        self.id: str | None = None
        self.Name: str | None = None
        self.a: u.Quantity | None = None
        self.d: u.Quantity | None = None
        self.sc: str | None = None
        self.Orbiters: dict[str, Star | None] = {}

        data = {}
        if orbit is not None and isinstance(orbit, Orb6Entry):
            data = orbit.to_dict()
            data["a"] = orbit.calculate_sma_AU(catalogue_entry.d)
            # assuming lpa (Longitude of the Periastron ϖ) refers to the argument of the periastron instead (ω)
            data["argp"] = data["lpa"]
            del data["lpa"]

        if crossref is not None:
            data = data | crossref
            if "st" in crossref and crossref["st"] != "":
                data["sc"] = crossref["st"]
            if catalogue_entry is None and "Name" in crossref:
                del data["Name"]

        if catalogue_entry is not None:
            if not isinstance(catalogue_entry, HipparcosEntry):
                catalogue_entry = HipparcosEntry(catalogue_entry)
            data = data | catalogue_entry.to_dict()
            data["id"] = catalogue_entry.id
            # renaming de_clination to dec_lination
            data["dec"] = data["de"]
            data["d"] = catalogue_entry.d

        self._parse_values(self.key_settings, data)

    def to_dict(self):
        json = {}
        json["Id"] = self.extract_value("id", None, None)
        json["Name"] = self.extract_value("Name", None, None)
        json["SC"] = self.extract_value("sc", None, None)

        physicalData = {
            "l": self.extract_value("l", 6, u.L_sun),
            "m": self.extract_value("m", 6, u.M_sun),
            "t": self.extract_value("t", 6, u.K),
            "g": self.extract_value("g", 6, u.Unit("cm/s**2")),
            "age": self.extract_value("age", 6, u.Gyr),
        }
        json["PhysicalData"] = {k: v for k, v in physicalData.items() if v}

        orbitalData = {
            "a": self.extract_value("a", 6, u.AU),
            "P": self.extract_value("P", 6, u.yr),
            "e": self.extract_value("e", 6, None),
            "i": self.extract_value("i", 3, u.deg),
            "lan": self.extract_value("lan", 3, u.deg),
            "argp": self.extract_value("argp", 3, u.deg),
        }
        json["OrbitalData"] = {k: v for k, v in orbitalData.items() if v}

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

    @classmethod
    def preorder_visit(cls, star: "Star"):
        yield star
        for orbiter in star.Orbiters.values():
            if orbiter is not None:
                yield from Star.preorder_visit(orbiter)
