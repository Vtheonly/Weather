"""
Solar Energy Forecasting Module.
"""
import math

class SolarEnergyForecaster:
    """
    Solar energy production forecasting model for Algeria.
    Uses solar irradiance data, panel efficiency, and geographic factors.
    """
    
    # Solar constant in W/m2
    SOLAR_CONSTANT = 1361  # W/m2
    
    # Average solar panel efficiency
    PANEL_EFFICIENCY = 0.20  # 20% efficiency
    
    # Performance ratio (accounting for losses)
    PERFORMANCE_RATIO = 0.75
    
    # Monthly irradiance factors for Algeria (relative to peak)
    MONTHLY_FACTORS = {
        1: 0.65,   # January
        2: 0.72,   # February
        3: 0.82,   # March
        4: 0.90,   # April
        5: 0.95,   # May
        6: 0.98,   # June (peak)
        7: 0.97,   # July
        8: 0.93,   # August
        9: 0.88,   # September
        10: 0.78,  # October
        11: 0.68,  # November
        12: 0.60   # December
    }
    
    def __init__(self, capacity_mw: float, lat: float, lon: float, solar_potential: float):
        self.capacity_mw = capacity_mw
        self.lat = lat
        self.lon = lon
        self.solar_potential = solar_potential
        
    def calculate_hourly_production(self, hour: int, month: int) -> float:
        """Calculate solar production for a specific hour and month."""
        # Solar irradiance model (simplified)
        # Peak hours typically 10:00 - 14:00
        
        if hour < 6 or hour > 19:
            return 0.0
        
        # Hourly factor (bell curve centered at noon)
        peak_hour = 12
        hour_factor = math.exp(-0.5 * ((hour - peak_hour) / 2.5) ** 2)
        
        # Monthly factor
        month_factor = self.MONTHLY_FACTORS.get(month, 0.85)
        
        # Geographic potential factor
        # Account for latitude (more sun in south)
        lat_factor = 1.0 + (30 - abs(self.lat)) * 0.01
        
        # Calculate production
        production = (
            self.capacity_mw * 
            hour_factor * 
            month_factor * 
            self.solar_potential * 
            lat_factor * 
            self.PERFORMANCE_RATIO
        )
        
        return max(0, production)
    
    def calculate_daily_production(self, month: int) -> float:
        """Calculate total daily production for a given month."""
        total = 0
        for hour in range(24):
            total += self.calculate_hourly_production(hour, month)
        return total
    
    def calculate_monthly_production(self, month: int) -> float:
        """Calculate total monthly production in MWh."""
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return self.calculate_daily_production(month) * days_in_month[month - 1]
    
    def get_annual_forecast(self) -> dict:
        """Get annual production forecast by month."""
        monthly_production = {}
        for month in range(1, 13):
            monthly_production[month] = self.calculate_monthly_production(month)
        return monthly_production
