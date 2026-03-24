import json
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator


class FeatureCreate(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    is_pro: bool = False


class FeatureOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    is_pro: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FeaturePackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    feature_ids: List[int] = []


class FeaturePackageOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    feature_ids: List[int] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("feature_ids", mode="before")
    @classmethod
    def parse_feature_ids(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
