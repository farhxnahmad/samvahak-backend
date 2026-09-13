from pydantic import BaseModel
from datetime import datetime

from app.models.enums import IncidentType, IncidentSeverity, IncidentStatus


class IncidentOut(BaseModel):
    id: int
    type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    title: str
    description: str | None = None
    state_id: int
    district_id: int
    road_id: int | None = None
    latitude: float
    longitude: float
    reported_at: datetime | None = None
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True


class IncidentCreate(BaseModel):
    type: IncidentType
    severity: IncidentSeverity
    title: str
    description: str | None = None
    state_id: int
    district_id: int
    road_id: int | None = None
    latitude: float
    longitude: float


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus
