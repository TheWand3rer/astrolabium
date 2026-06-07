"""Gliese parser using VizieR VOTable API.

The raw text format (V/70A/catalog.dat.gz) is blocked by CDS bot detection.
This parser uses the VOTable API which returns clean XML data.

Catalogue: V/70A — Preliminary Version of the Third Catalogue of Nearby Stars (CNS3)
Authors: Gliese W., Jahrweiss H. (1991)
Coverage: ~9,110 stars within 25 parsecs (~81 light-years)

VOTable columns:
- Name: Star identifier (e.g., "Gl 1", "GJ 1001", "NN 3001")
- RAB1950: Right Ascension B1950
- DEB1950: Declination B1950
- pm: Total proper motion (arcsec/yr)
- pmPA: Proper motion position angle (deg)
- RV: Radial velocity (km/s)
- Sp: Spectral type
- Vmag: V magnitude
- B-V: B-V color index
- plx: Trigonometric parallax (mas)
- _RA.icrs: RA J2000 (computed by VizieR)
- _DE.icrs: Dec J2000 (computed by VizieR)
"""

import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from tqdm import tqdm
import astrolabium.config as config
import astrolabium.fileIO as io
import logging
import re

logger = logging.getLogger(__name__)


class GlieseVOTableEntry:
    """Represents a single star entry from the Gliese catalogue (VOTable format)."""

    def __init__(self, data: dict):
        self.Name = data.get("Name", "")
        self.RAB1950 = data.get("RAB1950", "")
        self.DEB1950 = data.get("DEB1950", "")
        self.pm = data.get("pm", "")
        self.pmPA = data.get("pmPA", "")
        self.RV = data.get("RV", "")
        self.Sp = data.get("Sp", "")
        self.Vmag = data.get("Vmag", "")
        self.BV = data.get("BV", "")
        self.plx = data.get("plx", "")
        self.RAIcrs = data.get("RAIcrs", "")
        self.DEIcrs = data.get("DEIcrs", "")
        self.from_string = data.get("from_string", False)

    def to_dict(self) -> dict:
        return {
            "Name": self.Name,
            "RAB1950": self.RAB1950,
            "DEB1950": self.DEB1950,
            "pm": self.pm,
            "pmPA": self.pmPA,
            "RV": self.RV,
            "Sp": self.Sp,
            "Vmag": self.Vmag,
            "BV": self.BV,
            "plx": self.plx,
            "RAIcrs": self.RAIcrs,
            "DEIcrs": self.DEIcrs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GlieseVOTableEntry":
        data["from_string"] = True
        return cls(data)


class GlieseVOTableParser:
    """Parser for the Gliese catalogue using VizieR VOTable API.

    The VOTable API returns clean XML data, avoiding the CDS bot detection
    that blocks the raw text format download.
    """

    VOTABLE_URL = "https://vizier.cds.unistra.fr/viz-bin/votable?-source=V/70A"
    LOCAL_PATH = f"{config.path_datadir}/gliese_votable"

    def __init__(self, max_entries: int = 0):
        """
        Args:
            max_entries: Maximum number of entries to fetch (0 = all)
        """
        self.max_entries = max_entries
        self.entries: list[GlieseVOTableEntry] = []

    def download(self) -> str:
        """Download VOTable XML from VizieR API."""
        logger.info(f"Downloading Gliese catalogue from {self.VOTABLE_URL}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        response = requests.get(self.VOTABLE_URL, headers=headers, timeout=120)
        response.raise_for_status()
        return response.text

    def parse_xml(self, xml_text: str) -> list[dict]:
        """Parse VOTable XML and return list of star dictionaries."""
        root = ET.fromstring(xml_text)

        # Find the TABLE element
        ns = {"votable": "http://www.ivoa.net/xml/VOTable/v1.3"}
        table = root.find(".//votable:TABLE", ns)
        if table is None:
            # Try without namespace
            table = root.find(".//TABLE")

        if table is None:
            raise ValueError("No TABLE element found in VOTable")

        # Get field names
        fields = []
        for field in table.findall(".//FIELD") + table.findall(".//votable:FIELD", ns):
            field_name = field.get("name")
            if field_name:
                fields.append(field_name)

        # Get data rows
        rows = []
        for tr in table.findall(".//TR") + table.findall(".//votable:TR", ns):
            row = {}
            for i, td in enumerate(tr.findall(".//TD") + tr.findall(".//votable:TD", ns)):
                if i < len(fields):
                    value = td.text.strip() if td.text else ""
                    # Map VOTable field names to our internal names
                    field_name = fields[i]
                    if field_name == "_RA.icrs":
                        row["RAIcrs"] = value
                    elif field_name == "_DE.icrs":
                        row["DEIcrs"] = value
                    elif field_name == "B-V":
                        row["BV"] = value
                    else:
                        row[field_name] = value
            if row.get("Name"):  # Only keep rows with a name
                rows.append(row)

        return rows

    def parse(self, n: int = 0) -> list[GlieseVOTableEntry]:
        """Parse the Gliese catalogue and return star entries.

        Args:
            n: Number of entries to parse (0 = all)

        Returns:
            List of GlieseVOTableEntry objects
        """
        # Download and parse
        xml_text = self.download()
        rows = self.parse_xml(xml_text)

        # Limit to n entries if specified
        if n > 0:
            rows = rows[:n]

        # Convert to GlieseVOTableEntry objects
        self.entries = [GlieseVOTableEntry(row) for row in rows]
        return self.entries

    def convert(self) -> str:
        """Download, parse, and save to JSON file.

        Returns:
            Path to the saved JSON file
        """
        entries = self.parse()
        io.write_list_json([e.to_dict() for e in entries], self.LOCAL_PATH)
        logger.info(f"Saved {len(entries)} Gliese entries to {self.LOCAL_PATH}")
        return self.LOCAL_PATH

    def known_fields(self) -> list[str]:
        """Return list of known field names."""
        return ["Name", "RAB1950", "DEB1950", "pm", "pmPA", "RV", "Sp", "Vmag", "BV", "plx", "RAIcrs", "DEIcrs"]


def run(max_entries: int = 0):
    """Run the Gliese VOTable parser.

    Args:
        max_entries: Maximum number of entries to fetch (0 = all)
    """
    parser = GlieseVOTableParser(max_entries=max_entries)
    path = parser.convert()
    logger.info(f"Gliese catalogue parsed and saved to {path}")
    return parser.entries


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    entries = run()
    print(f"Parsed {len(entries)} Gliese entries")
    for entry in entries[:5]:
        print(entry.to_dict())
