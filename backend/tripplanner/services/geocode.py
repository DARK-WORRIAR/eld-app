"""
Geocoding service providing forward geocoding for logistics addresses and cities.
Integrates OpenStreetMap Nominatim with automated fallback to Photon (Komoot).
Includes in-memory caching and resilient error handling.
"""

from functools import lru_cache
import logging
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger(__name__)

NOMINATIM_SEARCH_ENDPOINT = "https://nominatim.openstreetmap.org/search"
PHOTON_SEARCH_ENDPOINT = "https://photon.komoot.io/api/"

DEFAULT_REQUEST_TIMEOUT_SECONDS = 15

REQUEST_HEADERS = {
    "User-Agent": "ELDLogisticsEngine/1.0 (Fleet Operations; contact: dispatch@eld-planner.internal)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


class GeocodeError(Exception):
    """Base exception for all geocoding errors."""
    pass


class LocationNotFoundError(GeocodeError):
    """Raised when an address or city query returns no valid coordinates."""
    pass


class GeocodeServiceUnavailableError(GeocodeError):
    """Raised when upstream geocoding providers fail to respond or return HTTP errors."""
    pass


def _query_nominatim(place_name: str, timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS) -> Optional[Dict[str, Any]]:
    """
    Query OpenStreetMap Nominatim forward geocoding API.
    """
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    try:
        response = requests.get(
            NOMINATIM_SEARCH_ENDPOINT,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            return None

        top = data[0]
        return {
            "lat": float(top["lat"]),
            "lon": float(top["lon"]),
            "display_name": top.get("display_name", place_name),
        }
    except requests.exceptions.RequestException as exc:
        logger.warning("Nominatim geocoding failed for '%s': %s", place_name, exc)
        return None


def _query_photon(place_name: str, timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS) -> Optional[Dict[str, Any]]:
    """
    Query Photon (Komoot OSM-based geocoder) as high-availability fallback.
    """
    params = {"q": place_name, "limit": 1}
    try:
        response = requests.get(
            PHOTON_SEARCH_ENDPOINT,
            params=params,
            headers=REQUEST_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        features = payload.get("features") or []
        if not features:
            return None

        primary = features[0]
        coordinates = primary["geometry"]["coordinates"]
        properties = primary.get("properties", {})

        address_parts = [
            properties.get("name"),
            properties.get("city"),
            properties.get("state"),
            properties.get("country"),
        ]
        formatted_name = ", ".join(p for p in address_parts if p)

        return {
            "lat": float(coordinates[1]),
            "lon": float(coordinates[0]),
            "display_name": formatted_name or place_name,
        }
    except requests.exceptions.RequestException as exc:
        logger.warning("Photon geocoding fallback failed for '%s': %s", place_name, exc)
        return None


@lru_cache(maxsize=512)
def geocode(place_name: str) -> Dict[str, Any]:
    """
    Resolves an address, city, or postal location into geographic coordinates.

    Utilizes Nominatim as the primary provider with automatic failover to Photon.
    Results are cached in-memory to prevent duplicate network calls.

    Args:
        place_name: Free-form text describing the location (e.g., 'Dallas, TX').

    Returns:
        Dict containing:
            lat (float): Latitude in decimal degrees.
            lon (float): Longitude in decimal degrees.
            display_name (str): Standardized location name.

    Raises:
        LocationNotFoundError: When the location cannot be resolved by any provider.
        GeocodeServiceUnavailableError: When providers are unreachable.
    """
    cleaned = (place_name or "").strip()
    if not cleaned:
        raise LocationNotFoundError("Location name cannot be empty.")

    # 1. Primary provider
    result = _query_nominatim(cleaned)
    if result:
        return result

    # 2. Resilient fallback provider
    result = _query_photon(cleaned)
    if result:
        return result

    raise LocationNotFoundError(f"Could not resolve location coordinates for '{cleaned}'.")
