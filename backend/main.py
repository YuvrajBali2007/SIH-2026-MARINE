from collections.abc import Mapping
import math
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import OptimizationRequest
from optimizer import run_optimization

app = FastAPI(title="SAIL Maritime Procurement API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_json_safe(value):
    if isinstance(value, Mapping):
        return {str(make_json_safe(k)): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, pd.DataFrame):
        return [make_json_safe(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return [make_json_safe(v) for v in value.tolist()]
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return [make_json_safe(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return make_json_safe(value.item())
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value

@app.get("/")
def root():
    return {"message": "SAIL Maritime Procurement API is running", "status": "ok"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/optimization/run")
def run_optimization_api(request: OptimizationRequest):
    result = run_optimization(request.model_dump())
    return make_json_safe(result)
