import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from wpf_engine.config.settings import Config
import os

class Evaluator:
    def __init__(self, model, scaler):
        self.model = model
        self.scaler = scaler
        # We need the min/max of the Target column to un-scale predictions for real metrics
        self.target_min = scaler.min_[Config.PHYSICS_FEATURES.index(Config.TARGET_COL)]
        self.target_scale = scaler.scale_[Config.PHYSICS_FEATURES.index(Config.TARGET_COL)]

    def unscale(self, data):
        """Converts normalized 0-1 data back to MW/kW."""
        return (data - self.target_min) / self.target_scale

    def evaluate_and_plot(self, test_gen):
        print("📊 Running Comprehensive Evaluation...")

        # 1. Generate Predictions
        # We take a subset of the test generator for visualization (e.g., first 50 batches)
        # to avoid OOM during plotting, but calculate metrics on more.

        all_trues = []
        all_preds = []

        # Iterate over validation set
        steps_to_eval = min(len(test_gen), 100) # Evaluate on ~25k samples
        print(f"   Processing {steps_to_eval} batches...")

        for i in range(steps_to_eval):
            x, y = test_gen[i]
            preds = self.model.predict(x, verbose=0)
            all_trues.append(y)
            all_preds.append(preds)

        # Flatten
        y_true = np.concatenate(all_trues, axis=0)
        y_pred = np.concatenate(all_preds, axis=0)

        # Unscale
        # Since we used MinMaxScaler, X_std = (X - min) / (max - min)
        # X = X_std * (max - min) + min
        # Sklearn: data = (val - min) / scale  ->  val = data * scale + min -> Wait, scale is (max-min) or 1/(max-min)?
        # Sklearn `scale_` attribute is (max-min). Actually: X_scaled = X * scale_ + min_
        # Correction: inverse_transform is safer.

        # Manual inverse for speed on just target
        y_true_real = (y_true - self.scaler.min_[9]) / self.scaler.scale_[9]
        y_pred_real = (y_pred - self.scaler.min_[9]) / self.scaler.scale_[9]

        # --- Metrics ---
        mse = mean_squared_error(y_true_real, y_pred_real)
        mae = mean_absolute_error(y_true_real, y_pred_real)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true_real.flatten(), y_pred_real.flatten())

        print(f"\n🏆 FINAL RESULTS:")
        print(f"   R² Score: {r2:.4f}")
        print(f"   RMSE:     {rmse:.4f} kW")
        print(f"   MAE:      {mae:.4f} kW")
        print(f"   MSE:      {mse:.4f}")

        self.generate_plots(y_true_real, y_pred_real)

        return {"r2": r2, "rmse": rmse, "mae": mae}

    def generate_plots(self, y_true, y_pred):
        plot_dir = Config.PLOT_DIR

        # Plot 1: Prediction vs Truth (Sample)
        plt.figure(figsize=(15, 6))
        # Plot random sample
        idx = np.random.randint(0, len(y_true))
        plt.plot(y_true[idx], label='Ground Truth (Real Physics)', color='black', linewidth=2)
        plt.plot(y_pred[idx], label='AI Prediction', color='dodgerblue', linestyle='--')
        plt.title(f"48-Hour Forecast Horizon (Sample #{idx})")
        plt.xlabel("Time Steps (10-min intervals)")
        plt.ylabel("Active Power (kW)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{plot_dir}/1_forecast_sample.png")
        plt.close()

        # Plot 2: Error Distribution
        errors = (y_true - y_pred).flatten()
        plt.figure(figsize=(10, 6))
        sns.histplot(errors, bins=100, kde=True, color='crimson')
        plt.title("Error Distribution (Residuals)")
        plt.xlabel("Prediction Error (kW)")
        plt.savefig(f"{plot_dir}/2_error_distribution.png")
        plt.close()

        # Plot 3: Performance Per Horizon Step (Does it get worse over time?)
        # Calculate RMSE per time step (0 to 288)
        rmse_per_step = np.sqrt(np.mean((y_true - y_pred)**2, axis=0))
        plt.figure(figsize=(12, 6))
        plt.plot(rmse_per_step, color='purple')
        plt.title("RMSE Degradation over 48-Hour Horizon")
        plt.xlabel("Forecast Step (10m)")
        plt.ylabel("RMSE (kW)")
        plt.grid(True)
        plt.savefig(f"{plot_dir}/3_rmse_per_step.png")
        plt.close()

        # Plot 4: Scatter Density
        plt.figure(figsize=(8, 8))
        # Sample points to keep plot light
        flat_true = y_true.flatten()
        flat_pred = y_pred.flatten()
        indices = np.random.choice(len(flat_true), size=10000, replace=False)
        plt.scatter(flat_true[indices], flat_pred[indices], alpha=0.1, s=1, c='green')
        plt.plot([0, flat_true.max()], [0, flat_true.max()], 'r--')
        plt.xlabel("Actual Power")
        plt.ylabel("Predicted Power")
        plt.title("Prediction Alignment (R² visual)")
        plt.savefig(f"{plot_dir}/4_scatter_alignment.png")
        plt.close()

        print(f"🎨 Plots saved to {plot_dir}/")
