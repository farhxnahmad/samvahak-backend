from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.db.session import Base
from app.models.enums import RouteStatus


class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)  # e.g. "AS", "AR"
    capital = Column(String(80), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)

    districts = relationship("District", back_populates="state")


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    population = Column(Integer, nullable=True)
    is_hilly_terrain = Column(Integer, default=1)  # 1/0 flag, kept simple

    state = relationship("State", back_populates="districts")


class Road(Base):
    """A physical road segment. geometry is a PostGIS LineString (lng/lat pairs)."""
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    road_type = Column(String(40), nullable=False, default="state_highway")
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    length_km = Column(Float, nullable=False)
    status = Column(Enum(RouteStatus), nullable=False, default=RouteStatus.ACCESSIBLE)
    landslide_history_score = Column(Float, default=0.0)  # 0-1, historical frequency
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)

    district = relationship("District")


class Route(Base):
    """A named source->destination route composed conceptually of one or more roads."""
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    source_lat = Column(Float, nullable=False)
    source_lng = Column(Float, nullable=False)
    source_name = Column(String(120), nullable=False)
    destination_lat = Column(Float, nullable=False)
    destination_lng = Column(Float, nullable=False)
    destination_name = Column(String(120), nullable=False)
    distance_km = Column(Float, nullable=False)
    normal_eta_minutes = Column(Integer, nullable=False)
    status = Column(Enum(RouteStatus), nullable=False, default=RouteStatus.ACCESSIBLE)
    current_risk_score = Column(Integer, default=0)  # 0-100, updated by AI service
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
