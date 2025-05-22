import json
import lzma
import os.path
import typing
import logging

logger = logging.getLogger(__name__)

def create_directory(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def file_exists(path: str) -> bool:
    return os.path.exists(path)


def write_text_json(jsonString: str, filename: str):
    with open(f"{filename}.json", "w") as f:
        f.write(jsonString)


def write_dict_json(jsonDict: dict, filename: str, remove_id=False):
    with open(f"{filename}.json", "w") as f:
        f.write("{\n")
        items = list(jsonDict.items())
        n = len(items)
        for i, (key, value) in enumerate(items):
            to_dict = getattr(value, "to_dict", None)
            if callable(to_dict):
                value = to_dict()

            if remove_id:
                del value["id"]
            try:
                line = json.dumps(key) + ": " + json.dumps(value, separators=(",", ":"))
            except TypeError:
                raise TypeError("Item must implement <to_dict> method")
            if i < n - 1:
                line += ","
            f.write("  " + line + "\n")
        f.write("}\n")


def write_list_json(jsonList, filename, compressed=False):
    if compressed:
        logger.info("Compressing file...")
        with lzma.open(f"{filename}.json.xz", "wt", format=lzma.FORMAT_XZ) as f:
            json.dump(jsonList, f, default=lambda item: item.to_dict())
    else:
        with open(f"{filename}.json", "w") as f:
            f.write("[\n")
            n = len(jsonList)
            i = 0
            for i, item in enumerate(jsonList):
                to_dict = getattr(item, "to_dict", None)
                if callable(to_dict):
                    item = to_dict()

                line = json.dumps(item, separators=(",", ":"))
                if i < n - 1:
                    line += ","
                f.write("  " + line + "\n")
            f.write("]\n")


def read_dict_json(filename: str):
    path = f"{filename}.json"
    if not os.path.isfile(path):
        logger.error(f"Error: file {path} not found")
        return {}
    with open(path, "r", encoding="utf8") as f:
        data = json.load(f)
        return data


def read_list_json(filename: str, compressed=False) -> list[typing.Any]:
    logger.info(f"Loading: {filename}")
    if compressed:
        with lzma.open(f"{filename}.json.xz", "rt", format=lzma.FORMAT_XZ) as f:
            return json.load(f)
    else:
        path = f"{filename}.json"
        if not os.path.isfile(path):
            logger.error(f"Error: file {path} not found")
            return []
        with open(path, "r", encoding="utf8") as f:
            data = json.load(f)
            return data
