from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_permission
from app.modules.rbac import service
from app.modules.rbac.schemas import (
    UserCreate,
    UserUpdate,
    UserOut,
    RoleCreate,
    RoleOut,
    PermissionCreate,
    PermissionOut,
    AssignRole,
    AssignPermission,
)

router = APIRouter(prefix="/users", tags=["users"])
role_router = APIRouter(prefix="/roles", tags=["roles"])
permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


# ── User endpoints ─────────────────────────────────────────────────


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await service.create_user(db, data.username, data.email, data.password)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )


@router.get("", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user:read")),
):
    return await service.get_all_users(db)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user:read")),
):
    user = await service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user:update")),
):
    update_data = data.model_dump(exclude_unset=True)
    user = await service.update_user(db, user_id, **update_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user:delete")),
):
    if not await service.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")


# ── User ↔ Role ────────────────────────────────────────────────────


@router.get("/{user_id}/roles", response_model=List[RoleOut])
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("user:read")),
):
    roles = await service.get_user_roles(db, user_id)
    return roles


@router.post("/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(
    user_id: int,
    data: AssignRole,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:assign")),
):
    if not await service.assign_role_to_user(db, user_id, data.role_id):
        raise HTTPException(status_code=404, detail="User or role not found")


@router.delete(
    "/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_role(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:assign")),
):
    if not await service.revoke_role_from_user(db, user_id, role_id):
        raise HTTPException(status_code=404, detail="User or role not found")


# ── Role endpoints ─────────────────────────────────────────────────


@role_router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:create")),
):
    return await service.create_role(db, data.name, data.description)


@role_router.get("", response_model=List[RoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:read")),
):
    return await service.get_all_roles(db)


@role_router.get("/{role_id}", response_model=RoleOut)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:read")),
):
    role = await service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@role_router.put("/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: int,
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:update")),
):
    role = await service.update_role(
        db, role_id, name=data.name, description=data.description
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:delete")),
):
    if not await service.delete_role(db, role_id):
        raise HTTPException(status_code=404, detail="Role not found")


# ── Role ↔ Permission ─────────────────────────────────────────────


@role_router.get("/{role_id}/permissions", response_model=List[PermissionOut])
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("role:read")),
):
    role = await service.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role.permissions


@role_router.post(
    "/{role_id}/permissions", status_code=status.HTTP_204_NO_CONTENT
)
async def assign_permission(
    role_id: int,
    data: AssignPermission,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:assign")),
):
    if not await service.assign_permission_to_role(
        db, role_id, data.permission_id
    ):
        raise HTTPException(
            status_code=404, detail="Role or permission not found"
        )


@role_router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_permission(
    role_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:assign")),
):
    if not await service.revoke_permission_from_role(
        db, role_id, permission_id
    ):
        raise HTTPException(
            status_code=404, detail="Role or permission not found"
        )


# ── Permission endpoints ──────────────────────────────────────────


@permission_router.post(
    "", response_model=PermissionOut, status_code=status.HTTP_201_CREATED
)
async def create_permission(
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:create")),
):
    return await service.create_permission(
        db, data.key, data.name, data.description
    )


@permission_router.get("", response_model=List[PermissionOut])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:read")),
):
    return await service.get_all_permissions(db)


@permission_router.get("/{perm_id}", response_model=PermissionOut)
async def get_permission(
    perm_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:read")),
):
    perm = await service.get_permission_by_id(db, perm_id)
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


@permission_router.put("/{perm_id}", response_model=PermissionOut)
async def update_permission(
    perm_id: int,
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:update")),
):
    perm = await service.update_permission(
        db, perm_id, key=data.key, name=data.name, description=data.description
    )
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
    return perm


@permission_router.delete("/{perm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    perm_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("permission:delete")),
):
    if not await service.delete_permission(db, perm_id):
        raise HTTPException(status_code=404, detail="Permission not found")
