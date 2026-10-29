"""
Solar Vest ML Model - Training Script
======================================
Trains a Keras neural network to predict monthly kWh generation
from solar panel configuration and environmental features.
Uses NumPy + scikit-learn + TensorFlow (no pandas dependency).
"""

import os
import sys

if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.dummy_data import generate_dataset, save_dataset_csv

MODEL_PATH = os.path.join(os.path.dirname(__file__), "solar_model.keras")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "scaler.pkl")


def build_model(input_dim: int) -> tf.keras.Model:
    model = Sequential([
        Input(shape=(input_dim,)),
        Dense(128, activation="relu"),
        BatchNormalization(),
        Dropout(0.2),
        Dense(64, activation="relu"),
        BatchNormalization(),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1, activation="linear"),  # regression output
    ])
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"]
    )
    return model


def train():
    print("📊 Generating dummy dataset with physics-based formulas...")
    X, y = generate_dataset(10000)

    # Save CSV copy for reference
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "solar_dummy_data.csv")
    save_dataset_csv(csv_path, X, y)
    print(f"📁 Saved synthetic CSV dataset to {csv_path}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Normalize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"🧠 Training Keras neural network on {len(X_train)} samples...")
    model = build_model(X_train_scaled.shape[1])

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=7, min_lr=1e-5),
    ]

    history = model.fit(
        X_train_scaled, y_train,
        validation_split=0.15,
        epochs=120,
        batch_size=64,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate
    y_pred = model.predict(X_test_scaled).flatten()
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\n✅ Training complete!")
    print(f"   MAE  : {mae:.2f} kWh")
    print(f"   R²   : {r2:.4f}")

    # Save model and scaler
    model.save(MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"💾 Model saved → {MODEL_PATH}")
    print(f"💾 Scaler saved → {SCALER_PATH}")


if __name__ == "__main__":
    train()
