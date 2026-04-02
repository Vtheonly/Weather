"""
Wrapper for the Wind AI Model (Physics-Informed Transformer).
Handles model loading and inference for 48h forecasts.
"""

import os
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import streamlit as st

class WindProductionEngine:
    """
    Professional Inference Engine for Wind Power Forecasting.
    Requires: deep_physics_transformer.h5 and global_scaler.pkl.
    """
    def __init__(self, model_dir='pklh5_NN_engine/WPF_Production_Bundle'):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        
        self.physics_features = [
            "Wspd", "Wdir", "Etmp", "Itmp", "Ndir", "Pab1", "Pab2", "Pab3", "Prtv", 
            "Patv", "U", "V", "Energy_Flux", "Momentum"
        ]
        self.target_idx = self.physics_features.index("Patv")
        
        self._load_models()

    def _load_models(self):
        """Load pretrained Keras model and Scaler."""
        try:
            model_path = os.path.join(self.model_dir, 'deep_physics_transformer.h5')
            scaler_path = os.path.join(self.model_dir, 'global_scaler.pkl')
            
            if os.path.exists(model_path):
                # Load Keras model without compiling to avoid optimizer warnings/issues in inference
                self.model = tf.keras.models.load_model(model_path, compile=False)
            else:
                print(f"Wind Model not found at {model_path}")
                
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            else:
                print(f"Wind Scaler not found at {scaler_path}")
                
        except Exception as e:
            print(f"Error loading Wind AI models: {e}")

    def apply_physics(self, df):
        """Minimalist Physics Engine for Inference."""
        df = df.copy()
        # Ensure Patv is non-negative
        if 'Patv' in df.columns:
            df['Patv'] = df['Patv'].clip(lower=0)
            
        # Calculate U/V components from Wind Speed and Direction
        wdir_rad = np.deg2rad(df['Wdir'])
        df['U'] = df['Wspd'] * np.cos(wdir_rad)
        df['V'] = df['Wspd'] * np.sin(wdir_rad)
        
        # Energy Flux ~ Wind Speed cubed
        df['Energy_Flux'] = np.power(df['Wspd'], 3)
        
        # Momentum ~ Rate of change of wind speed
        df['Momentum'] = df['Wspd'].diff().fillna(0)
        
        return df.ffill().bfill()

    def predict_48h(self, history_df):
        """
        Run inference to predict the next 48 hours.
        Input: DataFrame with at least 144 rows (24 hours @ 10min).
        Output: Array of values (48 hour forecast).
        """
        if not self.model or not self.scaler:
            return None
            
        # Ensure we have the required columns
        required = ["Wspd", "Wdir", "Etmp", "Itmp", "Ndir", "Pab1", "Pab2", "Pab3", "Prtv", "Patv"]
        missing = [c for c in required if c not in history_df.columns]
        if missing:
            print(f"Missing columns for Wind AI: {missing}")
            return None
            
        # Take the last 144 steps (24 hours)
        if len(history_df) < 144:
            print(f"Insufficient history: {len(history_df)} rows. Need 144.")
            return None
            
        df_slice = history_df.tail(144).copy()
        
        # 1. Apply Physics
        df_phys = self.apply_physics(df_slice)
        
        # 2. Scale
        try:
            scaled_data = self.scaler.transform(df_phys[self.physics_features])
        except ValueError as e:
            print(f"Scaling error: {e}")
            return None
        
        # 3. Prepare Tensors
        x_hist = np.expand_dims(scaled_data, axis=0).astype(np.float32)
        x_anchor = np.array([[scaled_data[-1, self.target_idx]]], dtype=np.float32)
        
        # 4. Run AI Inference
        # Returns scaled delta reconstruction
        prediction_scaled = self.model.predict({
            "history_in": x_hist,
            "anchor_in": x_anchor
        }, verbose=0)
        
        # 5. Inverse Scale to Real kW
        p_min = self.scaler.min_[self.target_idx]
        p_scale = self.scaler.scale_[self.target_idx]
        
        real_forecast = (prediction_scaled[0] - p_min) / p_scale
        
        return real_forecast
