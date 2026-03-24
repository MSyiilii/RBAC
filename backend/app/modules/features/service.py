import json
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.features.models import Feature, FeaturePackage
from app.modules.entitlements.service import (
    delete_entitlements_by_feature_key,
    migrate_entitlement_feature_key,
)


async def create_feature(
    db: AsyncSession,
    key: str,
    name: str,
    description: Optional[str] = None,
    is_pro: bool = False,
) -> Feature:
    feature = Feature(key=key, name=name, description=description, is_pro=is_pro)
    db.add(feature)
    await db.commit()
    await db.refresh(feature)
    return feature


async def get_feature_by_id(db: AsyncSession, feature_id: int) -> Optional[Feature]:
    result = await db.execute(select(Feature).where(Feature.id == feature_id))
    return result.scalar_one_or_none()


async def get_all_features(db: AsyncSession) -> List[Feature]:
    result = await db.execute(select(Feature))
    return list(result.scalars().all())


async def update_feature(db: AsyncSession, feature_id: int, **kwargs) -> Optional[Feature]:
    feature = await get_feature_by_id(db, feature_id)
    if not feature:
        return None

    old_key = feature.key
    old_is_pro = feature.is_pro

    for key, value in kwargs.items():
        if value is not None:
            setattr(feature, key, value)

    await db.commit()
    await db.refresh(feature)

    if feature.key != old_key:
        await migrate_entitlement_feature_key(db, old_key, feature.key)

    if old_is_pro and not feature.is_pro:
        await delete_entitlements_by_feature_key(db, feature.key)

    return feature


async def delete_feature(db: AsyncSession, feature_id: int) -> bool:
    feature = await get_feature_by_id(db, feature_id)
    if not feature:
        return False
    fk = feature.key
    await db.delete(feature)
    await db.commit()
    await delete_entitlements_by_feature_key(db, fk)
    return True


async def create_feature_package(
    db: AsyncSession,
    name: str,
    description: Optional[str] = None,
    feature_ids: Optional[List[int]] = None,
) -> FeaturePackage:
    package = FeaturePackage(
        name=name,
        description=description,
        feature_ids=json.dumps(feature_ids or []),
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


async def get_feature_package_by_id(
    db: AsyncSession, package_id: int
) -> Optional[FeaturePackage]:
    result = await db.execute(
        select(FeaturePackage).where(FeaturePackage.id == package_id)
    )
    return result.scalar_one_or_none()


async def get_all_feature_packages(db: AsyncSession) -> List[FeaturePackage]:
    result = await db.execute(select(FeaturePackage))
    return list(result.scalars().all())


async def update_feature_package(
    db: AsyncSession, package_id: int, **kwargs
) -> Optional[FeaturePackage]:
    package = await get_feature_package_by_id(db, package_id)
    if not package:
        return None
    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "feature_ids":
            package.feature_ids = json.dumps(value)
        else:
            setattr(package, key, value)
    await db.commit()
    await db.refresh(package)
    return package


async def delete_feature_package(db: AsyncSession, package_id: int) -> bool:
    package = await get_feature_package_by_id(db, package_id)
    if not package:
        return False
    await db.delete(package)
    await db.commit()
    return True
