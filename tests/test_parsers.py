import unittest
from astrolabium.catalogues import Hipparcos
from astrolabium.parsers import WDSParser, Orb6Parser, HipparcosParser
from astrolabium.parsers.data import WDSEntry, Orb6Entry, HipparcosEntry
import astropy.units as u
import typing
import json
import logging

from astrolabium.parsers.data import EntryBase

logger = logging.getLogger(__name__)


class TestParsers(unittest.TestCase):
    def common_test(
        self,
        entry_type: typing.Type,
        parsed_entry: EntryBase,
        keys: list[str],
        expected_values: dict[str, typing.Any],
        json_data: str,
    ):
        self.assertTrue(isinstance(parsed_entry, entry_type), f"{type(parsed_entry)} expected {entry_type}")
        for key in keys:
            if not hasattr(parsed_entry, key):
                logger.warning(f"Warning: <{key}> not present in entry")
                continue

            value = getattr(parsed_entry, key, None)
            self.assertEqual(value, expected_values[key], f"{key}: {value} expected: {expected_values[key]}")

        result_todict = parsed_entry.to_dict()
        for key in keys:
            if key not in result_todict:
                logger.warning(f"Warning: <{key}> not present in entry")
                continue

            value = result_todict[key]
            expected_value = expected_values[key].value if hasattr(expected_values[key], "value") else expected_values[key]

            self.assertEqual(value, expected_value, f"{key}: {value} expected: {expected_value}")
        deserialized = entry_type(json.loads(json_data))

        for key in keys:
            self.assertEqual(getattr(parsed_entry, key, None), getattr(deserialized, key, None), key)

    def test_Hipparcos(self):
        line = " 12345| 95|3|1| 0.6935325342 -0.9570897690|   7.76|   18.06|  -16.03|  1.67|  1.75|  2.01|  2.37|  2.40|108|28.38| 3|   0.0|   0| 7.7290|0.0295|0.097|0| 0.380|0.010| 0.440|   1.03   0.36   1.06   0.18   0.34   1.04   0.11  -0.16   0.41   1.00  -0.13   0.41   0.11   0.00   1.00"

        hip = HipparcosParser()
        hip._validate_columns()
        result = hip.parse_line(line, 1)

        expected_values = {
            "HIP": "12345",
            "nc": 1,
            "ra": 0.6935325342 * u.rad,
            "de": -0.9570897690 * u.rad,
            "plx": 7.76 * u.mas,
            "pmRa": 18.0 * u.mas / u.yr,
            "pmDE": -16.03 * u.mas / u.yr,
            "e_ra": 1.67 * u.rad,
            "e_de": 1.75 * u.rad,
            "e_plx": 2.01 * u.mas,
            "e_pmRA": 2.37 * u.mas / u.yr,
            "e_pmDE": 2.40 * u.mas / u.yr,
        }
        json_deserialized = (
            '{"HIP":"12345","nc":1,"ra":0.6935325342,"de":-0.957089769,"plx":7.76,"pmDE":-16.03,"e_ra":1.67,"e_de":1.75,"e_plx":2.01,"e_pmDE":2.4}'
        )
        self.common_test(HipparcosEntry, result, hip.known_keys(), expected_values, json_deserialized)

    def test_WDS(self):
        line = "00002+4119TDS1235AB    1991 2016    3 105  68   0.5   1.7 10.27 10.67 K2        -001-008 -001-008 +40 5210  Y   000010.69+411928.9"

        wds = WDSParser()
        wds._validate_columns()
        result = wds.parse_line(line, 1)

        expected_values = {
            "WDS": "00002+4119",
            "disc": "TDS1235",
            "comp": "AB",
            "obs_f": 1991,
            "obs_l": 2016,
            "n_obs": 3,
            "pa1": 105 * u.deg,
            "pa2": 68 * u.deg,
            "sep1": 0.5 * u.arcsec,
            "sep2": 1.7 * u.arcsec,
            "mag1": 10.27,
            "mag2": 10.67,
            "st": "K2",
            "pm1_ra": -1 * u.arcsec / u.kyr,
            "pm1_dec": -8 * u.arcsec / u.kyr,
            "pm2_ra": -1 * u.arcsec / u.kyr,
            "pm2_dec": -8 * u.arcsec / u.kyr,
            "DM": "+40 5210",
            "notes": "Y",
            "coord": "000010.69+411928.9",
        }

        json_deserialized = '{"WDS":"00002+4119","disc":"TDS1235","comp":"AB","obs_f":1991,"obs_l":2016,"n_obs":3,"pa1":105.0,"pa2":68.0,"sep1":0.5,"sep2":1.7,"mag1":10.27,"mag2":10.67,"st":"K2","pm1_ra":-1.0,"pm1_dec":-8.0,"pm2_ra":-1.0,"pm2_dec":-8.0,"DM":"+40 5210","notes":"Y","coord":"000010.69+411928.9"}'
        self.common_test(WDSEntry, result, wds.known_keys(), expected_values, json_deserialized)

    def test_Orb6(self):
        line = "000123.67+393638.2 00014+3937 HLD  60        17178 224873    110   9.09   9.77    217.2694  y  16.5701     0.87865a  0.01750 128.050    4.231  147.353     2.957   1903.2511  y   1.6226   0.63041  0.01456  148.186    5.431       2015 3 n Izm2019  wds00014+3937e.png"

        orb6 = Orb6Parser()
        orb6._validate_columns()
        result = orb6.parse_line(line, 1)

        expected_values = {
            "WDS": "00014+3937",
            "HD": "224873",
            "HIP": "110",
            "P": 217.2694 * u.yr,
            "P_e": 16.5701 * u.yr,
            "a": 878.65 * u.mas,
            "a_e": 17.5 * u.mas,
            "i": 128.05 * u.deg,
            "i_e": 4.231 * u.deg,
            "lan": 147.353 * u.deg,
            "lan_e": 2.957 * u.deg,
            "lpa": 148.186 * u.deg,
            "lpa_e": 5.431 * u.deg,
            "e": 0.63041,
            "e_e": 0.01456,
            "orb_g": 3,
            "last": 2015,
            "notes": "n",
        }

        json_deserialized = '{"WDS":"00014+3937","HD":"224873","HIP":"110","P":217.2694,"P_e":16.5701,"a":878.65,"a_e":17.5,"i":128.05,"i_e":4.231,"lan":147.353,"lan_e":2.957,"e":0.63041,"e_e":0.01456,"lpa":148.186,"lpa_e":5.431,"orb_g":3,"last":2015,"notes":"n"}'
        self.common_test(Orb6Entry, result, orb6.known_keys(), expected_values, json_deserialized)
