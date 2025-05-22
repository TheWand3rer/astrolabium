from tqdm import tqdm
from astropy import units as u
import json
from astrolabium.parsers.data import Text, EntryBase
from typing import Any


class WikidataStar(EntryBase):
    key_settings = [
        # mypy: disable-error-code="has-type"
        # key, nullvalues, preproc, unit, digits]
        ["id", None, None, None, None],
        ["qid", None, None, None, None],
        ["name", [], None, None, None],
        ["const", [], None, None, None],
        ["l", [], lambda v: WikidataStar.__convert_luminosity(v, "LS"), u.L_sun, 6],
        ["m", [], lambda v: WikidataStar.__convert_mass(v, "MS"), u.M_sun, 6],
        ["t", [], lambda v: WikidataStar.__convert_temp(v, "K"), u.K, 3],
        ["ra", [], lambda v: WikidataStar.__convert_angle(v, "rad"), u.rad, 6],
        ["dec", [], lambda v: WikidataStar.__convert_angle(v, "rad"), u.rad, 6],
        ["plx", [], lambda v: WikidataStar.__convert_angle(v, "mas"), u.mas, 6],
        ["g", [], lambda v: WikidataStar.__convert_acceleration(v, "cm/s2"), u.Unit("cm/s**2"), 3],
        ["d", [], lambda v: WikidataStar.__convert_distance(v, "Lyr"), u.lyr, 6],
        ["rv", [], lambda v: WikidataStar.__convert_rv(v, "km/s"), u.km / u.s, 6],
        ["pmra", [], lambda v: WikidataStar.__convert_angular_v(v, "mas/y"), u.mas / u.yr, 6],
        ["pmdec", [], lambda v: WikidataStar.__convert_angular_v(v, "mas/y"), u.mas / u.yr, 6],
        ["age", [], lambda v: WikidataStar.__convert_age(v, "Gyr"), u.Gyr, 9],
        ["epo", [], None, None, None],
        ["cat", [], None, None, None],
    ]

    def __init__(self, qid: str, data: dict[str, Any]):
        try:
            data["qid"] = qid
            self.qid = qid
            self.d: u.Quantity | None = None
            self._parse_keys(self.key_settings, data)
            self.cat = data["cat"]

            if hasattr(self, "epo") and self.epo == "J2000":
                self.epo = None

        except (AttributeError, TypeError) as e:
            tqdm.write(f"in {qid}: <{data['name'] if 'name' in data else None}>\n{e}")
            raise

    def __find_name(self, data):
        self.name = data["name"]
        if self.id == self.name:
            if "bayer" in data["cat"]:
                bayer = data["cat"]["bayer"]
                letter_full = Text.greek_to_bayer(bayer[0])
                const = Text.short_constellation_to_genitive(bayer[1:])
                self.id = f"{letter_full} {const}"
            else:
                self.id = WikidataStar.id_from_wikidata_catalog(data["cat"])

    @classmethod
    def id_from_wikidata_catalog(cls, cat):
        cat_label = None
        if "bayer" in cat:
            return cat["bayer"]
        elif "fl" in cat:
            result, n, cst = Text.parse_flamsteed(cat["fl"])
            return f"{n} {Text.short_constellation_to_genitive(cst)}"
        elif "hd" in cat:
            cat_id = "hd"
        elif "hip" in cat:
            cat_id = "hip"
        elif "gj" in cat:
            cat_id = "gj"
            cat_label = "Gliese"
        elif "hr" in cat:
            cat_id = "hr"
        elif "tyc" in cat:
            cat_id = "tyc"
        elif "wds" in cat:
            cat_id = "wds"
        elif "gaia_dr3" in cat:
            cat_id = "gaia_dr3"
            cat_label = "Gaia DR3"
        elif "gaia_dr2" in cat:
            cat_id = "gaia_dr2"
            cat_label = "Gaia DR2"
        elif "PSR" in cat:
            cat_id = "PSR"
        else:
            raise ValueError("No catalogue data: " + json.dumps(cat))
        return f"{cat_label if cat_label else cat_id.upper()} {cat[cat_id]}"

    @staticmethod
    def __convert_age(age, unit) -> u.Quantity:
        if type(age) is float:
            value = age
        else:
            value, unit = WikidataStar.__expand(age)

        match unit:
            case "Gyr":
                return value * u.Gyr
            case "Myr":
                return (value * u.Myr).to(u.Gyr)
            case "yr":
                return (value * u.yr).to(u.Gyr)
            case _:
                raise TypeError(f"Age: {unit}")

    @staticmethod
    def __convert_angular_v(angv, unit) -> u.Quantity:
        if type(angv) is float:
            value = angv
        else:
            value, unit = WikidataStar.__expand(angv)

        match unit:
            case "mas/y":
                return value * u.mas / u.yr
            case _:
                raise TypeError(f"Angle: {unit}")

    @staticmethod
    def __convert_rv(rv, unit) -> u.Quantity:
        if type(rv) is float:
            value = rv
        else:
            value, unit = WikidataStar.__expand(rv)

        match unit:
            case "km/s":
                return value * u.km / u.s
            case _:
                raise TypeError(f"Angle: {unit}")

    @staticmethod
    def __convert_angle(angle, unit) -> u.Quantity:
        if type(angle) is float:
            value = angle
        else:
            value, unit = WikidataStar.__expand(angle)

        match unit:
            case "rad":
                return value * u.rad
            case "deg":
                return value * u.deg
            case "mas":
                return value * u.mas
            case _:
                raise TypeError(f"Angle: {unit}")

    @staticmethod
    def __convert_distance(d, unit) -> u.Quantity:
        if type(d) is float:
            value = d
        else:
            value, unit = WikidataStar.__expand(d)

        match unit:
            case "Kpc":
                return (value * u.kpc).to(u.pc)
            case "Mpc":
                return (value * u.mpc).to(u.pc)
            case "pc":
                return value * u.pc
            case "Lyr":
                return (value * u.lyr).to(u.pc)
            case _:
                raise TypeError(f"WikidataStarFactory distance : {unit}")

    @staticmethod
    def __convert_acceleration(acc, unit) -> u.Quantity:
        if type(acc) is float:
            value = acc
        else:
            value, unit = WikidataStar.__expand(acc)

        match unit:
            case "cm/s2":
                return value * u.Unit("cm/s**2")
            case "m/s2":
                return value * u.Unit("m/s**2")
            case _:
                raise TypeError(f"Acceleration: {unit}")

    @staticmethod
    def __convert_luminosity(sl, unit) -> u.Quantity:
        if type(sl) is float:
            value = sl
        else:
            value, unit = WikidataStar.__expand(sl)

        match unit:
            case "LS":
                return value * u.L_sun
            case _:
                raise TypeError(f"Luminosity: {unit}")

    @staticmethod
    def __convert_mass(mass, unit) -> u.Quantity:
        if type(mass) is float:
            value = mass
        else:
            value, unit = WikidataStar.__expand(mass)

        match unit:
            case "MS":
                return value * u.M_sun
            case "ME":
                em = value * u.M_earth
                sm = em.to(u.M_sun)
                if sm.value < 0.005:
                    tqdm.write(f">>> Mass too small {sm:.6f} original: {em:.3f}")
                    return None
                else:
                    return sm
            case "MJ":
                jm = value * u.M_jupiter
                sm = jm.to(u.M_sun)
                return sm
            case _:
                raise TypeError(f"In Mass: {unit}")

    @staticmethod
    def __convert_temp(temp, unit) -> u.Quantity:
        if type(temp) is float:
            value = temp
        else:
            value, unit = WikidataStar.__expand(temp)

        match unit:
            case "K":
                return value * u.K
            case _:
                raise TypeError(f"Temp: {unit}")

    @staticmethod
    def __expand(item):
        value = float(item["v"])
        unit = item["u"]
        return value, unit
