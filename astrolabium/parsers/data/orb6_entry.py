import astropy.units as u
from astrolabium.parsers.data import EntryBase
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from astrolabium.parsers.data import HipparcosEntry


class Orb6Entry(EntryBase):
    WDS: str
    HIP: Optional[str]
    HD: Optional[str]
    comp: Optional[str]
    last: Optional[int]
    a: u.Quantity
    P: u.Quantity
    i: u.quantity
    e: u.Quantity

    lan: u.Quantity  # longitude of the ascending node (Omega Ω)
    lpa: u.Quantity  # the Orb6 catalogue calls it longitude of periastron (omega) which should be denoted as ϖ. However, this is likely the argument of the periastron (omega ω) instead.
    i_e: u.Quantity
    e_e: u.Quantity
    lan_e: u.Quantity
    lpa_e: u.Quantity

    key_settings = [
        # key, nullvalues, preproc, unit, digits]
        ["WDS", None, None, None, None],
        ["HD", ["."], None, None, None],
        ["HIP", ["."], None, None, None],
        ["comp", None, None, None, None],
        ["P", ["."], lambda v: Orb6Entry.__parse_period(v), u.yr, 6],
        ["P_e", ["."], lambda v: float(v), None, 6],
        ["a", ["."], lambda v: Orb6Entry.__parse_sma(v), u.mas, 5],
        ["a_e", ["."], lambda v: float(v), None, 5],
        ["i", ["."], lambda v: float(v), u.deg, 4],
        ["i_e", ["."], lambda v: float(v), u.deg, 4],
        ["lan", ["."], lambda v: float(v if v[-1] not in ["q", "*"] else v[0:-1]), u.deg, 4],
        ["lan_e", ["."], lambda v: float(v), u.deg, 4],
        ["e", ["."], lambda v: float(v.split(" ")[0]), None, 6],
        ["e_e", [".", "--."], lambda v: float(v), None, 6],
        ["lpa", ["."], lambda v: float(v.split(" ")[0]), u.deg, 4],
        ["lpa_e", ["."], lambda v: float(v), u.deg, 4],
        ["orb_g", None, lambda v: int(v), None, None],
        ["last", None, lambda v: int(v), None, None],
        ["notes", None, None, None, None],
    ]

    def __init__(self, catalogue_entry, from_string=False):
        self._id = catalogue_entry["WDS"]
        try:
            if from_string:
                self._parse_keys(self.key_settings, catalogue_entry)
            else:
                self._parse_values(self.key_settings, catalogue_entry)

            if hasattr(self, "a_e"):
                self.a_e *= self.a.unit
            if hasattr(self, "P_e"):
                self.P_e *= self.P.unit

        except (ValueError, AttributeError):
            print(f"Error while parsing {self.WDS}\n{catalogue_entry}")
            raise

    def to_dict(self):
        if hasattr(self, "a_e"):
            to_unit = next(v[3] for v in self.key_settings if v[0] == "a")
            self.a_e = self.a_e.to(to_unit)
        if hasattr(self, "P_e"):
            to_unit = next(v[3] for v in self.key_settings if v[0] == "P")
            self.P_e = self.P_e.to(to_unit)
        return super().to_dict()

    @classmethod
    def __parse_period(cls, val) -> u.Quantity:
        unit = val[-1]
        value = float(val[0:-1].rstrip())
        unit_value: u.Quantity
        match unit:
            case "m":
                unit_value = value * u.s
            case "h":
                unit_value = value * u.h
            case "d":
                unit_value = value * u.d
            case "y":
                unit_value = value * u.yr
            case "c":
                unit_value = value * 100 * u.yr
            case _:
                raise TypeError(f"Unexpected unit <{unit}> for {val}")
        return unit_value

    @classmethod
    def __parse_sma(cls, val) -> u.Quantity:
        unit = val[-1]
        value = float(val[0:-1].rstrip())
        unit_value: u.Quantity
        match unit:
            case "a":
                unit_value = value * u.arcsec
            case "m":
                unit_value = value * u.mas
            case "M":
                unit_value = value * u.arcmin
            case "u":
                unit_value = value * u.uas
            case _:
                raise TypeError(f"Unexpected unit <{unit}> for {val}")

        return unit_value

    def calculate_sma_AU(self, d: u.Quantity):
        if not hasattr(self, "a"):
            return 0 * u.AU

        sma = self.a.to(u.arcsec).value * d.to(u.pc)
        return sma.value * u.AU
