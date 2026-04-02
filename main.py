"""
Algeria Renewable Energy Forecasting Application.
Main entry point.
"""

import streamlit as st
from config.settings import init_page_config
from ui.dashboard import render_dashboard

def main():
    """Run the application."""
    init_page_config()
    render_dashboard()

if __name__ == "__main__":
    main()
