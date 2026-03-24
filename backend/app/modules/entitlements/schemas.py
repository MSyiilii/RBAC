from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EntitlementCreate(BaseModel):
    user_id: int
    feature_key: str
    source: str
    source_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class EntitlementOut(BaseModel):
    id: int
    user_id: int
    feature_key: str
    source: str
    source_id: Optional[int] = None
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    model_config = {"from_attributes": True}


class GrantEntitlementRequest(BaseModel):
    user_id: int
    feature_key: str
    source: str
    source_id: Optional[int] = None
    expires_at: Optional[datetime] = None


class CheckEntitlementRequest(BaseModel):
    user_id: int