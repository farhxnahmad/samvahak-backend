from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole, RouteStatus, IncidentStatus, ShipmentStatus, ShipmentPriority
from app.models.geo import State, Route
from app.models.incident import Incident
from app.models.logistics import Vehicle, Shipment
from app.models.misc import WeatherRecord, Notification
from app.schemas.operations import (
    WeatherRecordOut, WeatherRecordCreate, NotificationOut, DashboardStats,
)
from app.services.ws_manager import manager

router = APIRouter(prefix="/api", tags=["operations"])


# ---------- Weather ----------

@router.get("/weather", response_model=list[WeatherRecordOut])
def list_weather(district_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(WeatherRecord)
    if district_id is not None:
        q = q.filter(WeatherRecord.district_id == district_id)
    return q.order_by(WeatherRecord.recorded_at.desc()).limit(100).all()


@router.post("/weather", response_model=WeatherRecordOut, status_code=201)
async def record_weather(
    payload: WeatherRecordCreate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER)),
):
    """
    Manual entry point for now (IMD feed integration is a future external
    integration point — see README). Broadcasts so dashboards update live.
    """
    record = WeatherRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)

    await manager.broadcast("weather_update", {
        "district_id": record.district_id, "rainfall_mm": record.rainfall_mm,
        "condition": record.condition, "alert_level": record.alert_level,
    })
    return record


# ---------- Notifications ----------

@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Notification)
    if unread_only:
        q = q.filter(Notification.is_read == 0)
    return q.order_by(Notification.created_at.desc()).limit(100).all()


@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = 1
    db.commit()
    db.refresh(notif)
    return notif


# ---------- Dashboard stats ----------

@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    """Single aggregate endpoint the Command Dashboard's KPI cards call on load."""
    total_routes = db.query(Route).count()
    accessible = db.query(Route).filter(Route.status == RouteStatus.ACCESSIBLE).count()
    at_risk = db.query(Route).filter(Route.status == RouteStatus.AT_RISK).count()
    blocked = db.query(Route).filter(Route.status == RouteStatus.BLOCKED).count()

    active_incidents = db.query(Incident).filter(
        Incident.status.in_([IncidentStatus.REPORTED, IncidentStatus.VERIFIED, IncidentStatus.IN_PROGRESS])
    ).count()

    active_shipments = db.query(Shipment).filter(
        Shipment.status.in_([ShipmentStatus.PENDING, ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELAYED])
    ).count()
    emergency_shipments = db.query(Shipment).filter(
        Shipment.priority == ShipmentPriority.EMERGENCY,
        Shipment.status.in_([ShipmentStatus.PENDING, ShipmentStatus.IN_TRANSIT, ShipmentStatus.DELAYED]),
    ).count()

    active_vehicles = db.query(Vehicle).filter(Vehicle.is_active == 1).count()
    unread_notifications = db.query(Notification).filter(Notification.is_read == 0).count()
    states_covered = db.query(State).count()

    return DashboardStats(
        total_routes=total_routes,
        accessible_routes=accessible,
        at_risk_routes=at_risk,
        blocked_routes=blocked,
        active_incidents=active_incidents,
        active_shipments=active_shipments,
        emergency_shipments=emergency_shipments,
        active_vehicles=active_vehicles,
        unread_notifications=unread_notifications,
        states_covered=states_covered,
    )
