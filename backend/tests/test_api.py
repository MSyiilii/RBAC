"""
Comprehensive API integration tests for the RBAC system.
Run with: cd backend && python -m pytest tests/ -v
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_data.db"

    from app.database import create_tables, engine
    from app.seed import seed_data
    await create_tables()
    await seed_data()
    yield
    await engine.dispose()
    if os.path.exists("test_data.db"):
        os.remove("test_data.db")


@pytest_asyncio.fixture
async def client():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def login(client: AsyncClient, username: str, password: str) -> dict:
    r = await client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    return {"Authorization": f"Bearer {data['access_token']}"}


# ────────────────────────────── Auth ──────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client):
    headers = await login(client, "admin", "admin123")
    assert "Authorization" in headers


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    r = await client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me(client):
    headers = await login(client, "admin", "admin123")
    r = await client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    assert any(role["name"] == "admin" for role in data["roles"])


@pytest.mark.asyncio
async def test_refresh_token(client):
    r = await client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    refresh_token = r.json()["refresh_token"]
    r2 = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


# ────────────────────────────── RBAC ──────────────────────────────


@pytest.mark.asyncio
async def test_list_users_as_admin(client):
    headers = await login(client, "admin", "admin123")
    r = await client.get("/api/users", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 4


@pytest.mark.asyncio
async def test_list_users_forbidden_for_normal_user(client):
    headers = await login(client, "user1", "user123")
    r = await client.get("/api/users", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_and_delete_user(client):
    headers = await login(client, "admin", "admin123")
    r = await client.post("/api/users", json={
        "username": "testuser", "email": "test@test.com", "password": "test123"
    })
    assert r.status_code == 201
    uid = r.json()["id"]

    r = await client.delete(f"/api/users/{uid}", headers=headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_list_roles(client):
    headers = await login(client, "admin", "admin123")
    r = await client.get("/api/roles", headers=headers)
    assert r.status_code == 200
    names = [role["name"] for role in r.json()]
    assert "admin" in names
    assert "user" in names
    assert "creator" in names
    assert "pro_user" in names


@pytest.mark.asyncio
async def test_list_permissions(client):
    headers = await login(client, "admin", "admin123")
    r = await client.get("/api/permissions", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 20


@pytest.mark.asyncio
async def test_assign_and_revoke_role(client):
    headers = await login(client, "admin", "admin123")
    r = await client.get("/api/roles", headers=headers)
    pro_role = next(role for role in r.json() if role["name"] == "pro_user")

    r = await client.get("/api/users", headers=headers)
    user1 = next(u for u in r.json() if u["username"] == "user1")

    r = await client.post(f"/api/users/{user1['id']}/roles", json={"role_id": pro_role["id"]}, headers=headers)
    assert r.status_code == 204

    r = await client.delete(f"/api/users/{user1['id']}/roles/{pro_role['id']}", headers=headers)
    assert r.status_code == 204


# ────────────────────────────── Features ──────────────────────────


@pytest.mark.asyncio
async def test_list_features(client):
    r = await client.get("/api/features")
    assert r.status_code == 200
    assert len(r.json()) >= 10


# ────────────────────────────── Courses ───────────────────────────


@pytest.mark.asyncio
async def test_create_online_course(client):
    headers = await login(client, "creator1", "creator123")
    future = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    r = await client.post("/api/courses", json={
        "title": "期权波动率进阶", "description": "线上课程",
        "course_type": "online",
        "starts_at": datetime.now(timezone.utc).isoformat(),
        "ends_at": future,
    }, headers=headers)
    assert r.status_code == 201
    assert r.json()["title"] == "期权波动率进阶"
    assert r.json()["ends_at"] is not None


@pytest.mark.asyncio
async def test_create_offline_course_permanent(client):
    headers = await login(client, "creator1", "creator123")
    r = await client.post("/api/courses", json={
        "title": "线下实战营", "description": "线下课",
        "course_type": "offline",
        "starts_at": datetime.now(timezone.utc).isoformat(),
    }, headers=headers)
    assert r.status_code == 201
    assert r.json()["ends_at"] is None


@pytest.mark.asyncio
async def test_create_course_forbidden_for_normal_user(client):
    headers = await login(client, "user1", "user123")
    r = await client.post("/api/courses", json={
        "title": "test", "course_type": "online",
        "starts_at": datetime.now(timezone.utc).isoformat(),
    }, headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_data_scope_creator_sees_own_courses(client):
    headers = await login(client, "creator1", "creator123")
    r = await client.get("/api/courses", headers=headers)
    assert r.status_code == 200
    for course in r.json():
        assert course["creator_id"] == 3


@pytest.mark.asyncio
async def test_subscribe_online_grants_1year_pro(client):
    headers_creator = await login(client, "creator1", "creator123")
    r = await client.get("/api/courses", headers=headers_creator)
    online_courses = [c for c in r.json() if c["course_type"] == "online"]
    assert len(online_courses) > 0
    course_id = online_courses[0]["id"]

    headers_user = await login(client, "user1", "user123")
    r = await client.post(
        f"/api/courses/{course_id}/subscribe", headers=headers_user,
    )
    assert r.status_code == 201
    assert r.json()["status"] == "active"

    headers_admin = await login(client, "admin", "admin123")
    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "chart_advanced",
    }, headers=headers_admin)
    assert r.json()["entitled"] is True


@pytest.mark.asyncio
async def test_subscribe_offline_grants_lifetime_pro(client):
    headers_creator = await login(client, "creator1", "creator123")
    r = await client.get("/api/courses", headers=headers_creator)
    offline_courses = [c for c in r.json() if c["course_type"] == "offline"]
    assert len(offline_courses) > 0
    course_id = offline_courses[0]["id"]

    headers_pro = await login(client, "pro1", "pro123")
    r = await client.post(
        f"/api/courses/{course_id}/subscribe", headers=headers_pro,
    )
    assert r.status_code == 201

    headers_admin = await login(client, "admin", "admin123")
    r = await client.post("/api/entitlements/check", json={
        "user_id": 4, "feature_key": "volatility_cloud",
    }, headers=headers_admin)
    assert r.json()["entitled"] is True


# ────────────────────────────── Points ────────────────────────────


@pytest.mark.asyncio
async def test_earn_points(client):
    headers = await login(client, "user1", "user123")
    r = await client.post("/api/points/earn", json={"action_key": "daily_checkin"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["change"] == 10
    assert r.json()["balance_after"] > 0


@pytest.mark.asyncio
async def test_daily_limit(client):
    headers = await login(client, "admin", "admin123")
    for _ in range(5):
        await client.post("/api/points/earn", json={"action_key": "invite_friend"}, headers=headers)

    r = await client.post("/api/points/earn", json={"action_key": "invite_friend"}, headers=headers)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_balance_and_ledger(client):
    headers = await login(client, "user1", "user123")
    r = await client.get("/api/points/balance", headers=headers)
    assert r.status_code == 200
    assert "balance" in r.json()

    r = await client.get("/api/points/ledger", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_unlock_rules(client):
    r = await client.get("/api/points/unlock-rules")
    assert r.status_code == 200
    assert len(r.json()) >= 3


# ────────────────────────────── Entitlements ──────────────────────


@pytest.mark.asyncio
async def test_grant_and_check_entitlement(client):
    headers = await login(client, "admin", "admin123")
    future = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    r = await client.post("/api/entitlements/grant", json={
        "user_id": 2, "feature_key": "volatility_cloud",
        "source": "admin", "expires_at": future
    }, headers=headers)
    assert r.status_code == 201

    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "volatility_cloud"
    }, headers=headers)
    assert r.status_code == 200
    assert r.json()["entitled"] is True


@pytest.mark.asyncio
async def test_revoke_entitlement(client):
    headers = await login(client, "admin", "admin123")
    r = await client.post("/api/features", json={
        "key": "test_revoke_feat", "name": "Test Revoke", "is_pro": True
    }, headers=headers)
    assert r.status_code == 201

    r = await client.post("/api/entitlements/grant", json={
        "user_id": 2, "feature_key": "test_revoke_feat", "source": "trial"
    }, headers=headers)
    eid = r.json()["id"]

    r = await client.post(f"/api/entitlements/revoke/{eid}", headers=headers)
    assert r.status_code == 204

    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "test_revoke_feat"
    }, headers=headers)
    assert r.json()["entitled"] is False


@pytest.mark.asyncio
async def test_entitlement_user_forbidden_to_grant(client):
    headers = await login(client, "user1", "user123")
    r = await client.post("/api/entitlements/grant", json={
        "user_id": 2, "feature_key": "chart_advanced", "source": "admin"
    }, headers=headers)
    assert r.status_code == 403


# ────────────────────── Consistency rules ─────────────────────────


@pytest.mark.asyncio
async def test_duplicate_subscribe_returns_409(client):
    headers_creator = await login(client, "creator1", "creator123")
    r = await client.get("/api/courses", headers=headers_creator)
    online_courses = [c for c in r.json() if c["course_type"] == "online"]
    assert len(online_courses) > 0
    course_id = online_courses[0]["id"]

    headers_admin = await login(client, "admin", "admin123")
    r = await client.post(f"/api/courses/{course_id}/subscribe", headers=headers_admin)
    if r.status_code == 201:
        r2 = await client.post(f"/api/courses/{course_id}/subscribe", headers=headers_admin)
        assert r2.status_code == 409
    else:
        assert r.status_code == 409


@pytest.mark.asyncio
async def test_creator_cannot_subscribe_own_course(client):
    headers_creator = await login(client, "creator1", "creator123")
    r = await client.get("/api/courses", headers=headers_creator)
    assert len(r.json()) > 0
    course_id = r.json()[0]["id"]
    r = await client.post(f"/api/courses/{course_id}/subscribe", headers=headers_creator)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_entitlement_upsert_no_duplicates(client):
    headers = await login(client, "admin", "admin123")
    future1 = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    future2 = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

    r1 = await client.post("/api/entitlements/grant", json={
        "user_id": 1, "feature_key": "chart_advanced",
        "source": "admin", "expires_at": future1,
    }, headers=headers)
    assert r1.status_code == 201
    eid1 = r1.json()["id"]

    r2 = await client.post("/api/entitlements/grant", json={
        "user_id": 1, "feature_key": "chart_advanced",
        "source": "admin", "expires_at": future2,
    }, headers=headers)
    assert r2.status_code == 201
    eid2 = r2.json()["id"]
    assert eid1 == eid2


@pytest.mark.asyncio
async def test_delete_feature_removes_entitlements(client):
    headers = await login(client, "admin", "admin123")
    r = await client.post("/api/features", json={
        "key": "test_del_sync", "name": "Test Del", "is_pro": True,
    }, headers=headers)
    fid = r.json()["id"]

    await client.post("/api/entitlements/grant", json={
        "user_id": 2, "feature_key": "test_del_sync", "source": "admin",
    }, headers=headers)

    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "test_del_sync",
    }, headers=headers)
    assert r.json()["entitled"] is True

    await client.delete(f"/api/features/{fid}", headers=headers)

    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "test_del_sync",
    }, headers=headers)
    assert r.json()["entitled"] is False


@pytest.mark.asyncio
async def test_is_pro_false_clears_entitlements(client):
    headers = await login(client, "admin", "admin123")
    r = await client.post("/api/features", json={
        "key": "test_pro_toggle", "name": "ProToggle", "is_pro": True,
    }, headers=headers)
    fid = r.json()["id"]

    await client.post("/api/entitlements/grant", json={
        "user_id": 2, "feature_key": "test_pro_toggle", "source": "admin",
    }, headers=headers)

    r = await client.put(f"/api/features/{fid}", json={
        "key": "test_pro_toggle", "name": "ProToggle", "is_pro": False,
    }, headers=headers)
    assert r.status_code == 200

    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "test_pro_toggle",
    }, headers=headers)
    assert r.json()["entitled"] is True


@pytest.mark.asyncio
async def test_free_feature_accessible_without_entitlement(client):
    headers = await login(client, "admin", "admin123")
    r = await client.post("/api/entitlements/check", json={
        "user_id": 2, "feature_key": "market_basic",
    }, headers=headers)
    assert r.json()["entitled"] is True
