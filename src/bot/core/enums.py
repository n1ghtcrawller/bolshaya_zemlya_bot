from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "client"
    DEALER = "dealer"
    SALES = "sales"
    HEAD_OF_SALES = "head_of_sales"
    MARKETING = "marketing"
    HEAD_OF_MARKETING = "head_of_marketing"
    ADMIN = "admin"


class RequestStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    TRANSFERRED_TO_DEALER = "transferred_to_dealer"
    KEPT_BY_SALES = "kept_by_sales"
    DONE = "done"
    REJECTED = "rejected"


class SalesMaterialCategory(StrEnum):
    CATALOGS = "catalogs"
    PHOTOS_VIDEOS = "photos_videos"
    PRESENTATIONS = "presentations"
    TEMPLATES = "templates"
    TRAINING = "training"


class SalesMaterialFileType(StrEnum):
    DOCUMENT = "document"
    PHOTO = "photo"
    VIDEO = "video"
    ANIMATION = "animation"


class ContentType(StrEnum):
    PLAN = "plan"
    IDEA = "idea"
    REGIONAL = "regional"
    SCHEDULED = "scheduled"


class ContentStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BroadcastStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class LeadType(StrEnum):
    REQUEST = "request"
    CONSULTATION = "consultation"
    CALLBACK = "callback"


class ServiceIssueType(StrEnum):
    WARRANTY = "warranty"
    REPAIR = "repair"
    SPARE_PARTS = "spare_parts"
    OTHER = "other"


class ServiceRequestStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"


class ApprovalStatus(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


class BitrixSyncStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class BitrixLeadSource(StrEnum):
    CLIENT_REQUEST = "client_request"
    SERVICE_REQUEST = "service_request"
