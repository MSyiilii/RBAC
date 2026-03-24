from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.courses.models import Course, CourseSubscription
from app.modules.entitlements.service import grant_entitlement
from app.modules.features.models import Feature


class SubscribeError(Exception):
    def __init__(self, message: str, code: str = "bad_request"):
        super().__init__(message)
        self.code = code


async def _get_pro_feature_keys(db: AsyncSession) -> List[str]:
    result = await db.execute(
        select(Feature.key).where(Feature.is_pro == True)  # noqa: E712
    )
    return list(result.scalars().all())


async def create_course(
    db: AsyncSession,
    creator_id: int,
    title: str,
    description: Optional[str],
    course_type: str,
    starts_at: datetime,
    ends_at: Optional[datetime] = None,
) -> Course:
    if ends_at is not None and ends_at <= starts_at:
        raise ValueError("ends_at must be after starts_at")
    course = Course(
        creator_id=creator_id,
        title=title,
        description=description,
        course_type=course_type,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def get_course_by_id(db: AsyncSession, course_id: int) -> Optional[Course]:
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def list_courses_by_creator(db: AsyncSession, creator_id: int) -> List[Course]:
    result = await db.execute(select(Course).where(Course.creator_id == creator_id))
    return list(result.scalars().all())


async def list_all_courses(db: AsyncSession) -> List[Course]:
    result = await db.execute(select(Course))
    return list(result.scalars().all())


async def update_course(
    db: AsyncSession, course_id: int, creator_id: int, **kwargs
) -> Optional[Course]:
    course = await get_course_by_id(db, course_id)
    if not course or course.creator_id != creator_id:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(course, key, value)
    if course.ends_at is not None and course.ends_at <= course.starts_at:
        raise ValueError("ends_at must be after starts_at")
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course_id: int, creator_id: int) -> bool:
    course = await get_course_by_id(db, course_id)
    if not course or course.creator_id != creator_id:
        return False
    await db.delete(course)
    await db.commit()
    return True


async def subscribe_user(
    db: AsyncSession,
    course_id: int,
    user_id: int,
) -> CourseSubscription:
    course = await get_course_by_id(db, course_id)
    if not course:
        raise SubscribeError("Course not found")

    if course.creator_id == user_id:
        raise SubscribeError("不能报名自己创建的课程", code="forbidden")

    existing = await db.execute(
        select(CourseSubscription).where(
            CourseSubscription.course_id == course_id,
            CourseSubscription.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise SubscribeError("已报名该课程，不可重复报名", code="conflict")

    sub = CourseSubscription(
        course_id=course_id,
        user_id=user_id,
        status="active",
    )
    db.add(sub)

    pro_keys = await _get_pro_feature_keys(db)

    if course.course_type == "offline":
        for fk in pro_keys:
            await grant_entitlement(
                db, user_id=user_id, feature_key=fk,
                source="course", source_id=course.id,
                expires_at=None, auto_commit=False,
            )
    else:
        for fk in pro_keys:
            await grant_entitlement(
                db, user_id=user_id, feature_key=fk,
                source="course", source_id=course.id,
                duration_days=365, auto_commit=False,
            )

    await db.commit()
    await db.refresh(sub)
    return sub


async def get_course_subscribers(
    db: AsyncSession, course_id: int
) -> List[CourseSubscription]:
    result = await db.execute(
        select(CourseSubscription).where(CourseSubscription.course_id == course_id)
    )
    return list(result.scalars().all())


async def get_my_subscriptions(
    db: AsyncSession, user_id: int
) -> List[CourseSubscription]:
    result = await db.execute(
        select(CourseSubscription).where(CourseSubscription.user_id == user_id)
    )
    return list(result.scalars().all())


async def check_and_expire_subscriptions(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CourseSubscription).where(CourseSubscription.status == "active")
    )
    subs = list(result.scalars().all())
    count = 0
    for sub in subs:
        course = await get_course_by_id(db, sub.course_id)
        if not course or course.ends_at is None:
            continue
        ends = course.ends_at if course.ends_at.tzinfo else course.ends_at.replace(tzinfo=timezone.utc)
        if ends <= now:
            sub.status = "expired"
            count += 1
    if count > 0:
        await db.commit()
    return count
