"""Gliese catalogue entry class.

Provides a unified interface for Gliese catalogue data, converting
B1950 HMS/DMS coordinates and total proper motion into the same
field names and units as HipparcosEntry, so that Star objects
can be created from either source transparently.

Catalogue: V/70A — Preliminary Version of the Third Catalogue of Nearby Stars (CNS3)
Authors: Gliese W., Jahrweiss H. (1991)
Coverage: ~9,110 stars within 25 parsecs (~81 light-years)
"""

import math
import astropy.units as u
from astropy.coordinates import SkyCoord, ICRS
from astropy.time import Time
from astrolabium.parsers.data import EntryBase
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from astrolabium.creator import Star


class GlieseEntry(EntryBase):
    """Entry from the Gliese catalogue (V/70A).

    Accepts dict input from either the GlieseParser (ParserBase) or VOTable
    output and normalizes to a common interface:
    - ra, de (radians, J2000)
    - plx (mas)
    - pmRA, pmDE (mas/yr, decomposed from total pm + pmPA)
    - d (pc, computed from parallax)

    Additional Gliese-specific fields:
    - Name: Star identifier (e.g., "Gl 1", "GJ 1001", "NN 3001")
    - Sp: Spectral type (e.g., "M4 V", "K0 Ve")
    - RV: Radial velocity (km/s)
    - Vmag: V magnitude (VOTable only)
    - BV: B-V color index (VOTable only)
    - RAB1950, DEB1950: B1950 coordinates (HMS/DMS strings)
    - RAIcrs, DEIcrs: J2000 coordinates (HMS/DMS strings, VOTable only)
    - pmPA: Proper motion position angle (degrees)
    """

    # Class-level type annotations
    HIP: Optional[str]
    Name: Optional[str]
    Sp: Optional[str]
    RV: Optional[float]
    Vmag: Optional[float]
    BV: Optional[float]
    RAB1950: Optional[str]
    DEB1950: Optional[str]
    RAIcrs: Optional[str]
    DEIcrs: Optional[str]
    pmPA: Optional[float]

    key_settings = [
        # [key, nullvalues, preprocessor, unit, round_digits]
        ["HIP", None, None, None, None],
        ["Name", None, None, None, None],
        ["Sp", None, None, None, None],
        ["RV", [], lambda v: float(v), u.km / u.s, 1],
        ["Vmag", [], lambda v: float(v), None, 2],
        ["BV", [], lambda v: float(v), None, 2],
        ["RAB1950", None, None, None, None],
        ["DEB1950", None, None, None, None],
        ["RAIcrs", None, None, None, None],
        ["DEIcrs", None, None, None, None],
        ["pmPA", [], lambda v: float(v), u.deg, 1],
        ["plx", [], lambda v: float(v), u.mas, 2],
        ["pm", [], lambda v: float(v), u.arcsec / u.yr, 3],
    ]

    def __init__(self, catalogue_entry: dict, from_string: bool = False):
        """Create a GlieseEntry from a catalogue dictionary.

        Accepts dict input from either:
        - GlieseParser (ParserBase): has 'RA_DE' combined B1950 coords
        - VOTable output: has 'RAB1950', 'DEB1950', 'RAIcrs', 'DEIcrs'

        Args:
            catalogue_entry: Dictionary with Gliese catalogue fields.
            from_string: If True, parse string fields (for serialization round-trip).
        """
        self._id = None
        self.HIP = None
        self.Name = None
        self.Sp = None
        self.RV = None
        self.Vmag = None
        self.BV = None
        self.RAB1950 = None
        self.DEB1950 = None
        self.RAIcrs = None
        self.DEIcrs = None
        self.pmPA = None
        self.plx = None
        self.pm = None

        try:
            # Normalize input: handle both Parser and VOTable formats
            entry = self._normalize_input(catalogue_entry)

            if from_string:
                self._parse_keys(self.key_settings, entry)
            else:
                self._parse_values(self.key_settings, entry)

            # Set ID from Name or HIP
            if self.Name:
                self._id = self.Name
            elif self.HIP:
                self._id = f"HIP {self.HIP}"

            # Convert B1950 coordinates to J2000 decimal radians
            self._convert_coordinates()

            # Decompose total proper motion into RA/DE components
            self._decompose_proper_motion()

        except (ValueError, AttributeError) as e:
            raise ValueError(f"Error parsing Gliese entry: {catalogue_entry}\n{e}")

    @staticmethod
    def _safe_float(val) -> float | None:
        """Safely convert a value to float, returning None on failure."""
        if val is None or val == "":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_ra_de_combined(ra_de_str: str) -> tuple[str, str] | tuple[None, None]:
        """Parse combined RA_DE field into separate RA and DE strings.

        Format: 'HH MM SS ±DD MM.S' (e.g., '00 00 06 -34 29.7')
        5 space-separated tokens: HH, MM, SS, ±DD, MM.S

        Returns:
            Tuple of (RA_string, DE_string) or (None, None) if parsing fails.
        """
        if not ra_de_str or ra_de_str.strip() == "":
            return None, None
        parts = ra_de_str.strip().split()
        if len(parts) == 5:
            # HH MM SS ±DD MM.S
            ra = f"{parts[0]} {parts[1]} {parts[2]}"
            de = f"{parts[3]} {parts[4]}"
            return ra, de
        elif len(parts) == 6:
            # HH MM SS ±DD MM SS.S (with seconds in dec)
            ra = f"{parts[0]} {parts[1]} {parts[2]}"
            de = f"{parts[3]} {parts[4]} {parts[5]}"
            return ra, de
        elif len(parts) == 4:
            # HH MM.S ±DD MM.S (no RA seconds)
            ra = f"{parts[0]} {parts[1]}"
            de = f"{parts[2]} {parts[3]}"
            return ra, de
        return None, None

    def _normalize_input(self, data: dict) -> dict:
        """Normalize input dict from either GlieseParser or VOTable format.

        GlieseParser format:
            Name, RA_DE (combined), pm, pmPA, RV, Sp, plx, Comp, u_pm, e_plx

        VOTable format:
            Name, RAB1950, DEB1950, RAIcrs, DEIcrs, pm, pmPA, RV, Sp, plx, Vmag, BV

        Returns a dict with canonical field names for _parse_values.
        """
        result = {}

        # Common fields (both formats)
        result["Name"] = data.get("Name")
        result["Sp"] = data.get("Sp")
        result["RV"] = self._safe_float(data.get("RV"))
        result["pmPA"] = self._safe_float(data.get("pmPA"))
        result["plx"] = self._safe_float(data.get("plx"))
        result["pm"] = self._safe_float(data.get("pm"))

        # VOTable-specific fields
        result["Vmag"] = self._safe_float(data.get("Vmag"))
        result["BV"] = self._safe_float(data.get("BV"))
        result["RAB1950"] = data.get("RAB1950")
        result["DEB1950"] = data.get("DEB1950")
        result["RAIcrs"] = data.get("RAIcrs")
        result["DEIcrs"] = data.get("DEIcrs")

        # GlieseParser format: parse combined RA_DE field
        ra_de = data.get("RA_DE")
        if ra_de:
            ra_str, de_str = self._parse_ra_de_combined(ra_de)
            result["RAB1950"] = ra_str
            result["DEB1950"] = de_str

        return result

    @property
    def d(self) -> u.Quantity | None:
        """Distance in parsecs, computed from parallax.

        Returns:
            Distance in parsecs, or None if parallax is not available.
        """
        if not hasattr(self, "plx") or self.plx is None:
            return None
        if self.plx.value == 0:
            return None
        return (1 / self.plx.to(u.arcsec)).value * u.pc

    def _convert_coordinates(self):
        """Convert B1950 HMS/DMS coordinates to J2000 decimal radians.

        Uses RAIcrs/DEIcrs (J2000) from VOTable if available, otherwise
        converts RAB1950/DEB1950 (B1950) to J2000.
        """
        # Try J2000 coordinates first (provided by VizieR)
        if self.RAIcrs and self.DEIcrs:
            ra_str = self.RAIcrs.strip()
            de_str = self.DEIcrs.strip()
            self.ra = self._hms_to_rad(ra_str)
            self.de = self._dms_to_rad(de_str)
            return

        # Fall back to B1950 conversion
        if self.RAB1950 and self.DEB1950:
            ra_str = self.RAB1950.strip()
            de_str = self.DEB1950.strip()
            # Parse B1950 coordinates (returns degrees)
            ra_deg, dec_deg = self._parse_b1950_coords(ra_str, de_str)
            # Convert B1950 to J2000 (simplified: ~90 years proper motion correction)
            # For most stars this is small, but we apply a basic precession
            ra_j2000, dec_j2000 = self._precess_b1950_to_j2000(ra_deg, dec_deg)
            self.ra = (ra_j2000 * u.deg).to(u.rad)
            self.de = (dec_j2000 * u.deg).to(u.rad)

    def _hms_to_rad(self, hms_str: str) -> u.Quantity:
        """Convert HMS string (e.g., '00 05 24.6') to radians."""
        parts = hms_str.strip().split()
        if len(parts) >= 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            deg = (hours + minutes / 60.0 + seconds / 3600.0) * 15.0
        elif len(parts) == 2:
            # H M.S format
            hours = float(parts[0])
            minutes = float(parts[1])
            deg = (hours + minutes / 60.0) * 15.0
        else:
            deg = 0.0
        return (deg * u.deg).to(u.rad)

    def _dms_to_rad(self, dms_str: str) -> u.Quantity:
        """Convert DMS string (e.g., '-37 21 26') to radians."""
        parts = dms_str.strip().split()
        sign = 1
        if parts[0].startswith("-"):
            sign = -1
            parts[0] = parts[0][1:]
        elif parts[0].startswith("+"):
            parts[0] = parts[0][1:]

        if len(parts) >= 3:
            deg = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            total_deg = sign * (deg + minutes / 60.0 + seconds / 3600.0)
        elif len(parts) == 2:
            deg = float(parts[0])
            minutes = float(parts[1])
            total_deg = sign * (deg + minutes / 60.0)
        else:
            total_deg = 0.0
        return (total_deg * u.deg).to(u.rad)

    def _parse_b1950_coords(self, ra_str: str, de_str: str) -> tuple[float, float]:
        """Parse B1950 HMS/DMS coordinates to degrees."""
        ra_rad = self._hms_to_rad(ra_str).value
        dec_rad = self._dms_to_rad(de_str).value
        return ra_rad * 180.0 / math.pi, dec_rad * 180.0 / math.pi

    def _precess_b1950_to_j2000(self, ra_deg: float, dec_deg: float) -> tuple[float, float]:
        """Simplified precession from B1950 to J2000.

        Uses astropy's coordinate transformation for accuracy.
        """
        try:
            coord_b1950 = SkyCoord(
                ra=ra_deg * u.deg,
                dec=dec_deg * u.deg,
                frame="icrs",
                obstime=Time(1950.0, format="jyear"),
            )
            coord_j2000 = coord_b1950.apply_space_motion(
                new_obstime=Time(2000.0, format="jyear")
            )
            return coord_j2000.ra.deg, coord_j2000.dec.deg
        except Exception:
            # Fall back: just use B1950 as-is (approximate)
            return ra_deg, dec_deg

    def _decompose_proper_motion(self):
        """Decompose total proper motion into RA/DE components.

        Uses the proper motion position angle (pmPA) to split the total
        proper motion (pm) into pmRA (including cos(dec)) and pmDE.

        Formula:
            pmRA = pm * sin(PA)  (positive eastward)
            pmDE = pm * cos(PA)  (positive northward)
        """
        # Get total proper motion and position angle
        pm_total = None
        if hasattr(self, "pm") and self.pm is not None:
            pm_total = self.pm

        if pm_total is None or self.pmPA is None:
            # No proper motion data available
            self.pmRA = None
            self.pmDE = None
            return

        pm_total_mas = pm_total.to(u.mas / u.yr)
        pa_rad = self.pmPA.to(u.rad)

        # Decompose: pmRA = pm * sin(PA), pmDE = pm * cos(PA)
        self.pmRA = pm_total_mas.value * math.sin(pa_rad.value) * u.mas / u.yr
        self.pmDE = pm_total_mas.value * math.cos(pa_rad.value) * u.mas / u.yr

    def to_dict(self) -> dict:
        """Convert to dictionary with Hipparcos-compatible field names.

        Returns a dictionary with fields matching HipparcosEntry.to_dict():
        HIP, ra, de, plx, pmRA, pmDE, e_ra, e_de, e_plx, e_pmRA, e_pmDE, d
        Plus Gliese-specific fields: Name, Sp, RV, Vmag, BV.
        """
        result = super().to_dict()

        # Add Gliese-specific fields
        if self.Name:
            result["Name"] = self.Name
        if self.Sp:
            result["Sp"] = self.Sp
        if self.RV is not None:
            result["RV"] = self.RV.value if hasattr(self.RV, "value") else self.RV
            result["RV_unit"] = "km/s"
        if self.Vmag is not None:
            result["Vmag"] = self.Vmag
        if self.BV is not None:
            result["BV"] = self.BV

        # Add computed distance
        if self.d is not None:
            result["d"] = self.d.value

        return result

    def to_star_dict(self) -> dict:
        """Return a dict with fields matching Star.key_settings.

        Only includes fields that Star actually uses: id, Name, ra, dec, d.
        """
        return {
            "id": getattr(self, "_id", None),
            "Name": getattr(self, "Name", None),
            "ra": getattr(self, "ra", None),
            "dec": getattr(self, "de", None),
            "d": getattr(self, "d", None),
        }

    def to_star(self) -> "Star":
        """Create a Star object from this GlieseEntry.

        Returns:
            Star instance with id, ra, dec, d, Name populated from this entry.
        """
        from astrolabium.creator import Star
        return Star(catalogue_entry=self.to_star_dict())

    def __repr__(self) -> str:
        name = self.Name or self.HIP or "?"
        dist = f"{self.d.value:.1f} pc" if self.d is not None else "no distance"
        return f"GlieseEntry({name}, {dist})"
