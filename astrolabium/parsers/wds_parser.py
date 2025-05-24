import re
from tqdm import tqdm
from astrolabium import config, fileIO as io
from astrolabium.parsers import ParserBase
from astrolabium.parsers.data import WDSEntry


class WDSParser(ParserBase):
    __filename = "wds"
    __wds_catalogue_url = "https://www.astro.gsu.edu/wds/Webtextfiles/wdsweb_summ2.txt"
    __wds_catalogue_local = f"{config.path_cataloguedir}/{__filename}.txt"
    __columns = [
        ["WDS", [1, 10], "left", re.compile(r"\d{5}[+-]\d{4}").fullmatch, ParserBase.pre_copy],
        ["disc", [11, 17], "left", re.compile(r"[A-Za-z0-9\s]{1,7}").fullmatch, ParserBase.pre_copy],
        ["comp", [18, 22], "left", re.compile(r"[A-Za-z0-9,]+").fullmatch, ParserBase.pre_copy],
        ["obs_f", [24, 27], "right", re.compile(r"[-]?\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["obs_l", [29, 32], "right", re.compile(r"[-]?\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["n_obs", [34, 37], "right", re.compile(r"\d{1,4}").fullmatch, ParserBase.pre_copy],
        ["pa1", [39, 41], "right", re.compile(r"[0-9\-]{1,3}").fullmatch, ParserBase.pre_copy],
        ["pa2", [43, 45], "right", re.compile(r"[0-9\-]{1,3}").fullmatch, ParserBase.pre_copy],
        ["sep1", [47, 51], "right", re.compile(r"[-]?\d{1,4}\.\d{1,3}").fullmatch, ParserBase.pre_copy],
        ["sep2", [53, 57], "right", re.compile(r"[-]?\d{1,4}\.\d{1,3}").fullmatch, ParserBase.pre_copy],
        ["mag1", [59, 63], "right", re.compile(r"[-]?\d{0,2}\.\s?\d{0,2}").fullmatch, ParserBase.pre_copy],
        ["mag2", [65, 69], "right", re.compile(r"[-]?\d{0,2}\.\s?\d{0,2}").fullmatch, ParserBase.pre_copy],
        ["st", [71, 79], "left", re.compile(r".{0,10}").fullmatch, ParserBase.pre_copy],
        ["pm1_ra", [81, 84], "right", re.compile(r"[+-]?\d{0,3}").fullmatch, ParserBase.pre_copy],
        ["pm1_dec", [85, 88], "right", re.compile(r"[+-]?\d{0,3}").fullmatch, ParserBase.pre_copy],
        ["pm2_ra", [90, 93], "right", re.compile(r"[+-]?\d{0,3}").fullmatch, ParserBase.pre_copy],
        ["pm2_dec", [94, 97], "right", re.compile(r"[+-]?\d{0,3}").fullmatch, ParserBase.pre_copy],
        ["DM", [99, 106], "left", re.compile(r"[0-9+\-\s]{0,8}").fullmatch, ParserBase.pre_copy],
        ["notes", [108, 111], "left", re.compile(r"[A-Z\s]*").fullmatch, ParserBase.pre_copy],
        ["coord", [113, 130], "left", re.compile(r"[0-9+-.\s]+").fullmatch, ParserBase.pre_copy],
    ]

    def __init__(self, compressed=False):
        ParserBase.__init__(
            self,
            "WDS",
            self.__wds_catalogue_url,
            self.__wds_catalogue_local,
            "wds",
            "Washington Double Star catalog",
            self.__columns,
            6,
            157161,
            WDSEntry,
            compressed,
        )

    def _validate_columns(self):
        ParserBase._validate_columns(self)

    @classmethod
    def run(cls):
        parser = WDSParser()
        parser.convert()
