from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "client"
    DEALER = "dealer"
    SALES = "sales"
    MARKETING = "marketing"


class RequestStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    TRANSFERRED_TO_DEALER = "transferred_to_dealer"
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
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BroadcastStatus(StrEnum):
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
