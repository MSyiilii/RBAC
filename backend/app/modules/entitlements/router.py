from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_permission
from app.modules.entitlements import service
from app.modules.entitlements.schemas import (
    EntitlementOut,
    GrantEntitlementRequest,
    CheckEntitlementRequest,
)
from app.modules.rbac.models import User

router = APIRouter(prefix="/entitlements", tags=["entitlements"])


@router.get("", response_model=List[EntitlementOut])
async def list_entitlements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("entitlement:read")),
):
    return await service.get_user_entitlements(db, current_user.id)


@router.post("/check")
async def check_entitlement(
    data: CheckEntitlementRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("entitlement:read")),
):
    return await service.get_user_entitlements(db, data.user_id)


@router.post(
    "/grant",
    response_model=EntitlementOut,
    status_code=status.HTTP_201_CREATED,
)
async def grant_entitlement(
    data: GrantEntitlementRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("entitlement:grant")),
):
    return await service.grant_entitlement(
        db,
        user_id=data.user_id,
        feature_key=data.feature_key,
        source=data.source,
        source_id=data.source_id,
        expires_at=data.expires_at,
    )


@router.post("/revoke/{entitlement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_entitlement(
    entitlement_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("entitlement:revoke")),
):
    if not await service.revoke_entitlement(db, entitlement_id):
        raise HTTPException(
            status_code=404, detail="Entitlement not found"
        )


@router.post("/expire-stale")
async def expire_stale(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("entitlement:manage")),
):
    count = await service.expire_stale_entitlements(db)
    return {"expired_count": count}
