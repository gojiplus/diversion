from dataclasses import replace
from unittest.mock import Mock

import pytest
import requests

from diversion import planner
from diversion.models import Discovery, Place, WalkRequest


def setup_planner(monkeypatch, route, place):
    monkeypatch.setattr(
        planner, "find_places", Mock(return_value=Discovery([place], attempted=3))
    )
    monkeypatch.setattr(planner, "resolve_place", Mock(return_value=place))

    def compute(key, origin, destination, stops=None, **kwargs):
        return [
            {
                **route,
                "duration": 900 if stops else 600,
                "stops": list(stops or []),
                "kind": "sightseeing" if stops else "direct",
            }
        ]

    mock = Mock(side_effect=compute)
    monkeypatch.setattr(planner, "compute_routes", mock)
    return mock


def test_includes_real_waypoints_and_enforces_minutes(monkeypatch, route, place):
    compute = setup_planner(monkeypatch, route, place)
    request = WalkRequest("A", "B", {"food": 5}, extra_minutes=5)
    plan = planner.plan_walk("key", request)
    assert len(plan.routes) == 2
    assert plan.routes[0]["stops"] == [place]
    assert plan.routes[0].get("extra_minutes") == 5
    assert compute.call_count == 2
    plan = planner.plan_walk("key", replace(request, extra_minutes=4))
    assert len(plan.routes) == 1
    assert not plan.routes[0]["stops"]
    assert plan.shortest_over_budget_minutes == 15


def test_required_stops_are_never_dropped(monkeypatch, route, place):
    setup_planner(monkeypatch, route, place)
    request = WalkRequest(
        "A", "B", {"food": 5}, extra_minutes=4, required_stops=("Garden Cafe",)
    )
    plan = planner.plan_walk("key", request)
    assert plan.routes == []
    assert plan.shortest_over_budget_minutes == 15
    plan = planner.plan_walk("key", replace(request, extra_minutes=5))
    assert all(r["stops"] == [place] for r in plan.routes)


def test_loop_does_not_request_zero_distance_baseline(monkeypatch, route, place):
    compute = setup_planner(monkeypatch, route, place)
    start = {**place, "id": "start"}
    monkeypatch.setattr(planner, "resolve_place", Mock(return_value=start))
    request = WalkRequest(
        "A", "", {"food": 5}, return_to_start=True, walking_minutes=15
    )
    plan = planner.plan_walk("key", request)
    assert plan.baseline_seconds is None
    assert len(plan.routes) == 1
    assert plan.routes[0]["kind"] == "loop"
    assert compute.call_args.args[1:3] == ("A", "A")
    assert compute.call_args.args[3] == [place]
    assert not planner.plan_walk("key", replace(request, walking_minutes=10)).routes


def test_partial_failure_keeps_direct_route(monkeypatch, route, place):
    compute = setup_planner(monkeypatch, route, place)
    compute.side_effect = [[route], requests.Timeout]
    plan = planner.plan_walk("key", WalkRequest("A", "B", {"food": 5}))
    assert len(plan.routes) == 1
    assert plan.failed_candidates == 1
    compute.side_effect = [[route], []]
    assert (
        planner.plan_walk("key", WalkRequest("A", "B", {"food": 5})).failed_candidates
        == 1
    )
    compute.side_effect = [[]]
    with pytest.raises(ValueError, match="No walking"):
        planner.plan_walk("key", WalkRequest("A", "B", {}))


def test_bounded_candidates_preserve_required_order(monkeypatch, route, place: Place):
    compute = setup_planner(monkeypatch, route, place)
    first = {**place, "id": "first"}
    second = {**place, "id": "second"}
    monkeypatch.setattr(planner, "resolve_place", Mock(side_effect=[first, second]))
    places: list[Place] = [{**place, "id": str(i)} for i in range(100)]
    monkeypatch.setattr(planner, "find_places", Mock(return_value=Discovery(places)))
    plan = planner.plan_walk(
        "key", WalkRequest("A", "B", {"food": 5}, required_stops=("one", "two"))
    )
    assert compute.call_count == 4
    for result in plan.routes:
        ids = [p["id"] for p in result["stops"]]
        assert ids.index("first") < ids.index("second")
        assert len(ids) <= 3


@pytest.mark.parametrize(
    "changes",
    [
        {"origin": ""},
        {"destination": "A"},
        {"extra_minutes": -1},
        {"walking_minutes": 0},
        {"visit_minutes": 181},
        {"required_stops": ("x", "y", "z")},
        {"required_stops": (" ",)},
        {"preferences": {"walkable": 5}},
        {"preferences": {"food": 6}},
    ],
)
def test_invalid_request_rejected_before_network(changes):
    with pytest.raises(ValueError, match=r"Enter|Choose|outside"):
        planner.plan_walk("key", replace(WalkRequest("A", "B", {}), **changes))


def test_deduplicates_geometry_and_stops(monkeypatch, route, place):
    compute = setup_planner(monkeypatch, route, place)
    compute.side_effect = [[route, route], [{**route, "stops": [place]}]]
    plan = planner.plan_walk("key", WalkRequest("A", "B", {"food": 5}))
    assert len(plan.routes) == 2
