from pydantic import BaseModel
from datetime import datetime

from app.models.enums import NotificationSeverity


class WeatherRecordOut(BaseModel):
    id: int
    district_id: int
    recorded_at: datetime | None = None
    rainfall_mm: float
    temperature_c: float | None = None
    condition: str
    alert_level: str

    class Config:
        from_attributes = True


class WeatherRecordCreate(BaseModel):
    district_id: int
    rainfall_mm: float = 0.0
    temperature_c: float | None = None
    condition: str = "clear"
    alert_level: str = "none"


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    severity: NotificationSeverity
    state_id: int | None = None
    is_read: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_routes: int
    accessible_routes: int
    at_risk_routes: int
    blocked_routes: int
    active_incidents: int
    active_shipments: int
    emergency_shipments: int
    active_vehicles: int
    unread_notifications: int
    states_covered: int
