"""Typed records for city walks, places, and planning results."""

from dataclasses import dataclass, field
from typing import Literal, NotRequired, TypedDict

type Preferences = dict[str, int]
type Point = tuple[float, float]


class Location(TypedDict):
    """Latitude and longitude of a place."""

    lat: float
    lng: float


class Attribution(TypedDict):
    """A data provider attribution returned by Google Places."""

    provider: str
    uri: str


class Place(TypedDict):
    """A Google place that can be used as a routing waypoint."""

    id: str
    name: str
    types: list[str]
    location: Location
    rating: float | None
    user_ratings_total: int
    maps_uri: str
    attributions: list[Attribution]


class Route(TypedDict):
    """Walking geometry and the stops explicitly included in the route."""

    duration: float
    distance: int
    polyline: str
    stops: list[Place]
    warnings: list[str]
    kind: Literal["direct", "alternative", "sightseeing", "loop"]
    extra_minutes: NotRequired[float]
    score: NotRequired[float]
    explanation: NotRequired[str]


@dataclass(slots=True)
class Discovery:
    """Places and evidence about the completeness of their discovery."""

    places: list[Place] = field(default_factory=list)
    attempted: int = 0
    failed: int = 0
    coverage_limited: bool = False


@dataclass(frozen=True, slots=True)
class WalkRequest:
    """A tourist's destination or round-trip walk and time constraints."""

    origin: str
    destination: str
    preferences: Preferences
    extra_minutes: int = 15
    return_to_start: bool = False
    walking_minutes: int = 60
    visit_minutes: int = 15
    required_stops: tuple[str, ...] = ()


@dataclass(slots=True)
class WalkPlan:
    """Feasible routes with their discovery status and baseline comparison."""

    request: WalkRequest
    routes: list[Route]
    discovery: Discovery
    baseline_seconds: float | None = None
    failed_candidates: int = 0
    shortest_over_budget_minutes: float | None = None
