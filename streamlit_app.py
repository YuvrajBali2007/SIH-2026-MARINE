from collections.abc import Mapping
from pathlib import Path
import math

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from optimizer import run_optimization


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


if not FRONTEND_DIST.exists():
    st.error("Frontend build not found.")
    st.code("cd frontend && npm run build")
    st.stop()


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


if (
    isinstance(component_value, dict)
    and component_value.get("type") == "optimization_request"
):
    request_id = component_value.get("request_id")

    if request_id != st.session_state.last_request_id:
        st.session_state.last_request_id = request_id

        try:
            parameters = component_value.get("parameters", {})

            result = run_optimization(parameters)

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