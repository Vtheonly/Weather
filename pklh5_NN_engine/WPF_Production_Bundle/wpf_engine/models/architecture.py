import tensorflow as tf
from tensorflow.keras import layers, Model
from wpf_engine.config.settings import Config

def build_differential_model():
    # --- Input 1: The Timeline (History) ---
    input_seq = layers.Input(shape=(Config.LOOKBACK_STEPS, len(Config.PHYSICS_FEATURES)), name="history_in")

    # --- Input 2: The Anchor (Current Power) ---
    input_anchor = layers.Input(shape=(1,), name="anchor_in")

    # 1. Feature Extraction (CNN for local patterns/gusts)
    x = layers.Conv1D(64, kernel_size=3, padding="same", activation="relu")(input_seq)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling1D(2)(x)

    # 2. Temporal Dynamics (Bi-LSTM for long-term memory)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True))(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=False))(x)

    # 3. Differential Prediction Head
    # We predict the *change* relative to the anchor, not absolute values.
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)

    # Output: Delta for 288 steps
    delta_pred = layers.Dense(Config.FORECAST_STEPS, name="delta_out")(x)

    # 4. Physics Reconstruction (Anchor + Delta)
    # Broadcast anchor to (Batch, 288)
    anchor_broadcast = layers.RepeatVector(Config.FORECAST_STEPS)(input_anchor)
    anchor_broadcast = layers.Reshape((Config.FORECAST_STEPS,))(anchor_broadcast)

    # Final = Anchor + Delta
    final_pred = layers.Add(name="reconstruction")([anchor_broadcast, delta_pred])

    # Physics Constraint: Power >= 0
    final_pred = layers.ReLU()(final_pred)

    model = Model(inputs=[input_seq, input_anchor], outputs=final_pred)

    optimizer = tf.keras.optimizers.Adam(learning_rate=Config.LEARNING_RATE)
    model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

    return model
