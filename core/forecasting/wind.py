"""
Wind Energy Forecasting Module.
"""
import random

class WindEnergyForecaster:
    """
    Wind energy production forecasting model for Algeria.
    Uses wind speed patterns, turbine characteristics, and geographic factors.
    """
    
    # Wind turbine parameters
    CUT_IN_SPEED = 3.0      # m/s
    RATED_SPEED = 12.0      # m/s
    CUT_OUT_SPEED = 25.0    # m/s
    
    # Monthly wind factors for Algeria
    MONTHLY_WIND_FACTORS = {
        1: 1.15,   # January (windier)
        2: 1.12,   # February
        3: 1.08,   # March
        4: 0.95,   # April
        5: 0.85,   # May
        6: 0.80,   # June (calmer)
        7: 0.78,   # July
        8: 0.82,   # August
        9: 0.90,   # September
        10: 1.05,  # October
        11: 1.10,  # November
        12: 1.18   # December (windiest)
    }
    
    def __init__(self, capacity_mw: float, lat: float, lon: float, wind_potential: float):
        self.capacity_mw = capacity_mw
        self.lat = lat
        self.lon = lon
        self.wind_potential = wind_potential
        
    def calculate_power_output(self, wind_speed: float) -> float:
        """Calculate power output based on wind speed using turbine power curve."""
        if wind_speed < self.CUT_IN_SPEED or wind_speed > self.CUT_OUT_SPEED:
            return 0.0
        elif wind_speed >= self.RATED_SPEED:
            return self.capacity_mw
        else:
            # Cubic relationship between cut-in and rated speed
            ratio = (wind_speed - self.CUT_IN_SPEED) / (self.RATED_SPEED - self.CUT_IN_SPEED)
            return self.capacity_mw * (ratio ** 3)
    
    def calculate_hourly_production(self, hour: int, month: int) -> float:
        """Calculate wind production for a specific hour and month."""
        # Base wind speed (typical average for Saharan regions)
        base_wind_speed = 6.5  # m/s
        
        # Hourly variation (windier at night and early morning in Sahara)
        hour_factors = {
            0: 1.20, 1: 1.22, 2: 1.25, 3: 1.23, 4: 1.20, 5: 1.15,
            6: 1.10, 7: 1.05, 8: 0.98, 9: 0.92, 10: 0.88, 11: 0.85,
            12: 0.82, 13: 0.80, 14: 0.82, 15: 0.85, 16: 0.90, 17: 0.95,
            18: 1.00, 19: 1.08, 20: 1.12, 21: 1.15, 22: 1.18, 23: 1.20
        }
        
        wind_speed = base_wind_speed * hour_factors[hour] * self.MONTHLY_WIND_FACTORS[month] * self.wind_potential
        
        # Add some realistic variation
        variation = random.uniform(0.85, 1.15)
        wind_speed *= variation
        
        return self.calculate_power_output(wind_speed)
    
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
