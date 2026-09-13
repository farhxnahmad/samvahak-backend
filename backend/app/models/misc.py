from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import RiskLevel, NotificationSeverity


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    rainfall_mm = Column(Float, default=0.0)
    temperature_c = Column(Float, nullable=True)
    condition = Column(String(60), nullable=False, default="clear")  # clear/rain/storm/fog
    alert_level = Column(String(20), nullable=False, default="none")  # none/watch/warning/severe


class RoutePrediction(Base):
    """Snapshot of an AI risk assessment for a route, kept for analytics/history."""
    __tablename__ = "route_predictions"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    risk_score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(Enum(RiskLevel), nullable=False)
    predicted_delay_minutes = Column(Integer, default=0)
    factors = Column(JSON, nullable=True)  # list of explanation strings
    generated_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(Enum(NotificationSeverity), nullable=False, default=NotificationSeverity.INFO)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
