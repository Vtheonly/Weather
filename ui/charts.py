"""
Charting logic for the Weather App.
"""
from config.data import ALGERIA_REGIONS
from core.forecasting.solar import SolarEnergyForecaster
from core.forecasting.wind import WindEnergyForecaster


def create_monthly_chart_data():
    """Generate chart data for the selected month."""
    
    months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    solar_data = []
    wind_data = []
    labels = []
    
    for i in range(12):
        labels.append(months_short[i])
        
        # Calculate total production for all regions
        total_solar = 0
        total_wind = 0
        
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
            
            total_solar += solar_forecaster.calculate_monthly_production(i + 1)
            total_wind += wind_forecaster.calculate_monthly_production(i + 1)
        
        solar_data.append(total_solar / 1000)  # Convert to GWh
        wind_data.append(total_wind / 1000)
    
    return labels, solar_data, wind_data
