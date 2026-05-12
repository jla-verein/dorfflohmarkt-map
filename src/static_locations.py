"""Load static map locations from JSON configuration."""
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from pydantic import ValidationError

from .config import settings
from .models import StaticLocation
from .pretix_client import _cached_geocode_nominatim

logger = logging.getLogger(__name__)

_OSM_TYPE_MAP = {
    "node": "N",
    "way": "W",
    "relation": "R",
    "n": "N",
    "w": "W",
    "r": "R",
}


def _get_static_locations_file_path() -> str:
    project_root = Path(__file__).resolve().parents[1]
    return str(project_root / settings.static_locations_file)


def _normalize_osm_id(osmid: Optional[str]) -> Optional[str]:
    if osmid is None:
        return None

    osm_text = str(osmid).strip()
    if not osm_text:
        return None

    if re.match(r'^[NWR]\d+$', osm_text, re.IGNORECASE):
        return osm_text.upper()

    if osm_text.isdigit():
        return f"N{osm_text}"

    prefix = osm_text[0].upper()
    if prefix in _OSM_TYPE_MAP and osm_text[1:].isdigit():
        return f"{prefix}{osm_text[1:]}"

    return None


def _lookup_osm_coordinates(osm_id: str) -> tuple[Optional[float], Optional[float]]:
    url = "https://nominatim.openstreetmap.org/lookup"
    params = {
        "osm_ids": osm_id,
        "format": "json",
        "addressdetails": 0,
    }

    try:
        response = httpx.get(url, params=params, timeout=10.0, headers={"User-Agent": "dorfflohmarkt-map"})
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            first = data[0]
            latitude = first.get("lat")
            longitude = first.get("lon")
            if latitude is not None and longitude is not None:
                return float(latitude), float(longitude)
    except Exception as e:
        logger.warning(f"Unable to resolve OSM ID {osm_id}: {e}")

    return None, None


def _resolve_static_location_coordinates(static_location: StaticLocation) -> tuple[Optional[float], Optional[float]]:
    if static_location.latitude is not None and static_location.longitude is not None:
        return static_location.latitude, static_location.longitude

    if static_location.osmid:
        osm_id = _normalize_osm_id(static_location.osmid)
        if osm_id:
            latitude, longitude = _lookup_osm_coordinates(osm_id)
            if latitude is not None and longitude is not None:
                logger.info(f"Resolved static location '{static_location.id or static_location.name}' from OSM ID {osm_id}")
                return latitude, longitude

    if static_location.address:
        full_address = f"{static_location.address}, {static_location.postal_code or ''} {static_location.city or ''}, {static_location.country or 'DE'}"
        latitude, longitude = _cached_geocode_nominatim(full_address)
        if latitude is not None and longitude is not None:
            logger.info(f"Geocoded static location '{static_location.id or static_location.name}' from address '{full_address}'")
            return latitude, longitude

    return None, None


def load_static_locations() -> list[StaticLocation]:
    file_path = _get_static_locations_file_path()
    if not os.path.exists(file_path):
        logger.info(f"No static locations file found at {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Unable to load static locations file {file_path}: {e}")
        return []

    static_locations: list[StaticLocation] = []
    for entry in data.get("static_locations", []):
        try:
            static_location = StaticLocation(**entry)
        except ValidationError as e:
            logger.warning(f"Invalid static location entry in {file_path}: {e}")
            continue

        latitude, longitude = _resolve_static_location_coordinates(static_location)
        if latitude is None or longitude is None:
            logger.warning(
                f"Static location '{static_location.id or static_location.name}' could not be resolved to coordinates and will be skipped."
            )
            continue

        static_location.latitude = latitude
        static_location.longitude = longitude
        static_locations.append(static_location)

    logger.info(f"Loaded {len(static_locations)} static map locations from {file_path}")
    return static_locations
