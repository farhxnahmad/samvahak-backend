"""
Seed the database with realistic demo data for all 8 North Eastern states.
Run with:  python -m app.db.seed
(Run AFTER alembic upgrade head has created the tables.)
"""
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal, engine, Base
from app.models.user import User
from app.models.geo import State, District, Road, Route
from app.models.logistics import Vehicle, Shipment
from app.models.incident import Incident
from app.models.misc import WeatherRecord, Notification
from app.models.enums import (
    UserRole, RouteStatus, IncidentType, IncidentSeverity, IncidentStatus,
    ShipmentCategory, ShipmentStatus, ShipmentPriority, NotificationSeverity,
)
from app.core.security import hash_password

# --- Real NER states with actual capitals and approximate coordinates ---
STATES = [
    {"name": "Assam", "code": "AS", "capital": "Dispur", "center_lat": 26.2006, "center_lng": 92.9376},
    {"name": "Arunachal Pradesh", "code": "AR", "capital": "Itanagar", "center_lat": 28.2180, "center_lng": 94.7278},
    {"name": "Meghalaya", "code": "ML", "capital": "Shillong", "center_lat": 25.4670, "center_lng": 91.3662},
    {"name": "Manipur", "code": "MN", "capital": "Imphal", "center_lat": 24.6637, "center_lng": 93.9063},
    {"name": "Mizoram", "code": "MZ", "capital": "Aizawl", "center_lat": 23.1645, "center_lng": 92.9376},
    {"name": "Nagaland", "code": "NL", "capital": "Kohima", "center_lat": 25.6751, "center_lng": 94.1086},
    {"name": "Tripura", "code": "TR", "capital": "Agartala", "center_lat": 23.9408, "center_lng": 91.9882},
    {"name": "Sikkim", "code": "SK", "capital": "Gangtok", "center_lat": 27.3389, "center_lng": 88.6065},
]

# A few real districts per state, with approximate centers
DISTRICTS = {
    "AS": [("Kamrup Metropolitan", 26.1445, 91.7362), ("Dibrugarh", 27.4728, 94.9120), ("Silchar (Cachar)", 24.8333, 92.7789)],
    "AR": [("Papum Pare", 27.1000, 93.6167), ("West Kameng", 27.2333, 92.4000), ("Lower Dibang Valley", 28.0667, 95.7500)],
    "ML": [("East Khasi Hills", 25.5788, 91.8933), ("West Garo Hills", 25.5138, 90.2201), ("Jaintia Hills", 25.4500, 92.2000)],
    "MN": [("Imphal West", 24.8170, 93.9368), ("Churachandpur", 24.3333, 93.6833), ("Ukhrul", 25.1167, 94.3667)],
    "MZ": [("Aizawl", 23.7271, 92.7176), ("Lunglei", 22.8879, 92.7343), ("Champhai", 23.4667, 93.3167)],
    "NL": [("Kohima", 25.6701, 94.1077), ("Dimapur", 25.9091, 93.7266), ("Mon", 26.7500, 95.0500)],
    "TR": [("West Tripura", 23.8315, 91.2868), ("Gomati", 23.5000, 91.5667), ("Dhalai", 23.9333, 91.8667)],
    "SK": [("East Sikkim", 27.3389, 88.6065), ("North Sikkim", 27.7167, 88.6167), ("West Sikkim", 27.2833, 88.2167)],
}

DEMO_USERS = [
    {"full_name": "Admin User", "email": "admin@samvahak.gov.in", "password": "Admin@123", "role": UserRole.ADMIN},
    {"full_name": "Rina Bora (Officer)", "email": "officer@samvahak.gov.in", "password": "Officer@123", "role": UserRole.GOVERNMENT_OFFICER},
    {"full_name": "Tenzing Lepcha (Field Staff)", "email": "field@samvahak.gov.in", "password": "Field@123", "role": UserRole.FIELD_STAFF},
    {"full_name": "Citizen Demo", "email": "citizen@samvahak.gov.in", "password": "Citizen@123", "role": UserRole.CITIZEN},
]


def run():
    Base.metadata.create_all(bind=engine)  # safety net for local/demo use
    db = SessionLocal()
    try:
        if db.query(State).first():
            print("Seed data already present — skipping.")
            return

        state_objs = {}
        for s in STATES:
            obj = State(**s)
            db.add(obj)
            state_objs[s["code"]] = obj
        db.flush()

        district_objs = []
        for code, districts in DISTRICTS.items():
            for name, lat, lng in districts:
                d = District(name=name, state_id=state_objs[code].id, center_lat=lat, center_lng=lng,
                              population=250000, is_hilly_terrain=1)
                db.add(d)
                district_objs.append(d)
        db.flush()

        for u in DEMO_USERS:
            db.add(User(
                full_name=u["full_name"], email=u["email"],
                hashed_password=hash_password(u["password"]), role=u["role"],
                preferred_language="en",
            ))

        # A handful of realistic routes connecting real towns
        routes = [
            Route(name="Guwahati - Shillong", source_name="Guwahati", source_lat=26.1445, source_lng=91.7362,
                  destination_name="Shillong", destination_lat=25.5788, destination_lng=91.8933,
                  distance_km=100, normal_eta_minutes=150, status=RouteStatus.ACCESSIBLE, current_risk_score=22),
            Route(name="Imphal - Ukhrul", source_name="Imphal", source_lat=24.8170, source_lng=93.9368,
                  destination_name="Ukhrul", destination_lat=25.1167, destination_lng=94.3667,
                  distance_km=83, normal_eta_minutes=180, status=RouteStatus.AT_RISK, current_risk_score=64),
            Route(name="Aizawl - Lunglei", source_name="Aizawl", source_lat=23.7271, source_lng=92.7176,
                  destination_name="Lunglei", destination_lat=22.8879, destination_lng=92.7343,
                  distance_km=160, normal_eta_minutes=300, status=RouteStatus.ACCESSIBLE, current_risk_score=35),
            Route(name="Itanagar - Ziro (Lower Dibang link)", source_name="Itanagar", source_lat=27.1000, source_lng=93.6167,
                  destination_name="Lower Dibang Valley", destination_lat=28.0667, destination_lng=95.7500,
                  distance_km=210, normal_eta_minutes=420, status=RouteStatus.BLOCKED, current_risk_score=88),
            Route(name="Agartala - Dhalai", source_name="Agartala", source_lat=23.8315, source_lng=91.2868,
                  destination_name="Dhalai", destination_lat=23.9333, destination_lng=91.8667,
                  distance_km=60, normal_eta_minutes=100, status=RouteStatus.ACCESSIBLE, current_risk_score=18),
            Route(name="Gangtok - North Sikkim (Lachen road)", source_name="Gangtok", source_lat=27.3389, source_lng=88.6065,
                  destination_name="North Sikkim", destination_lat=27.7167, destination_lng=88.6167,
                  distance_km=110, normal_eta_minutes=240, status=RouteStatus.AT_RISK, current_risk_score=71),
        ]
        for r in routes:
            db.add(r)
        db.flush()

        # Vehicles + shipments riding on some of those routes
        vehicles = [
            Vehicle(registration_number="AS-01-GT-4521", vehicle_type="truck", driver_name="Biju Hazarika",
                    driver_phone="9800000001", current_lat=26.05, current_lng=91.80),
            Vehicle(registration_number="MN-02-IM-1187", vehicle_type="mini_truck", driver_name="Rajkumar Singh",
                    driver_phone="9800000002", current_lat=24.90, current_lng=94.05),
            Vehicle(registration_number="MZ-01-AZ-0932", vehicle_type="truck", driver_name="David Lalrinliana",
                    driver_phone="9800000003", current_lat=23.40, current_lng=92.75),
        ]
        for v in vehicles:
            db.add(v)
        db.flush()

        shipments = [
            Shipment(tracking_code="SMH-1001", category=ShipmentCategory.MEDICINE,
                     description="Cold-chain vaccines and essential medicines",
                     vehicle_id=vehicles[0].id, route_id=routes[0].id,
                     origin_name="Guwahati Medical Store Depot", destination_name="Shillong Civil Hospital",
                     destination_lat=25.5788, destination_lng=91.8933,
                     status=ShipmentStatus.IN_TRANSIT, priority=ShipmentPriority.EMERGENCY,
                     eta=datetime.now(timezone.utc) + timedelta(hours=2), dispatched_at=datetime.now(timezone.utc) - timedelta(hours=1)),
            Shipment(tracking_code="SMH-1002", category=ShipmentCategory.RELIEF_MATERIALS,
                     description="Tarpaulins, blankets and dry ration for flood-affected families",
                     vehicle_id=vehicles[1].id, route_id=routes[1].id,
                     origin_name="Imphal Relief Warehouse", destination_name="Ukhrul Relief Camp",
                     destination_lat=25.1167, destination_lng=94.3667,
                     status=ShipmentStatus.DELAYED, priority=ShipmentPriority.URGENT,
                     eta=datetime.now(timezone.utc) + timedelta(hours=5), dispatched_at=datetime.now(timezone.utc) - timedelta(hours=3)),
            Shipment(tracking_code="SMH-1003", category=ShipmentCategory.CONSTRUCTION_MATERIALS,
                     description="Steel girders for bridge repair",
                     vehicle_id=vehicles[2].id, route_id=routes[2].id,
                     origin_name="Aizawl PWD Yard", destination_name="Lunglei Bridge Site",
                     destination_lat=22.8879, destination_lng=92.7343,
                     status=ShipmentStatus.PENDING, priority=ShipmentPriority.ROUTINE,
                     eta=datetime.now(timezone.utc) + timedelta(hours=8)),
        ]
        for s in shipments:
            db.add(s)

        # Incidents matching the risky routes above
        incidents = [
            Incident(type=IncidentType.LANDSLIDE, severity=IncidentSeverity.HIGH, status=IncidentStatus.VERIFIED,
                     title="Landslide blocks NH near Roing approach",
                     description="Heavy debris flow after continuous rainfall; single-lane traffic only.",
                     state_id=state_objs["AR"].id, district_id=district_objs[5].id,
                     latitude=27.9, longitude=95.5),
            Incident(type=IncidentType.FLOOD, severity=IncidentSeverity.SEVERE, status=IncidentStatus.IN_PROGRESS,
                     title="Flash flooding cuts off Ukhrul road link",
                     description="River overflow has submerged a 200m stretch of the highway.",
                     state_id=state_objs["MN"].id, district_id=district_objs[11].id,
                     latitude=25.0, longitude=94.3),
            Incident(type=IncidentType.HEAVY_RAINFALL, severity=IncidentSeverity.MODERATE, status=IncidentStatus.REPORTED,
                     title="Heavy rainfall warning — Lachen corridor",
                     description="IMD advisory of continuous heavy rain over next 48 hours.",
                     state_id=state_objs["SK"].id, district_id=district_objs[22].id,
                     latitude=27.7, longitude=88.6),
        ]
        for i in incidents:
            db.add(i)

        # A little weather + notifications so the dashboard doesn't feel empty
        db.add(WeatherRecord(district_id=district_objs[5].id, rainfall_mm=145.2, temperature_c=19.5,
                              condition="storm", alert_level="severe"))
        db.add(WeatherRecord(district_id=district_objs[11].id, rainfall_mm=98.0, temperature_c=24.0,
                              condition="rain", alert_level="warning"))
        db.add(Notification(title="Route blocked: Itanagar - Lower Dibang Valley",
                              message="Landslide has fully blocked this route. Reroute via alternate NH advised.",
                              severity=NotificationSeverity.CRITICAL, state_id=state_objs["AR"].id))
        db.add(Notification(title="Emergency shipment dispatched",
                              message="SMH-1001 (medicines) dispatched to Shillong Civil Hospital.",
                              severity=NotificationSeverity.INFO, state_id=state_objs["ML"].id))

        db.commit()
        print("Seed data inserted successfully.")
        print("Demo logins:")
        for u in DEMO_USERS:
            print(f"  {u['role'].value:20s} {u['email']:30s} {u['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
