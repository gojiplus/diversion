"""Display Google route geometry on Google Maps and build portable itineraries."""

from importlib.resources import files
from urllib.parse import urlencode

import polyline
import streamlit as st
from streamlit.components.v2 import component

from diversion.models import Route, WalkRequest


def directions_url(
    origin: str, destination: str, stops: list[str], place_ids: list[str] | None = None
) -> str:
    """Build a walking directions link with ordered intermediate stops.

    Args:
        origin: Starting address or landmark.
        destination: Ending address or landmark.
        stops: Ordered waypoint names, limited to three for mobile browsers.
        place_ids: Optional Google IDs corresponding to each waypoint name.

    Returns:
        A Google Maps URL. Google recalculates its route when the link opens.

    Raises:
        ValueError: There are too many stops or mismatched waypoint identifiers.
    """
    if len(stops) > 3 or (place_ids is not None and len(place_ids) != len(stops)):
        raise ValueError("Use at most three stops with matching identifiers")
    params = {
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": "walking",
    }
    if stops:
        params["waypoints"] = "|".join(stops)
        if place_ids:
            params["waypoint_place_ids"] = "|".join(place_ids)
    return "https://www.google.com/maps/dir/?" + urlencode(params)


def display_route_map(route: Route, browser_key: str) -> None:
    """Draw the chosen route using only an explicit browser-restricted key.

    Args:
        route: Selected walking route and its included stops.
        browser_key: Public Maps JavaScript key, separate from the server key.
    """
    render = component(
        "diversion_google_map",
        html=(
            '<div id="map" role="region" aria-label="Selected walking '
            'route" style="height:440px"></div><p id="status" '
            'role="status"></p>'
        ),
        js=files("diversion").joinpath("assets/map.js").read_text(),
        isolate_styles=False,
    )
    render(
        data={
            "key": browser_key,
            "points": [
                {"lat": lat, "lng": lng}
                for lat, lng in polyline.decode(route["polyline"])
            ],
            "stops": [
                {"name": stop["name"], "position": stop["location"]}
                for stop in route["stops"]
            ],
        },
        key="selected_walk_map",
        height=480,
    )


def display_route_card(route: Route, request: WalkRequest) -> None:
    """Show walking and visiting estimates, ordered stops, and attribution.

    Args:
        route: Selected feasible itinerary.
        request: Original request, including assumed minutes per visit.
    """
    walking = route["duration"] / 60
    visiting = len(route["stops"]) * request.visit_minutes
    left, middle, right = st.columns(3)
    left.metric("Walking", f"{walking:.0f} min")
    middle.metric("Distance", f"{route['distance'] / 1000:.1f} km")
    right.metric("With your stop allowance", f"{walking + visiting:.0f} min")
    st.caption(
        f"Visit allowance: {request.visit_minutes} min per intermediate stop. "
        "Endpoints, queues and opening hours are not included."
    )
    if "extra_minutes" in route:
        st.caption(
            f"{route['extra_minutes']:.0f} extra walking minutes "
            "versus the fastest direct option returned."
        )
    st.write(route.get("explanation", ""))
    st.text(f"Start: {request.origin}")
    for index, stop in enumerate(route["stops"], 1):
        st.link_button(f"{index}. {stop['name']}", stop["maps_uri"])
        if stop["rating"] is not None:
            st.caption(
                f"Google Maps rating: {stop['rating']:.1f}/5 "
                f"({stop['user_ratings_total']} reviews)"
            )
        for attribution in stop["attributions"]:
            if attribution["uri"].startswith("https://"):
                st.link_button(
                    attribution["provider"] or "Place data provider", attribution["uri"]
                )
            elif attribution["provider"]:
                st.text(attribution["provider"])
    destination = request.origin if request.return_to_start else request.destination
    st.text(f"Finish: {destination}")
    st.link_button(
        "Open walk in Google Maps",
        directions_url(
            request.origin,
            destination,
            [p["name"] for p in route["stops"]],
            [p["id"] for p in route["stops"]],
        ),
    )
    st.caption(
        "Google Maps recalculates directions when opened; the path may "
        "differ. Route and place data: Google Maps."
    )
    st.warning(
        "Walking routes are in beta and may be missing clear sidewalks "
        "or pedestrian paths. Check signs and conditions on the ground."
    )
    for warning in route["warnings"]:
        st.text(warning)
