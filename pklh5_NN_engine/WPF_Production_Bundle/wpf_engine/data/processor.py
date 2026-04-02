import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import tensorflow as tf
from wpf_engine.config.settings import Config

class PhysicsEngine:
    @staticmethod
    def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
        print("⚡ Igniting Physics Engine...")
        df['Patv'] = df['Patv'].clip(lower=0)
        wdir_rad = np.deg2rad(df['Wdir'])
        df['U'] = df['Wspd'] * np.cos(wdir_rad)
        df['V'] = df['Wspd'] * np.sin(wdir_rad)
        df['Energy_Flux'] = np.power(df['Wspd'], 3)
        df['Momentum'] = df.groupby('TurbID')['Wspd'].diff().fillna(0)
        df = df.ffill().bfill()
        return df

class DataManager:
    def __init__(self):
        self.scaler = MinMaxScaler()

    def prepare_data(self, df):
        print("⚖️ Scaling 4.7M+ rows (MinMax)...")
        df[Config.PHYSICS_FEATURES] = self.scaler.fit_transform(df[Config.PHYSICS_FEATURES])
        joblib.dump(self.scaler, Config.get_scaler_path())
        return df, self.scaler

class TimeSeriesGenerator(tf.keras.utils.Sequence):
    """
    Highly Optimized Vectorized Generator.
    Removes Python loops to maximize GPU throughput.
    """
    def __init__(self, df, indices, batch_size, **kwargs):
        super().__init__(**kwargs)
        self.indices = indices
        self.batch_size = batch_size
        self.lookback = Config.LOOKBACK_STEPS
        self.forecast = Config.FORECAST_STEPS

        # Matrix is loaded into RAM once
        self.data_matrix = df[Config.PHYSICS_FEATURES].values.astype(np.float32)
        self.target_idx = Config.PHYSICS_FEATURES.index(Config.TARGET_COL)

        # Pre-calculate offset arrays for broadcasting
        # This creates the "sliding window" indices in C-speed
        self.lookback_offsets = np.arange(self.lookback)
        self.forecast_offsets = np.arange(self.forecast) + self.lookback

    def __len__(self):
        return int(np.floor(len(self.indices) / self.batch_size))

    def __getitem__(self, index):
        # 1. Get the start indices for this batch
        starts = self.indices[index*self.batch_size : (index+1)*self.batch_size]

        # 2. Vectorized Slicing (Magic happens here)
        # Create a grid of indices: (Batch_Size, Lookback_Steps)
        # This replaces the 'for' loop entirely
        history_idx = starts[:, None] + self.lookback_offsets
        forecast_idx = starts[:, None] + self.forecast_offsets
        anchor_idx = starts + self.lookback - 1

        # 3. Bulk Fetch from RAM
        X_hist = self.data_matrix[history_idx] # Shape: (Batch, 144, Features)
        X_anchor = self.data_matrix[anchor_idx, self.target_idx] # Shape: (Batch,)
        Y_future = self.data_matrix[forecast_idx, self.target_idx] # Shape: (Batch, 288)

        # 4. Reshape Anchor to (Batch, 1) to match Model Input
        X_anchor = X_anchor[:, None]

        inputs = {
            "history_in": X_hist,
            "anchor_in": X_anchor
        }

        return inputs, Y_future
