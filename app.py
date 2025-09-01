import streamlit as st
import openai
from streamlit_folium import st_folium

from modules.route_finder import get_baseline_route, get_alternative_routes
from modules.route_scorer import score_routes
from modules.map_builder import create_route_map, display_route_card
from config.settings import get_google_maps_api_key, get_openai_api_key


st.set_page_config(page_title="Diversion", page_icon="🛤️", layout="wide")


def main():
    st.title("🛤️ Diversion")
    st.subheader("Find the scenic route")
    
    # API Key configuration in sidebar
    st.sidebar.header("🔑 API Configuration")
    
    # Check for keys in session state or environment
    google_maps_key = get_google_maps_api_key()
    openai_key = get_openai_api_key()
    
    # If no keys found, show input fields
    if not google_maps_key:
        google_maps_key = st.sidebar.text_input(
            "Google Maps API Key", 
            type="password",
            help="Get one at: https://console.cloud.google.com/google/maps-apis"
        )
        if google_maps_key:
            st.session_state['google_maps_api_key'] = google_maps_key
    else:
        st.sidebar.success("✅ Google Maps API key configured")
    
    if not openai_key:
        openai_key = st.sidebar.text_input(
            "OpenAI API Key", 
            type="password",
            help="Get one at: https://platform.openai.com/api-keys"
        )
        if openai_key:
            st.session_state['openai_api_key'] = openai_key
    else:
        st.sidebar.success("✅ OpenAI API key configured")
    
    # Initialize APIs
    if openai_key:
        openai.api_key = openai_key
    
    # Check if both keys are available
    if not google_maps_key or not openai_key:
        st.info("👈 Please enter your API keys in the sidebar to get started")
        st.write("**Required APIs:**")
        st.write("- **Google Maps**: For route finding and places data")
        st.write("- **OpenAI**: For AI-powered route explanations")
        st.write("\n**Note:** Keys are only stored for this session and are not saved.")
        return
    
    # Main input section
    col1, col2 = st.columns(2)
    with col1:
        origin = st.text_input("From", placeholder="Central Park, NYC")
    with col2:
        destination = st.text_input("To", placeholder="Brooklyn Bridge, NYC")
    
    travel_mode = st.radio("Travel mode", ["walking", "driving"], horizontal=True)
    
    # Preferences sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("What makes a route better?")
    
    preferences = {
        'scenic': st.sidebar.slider('Scenic areas', 0, 5, 3, 
                                   help="Parks, waterfront, tree-lined streets"),
        'food': st.sidebar.slider('Food & drink', 0, 5, 3,
                                 help="Cafes, restaurants, food markets"),
        'culture': st.sidebar.slider('Cultural spots', 0, 5, 2,
                                    help="Museums, galleries, bookstores"),
        'architecture': st.sidebar.slider('Interesting buildings', 0, 5, 2,
                                         help="Historic or unique architecture"),
        'walkable': st.sidebar.slider('Pedestrian-friendly', 0, 5, 4,
                                     help="Wide sidewalks, pedestrian areas")
    }
    
    # Constraints
    st.sidebar.subheader("Constraints")
    max_extra_time = st.sidebar.slider("Max extra time (%)", 0, 50, 20, step=5,
                                      help="% longer than fastest route")
    
    # Find routes button
    if st.button("Find Better Routes", type="primary") and origin and destination:
        try:
            with st.spinner("Finding interesting routes..."):
                # Get baseline route
                baseline = get_baseline_route(google_maps_key, origin, destination, travel_mode)

                # Get alternatives within time constraint
                alternatives = get_alternative_routes(
                    google_maps_key,
                    origin,
                    destination,
                    travel_mode,
                    baseline['duration'],
                    max_extra_time,
                    baseline_polyline=baseline['polyline'],
                )

                # Combine and score all routes
                all_routes = [baseline] + alternatives
                if all_routes:
                    scored_routes = score_routes(all_routes, preferences, google_maps_key)
                else:
                    scored_routes = []

            # Store results so they persist after reruns
            st.session_state['scored_routes'] = scored_routes

            if not scored_routes:
                st.error("No suitable routes found within your time constraint.")

        except Exception as e:
            st.error(f"Error finding routes: {str(e)}")
            st.write("Please check your API keys and network connection.")

    # Display existing results
    if st.session_state.get('scored_routes'):
        scored_routes = st.session_state['scored_routes']
        st.subheader("Route Comparison")
        route_map = create_route_map(scored_routes)
        if route_map:
            st_folium(route_map, width=700, height=500)

        st.subheader("Route Options")
        for i, route in enumerate(scored_routes):
            display_route_card(route, i+1)
    elif not origin or not destination:
        st.info("👆 Enter your starting point and destination to find better routes")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Powered by Google Maps, OpenAI, and lots of curiosity 🗺️")


if __name__ == "__main__":
    main()
