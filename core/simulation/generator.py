"""
Synthetic Data Generator for Solar AI Hybrid Engine.
Generates realistic weather and power time-series data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

class SolarDataGenerator:
    """
    Generates synthetic dataset for Solar AI training and inference.
    Features: ghi, temp, humidity, wind_speed, and actual power output with residuals.
    """
    
    def __init__(self, lat=32.0, lon=3.0, capacity_kw=100.0):
        self.lat = lat
        self.lon = lon
        self.capacity_kw = capacity_kw

    def generate_series(self, days=7, interval_minutes=15):
        """Generate a time-series DataFrame."""
        
        # Time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        freq = f'{interval_minutes}min'
        
        dates = pd.date_range(start=start_time, end=end_time, freq=freq)
        df = pd.DataFrame({'timestamp': dates})
        
        # 1. Solar Geometry & GHI (Simplified)
        df['hour'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60.0
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        
        # Declination angle
        df['declination'] = 23.45 * np.sin(np.radians(360/365 * (df['day_of_year'] - 81)))
        
        # Hour angle
        df['hour_angle'] = 15 * (df['hour'] - 12)
        
        # Solar Elevation (simplified)
        lat_rad = math.radians(self.lat)
        dec_rad = np.radians(df['declination'])
        ha_rad = np.radians(df['hour_angle'])
        
        df['elevation'] = np.degrees(np.arcsin(
            np.sin(lat_rad) * np.sin(dec_rad) + 
            np.cos(lat_rad) * np.cos(dec_rad) * np.cos(ha_rad)
        ))
        
        # GHI Generation (Clear Sky + Cloud Noise)
        df['ghi_clear'] = 1000 * np.sin(np.radians(df['elevation']))
        df.loc[df['ghi_clear'] < 0, 'ghi_clear'] = 0
        
        # Add random cloud cover noise
        noise = np.random.beta(a=2, b=5, size=len(df))  # Cloudiness distribution
        df['cloud_factor'] = 1 - (noise * 0.8) # 1 = clear, 0.2 = heavy clouds
        
        df['ghi'] = df['ghi_clear'] * df['cloud_factor']
        
        # 2. Temperature (Correlated with GHI + Lag)
        # Base temp curve (diurnal) + GHI heating + seasonal trend
        df['temp_base'] = 20 - 5 * np.cos(np.radians(15 * (df['hour'] - 4))) # Min at 4AM
        df['temp'] = df['temp_base'] + (df['ghi'] / 100) + np.random.normal(0, 1, len(df))
        
        # 3. Humidity (Inverse to Temp)
        df['humidity'] = 80 - (df['temp'] * 1.5) + np.random.normal(0, 5, len(df))
        df['humidity'] = df['humidity'].clip(10, 100)
        
        # 4. Wind Speed (Weibull / Random Walk)
        wind_noise = np.random.weibull(2, len(df)) * 3
        df['wind_speed'] = 3 + wind_noise
        
        # 5. Feature Engineering (Cyclic Time)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # 6. Power Simulation (The "True" Value we want to predict)
        # Efficiency drops with temp (approx -0.4% per degree over 25C)
        temp_coeff = -0.004
        df['eff_factor'] = 1 + temp_coeff * (df['temp'] - 25).clip(0)
        
        # Base Power = GHI * Area * Efficiency
        # Assume 1kW ~ 5-6 m2 panel area approx.
        # Simple proxy: Power (kW) = GHI (W/m2) / 1000 * Capacity * Efficiency
        df['theoretical_power'] = (df['ghi'] / 1000) * self.capacity_kw * 0.85 * df['eff_factor']
        
        # Add System Anomalies / Efficiency Drops for LSTM to catch
        df['actual_power'] = df['theoretical_power'] * (1 - np.random.uniform(0, 0.05, len(df)))
        
        # 7. Model Predictions (Simulated XGBoost Output)
        # XGBoost is "good" but misses the specific recent efficiency drops
        df['xgb_pred'] = df['theoretical_power'] * (1 + np.random.normal(0, 0.02, len(df)))
        
        # 8. Residuals (Input for LSTM)
        # Residual = Actual - XGB Prediction
        df['residual'] = df['actual_power'] - df['xgb_pred']
        
        # Clean up
        final_cols = ['timestamp', 'ghi', 'temp', 'humidity', 'wind_speed', 
                      'hour_sin', 'hour_cos', 'actual_power', 'xgb_pred', 'residual']
        
        return df[final_cols].reset_index(drop=True)

    def get_lstm_window(self, df, index):
        """Extract the last 24 residuals for the LSTM."""
        if index < 24:
            return None
        
        window = df['residual'].iloc[index-24:index].values
        return window.reshape(1, 24, 1)


class WindDataGenerator:
    """
    Generates synthetic telemetry for Wind Turbine AI.
    Features: Wspd, Wdir, Etmp, Itmp, Ndir, Pab1-3, Patv.
    """
    
    def __init__(self, capacity_kw=2000.0):
        self.capacity_kw = capacity_kw

    def generate_series(self, days=7, interval_minutes=10, end_time=None):
        """Generate a time-series DataFrame (10 min intervals)."""
        
        # Time range
        if end_time is None:
            end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        freq = f'{interval_minutes}min'
        
        dates = pd.date_range(start=start_time, end=end_time, freq=freq)
        df = pd.DataFrame({'timestamp': dates})
        n = len(df)
        
        # 1. Wind Speed (Weibull distributed + time correlation)
        # Base signal using random walk to simulate weather pattern
        random_walk = np.cumsum(np.random.normal(0, 0.1, n))
        rw_normalized = (random_walk - random_walk.min()) / (random_walk.max() - random_walk.min())
        
        # Scale to realistic wind speeds (3 to 20 m/s)
        df['Wspd'] = 3 + (rw_normalized * 12) + np.random.normal(0, 0.5, n)
        df['Wspd'] = df['Wspd'].clip(0, 25)
        
        # 2. Wind Direction (Slowly changing)
        # 0-360 degrees
        dir_walk = np.cumsum(np.random.normal(0, 2, n))
        df['Wdir'] = (180 + dir_walk) % 360
        
        # 3. Nacelle Direction (Tags along Wind Dir with lag)
        # Simulate yaw mechanism
        df['Ndir'] = df['Wdir'].rolling(window=3).mean().fillna(method='bfill') + np.random.normal(0, 1, n)
        
        # 4. Temperatures
        # daily cycle
        hour = df['timestamp'].dt.hour
        daily_temp = 20 - 5 * np.cos(np.radians(15 * (hour - 4)))
        df['Etmp'] = daily_temp + np.random.normal(0, 1, n)
        
        # Internal temp correlates with power/load + lag
        df['Itmp'] = df['Etmp'] + (df['Wspd'] * 0.5) + 10 + np.random.normal(0, 0.5, n)
        
        # 5. Blade Pitch Angles (Pab1, Pab2, Pab3)
        # Pitch control active above rated speed (~12 m/s)
        # Below 12 m/s, pitch is near 0 (capture max power)
        # Above 12 m/s, pitch increases to shed power
        
        df['pitch_target'] = 0.0
        mask_high_wind = df['Wspd'] > 12.0
        df.loc[mask_high_wind, 'pitch_target'] = (df.loc[mask_high_wind, 'Wspd'] - 12.0) * 2.5
        
        # Add slight variation between blades
        df['Pab1'] = df['pitch_target'] + np.random.normal(0, 0.1, n)
        df['Pab2'] = df['pitch_target'] + np.random.normal(0, 0.1, n)
        df['Pab3'] = df['pitch_target'] + np.random.normal(0, 0.1, n)
        
        # Reactive Power (Prtv) - usually correlates with Active but has grid variation
        df['Prtv'] = np.random.normal(0, 50, n)
        
        # 6. Active Power (Patv) - The Target
        # Power Curve
        cut_in = 3.0
        rated = 12.0
        cut_out = 25.0
        
        df['Patv'] = 0.0
        
        # Region 2 (Cubic)
        mask_ramp = (df['Wspd'] >= cut_in) & (df['Wspd'] < rated)
        df.loc[mask_ramp, 'Patv'] = self.capacity_kw * ((df.loc[mask_ramp, 'Wspd'] - cut_in) / (rated - cut_in)) ** 3
        
        # Region 3 (Rated)
        mask_rated = (df['Wspd'] >= rated) & (df['Wspd'] < cut_out)
        df.loc[mask_rated, 'Patv'] = self.capacity_kw
        
        # Add noise/efficiency
        df['Patv'] *= np.random.uniform(0.90, 1.0, n)
        
        return df
