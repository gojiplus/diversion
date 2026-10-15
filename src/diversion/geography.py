"""Distance-based sampling for bounded city-walk discovery."""

import itertools
import math

import polyline

from diversion.models import Point


def distance_meters(first: Point, second: Point) -> float:
    """Measure the great-circle distance between two latitude/longitude points.

    Args:
        first: First latitude and longitude pair.
        second: Second latitude and longitude pair.

    Returns:
        Distance in meters.
    """
    lat1, lat2 = math.radians(first[0]), math.radians(second[0])
    delta_lat = lat2 - lat1
    delta_lon = math.radians(second[1] - first[1])
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6_371_000 * 2 * math.asin(math.sqrt(min(1.0, haversine)))


def sample_route(
    encoded: str, spacing_meters: float = 500, max_points: int = 8
) -> tuple[list[Point], bool]:
    """Sample equal distances along a polyline, including its endpoints.

    Args:
        encoded: Google encoded polyline.
        spacing_meters: Desired maximum spacing between search centers.
        max_points: Hard cap on the number of searches.

    Returns:
        Sample points and whether the search cap widened their spacing.

    Raises:
        ValueError: The spacing or point cap is invalid.
    """
    if not math.isfinite(spacing_meters) or spacing_meters <= 0 or max_points < 2:
        raise ValueError("Spacing must be positive and the point cap at least two")
    points = polyline.decode(encoded)
    if len(points) < 2:
        return points, False
    lengths = [distance_meters(a, b) for a, b in itertools.pairwise(points)]
    total = sum(lengths)
    if total == 0:
        return points[:1], False
    desired = max(2, math.ceil(total / spacing_meters) + 1)
    count = min(desired, max_points)
    samples = [points[0]]
    segment = 0
    traversed = 0.0
    for index in range(1, count - 1):
        target = total * index / (count - 1)
        while segment < len(lengths) - 1 and traversed + lengths[segment] < target:
            traversed += lengths[segment]
            segment += 1
        fraction = (target - traversed) / lengths[segment] if lengths[segment] else 0
        start, end = points[segment], points[segment + 1]
        longitude_delta = (end[1] - start[1] + 180) % 360 - 180
        samples.append(
            (
                start[0] + fraction * (end[0] - start[0]),
                (start[1] + fraction * longitude_delta + 180) % 360 - 180,
            )
        )
    samples.append(points[-1])
    return samples, desired > max_points
