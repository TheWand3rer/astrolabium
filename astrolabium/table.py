from typing import Any
from tqdm import tqdm
from astrolabium.parsers.data import EntryBase


def join(table1: list, table2: list, key1: str, key2: str | None = None) -> list[Any]:
    if not key2:
        key2 = key1

    table_lookup = {str(entry[key2]): entry for entry in table2 if key2 in entry}
    result = []
    for entry in tqdm(table1, colour="GREEN", desc="Joining tables"):
        if isinstance(entry, EntryBase):
            entry = entry.to_dict()
        value = str(entry[key1])
        if value in table_lookup:
            joined = {**entry, **table_lookup[value]}
            result.append(joined)
    return result
