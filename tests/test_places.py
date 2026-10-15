from unittest.mock import Mock

import polyline
import pytest
import requests

from diversion.geography import distance_meters, sample_route
from diversion.poi_enricher import find_places, resolve_place


def raw_place(**overrides):
    return {
        "id": "p1",
        "displayName": {"text": "A museum"},
        "types": ["museum"],
        "location": {"latitude": 48.85, "longitude": 2.35},
        **overrides,
    }


def test_sampling_independent_of_vertex_density():
    sparse, limited = sample_route(polyline.encode([(0, 0), (0, 0.02)]))
    dense, dense_limited = sample_route(
        polyline.encode([(0, i / 10000) for i in range(201)])
    )
    assert not limited
    assert not dense_limited
    assert len(sparse) == len(dense) == 6
    assert max(distance_meters(a, b) for a, b in zip(sparse, dense, strict=True)) < 0.01
    assert sparse[0] == (0, 0)
    assert sparse[-1] == (0, 0.02)


def test_sampling_edge_cases():
    assert sample_route("") == ([], False)
    assert sample_route(polyline.encode([(1, 1), (1, 1)])) == ([(1, 1)], False)
    points, limited = sample_route(polyline.encode([(0, 0), (0, 1)]))
    assert len(points) == 8
    assert limited
    points, _ = sample_route(polyline.encode([(0, 179.99), (0, -179.99)]))
    assert all(abs(lng) > 179 for _, lng in points)
    with pytest.raises(ValueError, match="Spacing"):
        sample_route("", spacing_meters=0)


def test_discovery_keeps_unrated_deduplicates_and_attributes(monkeypatch):
    raw = raw_place(
        attributions=[{"provider": "Museum", "providerUri": "https://museum.example"}]
    )
    post = Mock(
        return_value=Mock(
            json=lambda: {
                "places": [
                    raw,
                    raw,
                    raw_place(id="closed", businessStatus="CLOSED_PERMANENTLY"),
                    raw_place(id="bad", location={}),
                ]
            }
        )
    )
    monkeypatch.setattr(requests, "post", post)
    result = find_places("key", [(48.85, 2.35)] * 2, {"culture": 5})
    assert result.attempted == 1
    assert result.failed == 0
    assert len(result.places) == 1
    assert result.places[0]["rating"] is None
    assert result.places[0]["attributions"][0]["provider"] == "Museum"
    assert post.call_args.kwargs["json"]["includedTypes"] == ["museum", "art_gallery"]


def test_failures_are_distinct_from_no_places(monkeypatch):
    def post(url, **kwargs):
        lat = kwargs["json"]["locationRestriction"]["circle"]["center"]["latitude"]
        if lat == 1:
            raise requests.Timeout
        return Mock(json=lambda: {"places": []})

    monkeypatch.setattr(requests, "post", post)
    result = find_places("key", [(1, 1), (2, 2)], {"parks": 5})
    assert result.attempted == 2
    assert result.failed == 1
    assert not result.places
    assert find_places("key", [(2, 2)], {"parks": 5}).failed == 0


def test_resolve_and_validate_places(monkeypatch):
    post = Mock(
        return_value=Mock(
            json=lambda: {"places": [raw_place(rating=4.8, userRatingCount=50)]}
        )
    )
    monkeypatch.setattr(requests, "post", post)
    place = resolve_place("key", "Museum, Paris")
    assert place["rating"] == 4.8
    assert post.call_args.kwargs["json"] == {
        "textQuery": "Museum, Paris",
        "pageSize": 1,
    }
    with pytest.raises(ValueError, match="Enter"):
        resolve_place("key", " ")
    post.return_value.json = lambda: {"places": []}
    with pytest.raises(ValueError, match="resolve"):
        resolve_place("key", "missing")
    post.return_value.json = lambda: {"places": "invalid"}
    assert find_places("key", [(0, 0)], {"food": 5}).failed == 1
    assert find_places("key", [(0, 0)], {"food": 0}).attempted == 0
    with pytest.raises(ValueError, match="eight"):
        find_places("key", [(0, 0)] * 9, {"food": 5})
    with pytest.raises(ValueError, match="radius"):
        find_places("key", [(0, 0)], {"food": 5}, radius_meters=6000)
