import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles
from app.models.enums import UserRole
from app.models.logistics import Vehicle, Shipment
from app.schemas.logistics import (
    VehicleOut, VehicleLocationUpdate, ShipmentOut, ShipmentCreate, ShipmentStatusUpdate,
)
from app.services.ws_manager import manager
from app.models.geo import Route
from app.ai.prediction import recommend_shipment_priority

router = APIRouter(prefix="/api", tags=["logistics"])


# ---------- Vehicles ----------

@router.get("/vehicles", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).filter(Vehicle.is_active == 1).all()


@router.patch("/vehicles/{vehicle_id}/location", response_model=VehicleOut)
async def update_vehicle_location(
    vehicle_id: int, payload: VehicleLocationUpdate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.current_lat = payload.current_lat
    vehicle.current_lng = payload.current_lng
    db.commit()
    db.refresh(vehicle)

    await manager.broadcast("vehicle_update", {
        "id": vehicle.id, "registration_number": vehicle.registration_number,
        "current_lat": vehicle.current_lat, "current_lng": vehicle.current_lng,
    })
    return vehicle


# ---------- Shipments ----------

@router.get("/shipments", response_model=list[ShipmentOut])
def list_shipments(status: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Shipment)
    if status:
        q = q.filter(Shipment.status == status)
    if category:
        q = q.filter(Shipment.category == category)
    return q.order_by(Shipment.created_at.desc()).all()


@router.get("/shipments/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@router.post("/shipments", response_model=ShipmentOut, status_code=201)
async def create_shipment(
    payload: ShipmentCreate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    shipment = Shipment(
        tracking_code=f"SMH-{uuid.uuid4().hex[:6].upper()}",
        **payload.model_dump(),
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    await manager.broadcast("shipment_created", {
        "id": shipment.id, "tracking_code": shipment.tracking_code,
        "category": shipment.category.value, "priority": shipment.priority.value,
    })
    return shipment


@router.get("/shipments/{shipment_id}/priority-recommendation")
def shipment_priority_recommendation(shipment_id: int, db: Session = Depends(get_db)):
    """
    AI prediction endpoint: should this shipment's priority be escalated,
    given the current risk score of the route it's travelling on?
    """
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    route_risk_score = 0
    if shipment.route_id:
        route = db.query(Route).filter(Route.id == shipment.route_id).first()
        if route:
            route_risk_score = route.current_risk_score

    result = recommend_shipment_priority(
        category=shipment.category.value,
        route_risk_score=route_risk_score,
        current_priority=shipment.priority,
    )
    return {
        "shipment_id": shipment.id,
        "tracking_code": shipment.tracking_code,
        "current_priority": shipment.priority.value,
        "route_risk_score": route_risk_score,
        **result,
    }


@router.patch("/shipments/{shipment_id}/status", response_model=ShipmentOut)
async def update_shipment_status(
    shipment_id: int, payload: ShipmentStatusUpdate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment.status = payload.status
    db.commit()
    db.refresh(shipment)

    await manager.broadcast("shipment_update", {
        "id": shipment.id, "tracking_code": shipment.tracking_code, "status": shipment.status.value,
    })
    return shipment
