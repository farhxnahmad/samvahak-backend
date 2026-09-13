from pydantic import BaseModel
from datetime import datetime

from app.models.enums import CitizenReportStatus


class CitizenReportCreate(BaseModel):
    client_uuid: str  # generated on-device, even while offline — makes sync idempotent
    issue_type: str
    description: str | None = None
    photo_url: str | None = None
    latitude: float
    longitude: float
    # timestamp the report was actually created on the device (may be in the past
    # if this arrives via delayed offline sync)
    captured_at: datetime | None = None


class CitizenReportOut(BaseModel):
    id: int
    client_uuid: str
    reporter_id: int | None = None
    issue_type: str
    description: str | None = None
    photo_url: str | None = None
    latitude: float
    longitude: float
    status: CitizenReportStatus
    submitted_at: datetime | None = None
    synced_from_offline: int

    class Config:
        from_attributes = True


class CitizenReportStatusUpdate(BaseModel):
    status: CitizenReportStatus


class OfflineSyncBatch(BaseModel):
    """A device sends a batch of everything it queued while offline."""
    reports: list[CitizenReportCreate]


class OfflineSyncResult(BaseModel):
    accepted: int
    duplicates: int
    reports: list[CitizenReportOut]
