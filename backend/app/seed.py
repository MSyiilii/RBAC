from sqlalchemy import select

from app.database import async_session_maker
from app.modules.rbac.models import User, Role, Permission
from app.modules.rbac.service import hash_password
from app.modules.features.models import Feature
from app.modules.points.models import PointRule, UnlockRule

PERMISSIONS = [
    ("user:read", "查看用户"),
    ("user:create", "创建用户"),
    ("user:update", "更新用户"),
    ("user:delete", "删除用户"),
    ("role:read", "查看角色"),
    ("role:create", "创建角色"),
    ("role:update", "更新角色"),
    ("role:delete", "删除角色"),
    ("role:assign", "分配角色"),
    ("permission:read", "查看权限"),
    ("permission:create", "创建权限"),
    ("permission:update", "更新权限"),
    ("permission:delete", "删除权限"),
    ("permission:assign", "分配权限"),
    ("feature:create", "创建功能"),
    ("feature:update", "更新功能"),
    ("feature:delete", "删除功能"),
    ("points:manage", "管理积分规则"),
    ("entitlement:grant", "授予权益"),
    ("entitlement:revoke", "撤销权益"),
    ("entitlement:manage", "管理权益"),
    ("course:create", "创建课程"),
    ("course:manage", "管理课程"),
]

FEATURES = [
    ("market_basic", "基础市场", "基础市场行情页", False),
    ("chart_light", "基础图表", "轻量级K线图", False),
    ("chart_advanced", "高级图表", "高级K线图及指标", True),
    ("volatility_analysis", "波动率分析", "隐含波动率分析", False),
    ("volatility_cloud", "波动率云图", "波动率云图(Pro)", True),
    ("volatility_overview", "波动率总览", "波动率总览面板(Pro)", True),
    ("term_structure", "期限结构", "波动率期限结构(Pro)", True),
    ("flow_ranking", "异动排行", "期权异动排行", False),
    ("option_flow", "期权流向", "期权流向分析(Pro)", True),
    ("strategy_builder", "策略构建器", "策略构建器基础版", False),
    ("strategy_advanced", "高级策略模板", "高级策略模板(Pro)", True),
    ("watchlist", "自选列表", "个人自选列表", False),
    ("community", "社区", "社区排行榜", False),
]

POINT_RULES = [
    ("daily_checkin", "每日签到", 10, 1),
    ("invite_friend", "邀请好友", 50, 5),
    ("complete_course", "完成课程", 100, None),
    ("community_interact", "社区互动", 5, 10),
]

UNLOCK_RULES = [
    ("chart_advanced", 200, 7),
    ("volatility_cloud", 500, 3),
    ("strategy_advanced", 300, 5),
]


async def seed_data():
    async with async_session_maker() as db:
        existing = await db.execute(select(User).where(User.username == "admin"))
        if existing.scalar_one_or_none() is not None:
            return

        perm_objects = {}
        for key, name in PERMISSIONS:
            p = Permission(key=key, name=name, description=name)
            db.add(p)
            perm_objects[key] = p
        await db.flush()

        admin_role = Role(name="admin", description="运营管理员 — 全部权限")
        admin_role.permissions = list(perm_objects.values())

        user_role = Role(name="user", description="注册用户 — 基础权限")

        creator_role = Role(name="creator", description="大V — 课程管理")
        creator_role.permissions = [
            perm_objects["course:create"],
            perm_objects["course:manage"],
        ]


        db.add_all([admin_role, user_role, creator_role])
        await db.flush()

        admin_user = User(
            username="admin",
            email="admin@openvlab.cn",
            hashed_password=hash_password("admin123"),
        )
        admin_user.roles = [admin_role,creator_role]

        demo_user = User(
            username="user1",
            email="user1@openvlab.cn",
            hashed_password=hash_password("user123"),
        )
        demo_user.roles = [user_role]

        creator_user = User(
            username="creator1",
            email="creator1@openvlab.cn",
            hashed_password=hash_password("creator123"),
        )
        creator_user.roles = [user_role, creator_role]


        db.add_all([admin_user, demo_user, creator_user])

        for key, name, desc, is_pro in FEATURES:
            db.add(Feature(key=key, name=name, description=desc, is_pro=is_pro))

        for action_key, name, pts, daily_limit in POINT_RULES:
            db.add(PointRule(
                action_key=action_key, name=name,
                points=pts, daily_limit=daily_limit,
            ))

        for feature_key, req_pts, trial_days in UNLOCK_RULES:
            db.add(UnlockRule(
                feature_key=feature_key,
                required_points=req_pts,
                trial_days=trial_days,
            ))

        await db.commit()
