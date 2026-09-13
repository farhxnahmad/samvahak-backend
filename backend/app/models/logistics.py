from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import ShipmentCategory, ShipmentStatus, ShipmentPriority


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(30), unique=True, nullable=False)
    vehicle_type = Column(String(40), nullable=False, default="truck")
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(20), nullable=True)
    current_lat = Column(Float, nullable=False)
    current_lng = Column(Float, nullable=False)
    is_active = Column(Integer, default=1)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    shipments = relationship("Shipment", back_populates="vehicle")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String(30), unique=True, nullable=False)
    category = Column(Enum(ShipmentCategory), nullable=False)
    description = Column(String(255), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    origin_name = Column(String(120), nullable=False)
    destination_name = Column(String(120), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    status = Column(Enum(ShipmentStatus), nullable=False, default=ShipmentStatus.PENDING)
    priority = Column(Enum(ShipmentPriority), nullable=False, default=ShipmentPriority.ROUTINE)
    eta = Column(DateTime(timezone=True), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="shipments")
