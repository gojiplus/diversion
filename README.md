# Diversion 🛤️

Find scenic and interesting routes between two locations by discovering points of interest along alternative paths. Instead of just getting from A to B, find routes that pass by cafes, parks, museums, and other places that match your preferences.

https://diversion.streamlit.app/

## Features

- **Smart Route Discovery**: Finds alternative routes within your time constraints
- **POI-Based Scoring**: Discovers restaurants, parks, museums, and cultural sites along routes
- **AI-Powered Recommendations**: Uses OpenAI to explain why each route is interesting
- **Interactive Maps**: Visual route comparison with POI markers
- **Customizable Preferences**: Weight routes by scenic areas, food, culture, architecture, and walkability

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API keys**:
   - Get a Google Maps API key from [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
   - Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - Copy `.env.example` to `.env` and add your keys

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

### Streamlit Community Cloud Deployment

For public deployment without exposing your API keys, the app accepts API keys through the UI:

1. **Deploy to Streamlit Community Cloud**:
   - Connect your GitHub repository to [Streamlit Community Cloud](https://streamlit.io/cloud)
   - No environment variables needed - users enter their own API keys

2. **User provides keys**:
   - Users enter their Google Maps and OpenAI API keys in the sidebar
   - Keys are stored only for the current session
   - No keys are saved or logged

This approach protects your API costs while allowing public deployment.
