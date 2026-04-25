"""Pretix API client for fetching order and seller data."""
import httpx
import logging
from typing import Optional
from geopy.geocoders import Nominatim
from .config import settings
from .models import Seller

logger = logging.getLogger(__name__)


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
        self.geocoder = Nominatim(user_agent="dorfflohmarkt-map")
        self._question_options_cache = {}  # Cache for question options

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

        Args:
            address: Street address
            city: City name
            postal_code: Postal code
            country: Country code

        Returns:
            Tuple of (latitude, longitude) or (None, None) if geocoding fails
        """
        try:
            full_address = f"{address}, {postal_code} {city}, {country}"
            location = self.geocoder.geocode(full_address, timeout=10)

            if location:
                return location.latitude, location.longitude
        except Exception as e:
            logger.warning(f"Error geocoding address '{full_address}': {e}")

        return None, None

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

            if order.get("positions"):
                for position in order["positions"]:
                    # Only process positions for the target product
                    if position.get("item") != self.product_id:
                        continue

                    for answer in position.get("answers", []):
                        question_id = answer.get("question")
                        option_identifiers = answer.get("option_identifiers", [])
                        answer_text = answer.get("answer", "")

                        # Question 2 is the location description
                        if question_id == 2 and answer_text:
                            location_description = answer_text

                        # Category questions have option_identifiers
                        if option_identifiers and question_id != 2:
                            # Fetch question options to map identifiers to text
                            options_map = await self._fetch_question_options(question_id, client)

                            # Convert identifiers to readable text
                            for identifier in option_identifiers:
                                category_text = options_map.get(identifier, identifier)
                                if category_text not in categories:
                                    categories.append(category_text)

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
