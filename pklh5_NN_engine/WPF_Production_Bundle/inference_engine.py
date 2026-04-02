import os
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import matplotlib.pyplot as plt

class WindProductionEngine:
    """
    Professional Inference Engine for local deployment.
    Requires: model.h5, scaler.pkl, and a CSV snippet.
    """
    def __init__(self, model_path, scaler_path):
        print("🤖 Loading Production AI Brain...")
        self.model = tf.keras.models.load_model(model_path)
        self.scaler = joblib.load(scaler_path)
        self.physics_features = [
            "Wspd", "Wdir", "Etmp", "Itmp", "Ndir", "Pab1", "Pab2", "Pab3", "Prtv", 
            "Patv", "U", "V", "Energy_Flux", "Momentum"
        ]
        self.target_idx = self.physics_features.index("Patv")

    def apply_physics(self, df):
        """Minimalist Physics Engine for Inference."""
        df = df.copy()
        df['Patv'] = df['Patv'].clip(lower=0)
        wdir_rad = np.deg2rad(df['Wdir'])
        df['U'] = df['Wspd'] * np.cos(wdir_rad)
        df['V'] = df['Wspd'] * np.sin(wdir_rad)
        df['Energy_Flux'] = np.power(df['Wspd'], 3)
        df['Momentum'] = df['Wspd'].diff().fillna(0)
        return df.ffill().bfill()

    def predict_48h(self, history_df):
        """
        Input: DataFrame with exactly 144 rows (24 hours).
        Output: Array of 288 values (48 hour forecast).
        """
        # 1. Apply Physics
        df_phys = self.apply_physics(history_df)
        
        # 2. Scale
        scaled_data = self.scaler.transform(df_phys[self.physics_features])
        
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
        # Formula: Real = (Scaled - Min) / Scale_Factor
        # Using the saved scaler attributes for 'Patv'
        p_min = self.scaler.min_[self.target_idx]
        p_scale = self.scaler.scale_[self.target_idx]
        
        real_forecast = (prediction_scaled[0] - p_min) / p_scale
        return real_forecast

# --- QUICK TEST SCRIPT ---
if __name__ == "__main__":
    # Settings
    MODEL_FILE = "deep_physics_transformer.h5"
    SCALER_FILE = "global_scaler.pkl"
    DATA_FILE = "wtbdata_245days.csv"
    
    if not os.path.exists(MODEL_FILE):
        print(f"❌ Error: Place {MODEL_FILE} in this folder.")
    else:
        engine = WindProductionEngine(MODEL_FILE, SCALER_FILE)
        
        # Load a random snippet from the dataset to simulate a "Live Turbine"
        raw_df = pd.read_csv(DATA_FILE).iloc[500:500+144] # 24 hours of history
        
        print("⚡ Running 48-hour forecast...")
        forecast = engine.predict_48h(raw_df)
        
        plt.figure(figsize=(12,5))
        plt.plot(forecast, color='green', label='AI Forecast (48h)')
        plt.title("Local Production Test: Wind Power Forecast")
        plt.xlabel("Steps (10 min)")
        plt.ylabel("Power (kW)")
        plt.legend()
        plt.grid(True)
        plt.show()
