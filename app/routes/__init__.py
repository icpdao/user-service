from fastapi import Request, APIRouter

from . import github
from . import user
from . import icpperships
from . import aws
from .app import discord

api_router = APIRouter()
api_router.include_router(github.router)
api_router.include_router(user.router)
api_router.include_router(icpperships.router)
api_router.include_router(aws.router)
api_router.include_router(discord.router)
