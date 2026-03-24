# OpenVlab RBAC 权限管理系统

基于 OpenVlab 期权交易平台业务场景的角色权限管理（RBAC）演示项目。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + Ant Design Vue 4 + Pinia + Vue Router |
| 后端 | FastAPI + SQLAlchemy 2.x + Pydantic v2 + python-jose |
| 数据库 | SQLite (aiosqlite, 零配置) |
| 测试 | pytest + httpx + pytest-asyncio |

## 项目结构

```
RBAC/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 + 路由注册
│   │   ├── config.py            # 配置项 (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy 异步引擎
│   │   ├── dependencies.py      # JWT解码、权限/角色校验工厂
│   │   ├── seed.py              # 种子数据 (用户/角色/权限/功能/积分规则)
│   │   └── modules/
│   │       ├── auth/            # 登录/刷新/当前用户
│   │       ├── rbac/            # 用户/角色/权限 CRUD + 关联管理
│   │       ├── features/        # 功能点/功能包管理
│   │       ├── courses/         # 课程/报名/Pro权益自动授予
│   │       ├── points/          # 积分规则/流水/解锁
│   │       └── entitlements/    # 权益授予/撤销/检查/过期回收
│   ├── tests/
│   │   └── test_api.py          # 30 项集成测试
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # Axios 封装 + 各模块 API
│       ├── stores/              # Pinia 认证 store
│       ├── router/              # 路由 + beforeEach 守卫
│       ├── utils/               # 工具函数 (时间格式化等)
│       └── views/               # 10 个页面组件
├── traget.md                    # 原始需求 + 补充后的5个示例场景
└── README.md
```

## 快速启动

### 1. 启动后端

```bash
# 环境python 3.10
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

启动后自动创建 SQLite 数据库并注入种子数据。

### 2. 启动前端

```bash
# 环境node 16.16.0
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 ，使用以下测试账号登录。

### 3. 运行测试

```bash
cd backend
python -m pytest tests/ -v
```

## 预置账号

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | admin123 | admin | 运营管理员 — 全部权限 |
| user1 | user123 | user | 注册用户 — 基础权限 |
| creator1 | creator123 | user, creator | 大V — 可创建/管理课程 |

## 数据库设计

### 核心表

```
users               用户表
roles               角色表
permissions         权限表 (key 唯一)
user_roles          用户-角色 多对多关联
role_permissions    角色-权限 多对多关联
```

### 业务表

```
features                   功能点定义 (is_pro 区分基础/Pro)
feature_packages           功能包 (JSON存储feature_ids)
courses                    课程 (creator_id, starts_at, ends_at 可空=永久)
course_subscriptions       课程报名记录 (报名时自动授予Pro权益)
point_rules                积分规则 (action_key, points, daily_limit)
point_ledger               积分流水 (change, balance_after, 事务保证一致性)
unlock_rules               解锁规则 (feature_key, required_points, trial_days)
user_feature_entitlements  用户功能权益 (source, expires_at, is_active)
```

## API 接口说明

所有接口均以 `/api` 为前缀。启动后端后访问 http://localhost:8000/docs 查看 Swagger 文档。

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 用户名密码登录，返回 JWT access/refresh token |
| POST | /api/auth/refresh | 刷新令牌 |
| GET  | /api/auth/me | 获取当前用户信息（含角色与权限） |

### 用户/角色/权限管理 (需 admin 权限)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/users | 用户列表/创建 |
| PUT/DELETE | /api/users/{id} | 更新/删除用户 |
| POST | /api/users/{id}/roles | 分配角色 |
| DELETE | /api/users/{id}/roles/{role_id} | 撤销角色 |
| GET/POST | /api/roles | 角色列表/创建 |
| POST | /api/roles/{id}/permissions | 分配权限 |
| GET/POST | /api/permissions | 权限列表/创建 |

### 课程管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/courses | 课程列表/创建 (大V仅看自己的，课程包含开始/结束时间) |
| PUT | /api/courses/{id} | 更新课程 (仅创建者) |
| DELETE | /api/courses/{id} | 删除课程 (仅创建者) |
| POST | /api/courses/{id}/subscribe | 报名课程（无需请求体，自动授予Pro权益） |
| GET | /api/courses/{id}/subscribers | 查看学员 (仅课程创建者) |
| GET | /api/my/subscriptions | 我的订阅列表（含课程名称、类型、Pro到期时间） |
| POST | /api/courses/expire-check | 批量到期检测 (admin) |

**课程报名规则：**
- 报名线下课程 → 授予所有 Pro 功能的**终身**权益 (`expires_at = null`)
- 报名线上课程 → 授予所有 Pro 功能的**一年**权益 (从报名时间起算 365 天)
- 课程结束时间为空表示课程永久有效

### 积分中心

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/points/earn | 赚取积分 (每日限额检查) |
| GET | /api/points/balance | 查询余额 |
| GET | /api/points/ledger | 积分流水 |
| POST | /api/points/unlock/{feature_key} | 积分解锁功能（同时创建权益记录） |
| GET | /api/points/unlock-rules | 解锁规则列表 |

### 权益管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/entitlements | 当前用户权益列表 |
| POST | /api/entitlements/grant | 授予权益 (admin) |
| POST | /api/entitlements/revoke/{id} | 撤销权益 (admin) |
| POST | /api/entitlements/check | 检查用户功能权限 |
| POST | /api/entitlements/expire-stale | 批量过期权益回收 (admin) |

## 权限体系设计要点

1. **RBAC 核心链路**: User → Roles → Permissions → API 端点保护
2. **数据范围隔离**: 大V 只能管理自己名下课程（`creator_id == current_user.id`）
3. **课程报名联动 Pro 权益**: 报名课程时动态查询 `features.is_pro=true` 的功能集合，在同一事务中创建订阅记录和 Pro 功能权益（线下课终身、线上课一年）
4. **报名约束**: 课程创建者不能报名自己的课程（403）；同一用户不能重复报名同一课程（409）
5. **唯一权益**: 同一用户同一功能只保留一条权益记录（`(user_id, feature_key)` 唯一约束）；新授权按顺延合并（已有终身则保持终身；两边都是有限期则在当前到期基础上叠加新时长）
6. **功能管理联动权益**: 删除功能同步清除所有用户的该功能权益；修改 `key` 同步迁移权益记录；`is_pro` 从 Pro 改为免费时清除权益（免费功能无需权益即可访问）；从免费改为 Pro 不做历史回填
7. **访问判定**: `check_entitlement` 先查功能是否免费，免费直接放行；Pro 功能才需要检查活跃权益记录
8. **到期双保险**: 读时判定 + 定时回收任务（`expire_stale_entitlements`）
9. **积分事务**: 积分变动走流水表事务，每日限额控制，解锁功能同时写入权益（按 `trial_days` 顺延）
10. **时间格式**: 所有前端时间统一转换为东八区 `yyyy-MM-dd HH:mm:ss` 格式显示

## AI 工具使用说明

### 使用的 AI 工具

- **Cursor IDE (Claude claude-4.6-opus-high-thinking)**: 方案设计、编码、调试、文档

### 关键操作过程

1. 通过 AI 访问 openvlab.cn 官网，抓取 robots.txt/sitemap.xml/各页面 meta 信息，分析出完整的模块结构和业务场景
2. 基于网站业务映射出 5 个 RBAC 示例场景（大V课程管理、积分解锁、Pro 权限、渠道数据隔离、个人中心）
3. 制定项目计划后由 AI 并行生成前后端骨架代码
4. 逐步修复 API 路径不匹配、时区比较、前后端数据结构对齐等问题
5. 重构课程模块：引入课程开始/结束时间，移除宽限期逻辑，实现报名课程自动授予 Pro 权益
6. 实现课程与权益一致性：禁止重复报名/创建者自报名，按 is_pro 动态授予，功能增删改联动权益，唯一权益+续期合并
7. 编写 30 项集成测试，全部通过

### 对 AI 产出的判断、修改和取舍

- **时区处理**: AI 生成的 datetime 比较代码没有处理 SQLite 存储的 naive datetime 与 Python 的 aware datetime 之间的兼容性，手动修复了 `check_entitlement` 和 `expire_stale_entitlements` 中的比较逻辑
- **前后端 API 对齐**: AI 分别生成前后端时产生了路径和参数不一致的问题（如 `/api` 前缀、字段名不匹配），需要统一修复
- **课程模块重构**: 根据业务需求将课程有效期从订阅维度迁移到课程维度，并实现报名联动 Pro 权益的事务化逻辑
- **Vite 版本**: 初始生成的 Vite 6 不兼容 Node 16，降级到 Vite 4
- **种子数据设计**: 根据 OpenVlab 实际业务定制了功能点和积分规则
- **安全边界**: 前端路由守卫只做体验优化，真正的安全校验全部在后端完成
