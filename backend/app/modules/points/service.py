from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.points.models import PointRule, PointLedger, UnlockRule


# ── PointRule CRUD ─────────────────────────────────────────────────

async def create_point_rule(
    db: AsyncSession,
    action_key: str,
    name: str,
    points: int,
    daily_limit: Optional[int] = None,
) -> PointRule:
    rule = PointRule(
        action_key=action_key, name=name, points=points, daily_limit=daily_limit
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_all_point_rules(db: AsyncSession) -> List[PointRule]:
    result = await db.execute(select(PointRule))
    return list(result.scalars().all())


async def get_point_rule_by_action(
    db: AsyncSession, action_key: str
) -> Optional[PointRule]:
    result = await db.execute(
        select(PointRule).where(PointRule.action_key == action_key)
    )
    return result.scalar_one_or_none()


# ── UnlockRule CRUD ────────────────────────────────────────────────

async def create_unlock_rule(
    db: AsyncSession,
    feature_key: str,
    required_points: int,
    trial_days: Optional[int] = None,
) -> UnlockRule:
    rule = UnlockRule(
        feature_key=feature_key,
        required_points=required_points,
        trial_days=trial_days,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_all_unlock_rules(db: AsyncSession) -> List[UnlockRule]:
    result = await db.execute(select(UnlockRule))
    return list(result.scalars().all())


# ── Points business logic ─────────────────────────────────────────

async def get_balance(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(PointLedger.balance_after)
        .where(PointLedger.user_id == user_id)
        .order_by(PointLedger.id.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row if row is not None else 0


async def get_ledger(db: AsyncSession, user_id: int) -> List[PointLedger]:
    result = await db.execute(
        select(PointLedger)
        .where(PointLedger.user_id == user_id)
        .order_by(PointLedger.id.desc())
    )
    return list(result.scalars().all())


async def earn_points(
    db: AsyncSession, user_id: int, action_key: str
) -> PointLedger:
    rule = await get_point_rule_by_action(db, action_key)
    if not rule:
        raise ValueError(f"Unknown action: {action_key}")

    if rule.daily_limit is not None:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        count_result = await db.execute(
            select(func.count())
            .select_from(PointLedger)
            .where(
                PointLedger.user_id == user_id,
                PointLedger.rule_id == rule.id,
                PointLedger.created_at >= today_start,
            )
        )
        count = count_result.scalar() or 0
        if count >= rule.daily_limit:
            raise ValueError(
                f"Daily limit ({rule.daily_limit}) reached for {action_key}"
            )

    balance = await get_balance(db, user_id)
    new_balance = balance + rule.points

    ledger = PointLedger(
        user_id=user_id,
        rule_id=rule.id,
        change=rule.points,
        balance_after=new_balance,
        reason=f"Earned from action: {rule.name}",
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(ledger)
    return ledger


async def check_unlock(
    db: AsyncSession, user_id: int, feature_key: str
) -> dict:
    result = await db.execute(
        select(UnlockRule).where(UnlockRule.feature_key == feature_key)
    )
    unlock_rule = result.scalar_one_or_none()
    if not unlock_rule:
        return {"can_unlock": False, "reason": "No unlock rule found"}

    balance = await get_balance(db, user_id)
    return {
        "can_unlock": balance >= unlock_rule.required_points,
        "required_points": unlock_rule.required_points,
        "current_balance": balance,
        "trial_days": unlock_rule.trial_days,
    }


async def do_unlock(
    db: AsyncSession, user_id: int, feature_key: str
) -> PointLedger:
    result = await db.execute(
        select(UnlockRule).where(UnlockRule.feature_key == feature_key)
    )
    unlock_rule = result.scalar_one_or_none()
    if not unlock_rule:
        raise ValueError(f"No unlock rule found for feature: {feature_key}")

    balance = await get_balance(db, user_id)
    if balance < unlock_rule.required_points:
        raise ValueError("Insufficient points")

    new_balance = balance - unlock_rule.required_points
    ledger = PointLedger(
        user_id=user_id,
        rule_id=None,
        change=-unlock_rule.required_points,
        balance_after=new_balance,
        reason=f"Unlock feature: {feature_key}",
    )
    db.add(ledger)

    from app.modules.entitlements.service import grant_entitlement
    await grant_entitlement(
        db, user_id=user_id, feature_key=feature_key,
        source="points", source_id=unlock_rule.id,
        duration_days=unlock_rule.trial_days,
        auto_commit=False,
    )

    await db.commit()
    await db.refresh(ledger)
    return ledger
