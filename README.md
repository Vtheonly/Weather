# Algeria Renewable Energy Forecasting Dashboard

An interactive Streamlit application for visualizing and forecasting renewable energy production (solar and wind) across Algeria's regions.

## Features

- **Interactive Map**: Folium-based map centered on Algeria with multiple layers
- **Solar Energy Forecasting**: Physics-based model using irradiance, geographic factors, and panel efficiency
- **Wind Energy Forecasting**: Turbine power curve model with seasonal and hourly variations
- **Production Zones**: Visualization of existing and planned energy projects
- **Energy Intensity Heatmap**: Spatial visualization of energy production potential
- **Regional Analysis**: Detailed statistics and forecasts for each region
- **Monthly Forecasts**: Seasonal variations in energy production

## Installation

```bash
# Navigate to the project directory
cd algeria-energy-forecast

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run algeria_energy_forecast.py
```

The application will open in your default web browser at `http://localhost:8501`

## Application Structure

```
algeria-energy-forecast/
├── algeria_energy_forecast.py   # Main application file
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Key Components

### 1. Geographic Data (`ALGERIA_REGIONS`)
- 20 Algerian regions with coordinates
- Solar and wind potential ratings
- Existing capacity and infrastructure
- Population and area statistics

### 2. Energy Projects (`ENERGY_PROJECTS`)
- Major operational and planned projects
- Capacity and status information
- Project types (solar, wind, hybrid)

### 3. Forecasting Models

#### SolarEnergyForecaster
- Solar constant: 1361 W/m²
- Panel efficiency: 20%
- Performance ratio: 75%
- Monthly irradiance factors
- Hourly production curves

#### WindEnergyForecaster
- Turbine cut-in speed: 3 m/s
- Rated speed: 12 m/s
- Cut-out speed: 25 m/s
- Seasonal wind patterns
- Hourly variation factors

### 4. Map Layers
- **Solar Potential Zones**: Green markers showing solar capacity
- **Wind Potential Zones**: Blue markers for wind resources
- **Energy Projects**: Project markers with status indicators
- **Intensity Heatmap**: Spatial energy intensity visualization
- **Production Forecast**: Forecast overlay circles

## Usage

1. **Select Month**: Choose the month for forecasting in the sidebar
2. **Toggle Layers**: Enable/disable map layers as needed
3. **Select Region**: Focus on a specific region or view all
4. **Explore Map**: Click markers for detailed information
5. **Analyze Data**: Review statistics and charts below the map

## Data Sources

The application uses simulated data based on:
- Algeria's geographic and climatic characteristics
- Actual renewable energy project locations and capacities
- Meteorological patterns for the Saharan region
- Industry-standard capacity factors

## Technical Notes

- The forecasting models are simplified but physically-based
- Actual production would require real-time meteorological data
- Capacity factors are estimated for the Algerian context
- Seasonal variations are modeled based on regional patterns

## License

This application is for educational and demonstration purposes.
