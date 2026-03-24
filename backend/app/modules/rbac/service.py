from typing import Optional, List

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.rbac.models import User, Role, Permission

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── User CRUD ──────────────────────────────────────────────────────

async def create_user(
    db: AsyncSession, username: str, email: str, password: str
) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> List[User]:
    result = await db.execute(
        select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
    )
    return list(result.scalars().all())


async def update_user(db: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "password":
            user.hashed_password = hash_password(value)
        else:
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True


# ── Role CRUD ──────────────────────────────────────────────────────

async def create_role(
    db: AsyncSession, name: str, description: Optional[str] = None
) -> Role:
    role = Role(name=name, description=description)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.permissions))
        .where(Role.id == role_id)
    )
    return result.scalar_one_or_none()


async def get_all_roles(db: AsyncSession) -> List[Role]:
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions))
    )
    return list(result.scalars().all())


async def update_role(db: AsyncSession, role_id: int, **kwargs) -> Optional[Role]:
    role = await get_role_by_id(db, role_id)
    if not role:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(role, key, value)
    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role_id: int) -> bool:
    role = await get_role_by_id(db, role_id)
    if not role:
        return False
    await db.delete(role)
    await db.commit()
    return True


# ── Permission CRUD ────────────────────────────────────────────────

async def create_permission(
    db: AsyncSession, key: str, name: str, description: Optional[str] = None
) -> Permission:
    perm = Permission(key=key, name=name, description=description)
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm


async def get_permission_by_id(
    db: AsyncSession, perm_id: int
) -> Optional[Permission]:
    result = await db.execute(
        select(Permission).where(Permission.id == perm_id)
    )
    return result.scalar_one_or_none()


async def get_all_permissions(db: AsyncSession) -> List[Permission]:
    result = await db.execute(select(Permission))
    return list(result.scalars().all())


async def update_permission(
    db: AsyncSession, perm_id: int, **kwargs
) -> Optional[Permission]:
    perm = await get_permission_by_id(db, perm_id)
    if not perm:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(perm, key, value)
    await db.commit()
    await db.refresh(perm)
    return perm


async def delete_permission(db: AsyncSession, perm_id: int) -> bool:
    perm = await get_permission_by_id(db, perm_id)
    if not perm:
        return False
    await db.delete(perm)
    await db.commit()
    return True


# ── Role ↔ User assignment ────────────────────────────────────────

async def assign_role_to_user(
    db: AsyncSession, user_id: int, role_id: int
) -> bool:
    user = await get_user_by_id(db, user_id)
    role = await get_role_by_id(db, role_id)
    if not user or not role:
        return False
    if role not in user.roles:
        user.roles.append(role)
        await db.commit()
    return True


async def revoke_role_from_user(
    db: AsyncSession, user_id: int, role_id: int
) -> bool:
    user = await get_user_by_id(db, user_id)
    role = await get_role_by_id(db, role_id)
    if not user or not role:
        return False
    if role in user.roles:
        user.roles.remove(role)
        await db.commit()
    return True


# ── Permission ↔ Role assignment ──────────────────────────────────

async def assign_permission_to_role(
    db: AsyncSession, role_id: int, permission_id: int
) -> bool:
    role = await get_role_by_id(db, role_id)
    perm = await get_permission_by_id(db, permission_id)
    if not role or not perm:
        return False
    if perm not in role.permissions:
        role.permissions.append(perm)
        await db.commit()
    return True


async def revoke_permission_from_role(
    db: AsyncSession, role_id: int, permission_id: int
) -> bool:
    role = await get_role_by_id(db, role_id)
    perm = await get_permission_by_id(db, permission_id)
    if not role or not perm:
        return False
    if perm in role.permissions:
        role.permissions.remove(perm)
        await db.commit()
    return True


# ── Helpers ────────────────────────────────────────────────────────

async def get_user_permissions(
    db: AsyncSession, user_id: int
) -> List[Permission]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return []
    seen_ids: set[int] = set()
    permissions: list[Permission] = []
    for role in user.roles:
        for perm in role.permissions:
            if perm.id not in seen_ids:
                seen_ids.add(perm.id)
                permissions.append(perm)
    return permissions


async def check_user_has_permission(
    db: AsyncSession, user_id: int, permission_key: str
) -> bool:
    permissions = await get_user_permissions(db, user_id)
    return any(p.key == permission_key for p in permissions)


async def get_user_roles(db: AsyncSession, user_id: int) -> List[Role]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return []
    return list(user.roles)
