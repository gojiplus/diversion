from copy import deepcopy
from unittest.mock import Mock

import pytest
from openai import OpenAIError

from diversion.models import Route
from diversion.route_scorer import explain_route, place_value, rank_routes


def test_ranking_prefers_actual_stops_and_penalizes_detours(route: Route, place):
    route["extra_minutes"] = 0
    sightseeing: Route = {**route, "stops": [place], "extra_minutes": 5}
    far: Route = {**sightseeing, "extra_minutes": 60}
    original = deepcopy(route)
    ranked = rank_routes([route, far, sightseeing], {"food": 5})
    assert ranked[0]["stops"] == [place]
    assert ranked[0].get("extra_minutes") == 5
    assert ranked[1]["stops"] == []
    assert route == original
    assert "score" not in route


def test_types_do_not_stack_and_ratings_are_shrunk(place):
    single = place_value(place, {"food": 5})
    place["types"] = ["cafe", "bakery", "restaurant"]
    assert place_value(place, {"food": 5}) == single
    place["user_ratings_total"] = 0
    assert place_value(place, {"food": 5}) == 1
    place["rating"] = None
    assert place_value(place, {"food": 5}) == 1
    assert place_value(place, {"culture": 5}) == 0


@pytest.mark.parametrize("content", ["A walk with a cafe stop.", "", None])
def test_ai_only_describes_and_never_changes_score(
    route, place, client, monkeypatch, content
):
    route["stops"] = [place]
    route = rank_routes([route], {"food": 5})[0]
    original = deepcopy(route)
    create = Mock(return_value=Mock(choices=[Mock(message=Mock(content=content))]))
    monkeypatch.setattr(client.chat.completions, "create", create)
    assert explain_route(route, client) == (content or None)
    assert route == original


def test_ai_failure(route, client, monkeypatch):
    monkeypatch.setattr(
        client.chat.completions,
        "create",
        Mock(side_effect=OpenAIError("Service unavailable")),
    )
    assert explain_route(route, client) is None
