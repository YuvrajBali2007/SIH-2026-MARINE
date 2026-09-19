import numpy as np
import pandas as pd

from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error,r2_score

def load_data(file_path):
    return pd.read_csv(file_path)

def create_features(df):

    df = df.copy()
    df["relative_wind_angle"] = (df["wind_direction"] - df["heading"] + 180) % 360 - 180
    angle_rad = np.radians(df["relative_wind_angle"])

    # Wind component along ship's direction
    df["headwind_component"] = (
        df["wind_speed"] * np.cos(angle_rad)
    )

    # Wind component perpendicular to ship
    df["crosswind_component"] = (
        df["wind_speed"] * np.sin(angle_rad)
    )
    df["relative_current_angle"] = (
        df["current_direction"] - df["heading"] + 180
    ) % 360 - 180

    current_angle_rad = np.radians(df["relative_current_angle"])

    df["current_along_route"] = (
        df["current_speed"] * np.cos(current_angle_rad)
    )

    # --------------------------------------------------------
    # Relative wave direction
    # --------------------------------------------------------
    df["relative_wave_angle"] = (
        df["wave_direction"] - df["heading"] + 180
    ) % 360 - 180

    wave_angle_rad = np.radians(df["relative_wave_angle"])

    df["wave_head_component"] = (
        df["wave_height"] * np.cos(wave_angle_rad)
    )

    # --------------------------------------------------------
    # Non-linear speed features
    # --------------------------------------------------------
    df["speed_squared"] = df["speed"] ** 2
    df["speed_cubed"] = df["speed"] ** 3

    return df

data = load_data("freight_ship_fuel_sample_1000.csv")
data = create_features(data)

data = pd.get_dummies(data,columns=["vessel_type"],dtype=int)

target = "fuel_consumed_tpd"
data = data.drop(columns=["vessel_id"])
X = data.drop(columns=[target])
y = data[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBRegressor(n_estimators=500,learning_rate=0.05,max_depth=8,subsample=0.8,colsample_bytree=0.8,objective="reg:squarederror",random_state=42)
model.fit(X_train, y_train)

# ============================================================
# 8. MODEL EVALUATION
# ============================================================

predictions = model.predict(X_test)
mae = mean_squared_error(y_test, predictions)

r2 = r2_score(y_test, predictions)

print("Mpdel performance:")
print(f"Mean Squared Error: {mae:.4f}")
print(f"R-squared: {r2:.4f}")


New_data = pd.DataFrame([{
    "vessel_type": "container",
    "engine_power": 13000,
    "dwt":10000,
    "vessel_age": 3,

    "draft": 15,

    "speed": 20,

    "distance_nm": 4400,

    "heading": 90,

    "wind_speed": 20,

    "wind_direction": 130,

    "wave_height": 2.5,

    "wave_period": 8,

    "wave_direction": 120,

    "current_speed": 1.2,

    "current_direction": 80
}])

# ============================================================
# 10. OPTIMIZATION FUNCTION
# ============================================================

def optimize_speed(    vessel_data,
    model,
    feature_columns,
    fuel_price,
    required_hours,
    min_speed=10,
    max_speed=20,
    speed_step=0.1
):
    results = []

    speeds = np.arange(
        min_speed,
        max_speed + speed_step,
        speed_step
    )

    for speed in speeds:

        row = vessel_data.copy()

        # Try this candidate speed
        row["speed"] = speed

        # Feature engineering
        row = create_features(row)
        row = pd.get_dummies(
            row,
            columns=["vessel_type"],
            dtype=int
        )

        # Make sure all required model columns exist
        for col in feature_columns:
            if col not in row.columns:
                row[col] = 0

        # Remove unexpected columns
        row = row[feature_columns]
         # ----------------------------------------------------
        # Predict fuel/day
        # ----------------------------------------------------
        fuel_per_day = model.predict(row)[0]

        # ----------------------------------------------------
        # Voyage time
        #
        # distance in nautical miles
        # speed in knots = nautical miles / hour
        # ----------------------------------------------------
        distance = vessel_data["distance_nm"].iloc[0]

        voyage_hours = distance / speed

        voyage_days = voyage_hours / 24

        # ----------------------------------------------------
        # Total fuel
        # ----------------------------------------------------
        total_fuel = fuel_per_day * voyage_days
        fuel_cost = total_fuel * fuel_price
        delay_hours = max(
            0,
            voyage_hours - required_hours
        )

        delay_penalty = delay_hours * 5000


        total_cost = fuel_cost + delay_penalty

        results.append({

            "speed": speed,

            "fuel_per_day": fuel_per_day,

            "voyage_hours": voyage_hours,

            "total_fuel": total_fuel,

            "fuel_cost": fuel_cost,

            "delay_hours": delay_hours,

            "delay_penalty": delay_penalty,

            "total_cost": total_cost
        })
    results_df = pd.DataFrame(results)

    # Only speeds satisfying ETA requirement
    feasible = results_df[
        results_df["voyage_hours"] <= required_hours
    ]

    if feasible.empty:

        print("No speed satisfies the ETA requirement.")

        return None, results_df

    best = feasible.loc[
        feasible["total_cost"].idxmin()
    ]

    return best, results_df


fuel_price = 620          # $ per tonne        can use api to get daily fuel price from https://www.steamingfuel.com/fuel-prices
required_hours = 300      # maximum allowed voyage time


best_speed, all_results = optimize_speed(

    New_data,
    model,

    feature_columns=X.columns.tolist(),

    fuel_price=fuel_price,

    required_hours=required_hours,

    min_speed=10,

    max_speed=20,

    speed_step=0.1
)

if best_speed is not None:

    print("\n================================")
    print("OPTIMAL VOYAGE PLAN")
    print("================================")

    print(
        "Optimal speed:",
        round(best_speed["speed"], 2),
        "knots"
    )

    print(
        "Fuel consumption:",
        round(best_speed["fuel_per_day"], 2),
        "tonnes/day"
    )

    print(
        "Voyage time:",
        round(best_speed["voyage_hours"], 2),
        "hours"
    )

    print(
        "Total fuel:",
        round(best_speed["total_fuel"], 2),
        "tonnes"
    )

    print(
        "Fuel cost: $",
        round(best_speed["fuel_cost"], 2)
    )

    print(
        "Delay:",
        round(best_speed["delay_hours"], 2),
        "hours"
    )

    print(
        "Total economic cost: $",
        round(best_speed["total_cost"], 2)
    )