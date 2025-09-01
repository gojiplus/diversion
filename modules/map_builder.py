import folium
import polyline
import googlemaps
import streamlit as st
from typing import List, Dict


def create_route_map(routes: List[Dict]) -> folium.Map:
    """Create a Folium map showing all routes with different colors"""
    
    if not routes:
        return None
    
    # Get center point from first route
    first_route_coords = polyline.decode(routes[0]['polyline'])
    center_lat = sum(coord[0] for coord in first_route_coords) / len(first_route_coords)
    center_lng = sum(coord[1] for coord in first_route_coords) / len(first_route_coords)
    
    # Create map
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
    
    # Colors for different routes
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    
    for i, route in enumerate(routes):
        route_coords = polyline.decode(route['polyline'])
        color = colors[i % len(colors)]
        
        # Add route line
        route_label = f"Route {i+1}"
        if route['type'] == 'fastest':
            route_label += " (Fastest)"
        route_label += f" - Score: {route.get('score', 0):.1f}/10"
        
        folium.PolyLine(
            route_coords,
            color=color,
            weight=4,
            opacity=0.8,
            popup=route_label
        ).add_to(m)
        
        # Add POI markers
        for poi in route.get('pois', [])[:5]:  # Show top 5 POIs per route
            folium.Marker(
                location=[poi['location']['lat'], poi['location']['lng']],
                popup=f"{poi['name']}<br>Rating: {poi.get('rating', 'N/A')}⭐",
                icon=folium.Icon(color='lightgreen', icon='info-sign'),
                tooltip=poi['name']
            ).add_to(m)
    
    # Add start and end markers
    start_coords = polyline.decode(routes[0]['polyline'])[0]
    end_coords = polyline.decode(routes[0]['polyline'])[-1]
    
    folium.Marker(
        location=start_coords,
        popup="Start",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)
    
    folium.Marker(
        location=end_coords,
        popup="End",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)
    
    return m


def display_route_card(route: Dict, route_number: int):
    """Display a route information card"""
    
    # Determine route type display
    route_type = ""
    if route['type'] == 'fastest':
        route_type = "⚡ Fastest Route"
    else:
        route_type = f"🎯 Alternative (+{route.get('extra_time_percent', 0):.0f}% time)"
    
    # Create expandable card
    with st.expander(f"**Route {route_number}** - Score: {route.get('score', 0):.1f}/10 - {route_type}"):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Duration:** {route.get('duration_text', 'N/A')}")
            st.write(f"**Distance:** {route.get('distance_text', 'N/A')}")
            if route.get('extra_time_percent', 0) > 0:
                st.write(f"**Extra time:** +{route['extra_time_percent']:.0f}%")
        
        with col2:
            st.write(f"**Score:** {route.get('score', 0):.1f}/10")
            st.write(f"**POIs found:** {len(route.get('pois', []))}")
        
        # Route explanation
        if route.get('explanation'):
            st.write(f"**Why this route:** {route['explanation']}")
        
        # Show interesting places
        pois = route.get('pois', [])
        if pois:
            st.write("**Interesting places along the way:**")
            for poi in pois[:5]:  # Show top 5
                rating_text = f" ({poi.get('rating', 'N/A')}⭐)" if poi.get('rating') else ""
                st.write(f"• {poi['name']}{rating_text}")
        
        # Technical details
        with st.expander("Technical details"):
            st.write(f"Scoring method: {route.get('scoring_method', 'unknown')}")
            st.write(f"Total POIs: {len(pois)}")
            if pois:
                avg_rating = sum(poi.get('rating', 0) for poi in pois if poi.get('rating')) / len([p for p in pois if p.get('rating')])
                st.write(f"Average POI rating: {avg_rating:.1f}⭐")