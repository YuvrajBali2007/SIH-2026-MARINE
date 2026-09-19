"""
optimizer.py — SAIL Maritime Freight & Chartering Decision Support System
==========================================================================
Unified pipeline bridge integrating:
  • FreightEngine   — XGBoost freight-rate forecaster
  • FuelEngine      — XGBoost bunker-fuel / speed optimizer
  • TimingEngine    — GBR + LR charter-timing ensemble
  • VesselEngine    — Rule-based vessel allocation ranker

Master function: run_optimization(params) → dict
"""

from __future__ import annotations

import os
import warnings
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
_FREIGHT_DIR   = _BASE / "feight model"
_FUEL_DIR      = _BASE / "fuel model"
_TIMING_DIR    = _BASE / "timing model"
_VESSEL_DIR    = _BASE / "vessel model"

# ─────────────────────────────────────────────────────────────────────────────
# PORT PHYSICAL CONSTRAINTS
# ─────────────────────────────────────────────────────────────────────────────
PORT_CONSTRAINTS: dict[str, dict] = {
    "Haldia": {
        "max_draft": 8.5,
        "allowed_classes": ["Handysize", "Supramax"],
        "max_dwt": 55_000,
        "queue_days_avg": 3.5,
        "demurrage_usd_day": 18_000,
    },
    "Paradip": {
        "max_draft": 14.0,
        "allowed_classes": ["Handysize", "Supramax", "Panamax", "Capesize"],
        "max_dwt": 180_000,
        "queue_days_avg": 1.5,
        "demurrage_usd_day": 22_000,
    },
    "Vizag": {
        "max_draft": 14.5,
        "allowed_classes": ["Handysize", "Supramax", "Panamax", "Capesize"],
        "max_dwt": 200_000,
        "queue_days_avg": 2.0,
        "demurrage_usd_day": 20_000,
    },
    "Ennore": {
        "max_draft": 12.5,
        "allowed_classes": ["Handysize", "Supramax", "Panamax"],
        "max_dwt": 90_000,
        "queue_days_avg": 2.5,
        "demurrage_usd_day": 19_000,
    },
    "Kolkata": {
        "max_draft": 8.0,
        "allowed_classes": ["Handysize"],
        "max_dwt": 40_000,
        "queue_days_avg": 4.0,
        "demurrage_usd_day": 16_000,
    },
    "Mormugao": {
        "max_draft": 13.0,
        "allowed_classes": ["Handysize", "Supramax", "Panamax"],
        "max_dwt": 100_000,
        "queue_days_avg": 1.8,
        "demurrage_usd_day": 17_000,
    },
}

VESSEL_CLASS_DRAFT: dict[str, float] = {
    "Handysize":  9.5,
    "Supramax":  12.5,
    "Panamax":   14.2,
    "Capesize":  18.5,
}

VESSEL_CLASS_DWT: dict[str, tuple[int, int]] = {
    "Handysize":  (15_000,  40_000),
    "Supramax":  (40_001,  65_000),
    "Panamax":   (65_001, 100_000),
    "Capesize":  (100_001, 250_000),
}

# ─────────────────────────────────────────────────────────────────────────────
# FREIGHT ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class FreightEngine:
    """Loads pre-trained XGBoost freight-rate model + LabelEncoders."""

    _MODEL_RMSE = 3.8   # $/tonne — approximate; used for uncertainty bands

    def __init__(self) -> None:
        model_path = _FREIGHT_DIR / "freight_model.pkl"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Freight model not found at {model_path}. "
                "Run 'freight_model (1).py' first to train and save it."
            )
        self.model: XGBRegressor = joblib.load(model_path)

        enc_names = ["route", "cargo_type", "vessel_class", "market_event"]
        self.encoders: dict[str, LabelEncoder] = {}
        for name in enc_names:
            enc_path = _FREIGHT_DIR / f"{name}_encoder.pkl"
            if enc_path.exists():
                self.encoders[name] = joblib.load(enc_path)

        # Derive valid categories from encoders
        self.valid_routes = (
            list(self.encoders["route"].classes_)
            if "route" in self.encoders else []
        )
        self.valid_cargo = (
            list(self.encoders["cargo_type"].classes_)
            if "cargo_type" in self.encoders else []
        )
        self.valid_vessel_classes = (
            list(self.encoders["vessel_class"].classes_)
            if "vessel_class" in self.encoders else []
        )
        self.valid_market_events = (
            list(self.encoders["market_event"].classes_)
            if "market_event" in self.encoders else []
        )

    def _safe_encode(self, col: str, value: str) -> int:
        le = self.encoders[col]
        if value is None or (isinstance(value, str) and value.strip().lower() == "none"):
            value = np.nan
        if value not in le.classes_:
            value = le.classes_[0]
        return int(le.transform([value])[0])

    def predict_rate(
        self,
        route: str,
        cargo_type: str,
        vessel_class: str,
        market_event: str,
        vessel_dwt: float,
        distance_nm: float,
        baltic_style_index: float,
        bunker_fuel_price: float,
        port_congestion_days: float,
        month: int,
        year: int,
        week_of_year: int,
    ) -> float:
        row = pd.DataFrame([{
            "route_enc":         self._safe_encode("route", route),
            "cargo_type_enc":    self._safe_encode("cargo_type", cargo_type),
            "vessel_class_enc":  self._safe_encode("vessel_class", vessel_class),
            "market_event_enc":  self._safe_encode("market_event", market_event),
            "vessel_dwt":        vessel_dwt,
            "distance_nm":       distance_nm,
            "baltic_style_index": baltic_style_index,
            "bunker_fuel_price_usd_ton": bunker_fuel_price,
            "port_congestion_days":      port_congestion_days,
            "month":       month,
            "year":        year,
            "week_of_year": week_of_year,
        }])
        return float(self.model.predict(row)[0])

    def forecast_14d(
        self,
        base_params: dict,
        bdi_trend: float = 0.003,   # 0.3% daily BDI drift
        fuel_trend: float = 0.001,  # 0.1% daily bunker drift
        n_uncertainty: int = 200,
    ) -> dict:
        """
        Return 14-day daily freight rate forecast with ±1σ uncertainty bands.
        Simulates daily BDI and bunker drift, then bootstraps residuals.
        """
        today = datetime.date.today()
        dates, means, lowers, uppers = [], [], [], []

        rng = np.random.default_rng(42)

        for d in range(14):
            fcast_date = today + datetime.timedelta(days=d)
            p = base_params.copy()
            p["baltic_style_index"] = p["baltic_style_index"] * ((1 + bdi_trend) ** d)
            p["bunker_fuel_price"]  = p["bunker_fuel_price"]  * ((1 + fuel_trend) ** d)
            p["month"]        = fcast_date.month
            p["year"]         = fcast_date.year
            p["week_of_year"] = int(fcast_date.isocalendar()[1])

            point = self.predict_rate(**p)
            residuals = rng.normal(0, self._MODEL_RMSE, n_uncertainty)
            dates.append(fcast_date.isoformat())
            means.append(round(point, 4))
            lowers.append(round(point + residuals.min(), 4))
            uppers.append(round(point + residuals.max(), 4))

        return {"dates": dates, "mean": means, "lower": lowers, "upper": uppers}


# ─────────────────────────────────────────────────────────────────────────────
# FUEL ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class FuelEngine:
    """
    Trains XGBoost on the 1,000-row ship-fuel dataset.
    Exposes: predict_fuel(), optimize_speed(), forecast_bunker_14d()
    """

    def __init__(self) -> None:
        csv_path = _FUEL_DIR / "freight_ship_fuel_sample_1000 (1).csv"
        data = pd.read_csv(csv_path)
        data = self._create_features(data)
        data = pd.get_dummies(data, columns=["vessel_type"], dtype=int)
        data = data.drop(columns=["vessel_id"], errors="ignore")

        self._target = "fuel_consumed_tpd"
        X = data.drop(columns=[self._target])
        y = data[self._target]
        self._feature_cols = X.columns.tolist()

        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8,
            objective="reg:squarederror", random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

    @staticmethod
    def _create_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["relative_wind_angle"]  = (df["wind_direction"] - df["heading"] + 180) % 360 - 180
        ar = np.radians(df["relative_wind_angle"])
        df["headwind_component"]   = df["wind_speed"] * np.cos(ar)
        df["crosswind_component"]  = df["wind_speed"] * np.sin(ar)
        df["relative_current_angle"] = (df["current_direction"] - df["heading"] + 180) % 360 - 180
        cr = np.radians(df["relative_current_angle"])
        df["current_along_route"]  = df["current_speed"] * np.cos(cr)
        df["relative_wave_angle"]  = (df["wave_direction"] - df["heading"] + 180) % 360 - 180
        wr = np.radians(df["relative_wave_angle"])
        df["wave_head_component"]  = df["wave_height"] * np.cos(wr)
        df["speed_squared"]        = df["speed"] ** 2
        df["speed_cubed"]          = df["speed"] ** 3
        return df

    def _prep_row(self, row: pd.DataFrame) -> pd.DataFrame:
        row = self._create_features(row)
        row = pd.get_dummies(row, columns=["vessel_type"], dtype=int)
        for col in self._feature_cols:
            if col not in row.columns:
                row[col] = 0
        row = row.drop(columns=[self._target], errors="ignore")
        return row[self._feature_cols]

    def predict_fuel(self, vessel_row: pd.DataFrame) -> float:
        return float(self.model.predict(self._prep_row(vessel_row))[0])

    def optimize_speed(
        self,
        vessel_data: pd.DataFrame,
        fuel_price: float,
        required_hours: float,
        min_speed: float = 10.0,
        max_speed: float = 20.0,
        speed_step: float = 0.5,
    ) -> dict:
        results = []
        for speed in np.arange(min_speed, max_speed + speed_step, speed_step):
            row = vessel_data.copy()
            row["speed"] = speed
            fuel_per_day   = float(self.model.predict(self._prep_row(row))[0])
            distance       = float(vessel_data["distance_nm"].iloc[0])
            voyage_hours   = distance / speed
            voyage_days    = voyage_hours / 24.0
            total_fuel     = fuel_per_day * voyage_days
            fuel_cost      = total_fuel * fuel_price
            delay_hours    = max(0.0, voyage_hours - required_hours)
            delay_penalty  = delay_hours * 5_000
            total_cost     = fuel_cost + delay_penalty
            results.append({
                "speed": round(float(speed), 2),
                "fuel_per_day": round(fuel_per_day, 2),
                "voyage_hours": round(voyage_hours, 2),
                "total_fuel": round(total_fuel, 2),
                "fuel_cost": round(fuel_cost, 2),
                "delay_penalty": round(delay_penalty, 2),
                "total_cost": round(total_cost, 2),
            })
        df_r = pd.DataFrame(results)
        feasible = df_r[df_r["voyage_hours"] <= required_hours]
        if feasible.empty:
            best = df_r.loc[df_r["total_cost"].idxmin()].to_dict()
            best["feasible"] = False
        else:
            best = feasible.loc[feasible["total_cost"].idxmin()].to_dict()
            best["feasible"] = True
        best["all_results"] = df_r
        return best

    def forecast_bunker_14d(self, base_price: float, daily_drift: float = 0.0012) -> dict:
        """Simple AR(1) bunker price projection for 14 days."""
        today = datetime.date.today()
        rng   = np.random.default_rng(99)
        dates, prices = [], []
        p = base_price
        for d in range(14):
            p = p * (1 + daily_drift + rng.normal(0, 0.002))
            dates.append((today + datetime.timedelta(days=d)).isoformat())
            prices.append(round(p, 2))
        return {"dates": dates, "price": prices}


# ─────────────────────────────────────────────────────────────────────────────
# TIMING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class TimingEngine:
    """
    GBR + LinearRegression (70/30) ensemble for charter-timing decisions.
    Synthesises current_charter_rate and future_charter_rate_7d from the
    fuel dataset, then learns the differential.
    """
    FEATURES = ["dwt", "vessel_age", "fuel_price", "wind_speed",
                "wave_height", "speed", "distance_nm"]
    WAIT_PENALTY = 5_000  # USD

    def __init__(self) -> None:
        csv_path = _TIMING_DIR / "freight_ship_fuel_sample_1000 (1).csv"
        df = pd.read_csv(csv_path)
        np.random.seed(42)

        df["current_charter_rate"] = (
            15_000
            + 0.15 * df["dwt"]
            - 200  * df["vessel_age"]
            + 8    * df["fuel_price"]
            + np.random.normal(0, 500, len(df))
        )
        wind_vol = df["wind_speed"].std()
        shock    = wind_vol * np.random.normal(0.5, 0.3, len(df))
        df["future_charter_rate_7d"] = (
            df["current_charter_rate"]
            + shock * 100
            + np.random.normal(0, 300, len(df))
        )
        self._df = df

        X = df[self.FEATURES]
        y = df["future_charter_rate_7d"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )
        gbr = GradientBoostingRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42
        )
        lr  = LinearRegression()
        self.ensemble = VotingRegressor(
            estimators=[("gbr", gbr), ("lr", lr)],
            weights=[0.7, 0.3],
        )
        self.ensemble.fit(X_train, y_train)

        # Directional accuracy on holdout
        y_pred = self.ensemble.predict(X_test)
        current_h = df.loc[X_test.index, "current_charter_rate"].values
        self.directional_accuracy = float(
            np.mean((y_pred > current_h) == (y_test.values > current_h)) * 100
        )
        self.mae_holdout = float(np.mean(np.abs(y_pred - y_test.values)))

    def get_decision(
        self,
        dwt: float,
        vessel_age: float,
        fuel_price: float,
        wind_speed: float,
        wave_height: float,
        speed: float,
        distance_nm: float,
        cargo_tonnes: float,
        inventory_hold_cost_per_day: float = 12_000,
        defer_days: int = 7,
    ) -> dict:
        """
        Returns timing decision dict with:
          decision, current_rate, predicted_future, savings_if_wait,
          optimal_t_star, total_landed_cost components
        """
        feat = pd.DataFrame([{
            "dwt": dwt, "vessel_age": vessel_age, "fuel_price": fuel_price,
            "wind_speed": wind_speed, "wave_height": wave_height,
            "speed": speed, "distance_nm": distance_nm,
        }])
        current_rate = float(
            15_000 + 0.15 * dwt - 200 * vessel_age + 8 * fuel_price
        )
        predicted_future = float(self.ensemble.predict(feat)[0])
        penalised_future = predicted_future - self.WAIT_PENALTY

        # Optimal t* = day when expected rate is minimised (simple greedy scan)
        rng = np.random.default_rng(7)
        daily_rates = [current_rate]
        for t in range(1, defer_days + 1):
            r = current_rate * (1 + rng.normal(0.001, 0.005))
            daily_rates.append(r)
        t_star   = int(np.argmin(daily_rates))
        min_rate = daily_rates[t_star]

        # Decision
        if current_rate <= penalised_future:
            decision       = "EXECUTE_NOW"
            decision_label = f"EXECUTE FIXTURE — LOCK RATE NOW  [T+0]"
            savings_if_wait = 0.0
        else:
            decision = "DEFER"
            if t_star == 0:
                t_star = max(1, defer_days // 2)
            decision_label = (
                f"DECISION RECOMMENDATION: DEFER FIXTURE  "
                f"(T+{t_star} TARGET)"
            )
            savings_if_wait = current_rate - min_rate

        # Total Landed Cost breakdown
        base_freight          = current_rate * (distance_nm / 1000)
        bunker_surcharge      = fuel_price   * 0.08 * (distance_nm / 1000)
        demurrage_risk        = 0.0           # calculated per-port in VesselEngine
        inventory_hold        = inventory_hold_cost_per_day * (distance_nm / (speed * 24))
        total_landed_cost     = base_freight + bunker_surcharge + demurrage_risk + inventory_hold

        return {
            "decision":          decision,
            "decision_label":    decision_label,
            "current_rate":      round(current_rate, 2),
            "predicted_future":  round(predicted_future, 2),
            "penalised_future":  round(penalised_future, 2),
            "optimal_t_star":    t_star,
            "savings_if_wait":   round(savings_if_wait, 2),
            "daily_rates":       [round(r, 2) for r in daily_rates],
            "base_freight":      round(base_freight, 2),
            "bunker_surcharge":  round(bunker_surcharge, 2),
            "inventory_hold":    round(inventory_hold, 2),
            "total_landed_cost": round(total_landed_cost, 2),
            "directional_accuracy": round(self.directional_accuracy, 1),
        }


# ─────────────────────────────────────────────────────────────────────────────
# VESSEL ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class VesselEngine:
    """Rule-based vessel ranker with port-constraint enforcement."""

    def __init__(self) -> None:
        csv_path = _VESSEL_DIR / "vessels.csv"
        self._df = pd.read_csv(csv_path)

    @staticmethod
    def _norm_hi(s: pd.Series) -> pd.Series:
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn) * 100 if mx != mn else pd.Series(100.0, index=s.index)

    @staticmethod
    def _norm_lo(s: pd.Series) -> pd.Series:
        mn, mx = s.min(), s.max()
        return (mx - s) / (mx - mn) * 100 if mx != mn else pd.Series(100.0, index=s.index)

    def rank(
        self,
        cargo_tonnes: float,
        distance_nm: float,
        port: str,
        required_days: float,
        fuel_predictions: pd.Series | None = None,
    ) -> pd.DataFrame:
        port_cfg      = PORT_CONSTRAINTS.get(port, PORT_CONSTRAINTS["Paradip"])
        max_draft     = port_cfg["max_draft"]
        demurrage_day = port_cfg["demurrage_usd_day"]
        queue_days    = port_cfg["queue_days_avg"]

        df = self._df.copy()
        if fuel_predictions is not None:
            df["fuel_consumed_tpd"] = fuel_predictions.values

        # Suitability filter
        def _is_suitable(v: pd.Series) -> tuple[bool, str]:
            vd = float(v["distance_nm"]) if "distance_nm" in v else distance_nm
            voyage_days = distance_nm / (float(v["speed"]) * 24)
            if float(v["dwt"]) < cargo_tonnes:
                return False, "Insufficient DWT"
            if float(v["draft"]) > max_draft:
                return False, f"Draft {v['draft']:.1f}m > port limit {max_draft}m"
            if voyage_days > required_days:
                return False, "Exceeds transit window"
            return True, "Suitable"

        suitability = df.apply(_is_suitable, axis=1, result_type="expand")
        suitability.columns = ["suitable", "suitability_reason"]
        df = pd.concat([df, suitability], axis=1)

        suited = df[df["suitable"]].copy()
        if suited.empty:
            return pd.DataFrame()

        suited["fuel_efficiency"]     = suited["fuel_consumed_tpd"] / suited["dwt"]
        suited["demurrage_exposure"]  = queue_days * demurrage_day
        suited["capacity_score"]      = self._norm_hi(suited["dwt"])
        suited["speed_score"]         = self._norm_hi(suited["speed"])
        suited["fuel_score"]          = self._norm_lo(suited["fuel_efficiency"])
        suited["charter_cost_score"]  = self._norm_lo(suited["charter_rate_usd_day"])
        suited["age_score"]           = self._norm_lo(suited["vessel_age"])

        suited["vessel_score"] = (
            suited["capacity_score"]     * 0.20
            + suited["speed_score"]      * 0.15
            + suited["fuel_score"]       * 0.25
            + suited["charter_cost_score"] * 0.30
            + suited["age_score"]        * 0.10
        )

        ranked = suited.sort_values("vessel_score", ascending=False).copy()
        ranked["rank"] = range(1, len(ranked) + 1)

        out_cols = [
            "rank", "candidate_id", "vessel_id", "vessel_type",
            "dwt", "speed", "draft", "vessel_age",
            "charter_rate_usd_day", "fuel_efficiency",
            "demurrage_exposure", "vessel_score", "suitability_reason",
        ]
        return ranked[[c for c in out_cols if c in ranked.columns]]

    def port_compliance_matrix(self) -> pd.DataFrame:
        """Returns a DataFrame showing which vessel classes clear each port."""
        rows = []
        for port, cfg in PORT_CONSTRAINTS.items():
            row = {"Port": port, "Max Draft (m)": cfg["max_draft"],
                   "Queue (days)": cfg["queue_days_avg"],
                   "Demurrage (USD/day)": cfg["demurrage_usd_day"]}
            for vc, draft in VESSEL_CLASS_DRAFT.items():
                row[vc] = "✅ CLEAR" if draft <= cfg["max_draft"] else "🚫 BLOCKED"
            rows.append(row)
        return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# MASTER OPTIMIZATION FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def run_optimization(params: dict) -> dict:
    """
    Unified pipeline function.

    Expected keys in params:
      route, cargo_type, vessel_class, market_event,
      vessel_dwt, distance_nm, baltic_style_index,
      bunker_fuel_price, port_congestion_days,
      port (destination port name),
      cargo_tonnes, required_days,
      wind_speed, wave_height, speed, vessel_age,
      inventory_hold_cost_per_day

    Returns:
      freight_forecast, fuel_forecast, speed_opt,
      timing_decision, ranked_vessels, port_compliance,
      total_landed_cost_breakdown, net_savings_usd, optimal_t_star
    """
    from optimizer import FreightEngine, FuelEngine, TimingEngine, VesselEngine

    # ── Engines (callers should cache these via st.cache_resource) ──────────
    freight_eng = FreightEngine()
    fuel_eng    = FuelEngine()
    timing_eng  = TimingEngine()
    vessel_eng  = VesselEngine()

    today = datetime.date.today()

    # ── 1. Freight Forecast ─────────────────────────────────────────────────
    freight_params = {
        "route":              params["route"],
        "cargo_type":         params["cargo_type"],
        "vessel_class":       params["vessel_class"],
        "market_event":       params.get("market_event", "None"),
        "vessel_dwt":         params["vessel_dwt"],
        "distance_nm":        params["distance_nm"],
        "baltic_style_index": params["baltic_style_index"],
        "bunker_fuel_price":  params["bunker_fuel_price"],
        "port_congestion_days": params.get("port_congestion_days", 1.5),
        "month":              today.month,
        "year":               today.year,
        "week_of_year":       int(today.isocalendar()[1]),
    }
    freight_forecast = freight_eng.forecast_14d(freight_params)

    # ── 2. Fuel Forecast ────────────────────────────────────────────────────
    fuel_forecast = fuel_eng.forecast_bunker_14d(params["bunker_fuel_price"])

    # ── 3. Speed Optimization ───────────────────────────────────────────────
    vessel_row = pd.DataFrame([{
        "vessel_type":     _dwt_to_type(params["vessel_dwt"]),
        "dwt":             params["vessel_dwt"],
        "engine_power":    15_000,
        "vessel_age":      params.get("vessel_age", 8),
        "draft":           VESSEL_CLASS_DRAFT.get(params["vessel_class"], 12.0),
        "speed":           params.get("speed", 14.0),
        "distance_nm":     params["distance_nm"],
        "heading":         90,
        "wind_speed":      params.get("wind_speed", 12.0),
        "wind_direction":  130,
        "wave_height":     params.get("wave_height", 2.0),
        "wave_period":     8,
        "wave_direction":  120,
        "current_speed":   1.2,
        "current_direction": 80,
        "fuel_price":      params["bunker_fuel_price"],
    }])
    speed_opt = fuel_eng.optimize_speed(
        vessel_data=vessel_row,
        fuel_price=params["bunker_fuel_price"],
        required_hours=params["distance_nm"] / 12.0,   # assume 12-knot baseline
    )

    # ── 4. Timing Decision ──────────────────────────────────────────────────
    timing_decision = timing_eng.get_decision(
        dwt=params["vessel_dwt"],
        vessel_age=params.get("vessel_age", 8),
        fuel_price=params["bunker_fuel_price"],
        wind_speed=params.get("wind_speed", 12.0),
        wave_height=params.get("wave_height", 2.0),
        speed=params.get("speed", 14.0),
        distance_nm=params["distance_nm"],
        cargo_tonnes=params["cargo_tonnes"],
        inventory_hold_cost_per_day=params.get("inventory_hold_cost_per_day", 12_000),
    )

    # ── 5. Vessel Ranking + Port Constraints ────────────────────────────────
    port = params.get("port", "Paradip")
    ranked_vessels = vessel_eng.rank(
        cargo_tonnes=params["cargo_tonnes"],
        distance_nm=params["distance_nm"],
        port=port,
        required_days=params.get("required_days", 30),
    )

    # ── 6. Port Compliance Matrix ───────────────────────────────────────────
    port_compliance = vessel_eng.port_compliance_matrix()

    # ── 7. Total Landed Cost ────────────────────────────────────────────────
    port_cfg          = PORT_CONSTRAINTS.get(port, PORT_CONSTRAINTS["Paradip"])
    demurrage_risk    = port_cfg["queue_days_avg"] * port_cfg["demurrage_usd_day"]
    tlc_breakdown = {
        "base_freight":      timing_decision["base_freight"],
        "bunker_surcharge":  timing_decision["bunker_surcharge"],
        "demurrage_risk":    round(demurrage_risk, 2),
        "inventory_hold":    timing_decision["inventory_hold"],
        "total_landed_cost": round(
            timing_decision["base_freight"]
            + timing_decision["bunker_surcharge"]
            + demurrage_risk
            + timing_decision["inventory_hold"],
            2,
        ),
    }

    # ── 8. Net Savings ──────────────────────────────────────────────────────
    net_savings_usd = timing_decision["savings_if_wait"]

    return {
        "freight_forecast":        freight_forecast,
        "fuel_forecast":           fuel_forecast,
        "speed_opt":               speed_opt,
        "timing_decision":         timing_decision,
        "ranked_vessels":          ranked_vessels,
        "port_compliance":         port_compliance,
        "tlc_breakdown":           tlc_breakdown,
        "net_savings_usd":         net_savings_usd,
        "optimal_t_star":          timing_decision["optimal_t_star"],
        "decision":                timing_decision["decision"],
        "decision_label":          timing_decision["decision_label"],
        "port_constraints":        PORT_CONSTRAINTS[port],
    }


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _dwt_to_type(dwt: float) -> str:
    if dwt <= 40_000:
        return "Bulk Carrier"
    elif dwt <= 65_000:
        return "Bulk Carrier"
    elif dwt <= 100_000:
        return "Bulk Carrier"
    else:
        return "Bulk Carrier"


if __name__ == "__main__":
    # Quick smoke test
    test_params = {
        "route":              "Dampier, Australia - Visakhapatnam",
        "cargo_type":         "Coal Ore",
        "vessel_class":       "Panamax",
        "market_event":       "None",
        "vessel_dwt":         78_000,
        "distance_nm":        3_570,
        "baltic_style_index": 1_550,
        "bunker_fuel_price":  640,
        "port_congestion_days": 1.5,
        "port":               "Vizag",
        "cargo_tonnes":       60_000,
        "required_days":      30,
        "wind_speed":         12.0,
        "wave_height":        2.0,
        "speed":              14.0,
        "vessel_age":         8,
        "inventory_hold_cost_per_day": 12_000,
    }
    result = run_optimization(test_params)
    print("Decision:", result["decision_label"])
    print("Net Savings: ${:,.0f}".format(result["net_savings_usd"]))
    print("TLC Breakdown:", result["tlc_breakdown"])
    print("Optimal T*: T+{}".format(result["optimal_t_star"]))
