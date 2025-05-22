import astropy.units as u
from astrolabium.parsers.data import EntryBase
import logging

logger = logging.getLogger(__name__)

class WDSEntry(EntryBase):
    key_settings = [
        # key, nullvalues, postproc, unit, digits]
        ["WDS", None, None, None, None],
        ["disc", None, None, None, None],
        ["comp", None, None, None, None],
        ["obs_f", None, lambda v: int(v), None, 0],
        ["obs_l", None, lambda v: int(v), None, 0],
        ["n_obs", None, lambda v: int(v), None, 0],
        ["pa1", None, lambda v: float(v), u.deg, 0],
        ["pa2", None, lambda v: float(v), u.deg, 0],
        ["sep1", None, lambda v: float(v), u.arcsec, 1],
        ["sep2", None, lambda v: float(v), u.arcsec, 1],
        ["mag1", ["."], lambda v: float(v.replace(" ", "")), None, 2],
        ["mag2", ["."], lambda v: float(v), None, 2],
        ["st", None, None, None, None],
        ["pm1_ra", None, lambda v: float(v), u.arcsec / u.kyr, 0],
        ["pm1_dec", None, lambda v: float(v), u.arcsec / u.kyr, 0],
        ["pm1_ra", None, lambda v: float(v), u.arcsec / u.kyr, 0],
        ["pm1_dec", None, lambda v: float(v), u.arcsec / u.kyr, 0],
        ["pm2_ra", None, lambda v: float(v), u.arcsec / u.kyr, 0],
        ["pm2_dec", None, lambda v: float(v), u.arcsec / u.kyr, 0],
        ["DM", None, None, None, None],
        ["notes", None, None, None, None],
        ["coord", None, None, None, None],
    ]

    def __init__(self, catalogue_data, from_string=False):
        super().__init__(catalogue_data)
        self.st = None
        self.WDS: str
        self.comp: str | None
        self.disc: str

        try:
            if from_string:
                self._parse_keys(self.key_settings, catalogue_data)
            else:
                self._parse_values(self.key_settings, catalogue_data)

            assert self.disc is not None
        except (KeyError, AttributeError) as e:
            logger.error("Missing key:", e)
            logger.error(catalogue_data)
            raise

    def _parse_pm(self, val):
        val = val.strip()
        return int(val) * u.arcsec / u.kyr if val and val not in ["---", ""] else None

    @property
    def is_physical(self) -> bool:
        physical = False
        if hasattr(self, "notes"):
            notes = self.notes.strip()
            for i in range(0, len(notes)):
                c = notes[i]
                if c == "N":
                    continue
                elif c in ["C", "O", "T", "V", "Z"]:
                    physical = True
                    # doubles that have these notes *are* considered to be physically bound
                    # C: Orbit and Linear solution. A published orbit exists
                    # O: Orbit, briefly described in WDSNOT MEMO and has entry in Orbit Catalog
                    # T: Statistically the same parallax within the errors and similar proper motion or other technique indicates that this pair is physical.
                    # V: Proper motion or other technique indicates that this  pair is physical.
                elif c in ["I", "L", "S", "U", "X", "Y"]:
                    physical = False
                    # doubles that have these notes are *not* considered to be physically bound
                    # L: Linear solution. Linear elements for this pair have been determined.
                    # S: Statistically different parallax and proper motion indicates that this pair is non-physical.
                    # U: Proper motion or other technique indicates that this pair is non-physical.
                    # X: A "Dubious Double" (or "Bogus Binary").
                    # Y: Statistically different parallax for the components indicates they are non-physical.
                    break
                else:
                    if c in "W":
                        logger.debug(f"<{self.WDS}> has additional components and/or measures in the WDS Supplement (WDSS) catalog.")
        if not hasattr(self, "comp"):
            physical = False

        return physical
