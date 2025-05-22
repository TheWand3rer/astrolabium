import typing
import re
from astroquery.simbad import Simbad
from tqdm import tqdm, trange
from astrolabium.parsers.data import Text


def cross_check(
    catalogue_ids: list[str], catalogue_labels: list[str], main_label="HIP", batch_size=5000, exclude_label=False
) -> list[typing.Any]:
    # Simbad.add_votable_fields("ids")

    n = len(catalogue_ids)
    entries = []
    for i in trange(0, n, batch_size, desc="Simbad", colour="GREEN"):
        batch = catalogue_ids[i : i + batch_size]
        if exclude_label:
            filter_ids = f"('{"', '".join([id for id in batch])}')"
        else:
            filter_ids = f"({', '.join(f"'{main_label} {id}'" for id in batch)})"
        query = f"""SELECT TOP {batch_size} main_id, otype, id, ids, otypes, sp_type
        FROM basic as b
        JOIN ident as i on b.oid = i.oidref 
        JOIN ids AS ids ON b.oid = ids.oidref 
        JOIN alltypes AS a ON b.oid = a.oidref
        WHERE id IN {filter_ids}
        """
        results = Simbad.query_tap(query)

        # results = Simbad.query_objects(catalogue_ids)

        for row in results:
            try:
                row_labels = catalogue_labels.copy()
                id_list = [i.strip() for i in row["ids"].split("|")]
                id_list.sort()
                entry = {}

                name = next((id for id in id_list if id.startswith("NAME")), None)
                if name:
                    entry["Name"] = name.replace("NAME", "").strip()
                    row_labels.remove("NAME")

                entry["st"] = row["sp_type"]

                classic_ids = [id for id in id_list if id.startswith("*")]
                if len(classic_ids) > 0:
                    for classic_id in classic_ids:
                        result, n, const = Text.parse_flamsteed(classic_id)
                        if result and "fl" in row_labels:
                            entry["fl"] = f"{n} {const}"
                            row_labels.remove("fl")
                        elif "b" in row_labels:
                            match = re.compile(r"\*{0,1}\s*[a-z0-9]+\s*[A-Za-z]*").fullmatch(classic_id)
                            if match:
                                entry["b"] = classic_id[1:].strip()
                                row_labels.remove("b")

                if "b" in row_labels:
                    row_labels.remove("b")
                if "fl" in row_labels:
                    row_labels.remove("fl")

                if main_label != "":
                    entry[main_label] = row["id"].replace(main_label, "").lstrip()

                for id in id_list:
                    for catalogue_label in row_labels:
                        if id.startswith(catalogue_label):
                            value = id.replace(catalogue_label, "").strip()
                            entry[catalogue_label] = value
                            break
                entry["otypes"] = row["otypes"].split("|")
                entries.append(entry)
            except ValueError:
                tqdm.write(f"Error in ${row['id']}")
    return entries


def get_names(catalogue_ids: list):
    Simbad.add_votable_fields("ids")
    results = Simbad.query_objects(catalogue_ids)
    dict = {}
    assert len(catalogue_ids) == len(results)
    for i, row in enumerate(results):
        assert __check_catalogue_id(catalogue_ids[i], row)
        match = re.compile(r".*NAME\s([A-Za-z0-9]+)?").fullmatch(row["ids"])
        if match:
            name = match.groups()[0]
            dict[id] = name

    return dict


def get_object_ids(catalogue_ids: list, only_first=True, batch_size=100):
    Simbad.add_votable_fields("otypes")

    obj_ids = []
    otype_array: list[str] = []
    for i in trange(0, len(catalogue_ids), batch_size, colour="GREEN",desc="Simbad"):
        batch = catalogue_ids[i : i + batch_size]
        try:
            results = Simbad.query_objects(batch)
            if len(results) == 0:
                return None

            previous_id = results[0]["user_specified_id"].rstrip()

            for i, row in enumerate(results):
                obj_type = row["otypes.otype"]
                if obj_type == "":
                    obj_type = None
                id = row["user_specified_id"].rstrip()
                if only_first and len(otype_array) > 0 and id == previous_id:
                    continue
                if (id != previous_id or i == len(results) - 1) and len(otype_array) > 0:
                    obj_ids.append({"id": previous_id, "otypes": otype_array})
                    otype_array = []
                otype_array.append(obj_type)
                previous_id = id
        except UnicodeDecodeError:
            print(batch)
            raise

    return obj_ids


def __check_catalogue_id(id, entry) -> bool:
    if id not in entry["ids"]:
        raise ValueError(f"{id} catalogue id does not match <{entry['ids']}>")
    else:
        return True
