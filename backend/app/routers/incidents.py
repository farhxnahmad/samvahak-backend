from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.session import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole, IncidentStatus
from app.models.incident import Incident
from app.schemas.incident import IncidentOut, IncidentCreate, IncidentStatusUpdate
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    state_id: int | None = None,
    status: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Incident)
    if state_id is not None:
        q = q.filter(Incident.state_id == state_id)
    if status:
        q = q.filter(Incident.status == status)
    if severity:
        q = q.filter(Incident.severity == severity)
    return q.order_by(Incident.reported_at.desc()).all()


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("", response_model=IncidentOut, status_code=201)
async def create_incident(
    payload: IncidentCreate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    incident = Incident(**payload.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)

    await manager.broadcast("incident_new", {
        "id": incident.id, "type": incident.type.value, "severity": incident.severity.value,
        "title": incident.title, "state_id": incident.state_id, "district_id": incident.district_id,
        "latitude": incident.latitude, "longitude": incident.longitude,
    })
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentOut)
async def update_incident_status(
    incident_id: int, payload: IncidentStatusUpdate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = payload.status
    if payload.status == IncidentStatus.RESOLVED:
        incident.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(incident)

    await manager.broadcast("incident_update", {
        "id": incident.id, "status": incident.status.value,
    })
    return incident
