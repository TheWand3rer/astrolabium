from astropy.units import Quantity, UnitConversionError
from typing import Any
import logging

logger = logging.getLogger(__name__)

class EntryBase:
    key_settings: list[Any]

    def __init__(self, catalogue_data):
        assert catalogue_data is not None, "catalogue_data"
        pass

    @classmethod
    def _get_value(data, key):
        return data[key]

    @property
    def id(self) -> str | None:
        return self._id

    @id.setter
    def id(self, value: str):
        self._id = value

    def _parse_keys(self, key_settings, data):
        for key, null_values, preprocessor, unit, round_d in key_settings:
            try:
                if EntryBase.is_string(key, data, null_values):
                    value = data[key]
                    if preprocessor:
                        value = preprocessor(value)
                    if value is not None:
                        if type(value) is not Quantity and unit is not None:
                            value *= unit
                        setattr(self, key, value)
            except UnitConversionError as e:
                raise UnitConversionError(f"Error in {key}: {value.unit} to {unit} <{data[key]}>\n{e}")
            except (TypeError, ValueError) as e:
                raise TypeError(f"Error in [{key}]: {value} [{unit}] <{data[key]}>\n{e}")

    def _parse_values(self, key_settings, data):
        for key, null_values, preprocessor, unit, round_d in key_settings:
            value = EntryBase.try_parse_value(key, data, float, unit)
            if value is not None:
                setattr(self, key, value)

    @classmethod
    def is_string(cls, key: str, data: dict[str, str], null_values: list[str] | str):
        if key in data:
            value = data[key]
            if value == "":
                return False

            if null_values is None or len(null_values) == 0:
                null_values = []
            elif type(null_values) is str:
                null_values = [null_values]

            if all(type(value) and value != nv for nv in null_values):
                return True
        return False

    @classmethod
    def try_parse(cls, key, data, cast_type, unit=None):
        if "key" in data:
            value = data[key]
            if type(value) is str:
                value = cast_type(value)
                if unit:
                    return value * unit
                else:
                    return value
        return None

    @classmethod
    def try_parse_string(cls, key, data, null_value):
        if EntryBase.is_string(key, data, null_value):
            return data[key]
        else:
            return None

    @classmethod
    def try_parse_value(cls, key, data, check_type, unit=None):
        if isinstance(data, dict) and key in data:
            value = data[key]
        elif isinstance(data, object):
            value = getattr(data, key, None)

        if isinstance(value, check_type):
            if unit:
                return value * unit

        return value

    def extract_value(self, key, round_d, unit=None):
        value = getattr(self, key, None)
        if value is not None:
            if unit:
                value = value.to(unit)
            if isinstance(value, Quantity):
                value = value.value
            if round_d and round_d > 0:
                return round(value, round_d)
            else:
                return value
        else:
            return None

    def to_dict(self):
        json = {}
        try:
            for key, null_values, postprocessor, unit, round_d in self.key_settings:
                json[key] = self.extract_value(key, round_d, unit)
        except UnitConversionError as e:
            logger.info(f"{key}: {getattr(self, key)} to {unit}")
            raise e

        try:
            return {k: v for k, v in json.items() if v is not None}
        except ValueError as e:
            logger.info(f"Error in {json} ")
            raise e

    def _get_indent(self, indent_spaces) -> str:
        indent = ""
        for i in range(0, indent_spaces):
            indent += " "
        return indent

    def to_string(self, indent_spaces=3) -> str:
        string = self.id

        for key, null_values, postprocessor, unit, round_d in self.key_settings:
            value = getattr(self, key, None)
            if value is not None:
                string += f"{self._get_indent(indent_spaces)}{key}: {value}"
        return string
