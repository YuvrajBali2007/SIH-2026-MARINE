"""
Charter Rate Prediction & Booking Decision Model
==================================================
1. Reads freight_ship_fuel_sample_1000 (1).csv
2. Synthesises current_charter_rate and future_charter_rate_7d (with wind-speed volatility shock)
3. Trains a 70 / 30 weighted ensemble (GradientBoostingRegressor + LinearRegression)
4. Applies a decision function (BOOK NOW vs WAIT) on a 5-row test sample
"""

import os, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

warnings.filterwarnings("ignore")
np.random.seed(42)

# ── 1. Load data ────────────────────────────────────────────────────────────
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(DATA_DIR, "freight_ship_fuel_sample_1000 (1).csv")
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} rows  |  Columns: {list(df.columns)}\n")

# ── 2. Synthesise target columns ────────────────────────────────────────────
# current_charter_rate: base driven by DWT, vessel_age, fuel_price + noise
df["current_charter_rate"] = (
    15_000
    + 0.15 * df["dwt"]
    - 200 * df["vessel_age"]
    + 8 * df["fuel_price"]
    + np.random.normal(0, 500, len(df))
)

# Wind-speed volatility shock (std-dev of wind_speed across the dataset)
wind_vol = df["wind_speed"].std()
shock = wind_vol * np.random.normal(0.5, 0.3, len(df))  # positive bias = slight rate increase

df["future_charter_rate_7d"] = (
    df["current_charter_rate"]
    + shock * 100                       # scale shock to dollar magnitude
    + np.random.normal(0, 300, len(df)) # additional noise
)

print(f"Synthetic columns added.  Wind-speed volatility (std): {wind_vol:.2f} knots")
print(df[["current_charter_rate", "future_charter_rate_7d"]].describe().round(2))
print()

# ── 3. Feature / target split ───────────────────────────────────────────────
FEATURES = ["dwt", "vessel_age", "fuel_price", "wind_speed",
            "wave_height", "speed", "distance_nm"]
TARGET   = "future_charter_rate_7d"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
print(f"Train: {len(X_train)}  |  Test: {len(X_test)}\n")

# ── 4. Build 70 / 30 weighted ensemble ─────────────────────────────────────
gbr = GradientBoostingRegressor(
    n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42
)
lr  = LinearRegression()

ensemble = VotingRegressor(
    estimators=[("gbr", gbr), ("lr", lr)],
    weights=[0.7, 0.3],
)
ensemble.fit(X_train, y_train)

y_pred = ensemble.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2  = r2_score(y_test, y_pred)

print("=" * 55)
print("  ENSEMBLE MODEL PERFORMANCE  (70% GBR / 30% LR)")
print("=" * 55)
print(f"  MAE  : ${mae:,.2f}")
print(f"  R2   :  {r2:.4f}")
print("=" * 55)
print()

# -- 5. Decision logic on 5-row test sample --
WAIT_PENALTY = 5_000  # USD

sample_idx = X_test.index[:5]
sample_X   = X_test.loc[sample_idx]
sample_pred = ensemble.predict(sample_X)
sample_current = df.loc[sample_idx, "current_charter_rate"].values

decisions = []
for cur, fut_pred in zip(sample_current, sample_pred):
    penalised = fut_pred - WAIT_PENALTY
    decision  = "BOOK NOW" if cur <= penalised else "WAIT"
    decisions.append({
        "current_rate": round(cur, 2),
        "predicted_future_7d": round(fut_pred, 2),
        "penalised_future": round(penalised, 2),
        "decision": decision,
    })

result_df = pd.DataFrame(decisions, index=sample_idx)
result_df.index.name = "row"

print("+" + "-" * 77 + "+")
print("|           BOOKING DECISION  (wait penalty = $5,000)                         |")
print("+" + "-" * 77 + "+")
print(result_df.to_string())
print("+" + "-" * 77 + "+")
