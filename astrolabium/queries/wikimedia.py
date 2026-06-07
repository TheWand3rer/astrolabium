import json
import os
import logging
from typing import Any

import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from astrolabium import config
from astrolabium import fileIO as io
from astrolabium.parsers.data import WikimediaStar

logger = logging.getLogger(__name__)

# Mapping: Wikipedia infobox key -> internal field name
__field_map: dict[str, str] = {
    "Mass": "m",
    "Luminosity": "l",
    "Temperature": "t",
    "Radius": "r",
    "Age": "age",
    "Surface gravity": "g",
    "Rotational velocity": None,  # Not stored in PhysicalData yet
    "Parallax": "plx",
}


def normalize_field(key: str) -> str | None:
    """Map a Wikipedia infobox key to our internal field name.

    :param key: Raw key from the EnterpriseWikMedia infobox (e.g. "Mass").
    :return: Internal field name (e.g. "m"), or None if not a PhysicalData field.
    """
    return __field_map.get(key)


class WikimediaClient:
    """Client for the EnterpriseWikMedia structured content API.

    Provides programmatic access to Wikipedia infobox data as structured JSON.
    Used as a fallback to fill missing stellar physical properties not available
    via Wikidata SPARQL.

    Authentication is explicit: call :meth:`authenticate` before using fetch methods.
    Fetch methods check the auth flag and return early if not authenticated.
    """

    AUTH_URL = "https://auth.enterprise.wikimedia.com/v1/login"
    DATA_URL_TEMPLATE = "https://api.enterprise.wikimedia.com/v2/structured-contents/{pageName}"

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        cache_dir: str | None = None,
    ) -> None:
        """Initialize the client.

        Credentials are read from environment variables if not provided explicitly.
        Cached infobox data is stored in ``cache_dir`` (defaults to ``temp/``).

        :param username: Wikimedia username. Falls back to ``WIKIMEDIA_USERNAME`` env var.
        :param password: Wikimedia password. Falls back to ``WIKIMEDIA_PASSWORD`` env var.
        :param cache_dir: Directory for caching parsed infobox data.
        :raises ValueError: If credentials are not provided or found in environment.
        """
        self._username = username or os.getenv("WIKIMEDIA_USERNAME")
        self._password = password or os.getenv("WIKIMEDIA_PASSWORD")
        self._access_token: str | None = None
        self._authenticated: bool = False
        self._session: requests.Session = requests.Session()
        self._cache_dir: str = cache_dir or config.path_temp

        if not self._username or not self._password:
            raise ValueError(
                "Wikimedia credentials not found. "
                "Provide username/password or set WIKIMEDIA_USERNAME and WIKIMEDIA_PASSWORD "
                "environment variables (or a .env file)."
            )

        io.create_directory(self._cache_dir)

    def authenticate(self) -> bool:
        """Authenticate with the EnterpriseWikMedia API.

        POSTs credentials to the auth endpoint and stores the access token.
        Sets ``_authenticated`` flag on success.

        :return: True if authentication succeeded, False otherwise.
        :raises requests.HTTPError: If the API returns an error (401/403/5xx).
        """
        logger.info("Authenticating with EnterpriseWikMedia API...")
        payload = {"username": self._username, "password": self._password, "format": "json", "Content-Type": "application/json"}
        response = self._session.post(self.AUTH_URL, params=payload)
        response.raise_for_status()

        data = response.json()
        token = data.get("access_token")
        if token is None:
            raise RuntimeError(f"Authentication succeeded but no access_token in response. Response: {data}")

        self._access_token = token
        self._authenticated = True
        logger.info("Authentication successful.")
        return True

    def is_authenticated(self) -> bool:
        """Check whether authentication has been performed successfully.

        :return: True if authenticated, False otherwise.
        """
        return self._authenticated

    def fetch_by_page_name(self, page_name: str) -> dict[str, Any] | None:
        """Fetch and parse the Wikipedia infobox for a given page name.

        :param page_name: Wikipedia page name (e.g. "Alpha_Centauri").
        :return: Dict of infobox key-value pairs, or None if not found or not authenticated.
        """
        if not self._authenticated:
            logger.warning("Not authenticated. Call authenticate() first.")
            return None

        cache_path = f"{self._cache_dir}/wikimedia_{page_name.replace(' ', '_')}.json"

        if not os.path.isfile(cache_path):
            data = self._fetch_from_api(page_name)
            if data is not None:
                io.write_list_json([data], cache_path)
                logger.debug(f"  Cached infobox for '{page_name}'")
            else:
                return None
        else:
            logger.debug(f"  Loading cached infobox for '{page_name}'")
            cached = io.read_list_json(cache_path)
            if cached and len(cached) > 0:
                data = cached[0]
            else:
                return None

        return self._flatten_infobox(data)

    def fetch_parsed(self, page_name: str) -> dict[str, str] | None:
        """Fetch infobox and normalize keys to internal field names.

        Convenience method that calls :meth:`fetch_by_page_name` and filters/renames
        keys using :func:`normalize_field`. Only returns fields that map to
        PhysicalData fields.

        :param page_name: Wikipedia page name.
        :return: Dict mapping internal field names to raw string values,
                 or None if not authenticated or no matching fields found.
        """
        raw = self.fetch_by_page_name(page_name)
        if raw is None:
            return None

        parsed: dict[str, str] = {}
        for key, value in raw.items():
            field = normalize_field(key)
            if field is not None:
                parsed[field] = value

        return parsed if parsed else None

    def fetch_wikimedia_star(self, page_name: str) -> WikimediaStar | None:
        """Fetch infobox and return a WikimediaStar instance.

        Convenience method that calls :meth:`fetch_by_page_name`, normalizes
        keys, and creates a WikimediaStar with parsed astropy Quantities.

        :param page_name: Wikipedia page name.
        :return: WikimediaStar instance, or None if not authenticated or
                 no matching fields found.
        """
        raw = self.fetch_by_page_name(page_name)
        if raw is None:
            return None

        return WikimediaStar.from_raw(raw)

    def _fetch_from_api(self, page_name: str) -> dict[str, Any] | None:
        """Make the API request and parse the infobox JSON response.

        :param page_name: Wikipedia page name.
        :return: Parsed infobox as dict, or None if not found or error.
        """
        url = self.DATA_URL_TEMPLATE.format(pageName=page_name)
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

        try:
            response = self._session.post(url, headers=headers, timeout=30)
            if response.status_code == 404:
                logger.warning(f"Page not found: {page_name}")
                return None
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching infobox for '{page_name}'")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching '{page_name}': {e}")
            return None

        try:
            json_data = response.json()
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON response for '{page_name}': {e}")
            return None

        return self._parse_infobox(json_data, page_name)

    @staticmethod
    def _parse_infobox(json_data: list[dict], page_name: str) -> dict[str, Any] | None:
        """Extract infobox data from the structured-contents API response.

        :param json_data: Parsed JSON response (list).
        :param page_name: Page name for logging.
        :return: Infobox dict or None.
        """
        if not json_data or len(json_data) < 2:
            logger.warning(f"Unexpected response structure for '{page_name}'")
            return None

        item = json_data[0]

        # Verify language
        lang = item.get("in_language", {}).get("identifier", "unknown")
        if lang != "en":
            logger.debug(f"Non-English page '{page_name}' (lang={lang}), skipping")
            return None

        # Navigate to infobox
        infobox = item.get("infoboxes")
        if not infobox or len(infobox) == 0:
            logger.debug(f"No infobox for '{page_name}'")
            return None

        try:
            parts = infobox[0]["has_parts"][0]["has_parts"]
        except (KeyError, IndexError):
            logger.debug(f"Could not navigate infobox structure for '{page_name}'")
            return None

        result: dict[str, Any] = {}
        for entry in parts:
            if "name" in entry and "value" in entry:
                result[entry["name"]] = entry["value"]

        return result

    @staticmethod
    def _flatten_infobox(data: dict[str, Any]) -> dict[str, Any]:
        """Flatten a nested infobox dict to simple key-value pairs.

        :param data: Raw parsed infobox dict (may contain nested dicts/lists).
        :return: Dict with string keys and string values.
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = value
            elif isinstance(value, dict):
                result[key] = value.get("text", str(value))
            elif isinstance(value, list):
                result[key] = ", ".join(str(v) for v in value)
            else:
                result[key] = str(value)
        return result
