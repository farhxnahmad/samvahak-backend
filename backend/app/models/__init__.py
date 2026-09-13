"""
Import every model here so that Base.metadata.create_all() and Alembic's
autogenerate can discover all tables from a single import of this package.
"""
from app.models.user import User
from app.models.geo import State, District, Road, Route
from app.models.logistics import Vehicle, Shipment
from app.models.incident import Incident
from app.models.citizen_report import CitizenReport
from app.models.misc import WeatherRecord, RoutePrediction, Notification

__all__ = [
    "User",
    "State",
    "District",
    "Road",
    "Route",
    "Vehicle",
    "Shipment",
    "Incident",
    "CitizenReport",
    "WeatherRecord",
    "RoutePrediction",
    "Notification",
]
