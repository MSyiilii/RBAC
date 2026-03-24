from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.modules.features import service
from app.modules.features.schemas import (
    FeatureCreate,
    FeatureOut,
    FeaturePackageCreate,
    FeaturePackageOut,
)

feature_router = APIRouter(prefix="/features", tags=["features"])
package_router = APIRouter(prefix="/feature-packages", tags=["feature-packages"])


@feature_router.post(
    "", response_model=FeatureOut, status_code=status.HTTP_201_CREATED
)
async def create_feature(
    data: FeatureCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:create")),
):
    return await service.create_feature(
        db, data.key, data.name, data.description, data.is_pro
    )


@feature_router.get("", response_model=List[FeatureOut])
async def list_features(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:read")),
):
    return await service.get_all_features(db)


@feature_router.get("/{feature_id}", response_model=FeatureOut)
async def get_feature(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:read")),
):
    feature = await service.get_feature_by_id(db, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


@feature_router.put("/{feature_id}", response_model=FeatureOut)
async def update_feature(
    feature_id: int,
    data: FeatureCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:update")),
):
    feature = await service.update_feature(
        db, feature_id,
        key=data.key, name=data.name,
        description=data.description, is_pro=data.is_pro,
    )
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


@feature_router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    feature_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:delete")),
):
    if not await service.delete_feature(db, feature_id):
        raise HTTPException(status_code=404, detail="Feature not found")


@package_router.post(
    "", response_model=FeaturePackageOut, status_code=status.HTTP_201_CREATED
)
async def create_package(
    data: FeaturePackageCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:create")),
):
    return await service.create_feature_package(
        db, data.name, data.description, data.feature_ids
    )


@package_router.get("", response_model=List[FeaturePackageOut])
async def list_packages(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:read")),
):
    return await service.get_all_feature_packages(db)


@package_router.get("/{package_id}", response_model=FeaturePackageOut)
async def get_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:read")),
):
    package = await service.get_feature_package_by_id(db, package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Feature package not found")
    return package


@package_router.put("/{package_id}", response_model=FeaturePackageOut)
async def update_package(
    package_id: int,
    data: FeaturePackageCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:update")),
):
    package = await service.update_feature_package(
        db, package_id,
        name=data.name, description=data.description,
        feature_ids=data.feature_ids,
    )
    if not package:
        raise HTTPException(status_code=404, detail="Feature package not found")
    return package


@package_router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("feature:delete")),
):
    if not await service.delete_feature_package(db, package_id):
        raise HTTPException(status_code=404, detail="Feature package not found")
