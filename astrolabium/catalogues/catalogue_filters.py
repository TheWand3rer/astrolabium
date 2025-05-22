from astropy import units as u
from astrolabium.catalogues import WDS
from astrolabium.parsers.data import WDSEntry


def distance(star: dict, distance_lyr: float = 100.0, distance_key="d"):
    if distance_key in star:
        distance = star[distance_key] * u.pc
        if distance < 0:
            return False
        else:
            return distance.to(u.lyr).value <= distance_lyr
    else:
        return False


def name(star: dict, name_key="Name"):
    return name_key in star


def any_catalogues(star: dict, catalogue_labels=["b", "fl", "Name"]):
    return any(cat in catalogue_labels for cat in star)


def all_catalogues(star: dict, catalogue_labels=["b", "fl"]):
    return all(cat in star for cat in catalogue_labels)


def wds_is_physical(star: dict, wds: WDS):
    entry = wds.select(star["WDS"][1:11])
    if entry is not None:
        return WDSEntry(entry).is_physical
    else:
        return False


crossref_filters = [lambda star: distance(star), lambda star: any_catalogues(star)]
