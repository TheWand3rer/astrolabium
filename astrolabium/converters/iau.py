import astrolabium.config as config
import astrolabium.queries.wikidata as wiki
import astrolabium.queries.simbad as simbad
import astrolabium.fileIO as io
import time
import json
import unicodedata
from tqdm import tqdm

__missing_ids = {"TrES-3": "Q1107722"}
__missing_names = {""}
# __iau_data = io.read_dict_json(f"{config.path_cataloguedir}/IAU-CSN")


def find_catalogue_ids(n=0):
    starDict = dict()
    jsonData = io.read_dict_json(f"{config.path_cataloguedir}/IAU-CSN")
    if n == 0:
        n = len(jsonData)
    for i, entry in enumerate(jsonData[:n]):
        name = entry["Name"]
        hip = entry["HIP"]
        if hip != "_":
            print(f"[{i + 1}/{n}] Parsing {name}")
            starDict[name] = hip
        else:
            print(f"[{i + 1}/{n}] No HIP for {name}")

    return starDict


def find_entries_without_catalogue_ids(catalog="HIP"):
    starDict = dict()
    n = len(__iau_data)
    counter = 1
    for i, entry in enumerate(__iau_data[:n]):
        hip = entry[catalog]
        if hip != "_":
            continue
        label = entry["Designation"]
        print(f"[{counter}/{i + 1}]: {label}")
        counter += 1
        starDict[label] = entry
    qid_list = []

    for key, value in tqdm(starDict.items(), colour="GREEN"):
        name = value["Name"]
        qid = __parse_entities(key, name)
        if qid is not None:
            qid_list.append(qid)
        else:
            if key in __missing_ids:
                qid = __missing_ids[key]
            else:
                qid = __parse_entities(key, name, False)

            if qid is not None:
                qid_list.append(qid)
            else:
                tqdm.write(f">>> Cannot find {key}: {name}")
        time.sleep(0.250)
    return qid_list


def __parse_entities(key: str, name: str, use_key=True):
    starFound = False
    try:
        for entity in wiki.get_entity_from_name(key if use_key else name):
            qid = entity["id"]
            starFound = __is_entity_star(entity, key, name, qid)
            if starFound:
                return qid
        if not starFound:
            return None
    except TypeError as e:
        return None


def __is_entity_star(entity, key, name, qid):
    if "description" not in entity:
        tqdm.write(f"Looking for <{key}/{name}> cannot parse qid:{qid}")
        return False
    desc = entity["description"].lower()
    tokens = ["star", "gamma ray", "pulsar"]
    if any(x in desc for x in tokens):
        tqdm.write(f"Looking for <{key}/{name}>, found qid: {qid} is a star")
        return True
    else:
        return False


def iau_to_wiki(out_filename=f"{config.path_outdir}/IAU-CSN"):
    iau_ids = find_catalogue_ids()
    print("\nRequesting qids from Wikidata\n...")
    iau_in_cat = wiki.get_qids_from_catalogue_entries("Q537199", "HIP", iau_ids.values())
    iau_not_cat = find_entries_without_catalogue_ids()
    iau_qids = [item["qid"] for item in iau_in_cat] + iau_not_cat
    n = len(iau_qids)
    print(f"   > Found {len(iau_in_cat) + len(iau_not_cat)} / {n} matching entities")

    iau_entries = wiki.get_entities_batch(iau_qids, batch_size=50)

    io.write_dict_json(iau_entries, out_filename)
    print(f"\n{n} Wikidata entities written to {config.path_outdir}/{out_filename}.json")


def normalise_names(filename=f"{config.path_outdir}/IAU-CSN"):
    print("Normalising names in IAU entities")
    name_key = "Name/Diacritics"
    iau_entities = io.read_dict_json(filename)
    for i, (key, value) in tqdm(enumerate(iau_entities.items())):
        if "name" in value:
            name = value["name"]
            using_name = True
        else:
            name = value["id"]
            using_name = False

        catalogue_id = value["cat"]["hip"] if "hip" in value["cat"] else list(value["cat"])[0]
        catalogue_id = (
            catalogue_id.split(" ")[1] if catalogue_id.startswith("HIP") or catalogue_id.startswith("HD") else None
        )

        iau_match = [star for star in __iau_data if star[name_key] == name]
        if len(iau_match) > 0:
            value["name"] = name
            tqdm.write(f"{key}: {name} matches")
            continue
        else:
            if using_name:
                iau_match = [star for star in __iau_data if star[name_key] == value["id"]]
                if len(iau_match) > 0:
                    value["name"] = value["id"]
                    tqdm.write(f"{key}: {value['id']} matches")
                    continue

        if catalogue_id is not None:
            iau_match = [star for star in __iau_data if star["HIP"] == catalogue_id or star["HD"] == catalogue_id]
            if len(iau_match) > 0:
                iau_name = iau_match[0][name_key]
                tqdm.write(f">>> {key}: {name} does not match with {iau_name}, using IAU name")
                value["name"] = iau_name
                continue

        iau_match = [star for star in __iau_data if star["Designation"] == name]
        if len(iau_match) > 0:
            iau_name = iau_match[0][name_key]
            tqdm.write(f">>> {key}: {name} does not match with {iau_name}, using IAU name")
            value["name"] = iau_name
            continue

        tqdm.write(f">>> {key}: {name} no name found")
        raise
    io.write_dict_json(iau_entities, filename)
    print("All stars matched!")


def add_simbad_otypes(filename=f"{config.path_outdir}/IAU-CSN"):
    print("Adding otypes from Simbad")
    iau_entities = io.read_dict_json(filename)

    iau_ids = []
    iau_map = {}
    valid_cat = ["hip", "tyc", "gaia_dr3", "PSR"]
    for i, (key, entity) in enumerate(iau_entities.items()):
        catalog = entity["cat"]
        iau_id = None
        for cat_type in list(catalog.items()):
            if cat_type[0] in valid_cat:
                iau_id = f"{cat_type[0].upper().replace('_', ' ')} {cat_type[1]}"
                iau_map[key] = iau_id
                iau_ids.append(iau_id)
                break

        if iau_id is None:
            raise ValueError(f"Catalog ids for {key}: {catalog}")

    results = simbad.get_object_ids(iau_ids)
    for result in tqdm(results):
        iau_map[result["id"]] = result["otypes"]
        tqdm.write(json.dumps(result))

    res_ids = [x["id"] for x in results]
    diff = set(iau_ids) - set(res_ids)
    print(diff)
    io.write_list_json(diff, filename + "_missing_simbad_otype")
