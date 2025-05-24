import requests
from pathlib import Path
from tqdm import tqdm
import astrolabium.config as config
import astrolabium.fileIO as io
import typing
import logging

logger = logging.getLogger(__name__)


class ParserBase:
    def __init__(
        self,
        catalogue_label,
        catalogue_url,
        catalogue_local,
        out_filename,
        catalogue_title,
        column_validators,
        start_line,
        end_line,
        star_f: typing.Callable,
        compressed=False,
        use_separator: str | None = None,
    ):
        self.catalogue_label = catalogue_label
        self.catalogue_url = catalogue_url
        self.catalogue_local = catalogue_local
        self.catalogue_title = catalogue_title
        self.validators = column_validators
        self.start_line = start_line
        self.end_line = end_line
        self.star_f = star_f
        self.__concise = False
        self.__concise_columns: list[str] = []
        self.out_filename = out_filename
        self.compressed = compressed
        self.use_separator = use_separator

    @classmethod
    def find_start(cls, str: str) -> str:
        while (str != "" and not str[0].isalpha()) and len(str) > 0:
            str = str[1:]
        return str

    @classmethod
    def pre_copy(cls, s: str) -> str:
        return s

    def download(self):
        logger.info(f"Downloading {self.catalogue_title} from {self.catalogue_url}")
        headers = {"User-Agent": "Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version"}

        response = requests.get(self.catalogue_url, stream=True, headers=headers, verify=False)
        with open(self.catalogue_local, "wb") as file:
            for data in tqdm(response.iter_content(chunk_size=1024), unit="kB", desc=f"Downloading {self.catalogue_label}"):
                file.write(data)

    def parse(self, n=0) -> list:
        if not Path(self.catalogue_local).is_file():
            self.download()
        self._validate_columns()
        total_lines = self.end_line - self.start_line + 1

        catalogue_stars = []
        with open(self.catalogue_local, "r", encoding="utf8") as f:
            for i in range(self.start_line - 1):
                next(f)

            count = 0
            line_idx = 0
            for line in tqdm(f, desc=f"Parsing {self.catalogue_label}", total=total_lines, colour="GREEN"):
                line_idx += 1
                if n > 0 and count == n or line_idx == total_lines:
                    break
                star = self.parse_line(line, line_idx)
                if not hasattr(star, "discard"):
                    catalogue_stars.append(star)
                    count += 1
                else:
                    tqdm.write(f"discarding {list(star.items())[0]}")
        return catalogue_stars

    def _validate_columns(self):
        for c in self.validators:
            assert c[1][1] >= c[1][0], "Invalid column interval: " + c[0]
            assert c[2] in ["left", "right"], "Invalid column alignment: " + c[0]

    def __parse_line_separator(self, line, line_idx):
        line = line.strip("\r\n\t").split(self.use_separator)
        catalogue_entry = {}
        for key, index, alignment, validator, preprocessor in self.validators:
            field = line[index].strip()
            if preprocessor:
                field = preprocessor(field)
            if not validator(field) and len(field) > 0:
                tqdm.write(f"Line {line_idx} > cannot parse {key}: {field}")
            catalogue_entry[key] = field
        return catalogue_entry

    def parse_line(self, line: str, line_idx: int):
        if self.use_separator:
            catalogue_entry = self.__parse_line_separator(line, line_idx)
        else:
            catalogue_entry = self.__parse_line_delimiters(line, line_idx)

        if self.star_f is not None:
            return self.star_f(catalogue_entry, from_string=True)
        else:
            return catalogue_entry

    def __parse_line_delimiters(self, line, line_idx):
        line = line.strip("\r\n\t")
        catalogue_entry = {}
        for key, interval, alignment, validator, preprocessor in self.validators:
            if self.__concise and key not in self.__concise_columns:
                continue
            field = line[interval[0] - 1 : interval[1]].strip()
            if preprocessor:
                field = preprocessor(field)

            if not validator(field) and len(field) > 0:
                tqdm.write(f"Line {line_idx} > cannot parse {key}: {field}")

            catalogue_entry[key] = field

        return catalogue_entry

    def convert(self):
        list = self.parse()
        io.write_list_json(list, f"{config.path_datadir}/{self.out_filename}", self.compressed)

    def known_keys(self) -> list[str]:
        return [v[0] for v in self.validators]
