from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_roles
from app.models.enums import UserRole
from app.models.user import User
from app.models.citizen_report import CitizenReport
from app.schemas.citizen_report import (
    CitizenReportOut, CitizenReportCreate, CitizenReportStatusUpdate,
    OfflineSyncBatch, OfflineSyncResult,
)
from app.services.ws_manager import manager

router = APIRouter(prefix="/api/citizen-reports", tags=["citizen-reports"])


def _get_or_create(db: Session, payload: CitizenReportCreate, reporter_id: int | None, synced_offline: bool) -> tuple[CitizenReport, bool]:
    """
    Idempotent insert keyed on client_uuid — the same report submitted twice
    (e.g. a retried offline sync) is never duplicated. Returns (report, created).
    """
    existing = db.query(CitizenReport).filter(CitizenReport.client_uuid == payload.client_uuid).first()
    if existing:
        return existing, False

    report = CitizenReport(
        client_uuid=payload.client_uuid,
        reporter_id=reporter_id,
        issue_type=payload.issue_type,
        description=payload.description,
        photo_url=payload.photo_url,
        latitude=payload.latitude,
        longitude=payload.longitude,
        synced_from_offline=1 if synced_offline else 0,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report, True


@router.get("", response_model=list[CitizenReportOut])
def list_reports(
    status: str | None = None, issue_type: str | None = None, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    q = db.query(CitizenReport)
    if status:
        q = q.filter(CitizenReport.status == status)
    if issue_type:
        q = q.filter(CitizenReport.issue_type == issue_type)
    return q.order_by(CitizenReport.submitted_at.desc()).all()


@router.get("/{report_id}", response_model=CitizenReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/track/{client_uuid}", response_model=CitizenReportOut)
def track_report_by_client_uuid(client_uuid: str, db: Session = Depends(get_db)):
    """Lets a citizen check status of their own report without logging in, via the local ID their device kept."""
    report = db.query(CitizenReport).filter(CitizenReport.client_uuid == client_uuid).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("", response_model=CitizenReportOut, status_code=201)
async def submit_report(payload: CitizenReportCreate, db: Session = Depends(get_db)):
    """Live (online) submission — open to anyone, including anonymous citizens."""
    report, created = _get_or_create(db, payload, reporter_id=None, synced_offline=False)
    if created:
        await manager.broadcast("citizen_report_new", {
            "id": report.id, "issue_type": report.issue_type,
            "latitude": report.latitude, "longitude": report.longitude,
        })
    return report


@router.post("/sync", response_model=OfflineSyncResult)
async def sync_offline_reports(payload: OfflineSyncBatch, db: Session = Depends(get_db)):
    """
    Called by the frontend once connectivity returns, with everything the
    device queued locally while offline. Safe to call repeatedly / partially —
    already-synced reports are recognized by client_uuid and skipped.
    """
    accepted, duplicates, results = 0, 0, []
    for item in payload.reports:
        report, created = _get_or_create(db, item, reporter_id=None, synced_offline=True)
        results.append(report)
        if created:
            accepted += 1
            await manager.broadcast("citizen_report_new", {
                "id": report.id, "issue_type": report.issue_type,
                "latitude": report.latitude, "longitude": report.longitude,
            })
        else:
            duplicates += 1

    return OfflineSyncResult(accepted=accepted, duplicates=duplicates, reports=results)


@router.patch("/{report_id}/status", response_model=CitizenReportOut)
async def update_report_status(
    report_id: int, payload: CitizenReportStatusUpdate, db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER, UserRole.FIELD_STAFF)),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = payload.status
    db.commit()
    db.refresh(report)

    await manager.broadcast("citizen_report_update", {"id": report.id, "status": report.status.value})
    return report
