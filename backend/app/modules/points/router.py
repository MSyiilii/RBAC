from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_permission
from app.modules.points import service
from app.modules.points.schemas import (
    PointRuleCreate,
    PointRuleOut,
    LedgerOut,
    UnlockRuleCreate,
    UnlockRuleOut,
    EarnPointsRequest,
)
from app.modules.rbac.models import User

router = APIRouter(prefix="/points", tags=["points"])


@router.post("/earn", response_model=LedgerOut)
async def earn_points(
    data: EarnPointsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("points:read")),
):
    try:
        return await service.earn_points(db, current_user.id, data.action_key)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("points:read")),
):
    balance = await service.get_balance(db, current_user.id)
    return {"user_id": current_user.id, "balance": balance}


@router.get("/ledger", response_model=List[LedgerOut])
async def get_ledger(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("points:read")),
):
    return await service.get_ledger(db, current_user.id)


@router.get("/unlock-rules", response_model=List[UnlockRuleOut])
async def list_unlock_rules(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("points:read")),
):
    return await service.get_all_unlock_rules(db)


@router.post("/unlock-rules", response_model=UnlockRuleOut, status_code=status.HTTP_201_CREATED)
async def create_unlock_rule(
    data: UnlockRuleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("points:manage")),
):
    return await service.create_unlock_rule(
        db, data.feature_key, data.required_points, data.trial_days
    )


@router.get("/unlock-check/{feature_key}")
async def check_unlock(
    feature_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("points:read")),
):
    return await service.check_unlock(db, current_user.id, feature_key)


@router.post("/unlock/{feature_key}", response_model=LedgerOut)
async def do_unlock(
    feature_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("points:read")),
):
    try:
        return await service.do_unlock(db, current_user.id, feature_key)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/rules", response_model=List[PointRuleOut])
async def list_point_rules(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("points:read")),
):
    return await service.get_all_point_rules(db)


@router.post("/rules", response_model=PointRuleOut, status_code=status.HTTP_201_CREATED)
async def create_point_rule(
    data: PointRuleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("points:manage")),
):
    return await service.create_point_rule(
        db, data.action_key, data.name, data.points, data.daily_limit
    )
