import openai
import requests
from typing import Dict, List, Any
from .poi_enricher import decode_polyline_to_points, find_pois_along_route


def calculate_heuristic_score(route: Dict, pois: List[Dict], preferences: Dict[str, int]) -> float:
    """Simple heuristic scoring as fallback"""
    
    base_score = 5.0
    
    # POI density bonus
    poi_bonus = min(2.0, len(pois) * 0.1)
    
    # Quality bonus based on average rating
    quality_bonus = 0
    if pois:
        avg_rating = sum(poi.get('rating', 0) for poi in pois) / len(pois)
        quality_bonus = max(0, avg_rating - 3.5) * 0.5
    
    # Preference matching bonus
    preference_bonus = 0
    preference_weights = {
        'restaurant': preferences.get('food', 0),
        'cafe': preferences.get('food', 0),
        'bakery': preferences.get('food', 0),
        'museum': preferences.get('culture', 0),
        'art_gallery': preferences.get('culture', 0),
        'library': preferences.get('culture', 0),
        'park': preferences.get('scenic', 0),
        'tourist_attraction': preferences.get('scenic', 0),
        'place_of_worship': preferences.get('architecture', 0),
        'city_hall': preferences.get('architecture', 0)
    }
    
    for poi in pois:
        for poi_type in poi.get('types', []):
            if poi_type in preference_weights:
                preference_bonus += preference_weights[poi_type] * 0.1
    
    # Time penalty for routes that are much longer
    time_penalty = max(0, route.get('extra_time_percent', 0) - 10) * 0.05
    
    final_score = base_score + poi_bonus + quality_bonus + preference_bonus - time_penalty
    return min(10.0, max(1.0, final_score))


def score_with_openai(route: Dict, pois: List[Dict], preferences: Dict[str, int]) -> Dict[str, Any]:
    """Get AI explanation and refined score"""
    if not pois:
        heuristic_score = calculate_heuristic_score(route, pois, preferences)
        explanation = "No notable places were found along this route."
        if route.get('extra_time_percent', 0) > 0:
            explanation += f" Takes {route['extra_time_percent']:.0f}% extra time."
        return {
            'score': heuristic_score,
            'explanation': explanation,
            'method': 'heuristic'
        }

    # Build context for AI using real POIs only
    poi_summary = []
    for poi in pois[:8]:  # Limit to top 8 to stay within token limits
        rating_text = f"({poi.get('rating', 'N/A')}⭐)" if poi.get('rating') else ""
        poi_summary.append(f"- {poi['name']} {rating_text}")
    
    active_prefs = [k for k, v in preferences.items() if v > 3]
    
    prompt = f"""You are a local guide helping someone find an interesting route.

Route info:
- Extra time: {route.get('extra_time_percent', 0):.1f}% longer than fastest route
- Places along the way:
{chr(10).join(poi_summary)}

User preferences (they care most about): {', '.join(active_prefs) if active_prefs else 'general exploration'}

Use only the places listed above and do not invent new locations.
Rate this route 1-10 for "interestingness" and write 2-3 sentences explaining why someone should (or shouldn't) take this path. Be conversational and specific about what makes it special.

Format your response as:
Score: X/10
Explanation: [your explanation]"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Parse response
        lines = content.split('\n')
        score_line = next((line for line in lines if 'Score:' in line), '')
        explanation_line = next((line for line in lines if 'Explanation:' in line), '')
        
        explanation = explanation_line.replace('Explanation:', '').strip() if explanation_line else "Interesting route with good options along the way."
        
        # Extract numeric score
        try:
            score_text = score_line.split('/')[0].split(':')[1].strip()
            ai_score = float(score_text)
        except:
            ai_score = calculate_heuristic_score(route, pois, preferences)
        
        return {
            'score': ai_score,
            'explanation': explanation,
            'method': 'ai'
        }
        
    except Exception as e:
        # Fallback to heuristic
        heuristic_score = calculate_heuristic_score(route, pois, preferences)
        explanation = f"Route has {len(pois)} interesting places nearby."
        if route.get('extra_time_percent', 0) > 0:
            explanation += f" Takes {route['extra_time_percent']:.0f}% extra time."
        
        return {
            'score': heuristic_score,
            'explanation': explanation,
            'method': 'heuristic'
        }


def score_routes(routes: List[Dict], preferences: Dict[str, int], api_key: str) -> List[Dict]:
    """Score all routes and return ranked list"""
    
    scored_routes = []
    
    for route in routes:
        # Get POIs along route
        route_points = decode_polyline_to_points(route['polyline'])
        pois = find_pois_along_route(api_key, route_points, preferences)
        
        # Score the route
        scoring_result = score_with_openai(route, pois, preferences)
        
        # Combine everything
        route['pois'] = pois
        route['score'] = scoring_result['score']
        route['explanation'] = scoring_result['explanation']
        route['scoring_method'] = scoring_result['method']
        
        scored_routes.append(route)
    
    # Sort by score (highest first)
    return sorted(scored_routes, key=lambda r: r['score'], reverse=True)
