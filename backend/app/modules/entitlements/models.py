from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserFeatureEntitlement(Base):
    __tablename__ = "user_feature_entitlements"
    __table_args__ = (
        UniqueConstraint("user_id", "feature_key", name="uq_user_feature"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    feature_key: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(20))
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
