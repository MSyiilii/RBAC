from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PointRuleCreate(BaseModel):
    action_key: str
    name: str
    points: int
    daily_limit: Optional[int] = None


class PointRuleOut(BaseModel):
    id: int
    action_key: str
    name: str
    points: int
    daily_limit: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LedgerOut(BaseModel):
    id: int
    user_id: int
    rule_id: Optional[int] = None
    change: int
    balance_after: int
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UnlockRuleCreate(BaseModel):
    feature_key: str
    required_points: int
    trial_days: Optional[int] = None


class UnlockRuleOut(BaseModel):
    id: int
    feature_key: str
    required_points: int
    trial_days: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EarnPointsRequest(BaseModel):
    action_key: str
