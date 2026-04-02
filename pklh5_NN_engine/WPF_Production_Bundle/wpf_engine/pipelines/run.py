import sys
import os

# --- PATH PATCH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)
# ------------------

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from wpf_engine.config.settings import Config
from wpf_engine.data.processor import PhysicsEngine, DataManager, TimeSeriesGenerator
from wpf_engine.models.architecture import build_differential_model
from wpf_engine.core.evaluator import Evaluator

def main():
    print(f"🚀 Initializing HIGH-PERFORMANCE Engine (Batch Size: {Config.BATCH_SIZE})...")

    # Load & Process
    try:
        df = pd.read_csv(Config.DATA_PATH)
    except FileNotFoundError:
        print("❌ Dataset not found.")
        return

    df = PhysicsEngine.engineer_features(df)
    manager = DataManager()
    df, scaler = manager.prepare_data(df)

    # Indices Logic
    print("⚙️ Computing valid sequence indices...")
    groups = df.groupby('TurbID')
    valid_indices = []
    total_len = Config.LOOKBACK_STEPS + Config.FORECAST_STEPS

    for turb_id, group in groups:
        g_indices = group.index.values
        n_samples = len(g_indices) - total_len
        if n_samples > 0:
            valid_indices.extend(g_indices[:n_samples])

    valid_indices = np.array(valid_indices)
    np.random.shuffle(valid_indices)
    print(f"✅ Found {len(valid_indices)} valid sequences.")

    # Split
    split_idx = int(len(valid_indices) * Config.TRAIN_TEST_SPLIT)
    train_idx = valid_indices[:split_idx]
    test_idx = valid_indices[split_idx:]

    # Generators (Vectorized = Fast)
    train_gen = TimeSeriesGenerator(df, train_idx, Config.BATCH_SIZE)
    test_gen = TimeSeriesGenerator(df, test_idx, Config.BATCH_SIZE)

    # Model
    model = build_differential_model()

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=4, restore_best_weights=True),
        ModelCheckpoint(Config.get_model_path(), save_best_only=True, monitor='val_loss'),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-5)
    ]

    print(f"🔥 Starting GPU Training (Batch Size {Config.BATCH_SIZE})...")

    # --- KERAS 3 FIX: Removed 'workers' and 'use_multiprocessing' ---
    # The Vectorized Generator is fast enough to run on the main thread
    history = model.fit(
        train_gen,
        validation_data=test_gen,
        epochs=Config.EPOCHS,
        callbacks=callbacks
    )

    # Evaluate
    evaluator = Evaluator(model, scaler)
    metrics = evaluator.evaluate_and_plot(test_gen)
    print("\n✅ Engine Run Complete.")

if __name__ == "__main__":
    main()
