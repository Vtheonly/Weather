"""
Main Dashboard UI Layout.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime
import requests
import os

from config.data import ALGERIA_REGIONS
from ui.map_components import (
    create_base_map, 
    add_algeria_regions_layer, 
    add_energy_projects_layer, 
    add_heatmap_layer,
    calculate_region_forecasts
)
from ui.charts import create_monthly_chart_data
from ui.fault_detection_page import render_fault_detection_page
from core.simulation.generator import SolarDataGenerator, WindDataGenerator

# API URL
API_URL = os.getenv("API_URL", "http://api:8000")


def get_solar_predictions(df):
    """
    Call the Backend API for Solar AI predictions.
    """
    try:
        url = f"{API_URL}/api/v1/ai/solar/predict"
        
        # Prepare points
        points = []
        for _, row in df.iterrows():
            points.append({
                "ghi": float(row['ghi']),
                "temp": float(row['temp']),
                "humidity": float(row['humidity']),
                "wind_speed": float(row['wind_speed']),
                "hour": int(row['timestamp'].hour)
            })
            
        payload = {"points": points}
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()['predictions_kw']
        else:
            st.error(f"Solar AI Error ({response.status_code}): {response.text}")
    except Exception as e:
        st.error(f"Solar AI Connection Error: {e}")
    
    return None


def get_wind_forecast(history_df):
    """
    Call the Backend API for Wind AI 48h forecast.
    """
    try:
        url = f"{API_URL}/api/v1/ai/wind/predict"
        
        # Prepare history records
        # Filter for required columns if possible, but pydantic model in API handles extra?
        # Actually, let's keep only what's needed.
        cols = ["Wspd", "Wdir", "Etmp", "Itmp", "Ndir", "Pab1", "Pab2", "Pab3", "Prtv", "Patv"]
        history = history_df[cols].to_dict(orient='records')
        
        payload = {"history": history}
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            return np.array(response.json()['forecast'])
        else:
            st.error(f"Wind AI Error ({response.status_code}): {response.text}")
    except Exception as e:
        st.error(f"Wind AI Connection Error: {e}")
    
    return None


def render_dashboard():
    """Render the main dashboard."""
    
    # Application header
    st.title("🇩🇿 Algeria Renewable Energy Forecasting Dashboard")
    st.markdown("""
    **Interactive map and forecasting system for solar and wind energy production across Algeria**
    """)
    
    # Sidebar
    st.sidebar.header("⚙️ Dashboard Controls")
    
    # Navigation
    page = st.sidebar.radio("Navigation", ["Map Overview", "Solar AI Simulator", "Wind AI Simulator", "Fault Detector"])
    
    if page == "Map Overview":
        render_map_page()
    elif page == "Solar AI Simulator":
        render_simulation_page()
    elif page == "Wind AI Simulator":
        render_wind_simulation_page()
    else:
        render_fault_detection_page()


def render_map_page():
    """Render the main map visualization page."""
    
    # Month selector
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    current_month = datetime.now().month
    selected_month = st.sidebar.selectbox(
        "Select Month for Forecast",
        options=range(1, 13),
        format_func=lambda x: month_names[x-1],
        index=current_month - 1
    )
    
    # Map layer controls
    st.sidebar.subheader("🗺️ Map Layers")
    show_solar = st.sidebar.checkbox("Solar Potential Zones", value=True)
    show_wind = st.sidebar.checkbox("Wind Potential Zones", value=True)
    show_projects = st.sidebar.checkbox("Energy Projects", value=True)
    show_heatmap = st.sidebar.checkbox("Intensity Heatmap", value=False)
    
    # Heatmap type
    if show_heatmap:
        heatmap_type = st.sidebar.radio(
            "Heatmap Type",
            options=['solar', 'wind'],
            format_func=lambda x: x.capitalize()
        )
    else:
        heatmap_type = 'solar'
    
    # Region selector
    st.sidebar.subheader("📍 Region Focus")
    region_list = list(ALGERIA_REGIONS.keys())
    selected_region = st.sidebar.selectbox(
        "Select a Region",
        options=['All Regions'] + region_list
    )
    
    # Calculate forecasts
    with st.spinner("Calculating energy forecasts..."):
        forecasts = calculate_region_forecasts(selected_month)
    
    st.subheader(f"📍 Interactive Energy Map - {month_names[selected_month-1]}")
    
    # Create Layout (Map + Stats)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Map Logic
        if selected_region != 'All Regions':
            region_data = ALGERIA_REGIONS[selected_region]
            m = create_base_map(
                center_lat=region_data['lat'], 
                center_lon=region_data['lon'], 
                zoom=7
            )
        else:
            m = create_base_map()
        
        if show_solar or show_wind:
            m = add_algeria_regions_layer(m)
        if show_projects:
            m = add_energy_projects_layer(m)
        if show_heatmap:
            m = add_heatmap_layer(m, heatmap_type)
        
        folium.LayerControl().add_to(m)
        st_folium(m, width=800, height=500)

    with col2:
        st.subheader("📊 Regional Statistics")
        if selected_region != 'All Regions':
            data = ALGERIA_REGIONS[selected_region]
            st.metric("Solar Potential", f"{data['solar_potential']*100:.0f}%")
            st.metric("Wind Potential", f"{data['wind_potential']*100:.0f}%")
            st.metric("Existing Solar", f"{data['existing_solar_mw']} MW")
            st.metric("Existing Wind", f"{data['existing_wind_mw']} MW")
            st.info(data['description'])
        else:
            st.info("Select a region to view specific details.")


def render_simulation_page():
    """Render the Solar AI Simulation page."""
    st.subheader("☀️ Solar AI Hybrid Engine Simulator")
    
    st.info("This module uses the XGBoost + LSTM Hybrid model (via API) to predict solar power output based on synthetic weather data.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days = st.slider("Simulation Days", 1, 30, 7)
    
    with col2:
        if st.button("Generate New Synthetic Data"):
            generator = SolarDataGenerator()
            df = generator.generate_series(days=days)
            st.session_state['sim_data'] = df
            st.success(f"Generated {len(df)} data points!")
    
    if 'sim_data' in st.session_state:
        df = st.session_state['sim_data']
        
        # Plot Weather Features
        st.subheader("1. Synthetic Weather Conditions")
        st.line_chart(df.set_index('timestamp')[['ghi', 'temp', 'wind_speed']])
        
        # Run Inference
        st.subheader("2. Hybrid Model Inference")
        
        if st.checkbox("Run Solar AI Model"):
            with st.spinner("Requesting predictions from API..."):
                preds = get_solar_predictions(df)
            
            if preds:
                df['ai_prediction'] = preds
                st.line_chart(df.set_index('timestamp')[['actual_power', 'ai_prediction']])
                mae = abs(df['actual_power'] - df['ai_prediction']).mean()
                st.metric("Model MAE (Mean Absolute Error)", f"{mae:.2f} kW")
            else:
                st.warning("Could not reach AI API. Using simulation data only.")
                st.line_chart(df.set_index('timestamp')[['theoretical_power', 'actual_power']])


def render_wind_simulation_page():
    """Render the Wind AI Simulation page."""
    st.subheader("🌬️ Wind Turbine AI Simulator")
    
    st.info("Physics-Informed Transformer model (via API) for 48-hour Wind Power Forecasting.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        days = st.slider("History Window (Days)", 2, 7, 3, key="wind_days")
        
    with col2:
        if st.button("Generate Wind Telemetry"):
            generator = WindDataGenerator()
            total_days = days + 2
            full_df = generator.generate_series(days=total_days, interval_minutes=10)
            split_idx = -288 
            
            history_df = full_df.iloc[:split_idx].copy()
            future_truth_df = full_df.iloc[split_idx:].copy()
            future_truth_df['type'] = 'Actual (Ground Truth)'
            
            st.session_state['wind_history'] = history_df
            st.session_state['wind_future_truth'] = future_truth_df
            st.session_state['wind_data'] = history_df
            st.success(f"Generated {len(history_df)} history points + {len(future_truth_df)} future validation points!")

    if 'wind_history' in st.session_state:
        df = st.session_state['wind_history']
        future_truth = st.session_state.get('wind_future_truth', None)
        
        # Prepare Data for Altair
        wind_parts = [df.copy()]
        if future_truth is not None:
            fw = future_truth.copy()
            fw['type'] = 'Future Wind (Forecast Input)'
            wind_parts.append(fw)
            
        wind_source = pd.concat(wind_parts)
        if 'type' not in wind_source.columns:
            wind_source['type'] = 'Historical Wind'
        
        power_source = df.copy()
        power_source['type'] = 'Actual (History)'
        
        st.subheader("3. AI 48-Hour Forecast & Analysis")
        st.write("Select a range on the **Wind Speed** chart to see the corresponding **Power Output** period.")
        
        forecast_df = None
        if st.button("Run AI Forecast"):
            with st.spinner("Requesting forecast from API..."):
                forecast = get_wind_forecast(df)
                
            if forecast is not None:
                last_time = df['timestamp'].iloc[-1]
                future_dates = pd.date_range(
                    start=last_time + pd.Timedelta(minutes=10), 
                    periods=288, 
                    freq='10min'
                )
                forecast_df = pd.DataFrame({
                    'timestamp': future_dates,
                    'Patv': forecast,
                    'type': 'AI Forecast'
                })
                st.success("Forecast generated via API!")
            else:
                st.error("Could not obtain forecast from API.")

        # Combine Power Data
        parts = [power_source[['timestamp', 'Patv', 'type']]]
        if forecast_df is not None:
            parts.append(forecast_df)
            if future_truth is not None:
                parts.append(future_truth[['timestamp', 'Patv', 'type']])
                
        combined_power = pd.concat(parts)
        import altair as alt

        brush = alt.selection_interval(encodings=['x'])
        
        wind_chart = alt.Chart(wind_source).mark_line().encode(
            x=alt.X('timestamp:T', axis=alt.Axis(title='Time')),
            y=alt.Y('Wspd:Q', axis=alt.Axis(title='Wind Speed (m/s)')),
            color=alt.condition(
                brush,
                alt.value('#1f77b4'),
                alt.value('lightgray')
            ),
            tooltip=['timestamp', 'Wspd', 'Wdir']
        ).properties(
            title='1. Wind Speed: History & Future (Drag here)',
            height=200,
            width='container'
        ).add_selection(brush)

        base_power = alt.Chart(combined_power).encode(
            x=alt.X('timestamp:T', axis=alt.Axis(title='Time')),
            y=alt.Y('Patv:Q', axis=alt.Axis(title='Active Power (kW)'))
        )
        
        ground_truth_layer = base_power.transform_filter(
            alt.datum.type == 'Actual (Ground Truth)'
        ).mark_line(
            color='#2ca02c',
            opacity=0.6,
            strokeDash=[2, 2]
        ).encode(tooltip=['timestamp', 'Patv', 'type'])
        
        interactive_layer = base_power.transform_filter(
            alt.datum.type != 'Actual (Ground Truth)'
        ).mark_line().encode(
            color=alt.condition(
                brush, 
                'type:N', 
                alt.value('lightgray'), 
                scale=alt.Scale(
                    domain=['Actual (History)', 'AI Forecast'], 
                    range=['#1f77b4', '#ff7f0e']
                )
            ), 
            strokeDash=alt.condition(
                alt.datum.type == 'AI Forecast',
                alt.value([5, 5]),
                alt.value([0])
            ),
            tooltip=['timestamp', 'Patv', 'type']
        )

        power_chart = (ground_truth_layer + interactive_layer).properties(
            title='2. Power Output: History -> Forecast vs Ground Truth',
            height=200,
            width='container'
        )
        
        st.altair_chart(wind_chart & power_chart, use_container_width=True)
