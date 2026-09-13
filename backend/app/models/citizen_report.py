from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Text
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import CitizenReportStatus


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)
    # client_uuid lets the offline-first frontend generate an ID while offline,
    # so re-sending after reconnecting doesn't create duplicates (idempotent upsert).
    client_uuid = Column(String(64), unique=True, nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    issue_type = Column(String(60), nullable=False)
    description = Column(Text, nullable=True)
    photo_url = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(Enum(CitizenReportStatus), nullable=False, default=CitizenReportStatus.SUBMITTED)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    # True if this row was created via a delayed offline-sync rather than live submission
    synced_from_offline = Column(Integer, default=0)
