"""Gaia GCNS (Gaia Catalogue of Nearby Stars) entry class.

GCNS contains 331,312 objects within 100 pc of the Sun from Gaia EDR3.
Based on paper: Gaia Collaboration et al. (2021), A&A 649, A6.

Data source: https://cdsarc.cds.unistra.fr/ftp/J/A+A/649/A6/table1c.dat.gz

Fixed-width format — columns defined in the VizieR ReadMe.
"""

from astropy import units as u
from astrolabium.parsers.data import EntryBase


class GaiaGCNSEntry(EntryBase):
    """Represents a single star entry from the Gaia GCNS catalogue.

    Key fields:
        source_id: Gaia EDR3 source_id (19-digit integer)
        ra, dec: Right ascension and declination (ICRS, epoch 2016.0)
        plx: Parallax (mas)
        pmRA, pmDE: Proper motion (mas/yr)
        Gmag, BPmag, RPmag: Gaia magnitudes
        RV: Radial velocity (km/s)
        Dist50: 50th percentile distance (kpc)
        xcoord50, ycoord50, zcoord50: Galactic frame coords (pc)
        Uvel50, Vvel50, Wvel50: Galactic frame velocities (km/s)
        2MASS: 2MASS name (if available)
        Jmag, Hmag, Ksmag: 2MASS magnitudes
        W1mag, W2mag: WISE magnitudes
    """

    key_settings = [
        # [key, null_values, preprocessor, unit, round_digits]
        ["source_id", None, lambda v: int(v), None, None],
        ["ra", [], lambda v: float(v), u.deg, 7],
        ["e_ra", [], lambda v: float(v), u.mas, 2],
        ["dec", [], lambda v: float(v), u.deg, 7],
        ["e_dec", [], lambda v: float(v), u.mas, 2],
        ["plx", [], lambda v: float(v), u.mas, 3],
        ["e_plx", [], lambda v: float(v), u.mas, 3],
        ["pmra", [], lambda v: float(v), u.mas / u.yr, 3],
        ["e_pmra", [], lambda v: float(v), u.mas / u.yr, 3],
        ["pmdec", [], lambda v: float(v), u.mas / u.yr, 3],
        ["e_pmdec", [], lambda v: float(v), u.mas / u.yr, 3],
        ["Gmag", [], lambda v: float(v), u.mag, 4],
        ["RFG", [], lambda v: float(v), None, 3],
        ["BPmag", [], lambda v: float(v), u.mag, 4],
        ["RFBP", [], lambda v: float(v), None, 3],
        ["RPmag", [], lambda v: float(v), u.mag, 4],
        ["RFRP", [], lambda v: float(v), None, 3],
        ["E_BPRP", [], lambda v: float(v), None, 3],
        ["RUWE", [], lambda v: float(v), None, 2],
        ["RV", [], lambda v: float(v), u.km / u.s, 3],
        ["e_RV", [], lambda v: float(v), u.km / u.s, 4],
        ["GCNS_prob", [], lambda v: float(v), None, 3],
        ["WD_prob", [], lambda v: float(v), None, 3],
        ["Dist1", [], lambda v: float(v), u.kpc, 5],
        ["Dist16", [], lambda v: float(v), u.kpc, 5],
        ["Dist50", [], lambda v: float(v), u.kpc, 5],
        ["Dist84", [], lambda v: float(v), u.kpc, 5],
        ["xcoord50", [], lambda v: float(v), u.pc, 5],
        ["xcoord16", [], lambda v: float(v), u.pc, 5],
        ["xcoord84", [], lambda v: float(v), u.pc, 5],
        ["ycoord50", [], lambda v: float(v), u.pc, 5],
        ["ycoord16", [], lambda v: float(v), u.pc, 5],
        ["ycoord84", [], lambda v: float(v), u.pc, 5],
        ["zcoord50", [], lambda v: float(v), u.pc, 5],
        ["zcoord16", [], lambda v: float(v), u.pc, 5],
        ["zcoord84", [], lambda v: float(v), u.pc, 5],
        ["Uvel50", [], lambda v: float(v), u.km / u.s, 3],
        ["Uvel16", [], lambda v: float(v), u.km / u.s, 3],
        ["Uvel84", [], lambda v: float(v), u.km / u.s, 3],
        ["Vvel50", [], lambda v: float(v), u.km / u.s, 3],
        ["Vvel16", [], lambda v: float(v), u.km / u.s, 3],
        ["Vvel84", [], lambda v: float(v), u.km / u.s, 3],
        ["Wvel50", [], lambda v: float(v), u.km / u.s, 3],
        ["Wvel16", [], lambda v: float(v), u.km / u.s, 3],
        ["Wvel84", [], lambda v: float(v), u.km / u.s, 3],
        ["2MASS", None, None, None, None],
        ["Jmag", [], lambda v: float(v), u.mag, 3],
        ["e_Jmag", [], lambda v: float(v), u.mag, 3],
        ["Hmag", [], lambda v: float(v), u.mag, 3],
        ["e_Hmag", [], lambda v: float(v), u.mag, 3],
        ["Ksmag", [], lambda v: float(v), u.mag, 3],
        ["e_Ksmag", [], lambda v: float(v), u.mag, 3],
        ["W1mag", [], lambda v: float(v), u.mag, 3],
        ["e_W1mag", [], lambda v: float(v), u.mag, 3],
        ["W2mag", [], lambda v: float(v), u.mag, 3],
        ["e_W2mag", [], lambda v: float(v), u.mag, 3],
    ]

    def __init__(self, catalogue_entry: dict, from_string: bool = False):
        """Create a GCNS entry.

        Args:
            catalogue_entry: dict with GCNS field names (from dict parser)
                            or fixed-width string (from line parser)
            from_string: True if catalogue_entry is a fixed-width line string
        """
        try:
            if from_string:
                self._parse_keys(self.key_settings, catalogue_entry)
            else:
                self._parse_values(self.key_settings, catalogue_entry)

            self.id = f"Gaia GCNS {self.source_id}"

        except KeyError:
            raise

    @property
    def d(self) -> u.Quantity | None:
        """Distance from 50th percentile (Dist50 in kpc → pc)."""
        if not hasattr(self, "Dist50") or self.Dist50 == 0:
            return None
        return self.Dist50.to(u.pc)

    @property
    def parallax_distance(self) -> u.Quantity | None:
        """Distance derived from parallax (1/plx)."""
        if not hasattr(self, "plx") or self.plx is None or self.plx.value == 0:
            return None
        return (1 / self.plx.to(u.arcsec)).value * u.pc

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Adds derived fields: d (distance), pcx, pcy, pcz (Galactic coords).
        """
        json = super().to_dict()
        if self.d is not None:
            json["d"] = self.d.value
            json["d_unit"] = "pc"
        if hasattr(self, "xcoord50") and self.xcoord50 is not None:
            json["pcx"] = self.xcoord50.value
            json["pcy"] = self.ycoord50.value
            json["pcz"] = self.zcoord50.value
        if hasattr(self, "Uvel50") and self.Uvel50 is not None:
            json["Uvel"] = self.Uvel50.value
            json["Vvel"] = self.Vvel50.value
            json["Wvel"] = self.Wvel50.value
        return json

    def to_star_dict(self) -> dict:
        """Return a dict with fields matching Star.key_settings.

        Only includes fields that Star actually uses: id, Name, ra, dec, d.
        """
        return {
            "id": getattr(self, "id", None),
            "Name": getattr(self, "2MASS", None) or getattr(self, "source_id", None),
            "ra": getattr(self, "ra", None),
            "dec": getattr(self, "dec", None),
            "d": getattr(self, "d", None),
        }

    def to_star(self) -> "Star":
        """Create a Star object from this GaiaGCNSEntry.

        Returns:
            Star instance with id, ra, dec, d populated from this entry.
        """
        from astrolabium.creator import Star
        return Star(catalogue_entry=self.to_star_dict())

    def to_string(self) -> str:
        """Serialize entry back to fixed-width format for round-trip."""
        parts = []
        parts.append(f"{self.source_id:019d}")
        parts.append(f"{self.ra:14.7f}")
        parts.append(f"{self.e_ra:7.2f}")
        parts.append(f"{self.dec:14.7f}")
        parts.append(f"{self.e_dec:7.2f}")
        parts.append(f"{self.plx:9.3f}")
        parts.append(f"{self.e_plx:7.3f}")
        parts.append(f"{self.pmra:9.3f}")
        parts.append(f"{self.e_pmra:7.3f}")
        parts.append(f"{self.pmdec:9.3f}")
        parts.append(f"{self.e_pmdec:7.3f}")
        parts.append(f"{self.Gmag:8.4f}")
        parts.append(f"{self.RFG:9.3f}")
        parts.append(f"{self.BPmag:8.4f}")
        parts.append(f"{self.RFBP:9.3f}")
        parts.append(f"{self.RPmag:8.4f}")
        parts.append(f"{self.RFRP:9.3f}")
        parts.append(f"{self.E_BPRP:8.4f}")
        parts.append(f"{self.RUWE:5.2f}")
        parts.append(f"{self.RV:8.3f}")
        parts.append(f"{self.e_RV:8.4f}")
        parts.append(f"{self.GCNS_prob:7.3f}")
        parts.append(f"{self.WD_prob:5.3f}")
        parts.append(f"{self.Dist1:12.5f}")
        parts.append(f"{self.Dist16:12.5f}")
        parts.append(f"{self.Dist50:12.5f}")
        parts.append(f"{self.Dist84:12.5f}")
        parts.append(f"{self.xcoord50:12.5f}")
        parts.append(f"{self.xcoord16:12.5f}")
        parts.append(f"{self.xcoord84:12.5f}")
        parts.append(f"{self.ycoord50:12.5f}")
        parts.append(f"{self.ycoord16:12.5f}")
        parts.append(f"{self.ycoord84:12.5f}")
        parts.append(f"{self.zcoord50:12.5f}")
        parts.append(f"{self.zcoord16:12.5f}")
        parts.append(f"{self.zcoord84:12.5f}")
        parts.append(f"{self.Uvel50:8.3f}")
        parts.append(f"{self.Uvel16:8.3f}")
        parts.append(f"{self.Uvel84:8.3f}")
        parts.append(f"{self.Vvel50:8.3f}")
        parts.append(f"{self.Vvel16:8.3f}")
        parts.append(f"{self.Vvel84:8.3f}")
        parts.append(f"{self.Wvel50:8.3f}")
        parts.append(f"{self.Wvel16:8.3f}")
        parts.append(f"{self.Wvel84:8.3f}")
        parts.append(f"{getattr(self, 'NAME_GUNN', ' ' * 20):20s}")
        parts.append(f"{getattr(self, 'REFNAME_GUNN', ' ' * 19):19s}")
        parts.append(f"{getattr(self, 'gmag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'egmag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'rmag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'ermag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'imag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'eimag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'zmag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'ezmag_GUNN', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'NAME_2MASS', ' ' * 17):17s}")
        parts.append(f"{getattr(self, 'jm2MASS', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'jmsig2MASS', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'hm2MASS', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'hmsig2MASS', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'km2MASS', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'kmsig2MASS', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'NAME_WISE', ' ' * 20):20s}")
        parts.append(f"{getattr(self, 'w1mpropmWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w1sigmWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w2mpropmWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w2sigmWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w3mproWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w3sigmWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w4mproWISE', ' ' * 7):7.3f}")
        parts.append(f"{getattr(self, 'w4sigmWISE', ' ' * 7):7.3f}")
        return "".join(parts)


class GaiaGCNSMultipleSystem(EntryBase):
    """Represents a resolved multiple system from GCNS table3.dat.

    Contains 19,176 resolved binary/multiple systems within the GCNS sample.

    Key fields:
        SourceID1: Gaia EDR3 source_id of primary
        SourceID2: Gaia EDR3 source_id of secondary
        Sep: Angular separation (arcsec)
        magDiff: G magnitude difference
        projSep: Projected separation (AU)
        binary: 1=binary, 0=multiple
        bound: 1=formally bound system, 0=unbound
    """

    key_settings = [
        ["SourceID1", None, lambda v: int(v), None, None],
        ["SourceID2", None, lambda v: int(v), None, None],
        ["Sep", [], lambda v: float(v), u.arcsec, 4],
        ["magDiff", [], lambda v: float(v), u.mag, 4],
        ["projSep", [], lambda v: float(v), u.AU, 4],
        ["binary", None, lambda v: int(v), None, None],
        ["Coma", None, lambda v: int(v), None, None],
        ["Hyades", None, lambda v: int(v), None, None],
        ["bound", None, lambda v: int(v), None, None],
    ]

    def __init__(self, catalogue_entry: dict, from_string: bool = False):
        try:
            if from_string:
                self._parse_keys(self.key_settings, catalogue_entry)
            else:
                self._parse_values(self.key_settings, catalogue_entry)

            self.id = f"GCNS Multiple {self.SourceID1}-{self.SourceID2}"

        except KeyError:
            raise

    def to_dict(self) -> dict:
        return {
            "SourceID1": self.SourceID1,
            "SourceID2": self.SourceID2,
            "Sep": self.Sep.value if self.Sep else None,
            "Sep_unit": "arcsec",
            "magDiff": self.magDiff.value if self.magDiff else None,
            "projSep": self.projSep.value if self.projSep else None,
            "projSep_unit": "AU",
            "binary": self.binary,
            "Coma": self.Coma,
            "Hyades": self.Hyades,
            "bound": self.bound,
        }

    def to_string(self) -> str:
        """Serialize to fixed-width format."""
        parts = []
        parts.append(f"{self.SourceID1:019d}")
        parts.append(f"{self.SourceID2:019d}")
        parts.append(f"{self.Sep:9.4f}")
        parts.append(f"{self.magDiff:7.4f}")
        parts.append(f"{self.projSep:11.4f}")
        parts.append(f"{self.binary}")
        parts.append(f"{self.Coma}")
        parts.append(f"{self.Hyades}")
        parts.append(f"{self.bound}")
        return "".join(parts)
