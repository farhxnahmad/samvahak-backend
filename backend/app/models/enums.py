import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    GOVERNMENT_OFFICER = "government_officer"
    FIELD_STAFF = "field_staff"
    CITIZEN = "citizen"


class RouteStatus(str, enum.Enum):
    ACCESSIBLE = "accessible"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentType(str, enum.Enum):
    LANDSLIDE = "landslide"
    FLOOD = "flood"
    BRIDGE_DAMAGE = "bridge_damage"
    ROAD_CLOSURE = "road_closure"
    HEAVY_RAINFALL = "heavy_rainfall"
    TRAFFIC_DISRUPTION = "traffic_disruption"


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class ShipmentCategory(str, enum.Enum):
    MEDICINE = "medicine"
    FOOD = "food"
    RELIEF_MATERIALS = "relief_materials"
    CONSTRUCTION_MATERIALS = "construction_materials"


class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    DELIVERED = "delivered"
    FAILED = "failed"


class ShipmentPriority(str, enum.Enum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class CitizenReportStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class NotificationSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
