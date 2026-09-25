from collections.abc import Mapping
from pathlib import Path
import datetime
import math

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from optimizer import (
    FreightEngine,
    FuelEngine,
    TimingEngine,
    VesselEngine,
    PORT_CONSTRAINTS,
    VESSEL_CLASS_DRAFT,
)


ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = ROOT / "frontend" / "dist"


st.set_page_config(
    page_title="Maritime Procurement Desk",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def make_json_safe(value):
    if isinstance(value, Mapping):
        return {
            str(make_json_safe(key)): make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, pd.DataFrame):
        return [
            make_json_safe(row)
            for row in value.to_dict(orient="records")
        ]

    if isinstance(value, pd.Series):
        return [
            make_json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(value, (list, tuple, set)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(value, np.ndarray):
        return [
            make_json_safe(item)
            for item in value.tolist()
        ]

    if isinstance(value, np.generic):
        return make_json_safe(value.item())

    if isinstance(value, float) and (
        math.isnan(value) or math.isinf(value)
    ):
        return None

    return value


# -------------------------------------------------------------------
# CACHE THE EXPENSIVE ML ENGINES
# -------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_engines():
    freight_eng = FreightEngine()
    fuel_eng = FuelEngine()
    timing_eng = TimingEngine()
    vessel_eng = VesselEngine()

    return freight_eng, fuel_eng, timing_eng, vessel_eng


# -------------------------------------------------------------------
# OPTIMIZATION PIPELINE
# -------------------------------------------------------------------

def run_cached_optimization(params):
    (
        freight_eng,
        fuel_eng,
        timing_eng,
        vessel_eng,
    ) = load_engines()

    today = datetime.date.today()

    # ---------------------------------------------------------------
    # 1. Freight Forecast
    # ---------------------------------------------------------------

    freight_params = {
        "route": params["route"],
        "cargo_type": params["cargo_type"],
        "vessel_class": params["vessel_class"],
        "market_event": params.get("market_event", "None"),
        "vessel_dwt": params["vessel_dwt"],
        "distance_nm": params["distance_nm"],
        "baltic_style_index": params["baltic_style_index"],
        "bunker_fuel_price": params["bunker_fuel_price"],
        "port_congestion_days": params.get(
            "port_congestion_days",
            1.5,
        ),
        "month": today.month,
        "year": today.year,
        "week_of_year": int(today.isocalendar()[1]),
    }

    freight_forecast = freight_eng.forecast_14d(
        freight_params
    )

    # ---------------------------------------------------------------
    # 2. Fuel Forecast
    # ---------------------------------------------------------------

    fuel_forecast = fuel_eng.forecast_bunker_14d(
        params["bunker_fuel_price"]
    )

    # ---------------------------------------------------------------
    # 3. Speed Optimization
    # ---------------------------------------------------------------

    vessel_class = params["vessel_class"]

    vessel_row = pd.DataFrame(
        [
            {
                "vessel_type": "Bulk Carrier",
                "dwt": params["vessel_dwt"],
                "engine_power": 15_000,
                "vessel_age": params.get("vessel_age", 8),
                "draft": VESSEL_CLASS_DRAFT.get(
                    vessel_class,
                    12.0,
                ),
                "speed": params.get("speed", 14.0),
                "distance_nm": params["distance_nm"],
                "heading": 90,
                "wind_speed": params.get(
                    "wind_speed",
                    12.0,
                ),
                "wind_direction": 130,
                "wave_height": params.get(
                    "wave_height",
                    2.0,
                ),
                "wave_period": 8,
                "wave_direction": 120,
                "current_speed": 1.2,
                "current_direction": 80,
                "fuel_price": params[
                    "bunker_fuel_price"
                ],
            }
        ]
    )

    speed_opt = fuel_eng.optimize_speed(
        vessel_data=vessel_row,
        fuel_price=params["bunker_fuel_price"],
        required_hours=params["distance_nm"] / 12.0,
    )

    # ---------------------------------------------------------------
    # 4. Charter Timing
    # ---------------------------------------------------------------

    timing_decision = timing_eng.get_decision(
        dwt=params["vessel_dwt"],
        vessel_age=params.get("vessel_age", 8),
        fuel_price=params["bunker_fuel_price"],
        wind_speed=params.get(
            "wind_speed",
            12.0,
        ),
        wave_height=params.get(
            "wave_height",
            2.0,
        ),
        speed=params.get(
            "speed",
            14.0,
        ),
        distance_nm=params["distance_nm"],
        cargo_tonnes=params["cargo_tonnes"],
        inventory_hold_cost_per_day=params.get(
            "inventory_hold_cost_per_day",
            12_000,
        ),
    )

    # ---------------------------------------------------------------
    # 5. Vessel Ranking
    # ---------------------------------------------------------------

    port = params.get(
        "port",
        "Paradip",
    )

    ranked_vessels = vessel_eng.rank(
        cargo_tonnes=params["cargo_tonnes"],
        distance_nm=params["distance_nm"],
        port=port,
        required_days=params.get(
            "required_days",
            30,
        ),
    )

    # ---------------------------------------------------------------
    # 6. Port Compliance
    # ---------------------------------------------------------------

    port_compliance = (
        vessel_eng.port_compliance_matrix()
    )

    # ---------------------------------------------------------------
    # 7. Total Landed Cost
    # ---------------------------------------------------------------

    port_cfg = PORT_CONSTRAINTS.get(
        port,
        PORT_CONSTRAINTS["Paradip"],
    )

    demurrage_risk = (
        port_cfg["queue_days_avg"]
        * port_cfg["demurrage_usd_day"]
    )

    tlc_breakdown = {
        "base_freight": timing_decision[
            "base_freight"
        ],
        "bunker_surcharge": timing_decision[
            "bunker_surcharge"
        ],
        "demurrage_risk": round(
            demurrage_risk,
            2,
        ),
        "inventory_hold": timing_decision[
            "inventory_hold"
        ],
        "total_landed_cost": round(
            timing_decision["base_freight"]
            + timing_decision["bunker_surcharge"]
            + demurrage_risk
            + timing_decision["inventory_hold"],
            2,
        ),
    }

    # ---------------------------------------------------------------
    # 8. Net Savings
    # ---------------------------------------------------------------

    net_savings_usd = timing_decision[
        "savings_if_wait"
    ]

    return {
        "freight_forecast": freight_forecast,
        "fuel_forecast": fuel_forecast,
        "speed_opt": speed_opt,
        "timing_decision": timing_decision,
        "ranked_vessels": ranked_vessels,
        "port_compliance": port_compliance,
        "tlc_breakdown": tlc_breakdown,
        "net_savings_usd": net_savings_usd,
        "optimal_t_star": timing_decision[
            "optimal_t_star"
        ],
        "decision": timing_decision[
            "decision"
        ],
        "decision_label": timing_decision[
            "decision_label"
        ],
        "port_constraints": PORT_CONSTRAINTS[
            port
        ],
    }


# -------------------------------------------------------------------
# FRONTEND CHECK
# -------------------------------------------------------------------

if not FRONTEND_DIST.exists():
    st.error("Frontend build not found.")
    st.code("cd frontend && npm run build")
    st.stop()


# -------------------------------------------------------------------
# STREAMLIT COMPONENT STATE
# -------------------------------------------------------------------

if "last_request_id" not in st.session_state:
    st.session_state.last_request_id = None

if "optimization_result" not in st.session_state:
    st.session_state.optimization_result = None


_component = components.declare_component(
    "maritime_procurement",
    path=str(FRONTEND_DIST),
)


component_value = _component(
    optimization_result=st.session_state.optimization_result,
    key="maritime_procurement_app",
    default=None,
)


# -------------------------------------------------------------------
# HANDLE REACT OPTIMIZATION REQUEST
# -------------------------------------------------------------------

if (
    isinstance(component_value, dict)
    and component_value.get("type")
    == "optimization_request"
):

    request_id = component_value.get(
        "request_id"
    )

    if request_id != st.session_state.last_request_id:

        st.session_state.last_request_id = request_id

        try:
            parameters = component_value.get(
                "parameters",
                {},
            )

            result = run_cached_optimization(
                parameters
            )

            st.session_state.optimization_result = {
                "type": "optimization_result",
                "request_id": request_id,
                "success": True,
                "data": make_json_safe(result),
            }

        except Exception as exc:

            st.session_state.optimization_result = {
                "type": "optimization_result",
                "request_id": request_id,
                "success": False,
                "error": str(exc),
            }

        st.rerun()


st.stop()