from unittest.mock import Mock

import pytest
import requests

from diversion.models import Place
from diversion.route_finder import compute_routes


def test_routes_use_walk_waypoints_and_fractional_seconds(monkeypatch, place: Place):
    post = Mock(
        return_value=Mock(
            json=lambda: {
                "routes": [
                    {
                        "duration": "600.5s",
                        "distanceMeters": 900,
                        "polyline": {"encodedPolyline": "abc"},
                        "warnings": ["Steps"],
                    },
                    {"duration": "600.5s", "polyline": {"encodedPolyline": "abc"}},
                ]
            }
        )
    )
    monkeypatch.setattr(requests, "post", post)
    result = compute_routes("server-key", "A", "B", [place], alternatives=True)
    assert len(result) == 1
    assert result[0]["duration"] == 600.5
    assert result[0]["stops"] == [place]
    assert result[0]["warnings"] == ["Steps"]
    assert result[0]["kind"] == "sightseeing"
    payload = post.call_args.kwargs["json"]
    assert payload["intermediates"] == [{"placeId": "cafe"}]
    assert payload["travelMode"] == "WALK"
    assert not payload["computeAlternativeRoutes"]
    assert post.call_args.kwargs["timeout"] == (3.05, 15)
    post.return_value.raise_for_status.assert_called_once()


def test_fastest_returned_route_is_baseline(monkeypatch):
    post = Mock(
        return_value=Mock(
            json=lambda: {
                "routes": [
                    {"duration": "900s", "polyline": {"encodedPolyline": "b"}},
                    {"duration": "300s", "polyline": {"encodedPolyline": "a"}},
                ]
            }
        )
    )
    monkeypatch.setattr(requests, "post", post)
    result = compute_routes("key", "A", "B", alternatives=True)
    assert [r["duration"] for r in result] == [300, 900]
    assert result[0]["kind"] == "direct"
    assert post.call_args.kwargs["json"]["computeAlternativeRoutes"]


@pytest.mark.parametrize("seconds", ["nans", "-1s", "0s", "infs"])
def test_invalid_durations_rejected(monkeypatch, seconds):
    monkeypatch.setattr(
        requests,
        "post",
        Mock(
            return_value=Mock(
                json=lambda: {
                    "routes": [
                        {"duration": seconds, "polyline": {"encodedPolyline": "a"}}
                    ]
                }
            )
        ),
    )
    with pytest.raises(ValueError, match="invalid"):
        compute_routes("key", "A", "B")


def test_missing_routes_and_request_failure(monkeypatch):
    monkeypatch.setattr(requests, "post", Mock(return_value=Mock(json=dict)))
    assert compute_routes("key", "A", "B") == []
    monkeypatch.setattr(requests, "post", Mock(side_effect=requests.Timeout))
    with pytest.raises(requests.Timeout):
        compute_routes("key", "A", "B")


def test_invalid_inputs(place):
    with pytest.raises(ValueError, match="endpoints"):
        compute_routes("key", "", "B")
    with pytest.raises(ValueError, match="three"):
        compute_routes("key", "A", "B", [place] * 4)
    place["id"] = ""
    with pytest.raises(ValueError, match="place ID"):
        compute_routes("key", "A", "B", [place])
