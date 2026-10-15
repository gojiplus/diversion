"""City-walk discovery with editable tourism starters and honest time budgets."""

import os

import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from diversion.cities import CITY_WALKS, CityWalk
from diversion.map_builder import directions_url, display_route_card, display_route_map
from diversion.models import WalkPlan, WalkRequest
from diversion.planner import plan_walk
from diversion.route_scorer import explain_route
from diversion.settings import (
    get_browser_maps_api_key,
    get_google_maps_api_key,
    get_openai_api_key,
)


def _choose_walk(walk: CityWalk) -> None:
    st.session_state.update(
        origin=walk.origin,
        destination=walk.destination,
        stops="\n".join(walk.stops),
        loop=False,
    )
    st.session_state.pop("walk_plan", None)
    st.session_state.pop("ai_explanations", None)


def _starters() -> None:
    st.subheader("Start with a city")
    cities = list(dict.fromkeys(walk.city for walk in CITY_WALKS))
    for city, tab in zip(cities, st.tabs(cities), strict=True):
        with tab:
            columns = st.columns(2)
            walks = [walk for walk in CITY_WALKS if walk.city == city]
            for column, walk in zip(columns, walks, strict=True):
                with column:
                    st.markdown(f"**{walk.title}**")
                    st.write(walk.description)
                    st.caption(" → ".join([walk.origin, *walk.stops, walk.destination]))
                    st.button(
                        "Customize this walk",
                        key=walk.title,
                        on_click=_choose_walk,
                        args=(walk,),
                    )
                    st.link_button(
                        "Preview in Google Maps",
                        directions_url(walk.origin, walk.destination, list(walk.stops)),
                    )
                    st.link_button("Official visitor guide", walk.source)
    st.caption(
        "Editorial walking ideas, not precomputed routes. Preview links"
        " work without API keys. Opening hours, admission and "
        "accessibility need checking separately."
    )


def _configuration() -> tuple[str | None, str | None, str | None]:
    with st.sidebar.expander("API configuration"):
        if not os.getenv("GOOGLE_MAPS_API_KEY"):
            st.text_input(
                "Google Routes + Places key", type="password", key="google_maps_api_key"
            )
        else:
            st.caption("Google Routes + Places configured")
        if not os.getenv("GOOGLE_MAPS_BROWSER_API_KEY"):
            st.text_input(
                "Google Maps browser key (optional)",
                type="password",
                key="google_maps_browser_api_key",
                help=(
                    "Use a separate Maps JavaScript key restricted to this site's "
                    "referrers. This key is sent to the browser."
                ),
            )
        if not os.getenv("OPENAI_API_KEY"):
            st.text_input(
                "OpenAI key (optional)", type="password", key="openai_api_key"
            )
        st.caption(
            "Planning uses Google Routes and Places. The browser map and AI"
            " descriptions are optional. API usage may incur charges."
        )
    return get_google_maps_api_key(), get_browser_maps_api_key(), get_openai_api_key()


def _results(plan: WalkPlan, browser_key: str | None, openai_key: str | None) -> None:
    discovery = plan.discovery
    if discovery.failed:
        st.warning(
            f"{discovery.failed} of {discovery.attempted} place searches failed. "
            "Suggestions may be incomplete; this does not mean there are "
            "no places to visit."
        )
    elif discovery.attempted and not discovery.places:
        st.info(
            "No matching places were returned in the sampled area. Try "
            "different interests or add a named stop."
        )
    if discovery.coverage_limited:
        st.caption(
            "This walk exceeds the discovery sampling limit. Some stretches"
            " were not searched."
        )
    if plan.failed_candidates:
        st.warning(
            f"Could not calculate {plan.failed_candidates} candidate walk(s). "
            "Available options are shown below."
        )
    if not plan.routes:
        st.info("No calculated walk fits your budget and selected stops.")
        if plan.shortest_over_budget_minutes is not None:
            st.write(
                f"Shortest calculated option: "
                f"{plan.shortest_over_budget_minutes:.0f} walking minutes. "
                "Increase the budget or remove a stop."
            )
        return
    st.subheader("Your walking options")
    if plan.baseline_seconds is not None:
        st.caption(
            f"Fastest direct option returned: {plan.baseline_seconds / 60:.0f} min. "
            f"Allowed extra walking: {plan.request.extra_minutes} min."
        )
    labels = [
        f"{index + 1}. {route['duration'] / 60:.0f} min · "
        + (" → ".join(p["name"] for p in route["stops"]) or "Direct walk")
        for index, route in enumerate(plan.routes)
    ]
    selected = st.radio(
        "Choose a walk", range(len(labels)), format_func=lambda i: labels[i]
    )
    route = plan.routes[selected]
    if browser_key:
        display_route_map(route, browser_key)
    else:
        st.caption(
            "For an embedded map, add a separate browser-restricted Google "
            "Maps key. The itinerary and Google Maps link work without it."
        )
    display_route_card(route, plan.request)
    if st.button("Generate optional AI description", disabled=not openai_key):
        with (
            st.spinner("Describing this itinerary…"),
            OpenAI(api_key=openai_key, timeout=20, max_retries=0) as client,
        ):
            explanation = explain_route(route, client)
        if explanation:
            st.session_state.setdefault("ai_explanations", {})[selected] = explanation
        else:
            st.info(
                "AI description unavailable. Your itinerary and ranking are unchanged."
            )
    if explanation := st.session_state.get("ai_explanations", {}).get(selected):
        st.caption("AI description — does not affect ranking")
        st.write(explanation)
    with st.expander("How these options were chosen"):
        st.write(
            "Selected stops are included in every option, in their listed "
            "order. The planner checks up to three detours and ranks actual"
            " stops by your interests, with a small rating adjustment and a"
            " penalty for extra walking. Unrated places remain eligible. "
            "Nearby places alone do not raise a route's score."
        )
        st.write(
            "Discovery is limited to sampled areas and returned search "
            "results. This is not an exhaustive search or a measure of "
            "street scenery, quietness, sidewalk quality or accessibility. "
            "Visit allowances are your estimates."
        )


def main() -> None:
    """Run the city-walk planner, with free-to-browse starters before API setup."""
    load_dotenv()
    st.set_page_config(
        page_title="Diversion · City walks", page_icon="🚶", layout="wide"
    )
    st.title("Diversion")
    st.write(
        "Make a city walk worth wandering. Find sights, art, gardens "
        "and food within your walking budget."
    )
    _starters()
    google_key, browser_key, openai_key = _configuration()
    st.subheader("Make it your walk")
    origin = st.text_input(
        "Start",
        key="origin",
        placeholder="A landmark, station or address, including the city",
    )
    loop = st.checkbox("Return to start", key="loop")
    destination = st.text_input("Finish", key="destination", disabled=loop)
    stop_text = st.text_area(
        "Stops to include, in order (up to two; one per line)", key="stops"
    )
    st.caption(
        "Include the city in each stop name. Check the resolved names "
        "and map links in your results."
    )
    preferences = {
        category: st.sidebar.slider(label, 0, 5, value)
        for category, label, value in (
            ("landmarks", "Landmarks & history", 4),
            ("culture", "Museums & galleries", 3),
            ("parks", "Parks & gardens", 3),
            ("food", "Food & coffee", 2),
        )
    }
    extra_minutes = st.slider(
        "Extra walking minutes", 0, 120, 30, step=5, disabled=loop
    )
    walking_minutes = st.slider(
        "Total walking budget for a circular walk",
        5,
        240,
        60,
        step=5,
        disabled=not loop,
    )
    visit_minutes = st.slider(
        "Your visit allowance per stop (minutes)", 0, 180, 15, step=5
    )
    request = WalkRequest(
        origin=origin,
        destination=destination,
        preferences=preferences,
        extra_minutes=extra_minutes,
        return_to_start=loop,
        walking_minutes=walking_minutes,
        visit_minutes=visit_minutes,
        required_stops=tuple(
            line.strip() for line in stop_text.splitlines() if line.strip()
        ),
    )
    if st.button("Plan my walk", type="primary"):
        st.session_state.pop("walk_plan", None)
        st.session_state.pop("ai_explanations", None)
        if not google_key:
            st.info(
                "Add a Google Routes + Places key in API configuration to "
                "calculate walking options. You can already preview any city "
                "starter in Google Maps."
            )
        else:
            try:
                with st.spinner("Checking walks and stop detours…"):
                    st.session_state["walk_plan"] = plan_walk(google_key, request)
            except (requests.RequestException, ValueError, KeyError, TypeError):
                st.error(
                    "Could not plan this walk. Check the endpoints, stop names, "
                    "time limits, and Google API access. Use Return to start when "
                    "the endpoints are the same."
                )
    if plan := st.session_state.get("walk_plan"):
        if plan.request == request:
            _results(plan, browser_key, openai_key)
        else:
            st.info("Your choices changed. Plan again to update the walking options.")
