from fastapi import Request, APIRouter

from . import github
from . import user
from . import icpperships

api_router = APIRouter()
api_router.include_router(github.router)
api_router.include_router(user.router)
api_router.include_router(icpperships.router)
