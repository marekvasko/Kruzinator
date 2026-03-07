from .auth import auth_router
from .datapoints import router as datapoints_router
from .exports import router as exports_router
from .health import router as health_router
from .rewards import router as rewards_router
from .users import router as users_router
from .well_known import well_known_router

__all__ = [
    "auth_router",
    "datapoints_router",
    "exports_router",
    "health_router",
    "rewards_router",
    "users_router",
    "well_known_router",
]
