from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy import select, delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.entitlements.models import UserFeatureEntitlement


def _ensure_tz(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


async def grant_entitlement(
    db: AsyncSession,
    user_id: int,
    feature_key: str,
    source: str,
    source_id: Optional[int] = None,
    expires_at: Optional[datetime] = None,
    duration_days: Optional[int] = None,
    auto_commit: bool = True,
) -> UserFeatureEntitlement:
    """Upsert: one row per (user_id, feature_key). Lifetime wins; timed durations append."""
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UserFeatureEntitlement).where(
            UserFeatureEntitlement.user_id == user_id,
            UserFeatureEntitlement.feature_key == feature_key,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.is_active = True
        existing.source = source
        existing.source_id = source_id
        existing.granted_at = now

        old_exp = _ensure_tz(existing.expires_at)

        if old_exp is None:
            pass
        elif expires_at is None and duration_days is None:
            existing.expires_at = None
        elif duration_days is not None:
            base = max(old_exp, now) if old_exp > now else now
            existing.expires_at = base + timedelta(days=duration_days)
        elif expires_at is not None:
            new_exp = _ensure_tz(expires_at)
            if old_exp > now:
                delta = new_exp - now
                existing.expires_at = old_exp + delta
            else:
                existing.expires_at = new_exp
        if auto_commit:
            await db.commit()
            await db.refresh(existing)
        return existing

    ent = UserFeatureEntitlement(
        user_id=user_id,
        feature_key=feature_key,
        source=source,
        source_id=source_id,
        is_active=True,
        granted_at=now,
    )
    if duration_days is not None:
        ent.expires_at = now + timedelta(days=duration_days)
    else:
        ent.expires_at = _ensure_tz(expires_at)
    db.add(ent)
    if auto_commit:
        await db.commit()
        await db.refresh(ent)
    return ent


async def revoke_entitlement(db: AsyncSession, entitlement_id: int) -> bool:
    result = await db.execute(
        select(UserFeatureEntitlement).where(
            UserFeatureEntitlement.id == entitlement_id
        )
    )
    ent = result.scalar_one_or_none()
    if not ent:
        return False
    ent.is_active = False
    await db.commit()
    return True




async def check_entitlement(
    db: AsyncSession, user_id: int, feature_key: str
) -> bool:
    from app.modules.features.models import Feature
    feat_result = await db.execute(
        select(Feature).where(Feature.key == feature_key)
    )
    feature = feat_result.scalar_one_or_none()
    if feature is None:
        return False
    if not feature.is_pro:
        return True

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(UserFeatureEntitlement).where(
            UserFeatureEntitlement.user_id == user_id,
            UserFeatureEntitlement.feature_key == feature_key,
            UserFeatureEntitlement.is_active == True,  # noqa: E712
        )
    )
    ent = result.scalar_one_or_none()
    if ent is None:
        return False
    if ent.expires_at is None:
        return True
    exp = _ensure_tz(ent.expires_at)
    return exp > now


async def expire_stale_entitlements(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(UserFeatureEntitlement).where(
            UserFeatureEntitlement.is_active == True,  # noqa: E712
            UserFeatureEntitlement.expires_at.isnot(None),
        )
    )
    stale = list(result.scalars().all())
    count = 0
    for ent in stale:
        exp = _ensure_tz(ent.expires_at)
        if exp <= now:
            ent.is_active = False
            count += 1
    if count > 0:
        await db.commit()
    return count


async def get_user_entitlements(
    db: AsyncSession, user_id: int
) -> List[UserFeatureEntitlement]:
    result = await db.execute(
        select(UserFeatureEntitlement)
        .where(
            UserFeatureEntitlement.user_id == user_id,
            UserFeatureEntitlement.is_active == True,  # noqa: E712
        )
        .order_by(UserFeatureEntitlement.granted_at.desc())
    )
    return list(result.scalars().all())


async def delete_entitlements_by_feature_key(
    db: AsyncSession, feature_key: str
) -> int:
    result = await db.execute(
        sa_delete(UserFeatureEntitlement).where(
            UserFeatureEntitlement.feature_key == feature_key
        )
    )
    await db.commit()
    return result.rowcount


async def migrate_entitlement_feature_key(
    db: AsyncSession, old_key: str, new_key: str
) -> int:
    result = await db.execute(
        sa_update(UserFeatureEntitlement)
        .where(UserFeatureEntitlement.feature_key == old_key)
        .values(feature_key=new_key)
    )
    await db.commit()
    return result.rowcount
