from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from streamlit.testing.v1 import AppTest

from diversion import ui
from diversion.cities import CITY_WALKS
from diversion.map_builder import directions_url, display_route_map
from diversion.models import Discovery, Place, Route, WalkPlan, WalkRequest


def app():
    return AppTest.from_string(
        "from diversion.ui import main\nmain()", default_timeout=20
    ).run()


def button(at, label):
    return next(item for item in at.button if item.label == label)


def test_city_options_work_without_credentials():
    at = app()
    assert not at.exception
    assert [tab.label for tab in at.tabs] == [
        "Paris",
        "Hamburg",
        "Frankfurt",
        "Seattle",
    ]
    assert len([b for b in at.button if b.label == "Customize this walk"]) == 8
    at.button(key=CITY_WALKS[-1].title).click().run()
    assert at.text_input(key="origin").value == "Pier 62, Seattle, WA"
    assert "Olympic Sculpture Park" in (at.text_area(key="stops").value or "")
    button(at, "Plan my walk").click().run()
    assert "Add a Google" in at.info[0].value
    assert not at.exception


def test_planning_needs_no_openai_and_clears_stale_results(
    monkeypatch, route: Route, place: Place
):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "server-secret")

    def plan(key, request: WalkRequest) -> WalkPlan:
        assert key == "server-secret"
        return WalkPlan(
            request,
            [{**route, "stops": [place], "extra_minutes": 5}],
            Discovery([place]),
            baseline_seconds=300,
        )

    mock = Mock(side_effect=plan)
    monkeypatch.setattr(ui, "plan_walk", mock)
    at = app()
    at.button(key=CITY_WALKS[0].title).click().run()
    button(at, "Plan my walk").click().run()
    assert not at.exception
    assert len(at.metric) == 3
    assert button(at, "Generate optional AI description").disabled
    assert mock.call_count == 1
    at.text_input(key="origin").set_value("Changed").run()
    assert not at.metric
    assert "choices changed" in at.info[0].value
    mock.side_effect = requests.Timeout
    button(at, "Plan my walk").click().run()
    assert at.error
    assert not at.metric


def test_failure_messages_and_empty_budget(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "key")

    def plan(key, request):
        return WalkPlan(
            request,
            [],
            Discovery(attempted=4, failed=2, coverage_limited=True),
            failed_candidates=1,
            shortest_over_budget_minutes=70,
        )

    monkeypatch.setattr(ui, "plan_walk", plan)
    at = app()
    at.button(key=CITY_WALKS[1].title).click().run()
    button(at, "Plan my walk").click().run()
    assert len(at.warning) == 2
    assert "No calculated" in at.info[0].value
    assert not at.exception


def test_loop_and_optional_ai(monkeypatch, route: Route, place: Place):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai")
    monkeypatch.setattr(
        ui,
        "plan_walk",
        lambda key, request: WalkPlan(
            request, [{**route, "stops": [place]}], Discovery(attempted=1)
        ),
    )
    explain = Mock(return_value="A cafe walk.")
    monkeypatch.setattr(ui, "explain_route", explain)
    at = app()
    at.text_input(key="origin").set_value("Seattle")
    at.checkbox(key="loop").check().run()
    assert at.text_input(key="destination").disabled
    button(at, "Plan my walk").click().run()
    assert not at.exception
    explain.assert_not_called()
    button(at, "Generate optional AI description").click().run()
    assert explain.call_count == 1
    assert not at.exception
    assert "A cafe walk." in [item.value for item in at.markdown]
    explain.return_value = None
    button(at, "Generate optional AI description").click().run()
    assert any("unavailable" in info.value for info in at.info)


def test_map_only_receives_explicit_browser_key(monkeypatch, route, place):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "never-send-this")
    route["stops"] = [place]
    mount = Mock()
    register = Mock(return_value=mount)
    monkeypatch.setattr("diversion.map_builder.component", register)
    display_route_map(route, "public-browser-key")
    data = mount.call_args.kwargs["data"]
    assert data["key"] == "public-browser-key"
    assert "never-send-this" not in str(data)
    assert data["stops"][0]["name"] == place["name"]
    assert len(data["points"]) == 2
    assert "export default function" in register.call_args.kwargs["js"]


def test_navigation_links_preserve_order_and_unicode():
    query = parse_qs(
        urlparse(
            directions_url("Römerberg", "Städel", ["Goethe", "Market"], ["id1", "id2"])
        ).query
    )
    assert query["travelmode"] == ["walking"]
    assert query["waypoints"] == ["Goethe|Market"]
    assert query["waypoint_place_ids"] == ["id1|id2"]
    assert query["origin"] == ["Römerberg"]
    with pytest.raises(ValueError, match="three"):
        directions_url("A", "B", ["1"] * 4)
    with pytest.raises(ValueError, match="identifiers"):
        directions_url("A", "B", ["1"], [])


def test_session_keys_survive_reruns(monkeypatch, route: Route):
    planner = Mock(
        side_effect=lambda key, request: WalkPlan(request, [route], Discovery())
    )
    monkeypatch.setattr(ui, "plan_walk", planner)
    at = app()
    at.text_input(key="google_maps_api_key").set_value("session-key").run()
    at.button(key=CITY_WALKS[0].title).click().run()
    button(at, "Plan my walk").click().run()
    assert planner.call_args.args[0] == "session-key"
    assert at.text_input(key="google_maps_api_key").value == "session-key"
    at.run()
    assert at.text_input(key="google_maps_api_key").value == "session-key"
    assert not at.exception


def test_real_map_component_mounts_and_reruns(monkeypatch, route: Route):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "server-test")
    monkeypatch.setenv("GOOGLE_MAPS_BROWSER_API_KEY", "browser-test")
    monkeypatch.setattr(
        ui,
        "plan_walk",
        lambda key, request: WalkPlan(request, [route], Discovery()),
    )
    at = app()
    at.button(key=CITY_WALKS[0].title).click().run()
    button(at, "Plan my walk").click().run()
    assert not at.exception
    at.run()
    assert not at.exception
