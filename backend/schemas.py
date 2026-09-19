from pydantic import BaseModel, Field

class OptimizationRequest(BaseModel):
    route: str
    cargo_type: str
    vessel_class: str
    market_event: str = "None"
    vessel_dwt: float = Field(gt=0)
    distance_nm: float = Field(gt=0)
    baltic_style_index: float = Field(gt=0)
    bunker_fuel_price: float = Field(gt=0)
    port_congestion_days: float = Field(ge=0)
    port: str
    cargo_tonnes: float = Field(gt=0)
    required_days: float = Field(gt=0)
    wind_speed: float = Field(ge=0)
    wave_height: float = Field(ge=0)
    speed: float = Field(gt=0)
    vessel_age: float = Field(ge=0)
    inventory_hold_cost_per_day: float = Field(ge=0)
