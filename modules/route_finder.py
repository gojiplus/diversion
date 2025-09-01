import requests
import os
from typing import List, Dict, Any


def get_baseline_route(api_key: str, origin: str, destination: str, mode: str) -> Dict:
    """Get the fastest route as baseline for comparison"""
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps"
    }
    
    travel_mode_map = {"driving": "DRIVE", "walking": "WALK", "cycling": "BICYCLE", "transit": "TRANSIT"}
    
    data = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": travel_mode_map.get(mode, "DRIVE"),
        "computeAlternativeRoutes": False
    }
    
    response = requests.post(url, json=data, headers=headers)
    directions = response.json()
    
    if 'routes' not in directions or not directions['routes']:
        raise ValueError("No route found")
    
    route = directions['routes'][0]
    duration_seconds = int(route['duration'].rstrip('s'))
    distance_meters = route['distanceMeters']
    
    return {
        'duration': duration_seconds,
        'distance': distance_meters,
        'polyline': route['polyline']['encodedPolyline'],
        'steps': route.get('legs', [{}])[0].get('steps', []),
        'type': 'fastest',
        'duration_text': f"{duration_seconds // 60} min",
        'distance_text': f"{distance_meters / 1000:.1f} km" if distance_meters >= 1000 else f"{distance_meters} m"
    }


def get_alternative_routes(api_key: str, origin: str, destination: str, mode: str, 
                         baseline_duration: int, max_extra_percent: int) -> List[Dict]:
    """Get alternative routes within time constraints"""
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps"
    }
    
    travel_mode_map = {"driving": "DRIVE", "walking": "WALK", "cycling": "BICYCLE", "transit": "TRANSIT"}
    
    data = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": travel_mode_map.get(mode, "DRIVE"),
        "computeAlternativeRoutes": True,
        "routeModifiers": {
            "avoidTolls": mode == "driving"
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    directions = response.json()
    
    max_duration = baseline_duration * (1 + max_extra_percent / 100)
    viable_routes = []
    
    if 'routes' not in directions:
        return viable_routes
    
    for route in directions['routes'][1:]:  # Skip first route (usually same as baseline)
        duration_seconds = int(route['duration'].rstrip('s'))
        if duration_seconds <= max_duration:
            extra_time_percent = ((duration_seconds - baseline_duration) / baseline_duration) * 100
            distance_meters = route['distanceMeters']
            viable_routes.append({
                'duration': duration_seconds,
                'distance': distance_meters,
                'polyline': route['polyline']['encodedPolyline'],
                'steps': route.get('legs', [{}])[0].get('steps', []),
                'type': 'alternative',
                'extra_time_percent': extra_time_percent,
                'duration_text': f"{duration_seconds // 60} min",
                'distance_text': f"{distance_meters / 1000:.1f} km" if distance_meters >= 1000 else f"{distance_meters} m"
            })
    
    return viable_routes[:3]