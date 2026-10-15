"""Offline fixtures shared by the routing and UI tests."""

from collections.abc import Iterator
from unittest.mock import Mock

import polyline
import pytest
import requests
from openai import OpenAI

from diversion.models import Place, Route


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    for key in ("GOOGLE_MAPS_API_KEY", "GOOGLE_MAPS_BROWSER_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(
        requests.sessions.Session,
        "request",
        Mock(side_effect=AssertionError("Unexpected HTTP request")),
    )
    monkeypatch.setattr(
        OpenAI, "request", Mock(side_effect=AssertionError("Unexpected OpenAI request"))
    )


@pytest.fixture
def route() -> Route:
    return {
        "duration": 600,
        "distance": 1000,
        "polyline": polyline.encode([(40.7, -74.0), (40.71, -73.99)]),
        "stops": [],
        "warnings": [],
        "kind": "direct",
    }


@pytest.fixture
def place() -> Place:
    return {
        "id": "cafe",
        "name": "Garden Cafe",
        "rating": 4.5,
        "types": ["cafe"],
        "location": {"lat": 40.7, "lng": -74.0},
        "user_ratings_total": 20,
        "maps_uri": "https://www.google.com/maps/search/?api=1&query=Garden+Cafe",
        "attributions": [],
    }


@pytest.fixture
def client() -> Iterator[OpenAI]:
    with OpenAI(api_key="test-key", max_retries=0) as api_client:
        yield api_client
