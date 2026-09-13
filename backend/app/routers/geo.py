from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import require_roles
from app.models.enums import UserRole
from app.models.geo import State, District, Road, Route
from app.models.incident import Incident
from app.models.misc import WeatherRecord
from app.schemas.geo import (
    StateOut, DistrictOut, RoadOut, RouteOut,
    RouteIntelligenceRequest, RouteIntelligenceResponse, RouteOption,
)
from app.ai.prediction import assess_route_risk, generate_route_options

router = APIRouter(prefix="/api", tags=["geo"])


@router.get("/states", response_model=list[StateOut])
def list_states(db: Session = Depends(get_db)):
    return db.query(State).order_by(State.name).all()


@router.get("/states/{state_id}/districts", response_model=list[DistrictOut])
def list_districts_for_state(state_id: int, db: Session = Depends(get_db)):
    return db.query(District).filter(District.state_id == state_id).order_by(District.name).all()


@router.get("/districts", response_model=list[DistrictOut])
def list_all_districts(db: Session = Depends(get_db)):
    return db.query(District).order_by(District.name).all()


@router.get("/roads", response_model=list[RoadOut])
def list_roads(district_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Road)
    if district_id is not None:
        q = q.filter(Road.district_id == district_id)
    return q.all()


@router.get("/routes", response_model=list[RouteOut])
def list_routes(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Route)
    if status:
        q = q.filter(Route.status == status)
    return q.order_by(Route.current_risk_score.desc()).all()


@router.get("/routes/{route_id}", response_model=RouteOut)
def get_route(route_id: int, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.get("/routes/{route_id}/risk")
def get_route_risk(route_id: int, db: Session = Depends(get_db)):
    """Live AI risk assessment for a saved named route (Command Dashboard uses this)."""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Pull incidents/weather in a loose bounding box around the route's midpoint
    mid_lat = (route.source_lat + route.destination_lat) / 2
    mid_lng = (route.source_lng + route.destination_lng) / 2
    box = 1.0  # degrees, ~110km — generous for an MVP corridor match
    incidents = db.query(Incident).filter(
        Incident.latitude.between(mid_lat - box, mid_lat + box),
        Incident.longitude.between(mid_lng - box, mid_lng + box),
    ).all()
    weather = db.query(WeatherRecord).order_by(WeatherRecord.recorded_at.desc()).limit(20).all()

    result = assess_route_risk(route, incidents, weather)

    # Keep the route's cached risk score fresh for list views/map coloring
    route.current_risk_score = result["risk_score"]
    db.commit()

    return {"route_id": route.id, **result, "risk_level": result["risk_level"].value}


@router.post("/route-intelligence", response_model=RouteIntelligenceResponse)
def route_intelligence(payload: RouteIntelligenceRequest, db: Session = Depends(get_db)):
    """
    Core Route Intelligence page endpoint: given any source/destination, return
    safest/fastest/alternate options with AI risk scoring for each.
    """
    mid_lat = (payload.source_lat + payload.destination_lat) / 2
    mid_lng = (payload.source_lng + payload.destination_lng) / 2
    box = 1.0
    incidents = db.query(Incident).filter(
        Incident.latitude.between(mid_lat - box, mid_lat + box),
        Incident.longitude.between(mid_lng - box, mid_lng + box),
    ).all()
    weather = db.query(WeatherRecord).order_by(WeatherRecord.recorded_at.desc()).limit(20).all()

    options = generate_route_options(
        payload.source_lat, payload.source_lng, payload.source_name,
        payload.destination_lat, payload.destination_lng, payload.destination_name,
        incidents, weather,
    )
    return RouteIntelligenceResponse(
        source_name=payload.source_name,
        destination_name=payload.destination_name,
        options=[RouteOption(**o) for o in options],
    )


@router.post("/roads", response_model=RoadOut, status_code=201)
def create_road(payload: RoadOut, db: Session = Depends(get_db),
                 _=Depends(require_roles(UserRole.ADMIN, UserRole.GOVERNMENT_OFFICER))):
    road = Road(
        name=payload.name, road_type=payload.road_type, district_id=payload.district_id,
        length_km=payload.length_km, status=payload.status,
        landslide_history_score=payload.landslide_history_score,
    )
    db.add(road)
    db.commit()
    db.refresh(road)
    return road
