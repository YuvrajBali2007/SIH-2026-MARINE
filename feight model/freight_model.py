import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
import joblib

df = pd.read_csv("freight_rate_hypothetical_dataset_v2.csv", parse_dates=["date"])

df["month"] = df["date"].dt.month
df["year"] = df["date"].dt.year
df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)

categorical_cols = ["route", "cargo_type", "vessel_class", "market_event"]
encoders = {}

for col in categorical_cols:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col])
    encoders[col] = le

feature_cols = [
    "route_enc", "cargo_type_enc", "vessel_class_enc", "market_event_enc",
    "vessel_dwt", "distance_nm", "baltic_style_index",
    "bunker_fuel_price_usd_ton", "port_congestion_days",
    "month", "year", "week_of_year",
]

X = df[feature_cols]
y = df["freight_rate_usd_per_tonne"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = XGBRegressor(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))
r2 = r2_score(y_test, preds)

print("=== Freight Model — XGBoost performance ===")
print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R2   : {r2:.4f}")

importance = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("\nTop feature importances:")
print(importance.head(8).to_string())

joblib.dump(model, "freight_model.pkl")
for col, le in encoders.items():
    joblib.dump(le, f"{col}_encoder.pkl")

print("\nSaved: freight_model.pkl + encoders")


def predict_freight_rate(route, cargo_type, vessel_class, market_event,
                          vessel_dwt, distance_nm, baltic_style_index,
                          bunker_fuel_price_usd_ton, port_congestion_days,
                          month, year, week_of_year):

    def safe_encode(col, value):
        le = encoders[col]
        if value not in le.classes_:
            value = le.classes_[0]
        return le.transform([value])[0]

    row = pd.DataFrame([{
        "route_enc": safe_encode("route", route),
        "cargo_type_enc": safe_encode("cargo_type", cargo_type),
        "vessel_class_enc": safe_encode("vessel_class", vessel_class),
        "market_event_enc": safe_encode("market_event", market_event),
        "vessel_dwt": vessel_dwt,
        "distance_nm": distance_nm,
        "baltic_style_index": baltic_style_index,
        "bunker_fuel_price_usd_ton": bunker_fuel_price_usd_ton,
        "port_congestion_days": port_congestion_days,
        "month": month,
        "year": year,
        "week_of_year": week_of_year,
    }])
    return model.predict(row)[0]


example_pred = predict_freight_rate(
    route="Dampier, Australia - Visakhapatnam",
    cargo_type="Coal Ore",
    vessel_class="Panamax",
    market_event="None",
    vessel_dwt=78000,
    distance_nm=3570,
    baltic_style_index=1550,
    bunker_fuel_price_usd_ton=640,
    port_congestion_days=1.5,
    month=6, year=2026, week_of_year=24,
)
print(f"\nExample prediction: ${example_pred:.2f} per tonne")