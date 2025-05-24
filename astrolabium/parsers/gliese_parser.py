from astrolabium.parsers import ParserBase
from astrolabium import config
import re


class GlieseParser(ParserBase):
    __filename = "gliese"
    __gliese_catalogue_url = "https://cdsarc.cds.unistra.fr/viz-bin/nph-Cat/txt?V/70A/catalog.dat.gz"
    __gliese_catalogue_local = f"{config.path_cataloguedir}/{__filename}.txt"

    __columns = [
        ["Name", 0, "left", re.compile(r"[A-Za-z]{2}\s*[0-9.]+").fullmatch, lambda s: re.sub(r"\s{2,}", " ", s)],
        ["Comp", 1, "left", re.compile(r"[A-Z0-9\*\s\-]{0,2}").fullmatch, ParserBase.pre_copy],
        # Component ID, usually 'A', 'B', etc.
        ["RA_DE", 3, "left", re.compile(r"\d{2} \d{2} \d{2} [\+\-]\d{2} \d{2}\.\d*").fullmatch, ParserBase.pre_copy],
        ["pm", 4, "right", re.compile(r"[\+\-]?\d*\.\d+").fullmatch, ParserBase.pre_copy],  # total proper motion
        ["u_pm", 5, "left", re.compile(r"[\s:]?").fullmatch, ParserBase.pre_copy],  # uncertainty or source of pm
        ["pmPA", 6, "right", re.compile(r"\d{1,3}\.?\d*").fullmatch, ParserBase.pre_copy],  # proper motion angle
        ["RV", 7, "right", re.compile(r"[\+\-]?\d*\.\d?").fullmatch, ParserBase.pre_copy],  # radial velocity
        ["Sp", 9, "left", re.compile(r"\S*.*").fullmatch, ParserBase.pre_copy],  # spectral type
        ["plx", 25, "right", re.compile(r"\d+\.?\d*").fullmatch, ParserBase.pre_copy],  # parallax
        ["e_plx", 26, "right", re.compile(r"\d+\.?\d*").fullmatch, ParserBase.pre_copy],  # parallax error
    ]

    def _validate_columns(self):
        for i, c in enumerate(self.validators[1:]):
            assert c[1] > self.validators[i][1]
        return True

    def __init__(self):
        ParserBase.__init__(
            self,
            "GJ",
            self.__gliese_catalogue_url,
            self.__gliese_catalogue_local,
            "gliese",
            "Gliese-Jahrweiss catalogue",
            self.__columns,
            12,
            3814,
            None,
            use_separator="|",
        )


def run():
    parser = GlieseParser()
    parser.convert()
