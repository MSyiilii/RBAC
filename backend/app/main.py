from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    from app.seed import seed_data
    await seed_data()
    yield


app = FastAPI(title="RBAC System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.modules.auth.router import router as auth_router  # noqa: E402
from app.modules.rbac.router import (  # noqa: E402
    router as user_router,
    role_router,
    permission_router,
)
from app.modules.features.router import (  # noqa: E402
    feature_router,
    package_router,
)
from app.modules.courses.router import (  # noqa: E402
    router as course_router,
    my_router,
)
from app.modules.points.router import router as points_router  # noqa: E402
from app.modules.entitlements.router import (  # noqa: E402
    router as entitlements_router,
)

api = APIRouter(prefix="/api")
api.include_router(auth_router)
api.include_router(user_router)
api.include_router(role_router)
api.include_router(permission_router)
api.include_router(feature_router)
api.include_router(package_router)
api.include_router(course_router)
api.include_router(my_router)
api.include_router(points_router)
api.include_router(entitlements_router)

app.include_router(api)
