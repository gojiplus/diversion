import polyline
import requests
from typing import List, Dict, Tuple


def decode_polyline_to_points(encoded_polyline: str) -> List[Tuple[float, float]]:
    """Decode Google's polyline and sample points every ~200m"""
    coordinates = polyline.decode(encoded_polyline)
    
    # Sample points along route to avoid too many API calls
    sampled_points = []
    sample_interval = max(1, len(coordinates) // 10)
    
    for i in range(0, len(coordinates), sample_interval):
        sampled_points.append(coordinates[i])
    
    return sampled_points


def find_pois_along_route(api_key: str, route_points: List[Tuple[float, float]], 
                         preferences: Dict[str, int]) -> List[Dict]:
    """Find interesting places along the route based on user preferences"""
    
    # Map preferences to Google Places types
    poi_types = []
    if preferences.get('food', 0) > 0:
        poi_types.extend(['restaurant', 'cafe', 'bakery'])
    if preferences.get('culture', 0) > 0:
        poi_types.extend(['museum', 'art_gallery', 'library'])
    if preferences.get('scenic', 0) > 0:
        poi_types.extend(['park', 'tourist_attraction'])
    if preferences.get('architecture', 0) > 0:
        poi_types.extend(['place_of_worship', 'city_hall'])
    
    if not poi_types:
        poi_types = ['point_of_interest']
    
    all_pois = []
    search_radius = 100  # meters
    
    # Search around sampled points along the route
    for point in route_points[::2]:  # Sample every other point to reduce API calls
        try:
            url = "https://places.googleapis.com/v1/places:searchNearby"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": api_key,
                "X-Goog-FieldMask": "places.displayName,places.rating,places.types,places.priceLevel,places.location,places.userRatingCount"
            }
            
            data = {
                "includedTypes": poi_types[:3],  # Limit to first 3 types to avoid quota issues
                "maxResultCount": 10,
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": point[0],
                            "longitude": point[1]
                        },
                        "radius": search_radius
                    }
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            places_result = response.json()
            
            for place in places_result.get('places', []):
                if place.get('displayName', {}).get('text') and place.get('rating', 0) > 3.0:  # Filter low-rated places
                    poi = {
                        'name': place.get('displayName', {}).get('text'),
                        'rating': place.get('rating', 0),
                        'types': place.get('types', []),
                        'price_level': place.get('priceLevel', 0),
                        'location': {
                            'lat': place.get('location', {}).get('latitude', 0),
                            'lng': place.get('location', {}).get('longitude', 0)
                        },
                        'user_ratings_total': place.get('userRatingCount', 0)
                    }
                    all_pois.append(poi)
                    
        except Exception as e:
            continue  # Skip failed API calls
    
    # Remove duplicates based on name and return top POIs
    unique_pois = {}
    for poi in all_pois:
        if poi['name'] not in unique_pois:
            unique_pois[poi['name']] = poi
    
    # Sort by rating and limit results
    sorted_pois = sorted(unique_pois.values(), key=lambda x: x['rating'], reverse=True)
    return sorted_pois[:15]  # Limit to top 15 to control costs