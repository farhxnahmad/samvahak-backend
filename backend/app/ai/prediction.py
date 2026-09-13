"""
Samvahak AI Prediction Engine (MVP).

This module is intentionally deterministic and rule-based rather than a
trained model — it's built so every function here can later be replaced
with a call to a real ML model (e.g. a landslide-risk classifier trained on
IMD + satellite data) without changing any router code, since routers only
depend on this module's function signatures and return shapes.

All risk scores are 0-100. Risk levels: LOW < 25, MODERATE < 50, HIGH < 75,
CRITICAL >= 75.
"""
import hashlib
from datetime import datetime, timezone

from app.models.enums import RiskLevel, IncidentSeverity, RouteStatus, ShipmentPriority

SEVERITY_WEIGHT = {
    IncidentSeverity.LOW: 5,
    IncidentSeverity.MODERATE: 12,
    IncidentSeverity.HIGH: 22,
    IncidentSeverity.SEVERE: 35,
}

ROUTE_STATUS_WEIGHT = {
    RouteStatus.ACCESSIBLE: 0,
    RouteStatus.AT_RISK: 20,
    RouteStatus.BLOCKED: 45,
}


def risk_level_from_score(score: int) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def _weather_contribution(weather_records: list) -> tuple[int, list[str]]:
    """Rainfall/alert-driven risk points + human-readable factor strings."""
    if not weather_records:
        return 0, []
    points = 0
    factors = []
    max_rainfall = max((w.rainfall_mm or 0) for w in weather_records)
    if max_rainfall >= 100:
        points += 25
        factors.append(f"Heavy rainfall recorded ({max_rainfall:.0f}mm)")
    elif max_rainfall >= 50:
        points += 12
        factors.append(f"Moderate rainfall recorded ({max_rainfall:.0f}mm)")

    severe_alerts = [w for w in weather_records if w.alert_level in ("severe", "warning")]
    if severe_alerts:
        points += 10
        factors.append("Active IMD weather warning in the area")
    return points, factors


def _incident_contribution(incidents: list) -> tuple[int, list[str]]:
    if not incidents:
        return 0, []
    points = 0
    factors = []
    for inc in incidents:
        points += SEVERITY_WEIGHT.get(inc.severity, 5)
    points = min(points, 55)  # cap so incidents alone can't blow past a sane ceiling
    top = max(incidents, key=lambda i: SEVERITY_WEIGHT.get(i.severity, 0))
    factors.append(f"{len(incidents)} active incident(s) nearby — most severe: {top.type.value.replace('_', ' ')}")
    return points, factors


def _history_contribution(landslide_history_score: float) -> tuple[int, list[str]]:
    if landslide_history_score <= 0:
        return 0, []
    points = int(landslide_history_score * 20)  # history_score is 0-1
    factors = ["Route passes through a historically landslide-prone zone"] if points > 5 else []
    return points, factors


def assess_route_risk(route, incidents: list, weather_records: list, landslide_history_score: float = 0.0) -> dict:
    """
    Full risk assessment for an existing Route row.
    Returns: risk_score, risk_level, predicted_delay_minutes, factors[]
    """
    score = ROUTE_STATUS_WEIGHT.get(route.status, 0)
    factors: list[str] = []
    if route.status == RouteStatus.BLOCKED:
        factors.append("Route is currently reported as blocked")
    elif route.status == RouteStatus.AT_RISK:
        factors.append("Route is currently flagged at-risk by field reports")

    w_points, w_factors = _weather_contribution(weather_records)
    i_points, i_factors = _incident_contribution(incidents)
    h_points, h_factors = _history_contribution(landslide_history_score)

    score = min(100, score + w_points + i_points + h_points)
    factors += w_factors + i_factors + h_factors
    if not factors:
        factors.append("No significant risk factors detected — conditions normal")

    delay_minutes = int(route.normal_eta_minutes * (score / 100) * 0.8)

    return {
        "risk_score": score,
        "risk_level": risk_level_from_score(score),
        "predicted_delay_minutes": delay_minutes,
        "factors": factors,
    }


def _seeded_variance(*parts: str, spread: float = 0.15) -> float:
    """
    Deterministic pseudo-randomness in [-spread, +spread], seeded from the input
    parts. Used to generate distinct-but-reproducible safest/fastest/alternate
    route options from the same source/destination pair, in the absence of a
    real routing engine (OSRM/Valhalla would replace this in production).
    """
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    n = int(digest[:8], 16) / 0xFFFFFFFF  # 0..1
    return (n - 0.5) * 2 * spread


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def generate_route_options(source_lat, source_lng, source_name, dest_lat, dest_lng, dest_name,
                            nearby_incidents: list, nearby_weather: list) -> list[dict]:
    """
    Produces safest / fastest / alternate options between two points.
    Base distance/time come from haversine * a hilly-terrain road-winding factor;
    each option's risk is derived from real nearby incidents/weather plus a small
    deterministic variance so the three options are meaningfully different.
    """
    straight_km = _haversine_km(source_lat, source_lng, dest_lat, dest_lng)
    base_km = max(straight_km * 1.35, 5)  # NER roads wind through hills — rarely straight
    base_minutes = int(base_km * 2.1)  # ~28 km/h average on hill roads

    w_points, w_factors = _weather_contribution(nearby_weather)
    i_points, i_factors = _incident_contribution(nearby_incidents)
    base_score = min(90, w_points + i_points)
    base_factors = w_factors + i_factors or ["No significant risk factors detected on this corridor"]

    key = f"{round(source_lat,3)},{round(source_lng,3)}-{round(dest_lat,3)},{round(dest_lng,3)}"

    safest_score = max(5, int(base_score * 0.55 + _seeded_variance(key, "safest") * 100 * 0.2))
    safest = {
        "label": "safest",
        "distance_km": round(base_km * 1.18, 1),
        "eta_minutes": int(base_minutes * 1.25),
        "risk_score": min(safest_score, 100),
        "risk_level": risk_level_from_score(safest_score),
        "predicted_delay_minutes": int(base_minutes * 0.10),
        "factors": (base_factors + ["Routed via longer but historically stable corridor"]),
    }

    fastest_score = min(100, int(base_score * 1.25 + abs(_seeded_variance(key, "fastest")) * 100 * 0.3) + 8)
    fastest = {
        "label": "fastest",
        "distance_km": round(base_km, 1),
        "eta_minutes": base_minutes,
        "risk_score": fastest_score,
        "risk_level": risk_level_from_score(fastest_score),
        "predicted_delay_minutes": int(base_minutes * (fastest_score / 100) * 0.6),
        "factors": (base_factors + ["Most direct road — less margin if conditions worsen"]),
    }

    alt_score = max(5, int(base_score * 0.85 + _seeded_variance(key, "alternate") * 100 * 0.25))
    alternate = {
        "label": "alternate",
        "distance_km": round(base_km * 1.08, 1),
        "eta_minutes": int(base_minutes * 1.10),
        "risk_score": min(alt_score, 100),
        "risk_level": risk_level_from_score(alt_score),
        "predicted_delay_minutes": int(base_minutes * (alt_score / 100) * 0.5),
        "factors": (base_factors + ["Balanced option via secondary state highway"]),
    }

    return [safest, fastest, alternate]


def recommend_shipment_priority(category: str, route_risk_score: int, current_priority: ShipmentPriority) -> dict:
    """
    Suggests whether a shipment's priority should be escalated given current
    route risk — e.g. medicine on a high-risk route gets flagged for emergency
    handling even if it was dispatched as routine.
    """
    escalate = False
    reason = "No escalation needed — route conditions are within normal range"

    if category == "medicine" and route_risk_score >= 50 and current_priority != ShipmentPriority.EMERGENCY:
        escalate = True
        reason = "Medical shipment on a high-risk route — recommend escalating to EMERGENCY priority"
    elif category == "relief_materials" and route_risk_score >= 75:
        escalate = True
        reason = "Relief materials on a critical-risk route — recommend escalating to URGENT/EMERGENCY"

    return {"escalate": escalate, "reason": reason, "assessed_at": datetime.now(timezone.utc).isoformat()}
