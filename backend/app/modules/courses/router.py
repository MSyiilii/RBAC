from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_permission
from app.modules.courses import service
from app.modules.courses.service import SubscribeError
from app.modules.courses.schemas import CourseCreate, CourseOut, SubscriptionOut
from app.modules.rbac.models import User

router = APIRouter(prefix="/courses", tags=["courses"])
my_router = APIRouter(prefix="/my", tags=["my-subscriptions"])

_ERROR_MAP = {"forbidden": 403, "conflict": 409, "bad_request": 400}


def _has_perm(user: User, key: str) -> bool:
    for role in user.roles:
        for perm in role.permissions:
            if perm.key == key:
                return True
    return False


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("course:create")),
):
    try:
        return await service.create_course(
            db,
            creator_id=current_user.id,
            title=data.title,
            description=data.description,
            course_type=data.course_type.value,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[CourseOut])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("course:read")),
):
    if _has_perm(current_user, "course:manage"):
        return await service.list_all_courses(db)
    if _has_perm(current_user, "course:create"):
        return await service.list_courses_by_creator(db, current_user.id)
    return await service.list_all_courses(db)


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("course:read")),
):
    course = await service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put("/{course_id}", response_model=CourseOut)
async def update_course(
    course_id: int,
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("course:manage")),
):
    try:
        course = await service.update_course(
            db, course_id,
            creator_id=current_user.id,
            title=data.title,
            description=data.description,
            course_type=data.course_type.value,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found or you are not the creator",
        )
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("course:manage")),
):
    if not await service.delete_course(db, course_id, current_user.id):
        raise HTTPException(
            status_code=404,
            detail="Course not found or you are not the creator",
        )


@router.post(
    "/{course_id}/subscribe",
    response_model=SubscriptionOut,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = await service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    try:
        return await service.subscribe_user(
            db, course_id=course_id, user_id=current_user.id,
        )
    except SubscribeError as e:
        raise HTTPException(
            status_code=_ERROR_MAP.get(e.code, 400), detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{course_id}/subscribers")
async def list_subscribers(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("course:manage")),
):
    course = await service.get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.creator_id != current_user.id and not _has_perm(current_user, "user:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view subscribers for your own courses",
        )
    subs = await service.get_course_subscribers(db, course_id)
    return [_enrich_sub(s, course) for s in subs]


@my_router.get("/subscriptions")
async def my_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subs = await service.get_my_subscriptions(db, current_user.id)
    result = []
    for s in subs:
        course = await service.get_course_by_id(db, s.course_id)
        result.append(_enrich_sub(s, course))
    return result


def _enrich_sub(sub, course):
    from datetime import timedelta
    d = SubscriptionOut.model_validate(sub).model_dump()
    if course:
        d["course_title"] = course.title
        d["course_type"] = course.course_type
        if course.course_type == "offline":
            d["pro_expires_at"] = None
        else:
            created = sub.created_at
            d["pro_expires_at"] = (created + timedelta(days=365)).isoformat() if created else None
    return d


@router.post("/expire-check")
async def expire_check(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("course:manage")),
):
    count = await service.check_and_expire_subscriptions(db)
    return {"expired_count": count}
