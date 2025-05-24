import re
import astrolabium.config as config
import astrolabium.fileIO as io
from astrolabium.parsers.data import Orb6Entry
from astrolabium.parsers import ParserBase


class Orb6Parser(ParserBase):
    __orb6_catalogue_url = "https://www.astro.gsu.edu/wds/orb6/orb6orbits.txt"
    __orb6_catalogue_local = f"{config.path_cataloguedir}/orb6orbits.txt"

    __columns = [
        ["WDS", [20, 30], "left", re.compile(r"\d{5}[+-]\d{4}").fullmatch, ParserBase.pre_copy],
        ["comp", [38, 45], "left", re.compile(r"[A-Ha-h1-2,?]*").fullmatch, ParserBase.find_start],
        ["HD", [52, 58], "left", re.compile(r"[0-9.]{1,6}[BCJ]?").fullmatch, ParserBase.pre_copy],
        ["HIP", [59, 65], "left", re.compile(r"[0-9.]{1,6}B?").fullmatch, ParserBase.pre_copy],
        ["P", [82, 93], "left", re.compile(r"\d{0,4}\.\d{0,6}\s*[mhdyc]*").fullmatch, ParserBase.pre_copy],
        ["P_e", [95, 105], "left", re.compile(r"\d{0,4}\.\d{0,6}").fullmatch, ParserBase.pre_copy],
        ["a", [106, 115], "left", re.compile(r"\d{0,4}\.\d{0,5}\s*[amMu]*").fullmatch, ParserBase.pre_copy],
        ["a_e", [117, 125], "left", re.compile(r"\d{0,4}\.\d{0,5}").fullmatch, ParserBase.pre_copy],
        ["i", [126, 134], "left", re.compile(r"\d{0,3}\.\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["i_e", [135, 143], "left", re.compile(r"\d{0,3}\.\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["lan", [144, 152], "left", re.compile(r"-?\d{0,3}\.\d{0,4}\s*[\*q]?").fullmatch, ParserBase.pre_copy],
        ["lan_e", [154, 162], "left", re.compile(r"\d{0,3}\.\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["e", [188, 196], "left", re.compile(r"\d{0,1}\.\d{0,6}").fullmatch, ParserBase.pre_copy],
        ["e_e", [197, 205], "left", re.compile(r"\d{0,1}\.\d{0,6}").fullmatch, ParserBase.pre_copy],
        ["lpa", [206, 214], "left", re.compile(r"-?\d{0,3}\.\d{0,4}\s*q?").fullmatch, ParserBase.pre_copy],
        ["lpa_e", [215, 223], "left", re.compile(r"\d{0,3}\.\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["last", [229, 233], "left", re.compile(r"\d{0,4}").fullmatch, ParserBase.pre_copy],
        ["orb_g", [234, 235], "left", re.compile(r"\d{1}").fullmatch, ParserBase.pre_copy],
        ["notes", [236, 237], "left", re.compile(r"[a-z]{1}").fullmatch, ParserBase.pre_copy],
    ]

    def __init__(self):
        ParserBase.__init__(
            self,
            "ORB6",
            self.__orb6_catalogue_url,
            self.__orb6_catalogue_local,
            "orb6orbits",
            "Sixth Catalog of Orbits of Visual Binary Stars",
            self.__columns,
            8,
            3802,
            Orb6Entry,
        )

    @classmethod
    def run(cls):
        parser = Orb6Parser()
        list = parser.parse()
        io.write_list_json(list, f"{config.path_datadir}/orb6orbits")
