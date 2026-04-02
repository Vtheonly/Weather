import os

class Config:
    # -- Data Paths --
    DATA_PATH = "wtbdata_245days.csv"
    ARTIFACTS_DIR = "saved_models"
    PLOT_DIR = os.path.join(ARTIFACTS_DIR, "plots")

    # -- Physics & Time --
    LOOKBACK_STEPS = 144
    FORECAST_STEPS = 288

    # -- ULTRA SETTINGS --
    BATCH_SIZE = 4096      # Pushing to 4096 to fill VRAM
    EPOCHS = 30
    LEARNING_RATE = 5e-4   # Slightly lower LR for larger batches
    TRAIN_TEST_SPLIT = 0.9

    # -- Feature Definitions --
    TARGET_COL = "Patv"
    PHYSICS_FEATURES = [
        "Wspd", "Wdir", "Etmp", "Itmp", "Ndir", "Pab1", "Pab2", "Pab3", "Prtv",
        "Patv", "U", "V", "Energy_Flux", "Momentum"
    ]

    @classmethod
    def get_model_path(cls):
        return os.path.join(cls.ARTIFACTS_DIR, "deep_physics_transformer.h5")

    @classmethod
    def get_scaler_path(cls):
        return os.path.join(cls.ARTIFACTS_DIR, "global_scaler.pkl")
