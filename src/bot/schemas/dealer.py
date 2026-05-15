from pydantic import BaseModel


class DealerProfileUpdate(BaseModel):
    phone: str | None = None
    company: str | None = None
    region: str | None = None
    address: str | None = None
    description: str | None = None


class DealerStats(BaseModel):
    total: int
    new: int
    in_progress: int
    done: int
    rejected: int
