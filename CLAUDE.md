# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Diversion is a Python Streamlit application that finds scenic and interesting routes between two locations. The app goes beyond simple directions by discovering points of interest (POIs) along alternative routes and scoring them based on user preferences like scenic areas, food spots, cultural sites, and walkability.

## Development Commands

### Running the Application
```bash
streamlit run app.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
- Copy `.env.example` to `.env` and add your API keys:
  - `GOOGLE_MAPS_API_KEY` (required - get from Google Cloud Console)
  - `OPENAI_API_KEY` (required for AI route scoring - get from OpenAI Platform)

## Architecture Overview

### Core Application Flow
1. **Route Finding** (`modules/route_finder.py`): Queries Google Routes API for baseline and alternative routes
2. **POI Discovery** (`modules/poi_enricher.py`): Finds points of interest along route paths using Google Places API
3. **Route Scoring** (`modules/route_scorer.py`): Scores routes using OpenAI GPT-3.5-turbo with heuristic fallback
4. **Map Visualization** (`modules/map_builder.py`): Creates interactive Folium maps with route overlays and POI markers

### Module Structure
- `app.py`: Main Streamlit application with UI components
- `config/settings.py`: Configuration constants, API key management, and scoring parameters
- `modules/route_finder.py`: Google Routes API integration for baseline and alternative route discovery
- `modules/poi_enricher.py`: Google Places API integration for finding POIs along route segments
- `modules/route_scorer.py`: Route scoring system combining AI analysis with heuristic scoring
- `modules/map_builder.py`: Interactive map creation and route visualization
- `modules/utils.py`: Distance calculations and formatting utilities

### Key Design Patterns
- Uses Google's new Routes API v2 for route computation
- Samples route polylines to reduce API call volume while maintaining coverage
- Implements fallback scoring when OpenAI API is unavailable
- Filters POIs by rating threshold (>3.0) to ensure quality
- Modular architecture allows independent testing and development of each component

### API Dependencies
- Google Maps Routes API v2 for route finding
- Google Places API (new) for POI discovery
- OpenAI GPT-3.5-turbo for route explanation and refined scoring

### Scoring Algorithm
Routes are scored on a 1-10 scale considering:
- POI density and quality (rating threshold: 3.5+)
- User preference matching (food, culture, scenic, walkable)
- Time penalty for routes significantly longer than baseline
- AI-generated explanations when OpenAI API is available
