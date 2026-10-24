"""
Routing service for calculating multi-leg freight corridors, driving distances,
and high-fidelity stop marker geographic interpolations.
Uses OSRM (Open Source Routing Machine) engine with comprehensive distance modeling.
"""

import logging
import math
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

OSRM_ROUTE_ENDPOINT = "https://router.project-osrm.org/route/v1/driving/{coords}"
DEFAULT_ROUTING_TIMEOUT = 25

METERS_TO_MILES = 0.000621371
SECONDS_TO_HOURS = 1.0 / 3600.0
EARTH_RADIUS_MILES = 3958.8


class RoutingError(Exception):
    """Base exception for routing and corridor calculation errors."""
    pass


class RouteCalculationError(RoutingError):
    """Raised when the routing engine fails to find a drivable path between coordinates."""
    pass


def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in miles.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_MILES * c


def get_route(waypoints: List[Dict[str, float]], timeout: int = DEFAULT_ROUTING_TIMEOUT) -> Dict[str, Any]:
    """
    Queries OSRM driving engine for a multi-point route corridor.

    Args:
        waypoints: Ordered list of point dictionaries containing 'lat' and 'lon'.
                   Example: [origin, pickup, destination]
        timeout: Network timeout in seconds.

    Returns:
        Dict containing:
            geometry (List[List[float]]): Array of [lat, lon] coordinates along the corridor.
            total_distance_miles (float): Total route distance in statute miles.
            total_duration_hours (float): Total driving duration in hours.
            legs (List[Dict]): Ordered leg summaries with start and end cumulative mileages.

    Raises:
        RouteCalculationError: If no drivable route is found between waypoints.
        RoutingError: If the routing provider cannot be reached.
    """
    if len(waypoints) < 2:
        raise ValueError("At least two waypoints are required to compute a route.")

    coords_param = ";".join(f"{p['lon']:.6f},{p['lat']:.6f}" for p in waypoints)
    url = OSRM_ROUTE_ENDPOINT.format(coords=coords_param)
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        logger.error("OSRM route calculation request failed: %s", exc)
        raise RoutingError(f"Routing service communication failed: {exc}") from exc

    if data.get("code") != "Ok" or not data.get("routes"):
        error_msg = data.get("message", "No drivable route found between coordinates.")
        raise RouteCalculationError(f"Route calculation rejected by routing engine: {error_msg}")

    primary_route = data["routes"][0]
    raw_coords = primary_route["geometry"]["coordinates"]
    # Convert from OSRM [lon, lat] to Leaflet standard [lat, lon]
    geometry: List[List[float]] = [[lat, lon] for lon, lat in raw_coords]

    legs_data: List[Dict[str, Any]] = []
    cumulative_mileage = 0.0

    for leg in primary_route.get("legs", []):
        leg_dist = leg.get("distance", 0.0) * METERS_TO_MILES
        leg_dur = leg.get("duration", 0.0) * SECONDS_TO_HOURS
        start_mileage = cumulative_mileage
        end_mileage = cumulative_mileage + leg_dist

        legs_data.append({
            "distance_miles": round(leg_dist, 1),
            "duration_hours": round(leg_dur, 2),
            "start_cumulative_miles": round(start_mileage, 1),
            "end_cumulative_miles": round(end_mileage, 1),
        })
        cumulative_mileage = end_mileage

    total_miles = primary_route.get("distance", 0.0) * METERS_TO_MILES
    total_hours = primary_route.get("duration", 0.0) * SECONDS_TO_HOURS

    return {
        "geometry": geometry,
        "total_distance_miles": round(total_miles, 1),
        "total_duration_hours": round(total_hours, 2),
        "legs": legs_data,
    }


def point_at_distance(
    geometry: List[List[float]],
    total_route_miles: float,
    target_miles: float,
) -> Optional[List[float]]:
    """
    Interpolates a geographic coordinate [lat, lon] along the route polyline
    at a specific cumulative odometer mileage using great-circle segment projection.

    Args:
        geometry: Polyline coordinates as [[lat, lon], ...]
        total_route_miles: Total route distance in miles.
        target_miles: Cumulative mileage target for marker placement.

    Returns:
        [lat, lon] coordinate closest to the requested mileage point.
    """
    if not geometry:
        return None

    if target_miles <= 0.0 or len(geometry) == 1:
        return geometry[0]

    if target_miles >= total_route_miles:
        return geometry[-1]

    # Pre-calculate cumulative segment distances along polyline
    accumulated_miles = 0.0
    for i in range(len(geometry) - 1):
        p1 = geometry[i]
        p2 = geometry[i + 1]
        seg_dist = haversine_distance_miles(p1[0], p1[1], p2[0], p2[1])

        if accumulated_miles + seg_dist >= target_miles:
            # Target lies along segment (p1, p2)
            segment_remaining = target_miles - accumulated_miles
            ratio = (segment_remaining / seg_dist) if seg_dist > 0 else 0.0
            interp_lat = p1[0] + ratio * (p2[0] - p1[0])
            interp_lon = p1[1] + ratio * (p2[1] - p1[1])
            return [round(interp_lat, 6), round(interp_lon, 6)]

        accumulated_miles += seg_dist

    return geometry[-1]
