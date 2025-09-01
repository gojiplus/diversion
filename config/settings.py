import os
from dotenv import load_dotenv

load_dotenv()

# API Keys - Can be set in .env file for local dev or passed via session state
def get_google_maps_api_key():
    """Get Google Maps API key from session state or environment"""
    import streamlit as st
    return st.session_state.get('google_maps_api_key') or os.getenv('GOOGLE_MAPS_API_KEY')

def get_openai_api_key():
    """Get OpenAI API key from session state or environment"""
    import streamlit as st
    return st.session_state.get('openai_api_key') or os.getenv('OPENAI_API_KEY')

# Fallback for legacy usage
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# App settings
DEFAULT_SEARCH_RADIUS = 100  # meters
MAX_POIS_PER_ROUTE = 15
MAX_ROUTES_TO_SCORE = 4
DEFAULT_MAX_EXTRA_TIME = 20  # percent

# POI type mappings
POI_TYPE_MAPPING = {
    'food': ['restaurant', 'cafe', 'bakery', 'meal_takeaway'],
    'culture': ['museum', 'art_gallery', 'library', 'book_store'],
    'scenic': ['park', 'tourist_attraction', 'natural_feature'],
    'architecture': ['place_of_worship', 'city_hall', 'courthouse'],
    'walkable': ['pedestrian_street', 'plaza']
}

# Scoring weights
SCORING_WEIGHTS = {
    'poi_density': 0.1,
    'quality_threshold': 3.5,
    'quality_bonus': 0.5,
    'preference_bonus': 0.1,
    'time_penalty': 0.05
}