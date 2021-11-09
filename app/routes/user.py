import json

from fastapi import Request, APIRouter, BackgroundTasks

from pydantic import BaseModel
from typing import Optional
from app.helpers.discord import set_discord_role

import settings
from app.common.utils.errors import USER_WALLET_FORMAT_INVALID_ERROR, BIND_ACCOUNT_DISCORD_NOT_FOUND, \
    COMMON_NOT_AUTH_ERROR, BIND_ACCOUNT_DISCORD_EXISTED
from app.common.utils.route_helper import get_current_user
from app.common.models.icpdao.user import User, UserStatus
from app.common.models.icpdao.icppership import Icppership, IcppershipStatus


router = APIRouter()


class UpdateProfileItem(BaseModel):
    erc20_address: Optional[str] = None


def _user_profile_dict(user):
    icppership = Icppership.objects(icpper_user_id=str(user.id)).first()
    if not icppership:
        icppership = Icppership.objects(icpper_github_login=str(user.github_login)).first()
    res = {
        "nickname": user.nickname,
        "github_login": user.github_login,
        'github_user_id': user.github_user_id,
        "avatar": user.avatar,
        "status": user.status,
        "erc20_address": user.erc20_address,
        "icppership": {},
        "id": str(user.id)
    }
    if icppership:
        mentor = User.objects(id=icppership.mentor_user_id).first()

        number_of_instructors = Icppership.objects(
            mentor_user_id=str(mentor.id),
            status=IcppershipStatus.ICPPER.value
        ).count()

        res["icppership"] = {
            "id": str(icppership.id),
            "progress": icppership.progress, 
            "status": icppership.status,
            "mentor": {
                "nickname": mentor.nickname,
                "github_login": mentor.github_login,
                "avatar": mentor.avatar,
                "number_of_instructors": number_of_instructors
            }
        }
    return res


@router.get('/profile')
async def profile(request: Request):
    user = get_current_user(request)

    return {
        "success": True,
        "data": _user_profile_dict(user)
    }


@router.put('/profile')
async def update_profile(request: Request, item: UpdateProfileItem):
    user = get_current_user(request)
    erc20_address = item.erc20_address
    if erc20_address and len(erc20_address) != 42:
        return {
            "success": False,
            "errorCode": "400",
            "errorMessage": USER_WALLET_FORMAT_INVALID_ERROR
        }
    
    if erc20_address:
        user.erc20_address = erc20_address

    user.save()
    return {
        "success": True,
        "data": _user_profile_dict(user)
    }


@router.put('/connect/discord/{bind_id}')
async def discord_bind(bind_id: str, request: Request, background_tasks: BackgroundTasks):
    bind_discord = settings.ICPDAO_REDIS_LOCK_DB_CONN.get(bind_id)
    if bind_discord is None:
        return {
            "success": False,
            "errorCode": "404",
            "errorMessage": BIND_ACCOUNT_DISCORD_NOT_FOUND
        }

    bind_discord = str(bind_discord)
    user = get_current_user(request)
    if not user:
        return {
            "success": False,
            "errorCode": "404",
            "errorMessage": COMMON_NOT_AUTH_ERROR
        }

    bind_discord = json.loads(bind_discord)
    exist_user = User.objects(discord_user_id=bind_discord['id']).first()
    if exist_user:
        return {
            "success": False,
            "errorCode": "400",
            "errorMessage": BIND_ACCOUNT_DISCORD_EXISTED
        }

    user.discord_user_id = bind_discord['id']
    user.discord_username = bind_discord['username']
    user.save()
    settings.ICPDAO_REDIS_LOCK_DB_CONN.delete(bind_id)
    settings.ICPDAO_REDIS_LOCK_DB_CONN.delete(bind_discord['id'])
    need_set_id = settings.ICPDAO_DISCORD_NORMAL_ROLEID
    if user.status == UserStatus.ICPPER.value or user.status == UserStatus.PRE_ICPPER.value:
        need_set_id = settings.ICPDAO_DISCORD_ICPPER_ROLEID
    background_tasks.add_task(set_discord_role, settings.ICPDAO_DISCORD_GUILD, bind_discord['id'], need_set_id)
    return {"success": True}
