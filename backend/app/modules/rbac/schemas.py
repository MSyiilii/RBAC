from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class PermissionOut(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    permissions: List[PermissionOut] = []

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    roles: List[RoleOut] = []

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionCreate(BaseModel):
    key: str
    name: str
    description: Optional[str] = None


class AssignRole(BaseModel):
    role_id: int


class AssignPermission(BaseModel):
    permission_id: int
