import requests
import time
from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm, trange
from typing import Any
from astrolabium.parsers.data import WikidataStar
import logging

logger = logging.getLogger(__name__)

class Wikidata:
    prop_Parts = "P527"

    # props = [
    #     "itemLabel",
    #     "constellation",
    #     "sc",
    #     "luminosity",
    #     "mass",
    #     "temp",
    #     "metallicity",
    #     "radius",
    #     "gravity",
    #     "age",
    #     "distance",
    #     "parallax",
    #     "ra",
    #     "dec",
    #     "rvel",
    #     "magAp",
    #     "magAbs",
    #     "hip_id",
    #     "tyc_id",
    #     "gaia_id",
    # ]

    properties = {
        "P2561": "name",
        "P2060": "l",  # lum
        "P2067": "m",  # mass
        "P6879": "t",  # temp
        "P59": "const",  # constellation
        "P399": "co",  # companion
        "P215": "sc",  # spectral class
        "P2227": "met",  # metallicity
        "P2120": "r",  # radius
        "P7015": "g",  # gravity
        "P7584": "age",  # age
        "P2583": "d",  # distance
        "P2214": "plx",  # parallax
        "P6257": "ra",  # right ascension
        "P6258": "dec",  # declination
        "P10751": "pmra",  # proper motion ra
        "P10752": "pmde",  # proper motion de
        "P1096": "oe",  # orbital eccentricity
        "P2216": "rv",  # radial velocity
        "P1215": "map",  # apparent magnitude
        "P1457": "mab",  # absolute
        "P528": "cat",  # catalogue
        "P527": "pt",  # has parts
        "P6259": "epo",  # epoch
        # Add more as needed
    }

    units = {
        "Q28390": "deg",
        "Q3674704": "km/s",
        "Q180892": "MS",  # Solar Mass M☉
        "Q843877": "LS",  # Solar Lum L☉
        "Q48440": "RS",  # Solar Radius S☉
        "Q651336": "MJ",  # Jupiter Mass
        "Q3421309": "RJ",  # Jupiter Radius
        "Q681996": "ME",  # Earth Mass M🜨
        "Q524410": "Gyr",  # GigaYear (B)
        "Q20764": "Myr",  # MegaYear (M)
        "Q577": "yr",  # year
        "Q531": "Lyr",  # Light year
        "Q3773454": "Mpc",  # Megaparsec
        "Q11929860": "Kpc",  # Kiloparsec
        "Q12129": "pc",  # parsec
        "Q828224": "km",
        "Q21500224": "mas",  # milliarcsecond
        "Q22137107": "mas/y",  # milliarcsecond / y
        "Q11579": "K",  # Kelvin,
        "Q55662690": "m/s2",
        "Q39699418": "cm/s2",
        "1": "u",  # unitless
    }

    catalogs = {
        "Q111130": {"id": "HD", "label": "hd"},
        "Q1045111": {"id": "GJ", "label": "gj"},
        "Q537199": {"id": "HIP", "label": "hip"},  # Hipparcos
        "Q66061041": {"id": "Gaia DR3", "label": "gaia_dr3"},  # Gaia DR3
        "Q51905050": {"id": "Gaia DR2", "label": "gaia_dr2"},  # Gaia DR2
        "Q1563455": {"id": "TYC", "label": "tyc"},  # Tycho
        "Q105616": {"id": "", "label": "bayer"},  # Bayer designation
        "Q111116": {"id": "", "label": "fl"},  # Flamsteed
        "Q932275": {"id": "WDS", "label": "WDS"},  # Catalogue of Components of Double and Multiple Stars,
        "Q55712879": {"id": "SN", "label": "SN"},  # Supernova Catalogue
    }

    star_instances = {
        "Q523": "s",  # star
        "Q13890": "d",  # double
        "Q3037794": "opt",  # optical double
        "Q1993624": "spec",  # spectroscopic
        "Q6232": "tt",  # t-tauri
        "Q878367": "mul",  # multiple
        "Q2088753": "mul",  # triple star system
        "Q6243": "var",  # variable
        "Q50053": "b",  # binary
        "Q1457376": "ecb",  # eclipsing binary star
        "Q130019": "crb",  # carbon
        "Q6251": "wr",  # wolf-rayet
        "Q101600": "bd",  # brown dwarf
        "Q5871": "wd",  # white dwarf
        "Q1153392": "st",  # s-type
        "Q5898": "rsg",  # red sg
        "Q1048372": "bsg",  # blue sg
        "Q1142197": "ysg",  # yellow sg
        "Q4202": "ntr",  # neutron
        "Q4360": "pul",  # pulsar
        "Q3410780": "gpul",  # gamma pulsar
        "Q40392": "bh",  # black hole sm
        "Q71962386": "gam",  # gamma ray source
        "Q2154519": "xr",  # x-ray
        "Q190426": "mag",  # magnetar
        "Q2247863": "hpm",  # high proper-motion star
        "Q1140275": "mm",  # mercury-manganese star
        "Q353834": "pv",  # pulsating variable star
        "Q2168098": "rv",  # rotating variable star
    }

    star_exclude = {
        "Q318": "galaxy",
        "Q2488": "spiral galaxy",
        "Q195724": "grand design spiral galaxy",
        "Q217012": "radio galaxy",
        "Q644507": "interacting galaxy",
        "Q204107": "galaxy cluster",
        "Q192078": "lenticular galaxy",
        "Q854857": "diffuse nebula",
        "Q203958": "reflection nebula",
        "Q3937": "supernova",
    }

    star_epochs = {"Q1264450": "J2000"}

    constellation_map: dict[str, Any] = {
        "Q9256": {"short": "And"},
        "Q10481": {"short": "Ant"},
        "Q10506": {"short": "Aps"},
        "Q10576": {"short": "Aqr"},
        "Q10586": {"short": "Aql"},
        "Q9253": {"short": "Ara"},
        "Q10584": {"short": "Ari"},
        "Q10476": {"short": "Aur"},
        "Q8667": {"short": "Boo"},
        "Q10488": {"short": "Cae"},
        "Q8832": {"short": "Cam"},
        "Q8849": {"short": "Cnc"},
        "Q10452": {"short": "CVn"},
        "Q10538": {"short": "CMa"},
        "Q9305": {"short": "CMi"},
        "Q10535": {"short": "Cap"},
        "Q10470": {"short": "Car"},
        "Q10464": {"short": "Cas"},
        "Q8844": {"short": "Cen"},
        "Q10468": {"short": "Cep"},
        "Q8839": {"short": "Cet"},
        "Q10457": {"short": "Cha"},
        "Q10508": {"short": "Cir"},
        "Q10425": {"short": "Col"},
        "Q9285": {"short": "Com"},
        "Q10413": {"short": "CrA"},
        "Q10406": {"short": "CrB"},
        "Q10517": {"short": "Crv"},
        "Q9282": {"short": "Crt"},
        "Q10542": {"short": "Cru"},
        "Q8921": {"short": "Cyg"},
        "Q9302": {"short": "Del"},
        "Q8837": {"short": "Dor"},
        "Q8675": {"short": "Dra"},
        "Q10438": {"short": "Equ"},
        "Q10433": {"short": "Eri"},
        "Q8913": {"short": "For"},
        "Q8923": {"short": "Gem"},
        "Q10563": {"short": "Gru"},
        "Q10448": {"short": "Her"},
        "Q10574": {"short": "Hor"},
        "Q10578": {"short": "Hya"},
        "Q10416": {"short": "Hyi"},
        "Q10450": {"short": "Ind"},
        "Q10430": {"short": "Lac"},
        "Q8853": {"short": "Leo"},
        "Q10403": {"short": "LMi"},
        "Q10446": {"short": "Lep"},
        "Q10580": {"short": "Lib"},
        "Q10571": {"short": "Lup"},
        "Q10443": {"short": "Lyn"},
        "Q10484": {"short": "Lyr"},
        "Q9289": {"short": "Men"},
        "Q10492": {"short": "Mic"},
        "Q10428": {"short": "Mon"},
        "Q10435": {"short": "Mus"},
        "Q10582": {"short": "Nor"},
        "Q10503": {"short": "Oct"},
        "Q8906": {"short": "Oph"},
        "Q8860": {"short": "Ori"},
        "Q10515": {"short": "Pav"},
        "Q8864": {"short": "Peg"},
        "Q10511": {"short": "Per"},
        "Q10441": {"short": "Phe"},
        "Q10486": {"short": "Pic"},
        "Q8679": {"short": "Psc"},
        "Q10409": {"short": "PsA"},
        "Q9251": {"short": "Pup"},
        "Q10473": {"short": "Pyx"},
        "Q10498": {"short": "Ret"},
        "Q10513": {"short": "Sge"},
        "Q8866": {"short": "Sgr"},
        "Q8865": {"short": "Sco"},
        "Q9286": {"short": "Scl"},
        "Q10529": {"short": "Sct"},
        "Q8910": {"short": "Ser"},
        "Q10525": {"short": "Sex"},
        "Q10570": {"short": "Tau"},
        "Q10546": {"short": "Tel"},
        "Q10565": {"short": "Tri"},
        "Q10422": {"short": "TrA"},
        "Q10567": {"short": "Tuc"},
        "Q8918": {"short": "UMa"},
        "Q10478": {"short": "UMi"},
        "Q10521": {"short": "Vel"},
        "Q8842": {"short": "Vir"},
        "Q10437": {"short": "Vol"},
        "Q10519": {"short": "Vul"},
    }

    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql",
        agent="Mozilla/5.0 (platform; rv:gecko-version) Gecko/gecko-trail Firefox/firefox-version",
    )
    sparql.setReturnFormat(JSON)

    @staticmethod
    def get_entity(qid) -> dict:
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        r = requests.get(url)
        data = r.json()
        entity = data["entities"][qid]
        return entity

    @staticmethod
    def get_entities(qids):
        assert len(qids) <= 50, "size > 50"
        batch = "|".join(qids)
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={batch}&format=json"
        response = requests.get(url)
        data = response.json()
        return data["entities"]

    @staticmethod
    def get_entities_batch(qids: list, batch_size=50, parse_properties=True) -> dict[str, Any]:
        assert batch_size <= 50, "Batch size > 50"
        entries = {}
        n = len(qids)
        logger.info("\nRequesting qids from Wikidata\n...")
        try:
            for i in trange(0, n, batch_size, colour="GREEN", desc="Wikidata"):
                batch = qids[i : i + batch_size]
                tqdm.write(f"Requesting entities {i} to {min(i + batch_size, n)} from Wikidata")
                iau_entities = Wikidata.get_entities(batch)
                for qid, entity in iau_entities.items():
                    if parse_properties:
                        isStar, instances = Wikidata.get_instance_types(entity)
                        entry = Wikidata.parse_entity(entity, instances)
                        if entry is None:
                            raise ValueError("Returned empty entity")
                        entries[qid] = entry
                        label = entry["id"]
                    else:
                        label = entity.get("labels", {}).get("en", {}).get("value")
                        entries[qid] = label

                    tqdm.write(f"   > Parsing qid:{qid} [{label}]")
                time.sleep(0.250)
        except KeyboardInterrupt:
            pass
        return entries

    @staticmethod
    def get_entity_from_name(name):
        """
        :return: list of WikiData Entities
        """
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
        }
        r = requests.get(url, params=params)
        data = r.json()
        if data.get("search"):
            return data["search"]  # Return top result's Qid
        return None

    @staticmethod
    def get_qid_from_catalog(catalogId, prop_id="P528"):
        query = f"""
        SELECT ?item WHERE {{
        ?item wdt:{prop_id} "{catalogId}".
        }}
        LIMIT 1
        """
        return Wikidata.execute_query(query)

    @staticmethod
    def execute_query(query):
        Wikidata.sparql.setQuery(query)
        values = []
        propValue = None
        try:
            jsonData = Wikidata.sparql.query().convert()
            results = jsonData["results"]["bindings"]
            if not results:
                return None

            for result in results:
                entry = {}
                for prop in result:
                    propValue = result[prop]["value"]
                    if result[prop]["type"] == "uri":
                        propValue = propValue.split("/")[-1]
                    entry[prop] = propValue
                values.append(entry)
            return values

        except Exception as e:
            logger.error(query)
            logger.error(f"Error parsing results: {propValue}")
            raise e

    @staticmethod
    def get_qids_from_catalogue_entries(catalogue_qid: str, catalogue_label: str, catalogue_ids: list):
        """
        :param catalogue_id: the Qid of the catalogue type from wikidata. For example, "Q537199" for the Hipparcos catalogue
        :param catalogue_label: The prefix label for the catalogue, for example "HIP" for Hipparcos or "Gaia DR3"
        :catalogue_ids: a list of catalogue ids without the label
        """
        id_list = " ".join(f'"{catalogue_label} {id}"' for id in catalogue_ids)
        query = f"""
        SELECT ?qid ?qidLabel ?id WHERE {{
        ?qid p:P528 ?statement.
        ?statement ps:P528 ?id;
                    pq:P972 wd:{catalogue_qid}.
        VALUES ?id {{ {id_list} }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        results = Wikidata.execute_query(query)
        for result in results:
            if result["qidLabel"] == result["qid"]:
                del result["qidLabel"]
        return results

    @staticmethod
    def get_unit_symbol(qid, lang="en"):
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        try:
            r = requests.get(url)
            data = r.json()
            claims = data["entities"][qid]["claims"]
            symbols = claims.get("P5061", [])
            name = data["entities"][qid]["labels"].get(lang, {}).get("value", qid)
            for symbol_claim in symbols:
                snak = symbol_claim.get("mainsnak", {})
                if snak.get("snaktype") != "value":
                    continue
                return f"{snak['datavalue']['value']['text']} {name}"
        except Exception as e:
            logger.error(f"Error getting symbol for {qid}: {e}")
            raise e

    @staticmethod
    def get_property_value(entity_data, prop_id):
        claims = entity_data.get("claims", {})
        values = claims.get(prop_id, [])
        for claim in values:
            try:
                val = claim["mainsnak"]["datavalue"]["value"]
                amount = val["amount"]
                unit = val["unit"].split("/")[-1]  # QID of the unit
                return amount, unit
            except (KeyError, TypeError):
                continue
        return None, None

    @staticmethod
    def get_parts(entity_data, prop_id=prop_Parts):
        claims = entity_data.get("claims", {})
        values = claims.get(prop_id, [])
        components = []
        for claim in values:
            try:
                val = claim["mainsnak"]["datavalue"]["value"]
                components.append(val["id"])
            except (KeyError, TypeError):
                continue
        return len(components) > 0, components

    @staticmethod
    def get_instance_types(entity):
        """
        Given an entity and a dictionary of {QID: label}, returns a list of matching labels.
        """
        results = []
        claims = entity.get("claims", {})
        instances = claims.get("P31", [])

        for claim in instances:
            mainsnak = claim.get("mainsnak", {})
            datavalue = mainsnak.get("datavalue", {})
            if not datavalue or datavalue.get("type") != "wikibase-entityid":
                continue
            qid = datavalue["value"].get("id")
            if qid in Wikidata.star_exclude and claim["rank"] != "deprecated":
                return False, None
            if qid in Wikidata.star_instances:
                results.append(Wikidata.star_instances[qid])

        return len(results) > 0, results

    @staticmethod
    def parse_entity(entity, instanceMatches) -> dict | None:
        entry = {}
        entry["is"] = instanceMatches

        for pid, name in Wikidata.properties.items():
            propValue = Wikidata.parse_properties(pid, entity["claims"])
            if propValue:
                entry[name] = propValue

        if "cat" not in entry:
            return None

        label = entity.get("labels", {}).get("en", {}).get("value")
        if not label:
            label = WikidataStar.id_from_wikidata_catalog(entry["cat"])
        entry["id"] = label
        return entry

    @classmethod
    def parse_properties(cls, pid, entity):
        result = None
        if pid in entity:
            catalogue_ids = {}
            claims = entity[pid]
            match pid:
                case "P528":  # catalogue
                    for claim in claims:
                        catalogue_id = Wikidata.extract_value(claim)
                        qualifiers = claim.get("qualifiers", {})

                        if "P972" in qualifiers:
                            for q in qualifiers["P972"]:
                                cat_val = q.get("datavalue", {}).get("value", {}).get("id")
                                if cat_val in Wikidata.catalogs:
                                    catalogue_type = Wikidata.catalogs[cat_val]
                                    catalogue_ids[catalogue_type["label"]] = catalogue_id.replace(f"{catalogue_type['id']} ", "")
                        else:  # special case for PSR Pulsar Catalogue, which does not have a Q ref
                            if "PSR" in catalogue_id and "PSR" not in catalogue_ids:
                                catalogue_ids["PSR"] = catalogue_id.replace("PSR ", "")

                    result = catalogue_ids
                case "P59":  # constellations
                    propValue = Wikidata.get_best_value(claims)["id"]
                    result = Wikidata.constellation_map[propValue]["short"]
                case "P6259":  # epoch
                    propValue = Wikidata.get_best_value(claims)["id"]
                    result = Wikidata.star_epochs[propValue]
                case _:  # everything else
                    propValue = Wikidata.get_best_value(claims)
                    try:
                        if propValue is None:
                            return
                        if "amount" in propValue:
                            amount = propValue["amount"]
                            if amount.startswith("+"):
                                amount = amount.replace("+", "")
                            unitQ = propValue["unit"].split("/")[-1]
                            if unitQ not in Wikidata.units:
                                unit = unitQ
                                tqdm.write(f"Unit <{unitQ}> not available")
                            else:
                                unit = Wikidata.units[unitQ]
                            result = {"v": amount, "u": unit}
                        else:
                            if "id" in propValue:
                                result = propValue["id"]
                            else:
                                if "text" in propValue:
                                    result = propValue["text"]
                                else:
                                    result = propValue
                    except (KeyError, TypeError) as e:
                        logger.error(f"Error: {e}")
                        logger.error(f"{pid}: {propValue}")
                        raise e

        return result

    @staticmethod
    def extract_value(entry) -> dict[str, Any] | None:
        try:
            return entry["mainsnak"]["datavalue"]["value"]
        except (KeyError, TypeError):
            return None

    @staticmethod
    def get_best_value(claims) -> dict[str, Any] | None:
        if not isinstance(claims, list):
            return Wikidata.extract_value(claims)

        # Prefer 'preferred' ranked values
        preferred = [v for v in claims if isinstance(v, dict) and v.get("rank") == "preferred"]
        for v in preferred:
            val = Wikidata.extract_value(v)
            if val is not None:
                return val

        # Otherwise, take first 'normal' ranked value with a reference
        normal = [v for v in claims if isinstance(v, dict) and v.get("rank") == "normal"]
        referenced = [v for v in normal if v.get("references")]
        for v in referenced:
            val = Wikidata.extract_value(v)
            if val is not None:
                return val

        # Fallback: first normal value
        for v in normal:
            val = Wikidata.extract_value(v)
            if val is not None:
                return val

        return None
