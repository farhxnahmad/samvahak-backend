from pydantic import BaseModel
from datetime import datetime

from app.models.enums import RouteStatus, RiskLevel


class StateOut(BaseModel):
    id: int
    name: str
    code: str
    capital: str
    center_lat: float
    center_lng: float

    class Config:
        from_attributes = True


class DistrictOut(BaseModel):
    id: int
    name: str
    state_id: int
    center_lat: float
    center_lng: float
    population: int | None = None

    class Config:
        from_attributes = True


class RoadOut(BaseModel):
    id: int
    name: str
    road_type: str
    district_id: int
    length_km: float
    status: RouteStatus
    landslide_history_score: float

    class Config:
        from_attributes = True


class RouteOut(BaseModel):
    id: int
    name: str
    source_name: str
    source_lat: float
    source_lng: float
    destination_name: str
    destination_lat: float
    destination_lng: float
    distance_km: float
    normal_eta_minutes: int
    status: RouteStatus
    current_risk_score: int
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class RouteIntelligenceRequest(BaseModel):
    source_lat: float
    source_lng: float
    source_name: str = "Selected origin"
    destination_lat: float
    destination_lng: float
    destination_name: str = "Selected destination"


class RouteOption(BaseModel):
    label: str  # "safest" | "fastest" | "alternate"
    distance_km: float
    eta_minutes: int
    risk_score: int
    risk_level: RiskLevel
    predicted_delay_minutes: int
    factors: list[str]


class RouteIntelligenceResponse(BaseModel):
    source_name: str
    destination_name: str
    options: list[RouteOption]
