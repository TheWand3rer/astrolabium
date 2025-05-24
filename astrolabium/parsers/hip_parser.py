from astrolabium import config, fileIO as io
from astrolabium.parsers import ParserBase
import re
from astrolabium.parsers.data import HipparcosEntry


class HipparcosParser(ParserBase):
    __columns = [
        ["HIP", [1, 6], "left", re.compile(r"(\d+)?").fullmatch, ParserBase.pre_copy],
        ["Sn", [8, 10], "right", re.compile(r"(\d+)?").fullmatch, ParserBase.pre_copy],
        ["So", [12, 12], "left", re.compile(r"(\d)?").fullmatch, ParserBase.pre_copy],
        ["nc", [14, 14], "left", re.compile(r"(\d)?").fullmatch, ParserBase.pre_copy],
        ["ra", [16, 28], "left", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # rad Epoch 1991.25
        ["de", [30, 42], "left", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # rad Epoch 1991.25
        ["plx", [44, 50], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas
        ["pmRA", [52, 59], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas/yr
        ["pmDE", [61, 68], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas/yr
        ["e_ra", [70, 75], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas
        ["e_de", [77, 82], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas
        ["e_plx", [84, 89], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas
        ["e_pmRA", [91, 96], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas/yr
        ["e_pmDE", [98, 103], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mas/yr
        ["Ntr", [105, 107], "right", re.compile(r"(\d+)?").fullmatch, ParserBase.pre_copy],  # ---
        ["F2", [109, 113], "right", re.compile(r"-?(\d+\.?\d*)?").fullmatch, ParserBase.pre_copy],  # ---
        ["F1", [115, 116], "right", re.compile(r"(\d+)?").fullmatch, ParserBase.pre_copy],  # % rejected data
        ["var", [118, 123], "right", re.compile(r"(\d+\.?\d*)?").fullmatch, ParserBase.pre_copy],  # cosmic dispersion
        ["ic", [125, 128], "right", re.compile(r"(\d+)?").fullmatch, ParserBase.pre_copy],  # suppl. catalogues
        ["Hpmag", [130, 136], "right", re.compile(r"-?(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mag
        ["e_Hpmag", [138, 143], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mag
        ["sHp", [145, 149], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mag
        ["VA", [151, 151], "right", re.compile(r"(\d)?").fullmatch, ParserBase.pre_copy],  # variability annex
        ["B-V", [153, 158], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mag
        ["e_B-V", [160, 164], "right", re.compile(r"(\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mag
        ["V-I", [166, 171], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],  # mag
        # UW (15 fields of F7.2 format; each 7 characters wide, starting at col 172 to 276)
        ["UW1", [173, 179], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW2", [180, 186], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW3", [187, 193], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW4", [194, 200], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW5", [201, 207], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW6", [208, 214], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW7", [215, 221], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW8", [222, 228], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW9", [229, 235], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW10", [236, 242], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW11", [243, 249], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW12", [250, 256], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW13", [257, 263], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW14", [264, 270], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
        ["UW15", [271, 277], "right", re.compile(r"(-?\d+\.\d+)?").fullmatch, ParserBase.pre_copy],
    ]

    __concise_columns = ["HIP", "nc", "ra", "de", "plx", "pmRA", "pmDE"]

    def __init__(self, concise: bool = True, j2000: bool = False):
        self.__concise = concise
        self.__j2000 = j2000
        ParserBase.__init__(
            self,
            "HIP",
            catalogue_url="https://cdsarc.u-strasbg.fr/viz-bin/nph-Cat/txt.gz?I/311/hip2.dat.gz",
            catalogue_local=f"{config.path_cataloguedir}/hipparcos_2007.dat",
            out_filename="hipparcos2007",
            catalogue_title="Hipparcos 2 catalogue",
            column_validators=self.__columns,
            start_line=6,
            end_line=117961,
            star_f=HipparcosEntry,
        )

    def _validate_columns(self):
        ParserBase._validate_columns(self)
        for i in range(len(self.__columns) - 1):
            assert self.__columns[i + 1][1][0] - self.__columns[i][1][1] <= 2, (
                "Invalid spacing between columns: " + self.__columns[i + 1][0] + " and " + self.__columns[i][0]
            )

    @classmethod
    def run(concise=True, j2000=True):
        if not concise:
            raise NotImplementedError("Full parsing of the Hipparcos catalog not yet implemneted")

        parser = HipparcosParser(concise, j2000)
        stars = parser.parse()
        io.write_list_json([star.to_dict() for star in stars], f"{config.path_datadir}/hipparcos2007")
        return stars
