"""
UI Components for the Weather App.
"""

import folium
from folium import plugins
from streamlit_folium import st_folium
import streamlit as st
from config.data import ALGERIA_REGIONS, ENERGY_PROJECTS
from config.settings import DEFAULT_MAP_CENTER, DEFAULT_ZOOM, MAP_TILES, MAP_ATTR
from core.forecasting.solar import SolarEnergyForecaster
from core.forecasting.wind import WindEnergyForecaster


def create_base_map(center_lat=DEFAULT_MAP_CENTER[0], center_lon=DEFAULT_MAP_CENTER[1], zoom=DEFAULT_ZOOM):
    """Create the base Folium map centered on Algeria."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles=MAP_TILES,
        attr=MAP_ATTR,
        min_zoom=4,
        max_zoom=10
    )
    
    # Add alternative tile layers
    folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(m)
    
    return m


def add_algeria_regions_layer(m):
    """Add regional boundaries and markers for Algeria."""
    
    # Create feature groups for different layers
    solar_group = folium.FeatureGroup(name='Solar Potential Zones')
    wind_group = folium.FeatureGroup(name='Wind Potential Zones')
    
    for region_name, data in ALGERIA_REGIONS.items():
        # Determine color based on solar potential
        if data['solar_potential'] >= 0.95:
            solar_color = '#1a5f2a'  # Dark green - excellent
        elif data['solar_potential'] >= 0.90:
            solar_color = '#2d8a3e'  # Green - very good
        elif data['solar_potential'] >= 0.85:
            solar_color = '#5cb85c'  # Light green - good
        else:
            solar_color = '#8bc34a'  # Yellow-green - moderate
        
        # Create circle marker for solar potential
        solar_radius = data['existing_solar_mw'] / 10 + 5
        
        folium.CircleMarker(
            location=[data['lat'], data['lon']],
            radius=solar_radius,
            popup=folium.Popup(
                f"""
                <div style='width: 250px'>
                    <h4 style='color: #2d8a3e'>{region_name}</h4>
                    <p><b>Solar Potential:</b> {data['solar_potential']*100:.0f}%</p>
                    <p><b>Existing Capacity:</b> {data['existing_solar_mw']} MW</p>
                    <p><b>Area:</b> {data['area_km2']:,} km²</p>
                    <p><b>Population Density:</b> {data['population_density']} per km²</p>
                    <hr>
                    <p style='font-size: 11px'>{data['description']}</p>
                </div>
                """,
                max_width=300
            ),
            tooltip=f"{region_name} - Solar: {data['solar_potential']*100:.0f}%",
            color='#2d8a3e',
            weight=2,
            fill=True,
            fill_color=solar_color,
            fill_opacity=0.6
        ).add_to(solar_group)
        
        # Wind potential marker (smaller, offset)
        wind_radius = data['existing_wind_mw'] / 5 + 3
        
        if data['wind_potential'] >= 0.85:
            wind_color = '#1565c0'  # Dark blue - excellent
        elif data['wind_potential'] >= 0.75:
            wind_color = '#2196f3'  # Blue - very good
        elif data['wind_potential'] >= 0.65:
            wind_color = '#64b5f6'  # Light blue - good
        else:
            wind_color = '#90caf9'  # Pale blue - moderate
        
        folium.CircleMarker(
            location=[data['lat'] - 0.3, data['lon'] + 0.3],
            radius=wind_radius,
            popup=folium.Popup(
                f"""
                <div style='width: 200px'>
                    <h4 style='color: #1565c0'>{region_name} - Wind</h4>
                    <p><b>Wind Potential:</b> {data['wind_potential']*100:.0f}%</p>
                    <p><b>Existing Capacity:</b> {data['existing_wind_mw']} MW</p>
                </div>
                """,
                max_width=250
            ),
            tooltip=f"{region_name} - Wind: {data['wind_potential']*100:.0f}%",
            color='#1565c0',
            weight=1,
            fill=True,
            fill_color=wind_color,
            fill_opacity=0.5
        ).add_to(wind_group)
    
    solar_group.add_to(m)
    wind_group.add_to(m)
    
    return m


def add_energy_projects_layer(m):
    """Add markers for major energy projects."""
    
    projects_group = folium.FeatureGroup(name='Energy Projects')
    
    # Define icons and colors for different project types and statuses
    status_colors = {
        'operational': '#28a745',
        'construction': '#ffc107',
        'planned': '#17a2b8'
    }
    
    for project in ENERGY_PROJECTS:
        # Choose icon based on project type
        if project['type'] == 'solar':
            icon_name = 'sun'
            icon_color = 'orange'
        elif project['type'] == 'wind':
            icon_name = 'wind'
            icon_color = 'blue'
        else:  # hybrid
            icon_name = 'bolt'
            icon_color = 'purple'
        
        # Status badge
        status_emoji = {
            'operational': '✅',
            'construction': '🚧',
            'planned': '📋'
        }
        
        popup_content = f"""
        <div style='width: 280px'>
            <h4 style='color: {status_colors[project["status"]]}'><b>{project['name']}</b></h4>
            <p><b>Type:</b> {project['type'].capitalize()}</p>
            <p><b>Capacity:</b> {project['capacity_mw']} MW</p>
            <p><b>Status:</b> {status_emoji[project['status']]} {project['status'].capitalize()}</p>
            <p><b>Year:</b> {project['year']}</p>
        </div>
        """
        
        folium.Marker(
            location=[project['lat'], project['lon']],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{project['name']} ({project['capacity_mw']} MW)",
            icon=folium.Icon(
                icon=icon_name,
                prefix='fa',
                color=icon_color
            )
        ).add_to(projects_group)
    
    projects_group.add_to(m)
    return m


def add_heatmap_layer(m, energy_type='solar'):
    """Add a heatmap showing energy intensity across Algeria."""
    
    heat_data = []
    
    for region_name, data in ALGERIA_REGIONS.items():
        # Create multiple points around each region for better visualization
        if energy_type == 'solar':
            intensity = data['solar_potential'] * data['existing_solar_mw']
        else:
            intensity = data['wind_potential'] * data['existing_wind_mw']
        
        # Add central point
        heat_data.append([data['lat'], data['lon'], intensity])
        
        # Add surrounding points for spread effect
        for dx, dy in [(-0.5, -0.5), (-0.5, 0.5), (0.5, -0.5), (0.5, 0.5)]:
            heat_data.append([data['lat'] + dx, data['lon'] + dy, intensity * 0.5])
    
    heat_group = folium.FeatureGroup(name=f'{energy_type.capitalize()} Intensity Heatmap')
    plugins.HeatMap(
        heat_data,
        name=f'{energy_type.capitalize()} Intensity',
        min_opacity=0.3,
        max_opacity=0.8,
        radius=35,
        blur=25
    ).add_to(heat_group)
    
    heat_group.add_to(m)
    return m


def add_forecast_visualization(m, month: int, forecast_data: dict):
    """Add forecast visualization overlay to the map."""
    
    forecast_group = folium.FeatureGroup(name='Production Forecast')
    
    for region_name, data in ALGERIA_REGIONS.items():
        if region_name in forecast_data:
            region_forecast = forecast_data[region_name]
            
            # Create forecast popup
            popup_content = f"""
            <div style='width: 300px'>
                <h4 style='color: #2d8a3e'>{region_name} - {month}</h4>
                <hr>
                <p><b>☀️ Solar Forecast:</b></p>
                <ul>
                    <li>Daily: {region_forecast['solar_daily']:.1f} MWh</li>
                    <li>Monthly: {region_forecast['solar_monthly']:.1f} MWh</li>
                </ul>
                <p><b>💨 Wind Forecast:</b></p>
                <ul>
                    <li>Daily: {region_forecast['wind_daily']:.1f} MWh</li>
                    <li>Monthly: {region_forecast['wind_monthly']:.1f} MWh</li>
                </ul>
                <hr>
                <p><b>Total Monthly:</b> {region_forecast['total_monthly']:.1f} MWh</p>
            </div>
            """
            
            # Size based on total production
            radius = min(max(region_forecast['total_monthly'] / 500, 8), 30)
            
            folium.CircleMarker(
                location=[data['lat'], data['lon']],
                radius=radius,
                popup=folium.Popup(popup_content, max_width=320),
                tooltip=f"{region_name}: {region_forecast['total_monthly']:.0f} MWh/month",
                color='#ff7800',
                weight=3,
                fill=True,
                fill_color='#ffcc00',
                fill_opacity=0.4
            ).add_to(forecast_group)
    
    forecast_group.add_to(m)
    return m


def calculate_region_forecasts(month: int) -> dict:
    """Calculate energy forecasts for all regions."""
    forecasts = {}
    
    for region_name, data in ALGERIA_REGIONS.items():
        solar_forecaster = SolarEnergyForecaster(
            data['existing_solar_mw'],
            data['lat'],
            data['lon'],
            data['solar_potential']
        )
        
        wind_forecaster = WindEnergyForecaster(
            data['existing_wind_mw'],
            data['lat'],
            data['lon'],
            data['wind_potential']
        )
        
        solar_daily = solar_forecaster.calculate_daily_production(month)
        solar_monthly = solar_forecaster.calculate_monthly_production(month)
        wind_daily = wind_forecaster.calculate_daily_production(month)
        wind_monthly = wind_forecaster.calculate_monthly_production(month)
        
        forecasts[region_name] = {
            'solar_daily': solar_daily,
            'solar_monthly': solar_monthly,
            'wind_daily': wind_daily,
            'wind_monthly': wind_monthly,
            'total_monthly': solar_monthly + wind_monthly,
            'capacity_factor_solar': (solar_daily / (data['existing_solar_mw'] * 24)) * 100 if data['existing_solar_mw'] > 0 else 0,
            'capacity_factor_wind': (wind_daily / (data['existing_wind_mw'] * 24)) * 100 if data['existing_wind_mw'] > 0 else 0
        }
    
    return forecasts
