"""Resolve API keys from the current Streamlit session or environment."""

import os

import streamlit as st


def get_google_maps_api_key() -> str | None:
    """Return the session's Google Maps key, falling back to the environment."""
    return st.session_state.get("google_maps_api_key") or os.getenv(
        "GOOGLE_MAPS_API_KEY"
    )


def get_openai_api_key() -> str | None:
    """Return the session's OpenAI key, falling back to the environment."""
    return st.session_state.get("openai_api_key") or os.getenv("OPENAI_API_KEY")


def get_browser_maps_api_key() -> str | None:
    """Return only the separate public Maps JavaScript key."""
    return st.session_state.get("google_maps_browser_api_key") or os.getenv(
        "GOOGLE_MAPS_BROWSER_API_KEY"
    )
