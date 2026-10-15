"""Compute walking routes through actual Google Places waypoints."""

import math
from typing import Any

import requests

from diversion.models import Place, Route


def compute_routes(
    api_key: str,
    origin: str,
    destination: str,
    stops: list[Place] | None = None,
    *,
    alternatives: bool = False,
) -> list[Route]:
    """Get walking routes, preserving the order of selected stops.

    Args:
        api_key: Server-side Google Maps API key.
        origin: Starting address or landmark.
        destination: Ending address or landmark.
        stops: Up to three resolved places to visit in order.
        alternatives: Request alternatives when there are no intermediate stops.

    Returns:
        Distinct routes sorted by walking duration.

    Raises:
        ValueError: Inputs or returned route measurements are invalid.
    """
    stops = stops or []
    if not origin.strip() or not destination.strip() or len(stops) > 3:
        raise ValueError("Enter both endpoints and select no more than three stops")
    if any(not stop["id"] for stop in stops):
        raise ValueError("Every stop must have a place ID")
    payload: dict[str, Any] = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "WALK",
        "computeAlternativeRoutes": alternatives and not stops,
        "polylineQuality": "HIGH_QUALITY",
    }
    if stops:
        payload["intermediates"] = [{"placeId": stop["id"]} for stop in stops]
    response = requests.post(
        "https://routes.googleapis.com/directions/v2:computeRoutes",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "routes.duration,routes.distanceMeters,"
                "routes.polyline.encodedPolyline,routes.warnings"
            ),
        },
        json=payload,
        timeout=(3.05, 15),
    )
    response.raise_for_status()
    routes: list[Route] = []
    seen: set[str] = set()
    for data in response.json().get("routes", []) or []:
        seconds = float(data["duration"].removesuffix("s"))
        distance = int(data.get("distanceMeters", 0))
        geometry = data["polyline"]["encodedPolyline"]
        if not math.isfinite(seconds) or seconds <= 0 or distance < 0 or not geometry:
            raise ValueError("Route measurements or geometry are invalid")
        if geometry in seen:
            continue
        seen.add(geometry)
        routes.append(
            {
                "duration": seconds,
                "distance": distance,
                "polyline": geometry,
                "stops": list(stops),
                "warnings": data.get("warnings", []),
                "kind": "sightseeing" if stops else "alternative",
            }
        )
    routes.sort(key=lambda route: route["duration"])
    if routes and not stops:
        routes[0]["kind"] = "direct"
    return routes
