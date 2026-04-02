"""
Application settings and configuration.
"""

import streamlit as st

def init_page_config():
    """Initialize Streamlit page configuration."""
    st.set_page_config(
        page_title="Algeria Renewable Energy Forecast",
        page_icon="🌞",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Map Settings
DEFAULT_MAP_CENTER = [28.5, 2.5]
DEFAULT_ZOOM = 5
MAP_TILES = 'cartodbdark_matter'
MAP_ATTR = 'Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'

# Chart Settings
CHART_HEIGHT = 400
