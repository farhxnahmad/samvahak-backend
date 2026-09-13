from pydantic import BaseModel
from datetime import datetime

from app.models.enums import ShipmentCategory, ShipmentStatus, ShipmentPriority


class VehicleOut(BaseModel):
    id: int
    registration_number: str
    vehicle_type: str
    driver_name: str
    driver_phone: str | None = None
    current_lat: float
    current_lng: float
    is_active: int
    last_updated: datetime | None = None

    class Config:
        from_attributes = True


class VehicleLocationUpdate(BaseModel):
    current_lat: float
    current_lng: float


class ShipmentOut(BaseModel):
    id: int
    tracking_code: str
    category: ShipmentCategory
    description: str | None = None
    vehicle_id: int | None = None
    route_id: int | None = None
    origin_name: str
    destination_name: str
    destination_lat: float
    destination_lng: float
    status: ShipmentStatus
    priority: ShipmentPriority
    eta: datetime | None = None
    dispatched_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ShipmentCreate(BaseModel):
    category: ShipmentCategory
    description: str | None = None
    vehicle_id: int | None = None
    route_id: int | None = None
    origin_name: str
    destination_name: str
    destination_lat: float
    destination_lng: float
    priority: ShipmentPriority = ShipmentPriority.ROUTINE


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
