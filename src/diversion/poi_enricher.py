"""Discover tourist stops and distinguish missing data from empty results."""

import math
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import urlencode

import requests

from diversion.models import Discovery, Place, Point, Preferences

CATEGORY_TYPES = {
    "landmarks": ["historical_landmark", "monument", "tourist_attraction"],
    "culture": ["museum", "art_gallery"],
    "parks": ["park", "botanical_garden"],
    "food": ["cafe", "bakery", "restaurant"],
}
_FIELDS = (
    "places.id,places.displayName,places.rating,places.types,places.location,"
    "places.userRatingCount,places.googleMapsUri,places.businessStatus,places.attributions"
)


def _parse_place(data: dict[str, Any]) -> Place | None:
    name = data.get("displayName", {}).get("text")
    identity = data.get("id")
    location = data.get("location", {})
    latitude, longitude = location.get("latitude"), location.get("longitude")
    if (
        not name
        or not identity
        or not isinstance(latitude, (int, float))
        or not isinstance(longitude, (int, float))
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
        or data.get("businessStatus") in {"CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"}
    ):
        return None
    rating = data.get("rating")
    if (
        not isinstance(rating, (int, float))
        or not math.isfinite(rating)
        or not 1 <= rating <= 5
    ):
        rating = None
    return {
        "id": identity,
        "name": name,
        "rating": rating,
        "types": data.get("types", []),
        "location": {"lat": latitude, "lng": longitude},
        "user_ratings_total": max(0, int(data.get("userRatingCount", 0))),
        "maps_uri": "https://www.google.com/maps/search/?"
        + urlencode(
            {
                "api": 1,
                "query": name,
                "query_place_id": identity,
            }
        ),
        "attributions": [
            {"provider": item.get("provider", ""), "uri": item.get("providerUri", "")}
            for item in data.get("attributions", [])
        ],
    }


def _places_request(api_key: str, method: str, payload: dict[str, Any]) -> list[Place]:
    response = requests.post(
        f"https://places.googleapis.com/v1/places:{method}",
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": _FIELDS,
        },
        json=payload,
        timeout=(3.05, 10),
    )
    response.raise_for_status()
    raw_places = response.json().get("places", [])
    if not isinstance(raw_places, list):
        raise ValueError("Invalid places response")
    return [place for raw in raw_places if (place := _parse_place(raw)) is not None]


def resolve_place(api_key: str, query: str) -> Place:
    """Resolve a named stop or starting point to a routable place.

    Args:
        api_key: Server-side Google Maps API key.
        query: Place name including the city or a full address.

    Returns:
        The first valid text-search match, displayed for the user to confirm.

    Raises:
        ValueError: The query is blank or no usable place is returned.
    """
    if not query.strip():
        raise ValueError("Enter a place name or address")
    places = _places_request(api_key, "searchText", {"textQuery": query, "pageSize": 1})
    if not places:
        raise ValueError("Could not resolve a selected place; try its full address")
    return places[0]


def find_places(
    api_key: str,
    points: list[Point],
    preferences: Preferences,
    radius_meters: float = 300,
) -> Discovery:
    """Search around at most eight centers with four concurrent requests.

    Args:
        api_key: Server-side Google Maps API key.
        points: Search centers in latitude/longitude order.
        preferences: Interest weights; only positive categories are requested.
        radius_meters: Search radius, including a wider neighborhood for loops.

    Returns:
        Deduplicated places and attempted/failed search counts. Unrated sights
        remain eligible; a place's popularity is not a requirement to discover it.

    Raises:
        ValueError: The radius is invalid or more than eight centers are supplied.
    """
    if (
        not math.isfinite(radius_meters)
        or not 0 < radius_meters <= 5000
        or len(points) > 8
    ):
        raise ValueError("Use at most eight centers and a radius up to 5000 meters")
    types = [
        kind
        for category, kinds in CATEGORY_TYPES.items()
        if preferences.get(category, 0) > 0
        for kind in kinds
    ]
    if not types or not points:
        return Discovery()
    centers = list(dict.fromkeys((round(lat, 6), round(lng, 6)) for lat, lng in points))

    def search(point: Point) -> list[Place] | None:
        try:
            return _places_request(
                api_key,
                "searchNearby",
                {
                    "includedTypes": types,
                    "maxResultCount": 20,
                    "locationRestriction": {
                        "circle": {
                            "center": {"latitude": point[0], "longitude": point[1]},
                            "radius": radius_meters,
                        }
                    },
                },
            )
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return None

    unique: dict[str, Place] = {}
    failed = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        for places in executor.map(search, centers):
            if places is None:
                failed += 1
            else:
                for place in places:
                    unique.setdefault(place["id"], place)
    return Discovery(
        places=list(unique.values()), attempted=len(centers), failed=failed
    )
