from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def create_tables():
    from app.modules.rbac.models import User, Role, Permission  # noqa: F401
    from app.modules.features.models import Feature, FeaturePackage  # noqa: F401
    from app.modules.courses.models import Course, CourseSubscription  # noqa: F401
    from app.modules.points.models import PointRule, PointLedger, UnlockRule  # noqa: F401
    from app.modules.entitlements.models import UserFeatureEntitlement  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
