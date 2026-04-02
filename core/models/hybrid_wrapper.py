"""
Wrapper for the Hybrid Solar AI Model (XGBoost + LSTM).
Handles model loading and inference.
"""

import torch
import torch.nn as nn
import joblib
import pandas as pd
import numpy as np
import os
import streamlit as st

# Define LSTM Architecture (Must match saved model)
class ResidualLSTM(nn.Module):
    def __init__(self, input_dim=1, hidden_dim=64, num_layers=2):
        super(ResidualLSTM, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 2) 

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :] 
        return self.fc(out)


class SolarAIHybridModel:
    """
    Hybrid Solar Power Forecasting Model.
    Stage 1: XGBoost (Physics/Weather based)
    Stage 2: LSTM (Residual correction based on recent errors)
    """

    def __init__(self, model_dir='pklh5_NN_engine/solar_ai'):
        self.model_dir = model_dir
        self.xgb_model = None
        self.lstm_model = None
        self.scaler = None
        self._load_models()

    def _load_models(self):
        """Load pretrained models from disk."""
        try:
            xgb_path = os.path.join(self.model_dir, 'hybrid_v1_xgb.pkl')
            scaler_path = os.path.join(self.model_dir, 'hybrid_v1_scaler.pkl')
            lstm_path = os.path.join(self.model_dir, 'hybrid_v1_lstm.pt')

            # Load XGBoost & Scaler
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
            
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)

            # Load LSTM
            if os.path.exists(lstm_path):
                self.lstm_model = ResidualLSTM()
                self.lstm_model.load_state_dict(torch.load(lstm_path, map_location='cpu'))
                self.lstm_model.eval()
                
        except Exception as e:
            print(f"Error loading models: {e}")
            # Fallback or error handling

    def predict(self, features_df, recent_residuals):
        """
        Run inference.
        :param features_df: DataFrame with weather features for XGBoost
        :param recent_residuals: Numpy array (1, 24, 1) for LSTM
        :return: (prediction_kw, sigma)
        """
        if not self.xgb_model or not self.lstm_model:
            return 0.0, 0.0

        # Stage 1: XGBoost
        # Ensure columns match model training
        xgb_cols = ['ghi', 'temp', 'humidity', 'wind_speed', 'hour_sin', 'hour_cos']
        try:
            steps_input = features_df[xgb_cols]
            xgb_pred = self.xgb_model.predict(steps_input)[0]
        except KeyError as e:
            print(f"Missing columns for XGBoost: {e}")
            return 0.0, 0.0

        # Stage 2: LSTM Correction
        # LSTM expects normalized residuals
        if recent_residuals is not None and self.scaler:
            # Normalize
            res_flat = recent_residuals.flatten().reshape(-1, 1)
            res_scaled = self.scaler.transform(res_flat).reshape(1, 24, 1)
            
            # Convert to Tensor
            res_tensor = torch.FloatTensor(res_scaled)
            
            # Predict correction
            with torch.no_grad():
                lstm_out = self.lstm_model(res_tensor)
                correction_scaled = lstm_out.numpy()[0][0] # Mean prediction
                sigma_scaled = lstm_out.numpy()[0][1]      # Uncertainty
                
                # Inverse transform (approximate, since scaler was fitted on residuals)
                # We assume scaler is min-max or standard. 
                # For simplicity in this wrapper, we apply specific logic if needed.
                # Here we just use the raw output or inverse transform if possible.
                correction = self.scaler.inverse_transform([[correction_scaled]])[0][0]
                sigma = abs(self.scaler.inverse_transform([[sigma_scaled]])[0][0])
        else:
            correction = 0.0
            sigma = 0.0

        final_pred = max(0, xgb_pred + correction)
        return final_pred, sigma
