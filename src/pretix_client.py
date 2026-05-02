"""Pretix API client for fetching order and seller data."""
import httpx
import logging
import json
import os
import time
from typing import Optional
from geopy.geocoders import Nominatim
from .config import settings
from .models import Seller

logger = logging.getLogger(__name__)

# Module-level geocoder for use in cached function
_nominatim_geocoder = Nominatim(user_agent="dorfflohmarkt-map")
_last_geocode_time = 0
_geocode_cache = {}  # Manual cache that only stores successful results


def _cached_geocode_nominatim(full_address: str) -> tuple[Optional[float], Optional[float]]:
    """
    Cached function to geocode an address using Nominatim.

    Only caches successful results (latitude/longitude).
    Failed results (None, None) are not cached and will be retried.

    Includes rate limiting to ensure 1 request/second compliance.

    Args:
        full_address: Full formatted address string

    Returns:
        Tuple of (latitude, longitude) or (None, None) if geocoding fails
    """
    global _last_geocode_time

    # Check if we have a cached successful result
    if full_address in _geocode_cache:
        return _geocode_cache[full_address]

    # Rate limiting: Nominatim has a 1 request/second limit
    current_time = time.time()
    time_since_last_request = current_time - _last_geocode_time

    if time_since_last_request < 1.5:
        sleep_time = 1.5 - time_since_last_request
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s before geocoding '{full_address}'")
        time.sleep(sleep_time)

    # Update last request time
    _last_geocode_time = time.time()

    # Perform geocoding
    result = None, None
    try:
        location = _nominatim_geocoder.geocode(full_address, timeout=10)
        if location:
            result = location.latitude, location.longitude
            logger.debug(f"Geocoded '{full_address}' -> ({result[0]}, {result[1]})")
            # Only cache successful results
            _geocode_cache[full_address] = result
    except Exception as e:
        logger.warning(f"Error geocoding address '{full_address}': {e}")
        # Don't cache failed results - allow retry later

    return result


class PretixClient:
    """Client for interacting with the Pretix API."""

    def __init__(self):
        """Initialize the Pretix API client."""
        self.base_url = settings.pretix_api_base_url
        self.organizer = settings.pretix_organizer
        self.event = settings.pretix_event_slug
        self.product_id = settings.pretix_product_id
        self.api_token = settings.pretix_api_token
        self.headers = {"Authorization": f"Token {self.api_token}"}
        self._question_options_cache = {}  # Cache for question options
        self._address_overrides = self._load_address_overrides()

    def _load_address_overrides(self) -> dict:
        """
        Load address overrides from overrides.json file.

        Returns:
            Dictionary mapping original address combinations to overrides
        """
        overrides = {}

        # Try to load from overrides.json in the root directory
        overrides_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "overrides.json")

        if os.path.exists(overrides_file):
            try:
                with open(overrides_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for override_entry in data.get("overrides", []):
                    original = override_entry.get("original", {})

                    # Create a key from the original address components
                    key = (
                        original.get("address", "").lower().strip(),
                        original.get("postal_code", "").lower().strip(),
                        original.get("city", "").lower().strip(),
                    )

                    overrides[key] = override_entry.get("override", {})

                logger.info(f"Loaded {len(overrides)} address overrides from {overrides_file}")
            except Exception as e:
                logger.error(f"Error loading address overrides: {e}")

        return overrides

    def _get_address_override(self, address: str, postal_code: str, city: str) -> Optional[dict]:
        """
        Check if there's an override for the given address.

        Args:
            address: Street address
            postal_code: Postal code
            city: City name

        Returns:
            Override dictionary or None
        """
        key = (address.lower().strip(), postal_code.lower().strip(), city.lower().strip())
        return self._address_overrides.get(key)

    async def get_sellers(self) -> list[Seller]:
        """
        Fetch all paid orders with seller information.

        Returns:
            List of Seller objects
        """
        sellers = []
        url = f"{self.base_url}/organizers/{self.organizer}/events/{self.event}/orders/"
        params = {
            "status": "p",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            for order in data.get("results", []):
                seller = await self._extract_seller_from_order(order, client)
                if seller:
                    sellers.append(seller)

            # Handle pagination
            while data.get("next"):
                next_url = data["next"]
                next_response = await client.get(next_url, headers=self.headers)
                next_response.raise_for_status()
                data = next_response.json()
                for order in data.get("results", []):
                    seller = await self._extract_seller_from_order(order, client)
                    if seller:
                        sellers.append(seller)

        return sellers

    async def _fetch_question_options(self, question_id: int, client: httpx.AsyncClient) -> dict:
        """
        Fetch and cache question options for mapping identifiers to text.

        Args:
            question_id: Question ID from Pretix
            client: HTTP client for making requests

        Returns:
            Dictionary mapping option identifier to de-informal text
        """
        if question_id in self._question_options_cache:
            return self._question_options_cache[question_id]

        try:
            url = f"{self.base_url}/organizers/{self.organizer}/events/{self.event}/questions/{question_id}/options/"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            options_map = {}
            for option in data.get("results", []):
                identifier = option.get("identifier")
                answer_text = option.get("answer", {}).get("de-informal", "")
                if identifier and answer_text:
                    options_map[identifier] = answer_text

            self._question_options_cache[question_id] = options_map
            return options_map
        except Exception as e:
            logger.warning(f"Error fetching question options for question {question_id}: {e}")
            return {}

    def _geocode_address(self, address: str, city: str, postal_code: str, country: str) -> tuple[Optional[float], Optional[float]]:
        """
        Geocode an address to get latitude and longitude.

        Handles address overrides and delegates to cached geocoding function.
        - If override has coordinates, use those directly
        - If override has an address, geocode the override address instead
        - Otherwise, geocode the original address
        - Results are cached to avoid redundant requests and rate limiting delays

        Args:
            address: Street address
            city: City name
            postal_code: Postal code
            country: Country code

        Returns:
            Tuple of (latitude, longitude) or (None, None) if geocoding fails
        """
        # Check for address override
        override = self._get_address_override(address, postal_code, city)

        if override:
            # If override has direct coordinates, use those
            if "latitude" in override and "longitude" in override:
                logger.info(f"Using override coordinates for address '{address}'")
                return override["latitude"], override["longitude"]

            # If override has an address, use that for geocoding
            if "address" in override:
                address = override["address"]
                city = override.get("city", city)
                postal_code = override.get("postal_code", postal_code)
                logger.info(f"Using override address for original address, geocoding: {address}")

        # Build full address string and use cached geocoding
        full_address = f"{address}, {postal_code} {city}, {country}"
        return _cached_geocode_nominatim(full_address)

    async def _extract_seller_from_order(self, order: dict, client: httpx.AsyncClient) -> Optional[Seller]:
        """
        Extract seller information from a Pretix order.

        Args:
            order: Order dictionary from Pretix API
            client: HTTP client for fetching additional data

        Returns:
            Seller object or None if extraction fails
        """
        try:
            # Extract address info from invoice address
            invoice_address = order.get("invoice_address", {})
            address = invoice_address.get("street", "")
            city = invoice_address.get("city", "")
            postal_code = invoice_address.get("zipcode", "")
            country = invoice_address.get("country", "DE")

            # Extract categories and location description from order position answers
            categories = []
            location_description = None
            other_text = None

            if order.get("positions"):
                for position in order["positions"]:
                    # Only process positions for the target product
                    if position.get("item") != self.product_id:
                        continue

                    for answer in position.get("answers", []):
                        question_id = answer.get("question")
                        question_identifier = answer.get("question_identifier")
                        option_identifiers = answer.get("option_identifiers", [])
                        answer_text = answer.get("answer", "").replace("\r\n", "<br>")

                        # Question 1 is the categories
                        if question_id == 1 and option_identifiers:
                            options_map = await self._fetch_question_options(question_id, client)
                            for identifier in option_identifiers:
                                category_text = options_map.get(identifier, identifier)
                                if category_text not in categories:
                                    categories.append(category_text)

                        # Question 2 is the location description
                        if question_id == 2 and answer_text:
                            location_description = answer_text
                        
                        if question_identifier == "other-public" and answer_text:
                            other_text = answer_text if answer_text else None


            # Only create seller if we have address info
            if address or city:
                # Geocode the address
                latitude, longitude = self._geocode_address(address, city, postal_code, country)

                return Seller(
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    country=country,
                    categories=categories if categories else ["Other"],
                    location_description=location_description,
                    other_text=other_text,
                    latitude=latitude,
                    longitude=longitude,
                )
        except Exception as e:
            logger.error(f"Error extracting seller from order: {e}")
            return None

        return None

    def get_all_categories(self, sellers: list[Seller]) -> list[str]:
        """
        Extract all unique categories from sellers.

        Args:
            sellers: List of Seller objects

        Returns:
            Sorted list of unique categories
        """
        categories = set()
        for seller in sellers:
            categories.update(seller.categories)
        return sorted(list(categories))


# Create a singleton instance
pretix_client = PretixClient()
