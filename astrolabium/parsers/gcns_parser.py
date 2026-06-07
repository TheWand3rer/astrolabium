"""Gaia GCNS (Gaia Catalogue of Nearby Stars) parser.

GCNS contains 331,312 objects within 100 pc of the Sun from Gaia EDR3.
Based on: Gaia Collaboration et al. (2021), A&A 649, A6.

Data file: table1c.dat.gz — 331,312 records, 760 bytes/line, fixed-width ASCII.
"""

import re
from pathlib import Path

from astrolabium.parsers.parser_base import ParserBase
from astrolabium.parsers.data import GaiaGCNSEntry
import logging

logger = logging.getLogger(__name__)

# Regex validators for field types
_RE_INT = re.compile(r"^-?\d+$")
_RE_FLOAT = re.compile(r"^-?\d+\.\d+$")
_RE_STR = re.compile(r"^[\w\s.\-]+$")


def _preprocess_int(s: str) -> int:
    """Convert string to int."""
    return int(s.strip()) if s.strip() else None


def _preprocess_float(s: str) -> float:
    """Convert string to float."""
    return float(s.strip()) if s.strip() else None


def _preprocess_str(s: str) -> str:
    """Strip whitespace from string."""
    return s.strip() if s else ""


class GaiaGCNSParser(ParserBase):
    """Parser for the Gaia GCNS catalogue (table1c.dat.gz).

    Inherits from ParserBase and uses its fixed-width parsing with
    gzip decompression support.
    """

    CATALOGUE_LABEL = "GaiaGCNS"
    CATALOGUE_URL = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/649/A6/table1c.dat.gz"
    CATALOGUE_LOCAL = "catalogues/gaia_gcns_table1c.dat.gz"
    OUT_FILENAME = "gcns_catalogue.json"
    CATALOGUE_TITLE = "Gaia GCNS Catalogue"
    START_LINE = 1  # No header lines
    END_LINE = 331312  # Total records in the catalogue

    # Essential fields for concise JSON output
    __concise_columns = [
        "source_id",
        "ra", "dec",
        "plx", "e_plx",
        "pmra", "pmdec", "e_pmra", "e_pmdec",
        "Gmag", "BPmag", "RPmag",
        "Dist50",
        "xcoord50", "ycoord50", "zcoord50",
        "Uvel50", "Vvel50", "Wvel50",
    ]

    # Column definitions: (key, interval, alignment, validator, preprocessor)
    # VizieR uses 1-indexed byte positions
    __COLUMNS = [
        ("source_id", (3, 21), "right", _RE_INT, _preprocess_int),
        ("ra", (23, 37), "right", _RE_FLOAT, _preprocess_float),
        ("e_ra", (38, 45), "right", _RE_FLOAT, _preprocess_float),
        ("dec", (46, 60), "right", _RE_FLOAT, _preprocess_float),
        ("e_dec", (61, 68), "right", _RE_FLOAT, _preprocess_float),
        ("plx", (69, 78), "right", _RE_FLOAT, _preprocess_float),
        ("e_plx", (79, 86), "right", _RE_FLOAT, _preprocess_float),
        ("pmra", (87, 96), "right", _RE_FLOAT, _preprocess_float),
        ("e_pmra", (97, 104), "right", _RE_FLOAT, _preprocess_float),
        ("pmdec", (105, 114), "right", _RE_FLOAT, _preprocess_float),
        ("e_pmdec", (115, 122), "right", _RE_FLOAT, _preprocess_float),
        ("Gmag", (123, 131), "right", _RE_FLOAT, _preprocess_float),
        ("RFG", (132, 141), "right", _RE_FLOAT, _preprocess_float),
        ("BPmag", (142, 150), "right", _RE_FLOAT, _preprocess_float),
        ("RFBP", (151, 160), "right", _RE_FLOAT, _preprocess_float),
        ("RPmag", (161, 169), "right", _RE_FLOAT, _preprocess_float),
        ("RFRP", (170, 179), "right", _RE_FLOAT, _preprocess_float),
        ("E_BPRP", (180, 188), "right", _RE_FLOAT, _preprocess_float),
        ("RUWE", (189, 194), "right", _RE_FLOAT, _preprocess_float),
        ("RV", (199, 207), "right", _RE_FLOAT, _preprocess_float),
        ("e_RV", (208, 216), "right", _RE_FLOAT, _preprocess_float),
        ("GCNS_prob", (240, 245), "right", _RE_FLOAT, _preprocess_float),
        ("WD_prob", (246, 251), "right", _RE_FLOAT, _preprocess_float),
        ("Dist1", (252, 264), "right", _RE_FLOAT, _preprocess_float),
        ("Dist16", (265, 277), "right", _RE_FLOAT, _preprocess_float),
        ("Dist50", (278, 290), "right", _RE_FLOAT, _preprocess_float),
        ("Dist84", (291, 303), "right", _RE_FLOAT, _preprocess_float),
        ("xcoord50", (304, 316), "right", _RE_FLOAT, _preprocess_float),
        ("xcoord16", (317, 329), "right", _RE_FLOAT, _preprocess_float),
        ("xcoord84", (330, 342), "right", _RE_FLOAT, _preprocess_float),
        ("ycoord50", (343, 355), "right", _RE_FLOAT, _preprocess_float),
        ("ycoord16", (356, 368), "right", _RE_FLOAT, _preprocess_float),
        ("zcoord50", (382, 394), "right", _RE_FLOAT, _preprocess_float),
        ("zcoord16", (395, 407), "right", _RE_FLOAT, _preprocess_float),
        ("zcoord84", (408, 420), "right", _RE_FLOAT, _preprocess_float),
        ("Uvel50", (421, 429), "right", _RE_FLOAT, _preprocess_float),
        ("Uvel16", (430, 438), "right", _RE_FLOAT, _preprocess_float),
        ("Uvel84", (439, 447), "right", _RE_FLOAT, _preprocess_float),
        ("Vvel50", (448, 456), "right", _RE_FLOAT, _preprocess_float),
        ("Vvel16", (457, 465), "right", _RE_FLOAT, _preprocess_float),
        ("Vvel84", (466, 474), "right", _RE_FLOAT, _preprocess_float),
        ("Wvel50", (475, 483), "right", _RE_FLOAT, _preprocess_float),
        ("Wvel16", (484, 492), "right", _RE_FLOAT, _preprocess_float),
        ("Wvel84", (493, 501), "right", _RE_FLOAT, _preprocess_float),
        ("NAME_GUNN", (502, 522), "left", _RE_STR, _preprocess_str),
        ("REFNAME_GUNN", (524, 543), "left", _RE_STR, _preprocess_str),
        ("gmag_GUNN", (544, 551), "right", _RE_FLOAT, _preprocess_float),
        ("egmag_GUNN", (552, 559), "right", _RE_FLOAT, _preprocess_float),
        ("rmag_GUNN", (560, 567), "right", _RE_FLOAT, _preprocess_float),
        ("ermag_GUNN", (568, 575), "right", _RE_FLOAT, _preprocess_float),
        ("imag_GUNN", (576, 583), "right", _RE_FLOAT, _preprocess_float),
        ("eimag_GUNN", (584, 591), "right", _RE_FLOAT, _preprocess_float),
        ("zmag_GUNN", (592, 599), "right", _RE_FLOAT, _preprocess_float),
        ("ezmag_GUNN", (600, 607), "right", _RE_FLOAT, _preprocess_float),
        ("NAME_2MASS", (611, 628), "left", _RE_STR, _preprocess_str),
        ("jm2MASS", (629, 636), "right", _RE_FLOAT, _preprocess_float),
        ("jmsig2MASS", (637, 644), "right", _RE_FLOAT, _preprocess_float),
        ("hm2MASS", (645, 652), "right", _RE_FLOAT, _preprocess_float),
        ("hmsig2MASS", (653, 660), "right", _RE_FLOAT, _preprocess_float),
        ("km2MASS", (661, 668), "right", _RE_FLOAT, _preprocess_float),
        ("kmsig2MASS", (669, 676), "right", _RE_FLOAT, _preprocess_float),
        ("NAME_WISE", (677, 697), "left", _RE_STR, _preprocess_str),
        ("w1mpropmWISE", (698, 705), "right", _RE_FLOAT, _preprocess_float),
        ("w1sigmWISE", (706, 713), "right", _RE_FLOAT, _preprocess_float),
        ("w2mpropmWISE", (714, 721), "right", _RE_FLOAT, _preprocess_float),
        ("w2sigmWISE", (722, 729), "right", _RE_FLOAT, _preprocess_float),
        ("w3mproWISE", (730, 737), "right", _RE_FLOAT, _preprocess_float),
        ("w3sigmWISE", (738, 745), "right", _RE_FLOAT, _preprocess_float),
        ("w4mproWISE", (746, 753), "right", _RE_FLOAT, _preprocess_float),
        ("w4sigmWISE", (754, 761), "right", _RE_FLOAT, _preprocess_float),
    ]

    def __init__(self, concise: bool = True):
        """Initialize the GCNS parser with column validators and gzip support.

        Args:
            concise: If True, only parse essential fields for a compact JSON output.
                     Essential fields: source_id, astrometry (ra/dec/plx/pmma),
                     photometry (G/BP/RP), distance, and Galactic coords/velocities.
        """
        super().__init__(
            catalogue_label=self.CATALOGUE_LABEL,
            catalogue_url=self.CATALOGUE_URL,
            catalogue_local=self.CATALOGUE_LOCAL,
            out_filename=self.OUT_FILENAME,
            catalogue_title=self.CATALOGUE_TITLE,
            column_validators=self.__COLUMNS,
            start_line=self.START_LINE,
            end_line=self.END_LINE,
            star_f=GaiaGCNSEntry,
            compressed=False,  # Output JSON compression (not input)
        )
        # Enable gzip decompression for input file
        self._ParserBase__compressed = True
        # Enable concise mode for compact JSON output
        self._ParserBase__concise = concise
        self._ParserBase__concise_columns = self.__concise_columns

    def download(self):
        """Download the GCNS catalogue from CDS.

        Uses urllib to download the gzip-compressed file directly,
        bypassing CDS Anubis bot detection.
        """
        import urllib.request

        path = Path(self.catalogue_local)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            logger.info(f"Using cached GCNS catalogue: {path}")
            return

        logger.info(f"Downloading GCNS catalogue from {self.CATALOGUE_URL}")
        urllib.request.urlretrieve(self.CATALOGUE_URL, str(path))
        logger.info(f"Saved to {path}")
