"""Build bounded sightseeing itineraries from real walking routes."""

import itertools

import requests

from diversion.geography import distance_meters, sample_route
from diversion.models import Place, Route, WalkPlan, WalkRequest
from diversion.poi_enricher import CATEGORY_TYPES, find_places, resolve_place
from diversion.route_finder import compute_routes
from diversion.route_scorer import place_value, rank_routes


def _validate(request: WalkRequest) -> None:
    if not request.origin.strip() or (
        not request.return_to_start and not request.destination.strip()
    ):
        raise ValueError("Enter a start and destination")
    if (
        not request.return_to_start
        and request.origin.strip().casefold() == request.destination.strip().casefold()
    ):
        raise ValueError("Choose Return to start for a circular walk")
    if (
        not 0 <= request.extra_minutes <= 120
        or not 5 <= request.walking_minutes <= 240
        or not 0 <= request.visit_minutes <= 180
    ):
        raise ValueError("Walking or visit time is outside the supported range")
    if len(request.required_stops) > 2 or any(
        not stop.strip() for stop in request.required_stops
    ):
        raise ValueError("Choose at most two named stops")
    if any(
        key not in CATEGORY_TYPES or not 0 <= weight <= 5
        for key, weight in request.preferences.items()
    ):
        raise ValueError("Choose supported interests with weights from zero to five")


def _insert_stop(
    required: list[Place],
    candidate: Place,
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> list[Place]:
    def length(stops: list[Place]) -> float:
        points = [
            origin,
            *((p["location"]["lat"], p["location"]["lng"]) for p in stops),
            destination,
        ]
        return sum(distance_meters(a, b) for a, b in itertools.pairwise(points))

    options = [
        [*required[:index], candidate, *required[index:]]
        for index in range(len(required) + 1)
    ]
    return min(options, key=length)


def plan_walk(api_key: str, request: WalkRequest) -> WalkPlan:
    """Compute destination or circular walks with at most three candidate detours.

    Args:
        api_key: Server-side Google Routes and Places key.
        request: Endpoints, interests, time constraints, and optional named stops.

    Returns:
        Ranked feasible walks, search failures, and the shortest rejected time.
        Every result includes all required stops in their original order.

    Raises:
        ValueError: Inputs are invalid, a required stop cannot be resolved, or no
            direct route is available. Provider request errors propagate when
            the baseline or a required stop cannot be retrieved.
    """
    _validate(request)
    required = list(
        {
            place["id"]: place
            for query in request.required_stops
            if (place := resolve_place(api_key, query))
        }.values()
    )
    destination = request.origin if request.return_to_start else request.destination
    baseline: list[Route] = []
    if request.return_to_start:
        start = resolve_place(api_key, request.origin)
        origin_point = (start["location"]["lat"], start["location"]["lng"])
        end_point = origin_point
        discovery = find_places(
            api_key,
            [origin_point],
            request.preferences,
            radius_meters=min(5000, request.walking_minutes * 40),
        )
        discovery.places = [p for p in discovery.places if p["id"] != start["id"]]
        plan = WalkPlan(request, [], discovery)
        limit = request.walking_minutes * 60
    else:
        baseline = compute_routes(
            api_key, request.origin, destination, alternatives=True
        )
        if not baseline:
            raise ValueError("No walking route was returned for these endpoints")
        points, capped = sample_route(baseline[0]["polyline"])
        if not points:
            raise ValueError("The route has no usable geometry")
        origin_point, end_point = points[0], points[-1]
        discovery = find_places(api_key, points, request.preferences)
        discovery.coverage_limited = capped
        plan = WalkPlan(
            request, [], discovery, baseline_seconds=baseline[0]["duration"]
        )
        limit = baseline[0]["duration"] + request.extra_minutes * 60
    candidates = sorted(
        discovery.places,
        key=lambda p: (
            -place_value(p, request.preferences),
            distance_meters(origin_point, (p["location"]["lat"], p["location"]["lng"])),
            p["id"],
        ),
    )
    required_ids = {p["id"] for p in required}
    candidates = [
        p
        for p in candidates
        if p["id"] not in required_ids and place_value(p, request.preferences) > 0
    ]
    combinations = [required] if required else []
    combinations.extend(
        _insert_stop(required, candidate, origin_point, end_point)
        for candidate in candidates[: 3 - len(combinations)]
    )
    routes = [] if required or request.return_to_start else baseline
    for stops in combinations:
        try:
            options = compute_routes(api_key, request.origin, destination, stops)
            if not options:
                plan.failed_candidates += 1
            routes.extend(options)
        except (requests.RequestException, ValueError, KeyError, TypeError):
            plan.failed_candidates += 1
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for route in routes:
        if request.return_to_start:
            route["kind"] = "loop"
        elif plan.baseline_seconds is not None:
            route["extra_minutes"] = max(
                0, (route["duration"] - plan.baseline_seconds) / 60
            )
        if route["duration"] > limit:
            minutes = route["duration"] / 60
            previous = plan.shortest_over_budget_minutes
            plan.shortest_over_budget_minutes = (
                minutes if previous is None else min(previous, minutes)
            )
            continue
        identity = (route["polyline"], tuple(p["id"] for p in route["stops"]))
        if identity not in seen:
            plan.routes.append(route)
            seen.add(identity)
    plan.routes = rank_routes(plan.routes, request.preferences)
    return plan
