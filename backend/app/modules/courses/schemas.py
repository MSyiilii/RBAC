import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CourseType(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    course_type: CourseType
    starts_at: datetime
    ends_at: Optional[datetime] = None


class CourseOut(BaseModel):
    id: int
    creator_id: int
    title: str
    description: Optional[str] = None
    course_type: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionOut(BaseModel):
    id: int
    course_id: int
    user_id: int
    status: str
    created_at: datetime
    course_title: Optional[str] = None
    course_type: Optional[str] = None
    pro_expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
