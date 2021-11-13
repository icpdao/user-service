import enum
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

import settings
from app.common.models.icpdao.icppership import Icppership
from app.common.models.icpdao.user import User

router = APIRouter(prefix='/app/discord')


class DiscordLinkItem(BaseModel):
    discord_id: str
    discord_username: str
    # github_id: Optional[str]


class APPDiscordResponseCode(enum.Enum):
    EXIST = 1100
    NOT_EXIST = 1101
    BIND = 1102
    UNBIND = 1103


@router.put('/bind')
async def bind(item: DiscordLinkItem, request: Request):
    exist_user = User.objects(discord_user_id=item.discord_id).first()
    if exist_user:
        return {
            "success": True,
            "data": {
                "code": APPDiscordResponseCode.EXIST.value,
                "role": exist_user.status
            }
        }
    # if item.github_id:
    #     user = User.objects(github_user_id=int(item.github_id)).first()
    #     if user:
    #         user.discord_user_id = item.discord_id
    #         user.discord_username = item.discord_username
    #         user.save()
    #         return {
    #             "success": True,
    #             "data": {
    #                 "code": APPDiscordResponseCode.BIND.value,
    #                 "role": user.status
    #             }
    #         }
    exist_uid = settings.ICPDAO_REDIS_LOCK_DB_CONN.get(item.discord_id)
    if exist_uid is not None:
        random_uuid = exist_uid.decode('utf-8')
    else:
        random_uuid = uuid.uuid4().hex
        settings.ICPDAO_REDIS_LOCK_DB_CONN.setex(
            random_uuid, 5 * 60 + 1, json.dumps({
                'id': item.discord_id,
                'username': item.discord_username
            })
        )
        settings.ICPDAO_REDIS_LOCK_DB_CONN.setex(item.discord_id, 5 * 60 + 1, random_uuid)
    return {
        "success": True,
        "data": {
            "code": APPDiscordResponseCode.UNBIND.value,
            "bind_link": f'{settings.ICPDAO_FRONTEND_URL}/bind/discord/{random_uuid}'
        }
    }


@router.put('/{discord_id}/unbind')
async def unbind(discord_id: str):
    exist_user = User.objects(discord_user_id=discord_id).first()
    if not exist_user:
        return {
            "success": False,
            "errorCode": APPDiscordResponseCode.NOT_EXIST.value
        }
    exist_user.discord_user_id = None
    exist_user.discord_username = None
    exist_user.save()
    return {"success": True}


@router.get('/{discord_id}/mentor')
async def mentor(discord_id: str):
    user = User.objects(discord_user_id=discord_id).first()
    if not user:
        return {
            "success": False,
            "errorCode": APPDiscordResponseCode.NOT_EXIST.value
        }
    icppership = Icppership.objects(icpper_user_id=str(user.id)).first()
    if not icppership:
        icppership = Icppership.objects(icpper_github_login=str(user.github_login)).first()
    if icppership:
        mentor_user = User.objects(id=icppership.mentor_user_id).first()
        return {
            "success": True,
            "data": {
                "nickname": mentor_user.nickname,
                "github_login": mentor_user.github_login,
                "github_id": str(mentor_user.github_user_id),
                'discord_username': mentor_user.discord_username,
                'discord_id': mentor_user.discord_user_id,
                'progress': icppership.progress,
            }
        }
    return {"success": True, "data": {}}


@router.get('/{discord_id}/icppers')
async def icppers(discord_id: str):
    user = User.objects(discord_user_id=discord_id).first()
    if not user:
        return {
            "success": False,
            "errorCode": APPDiscordResponseCode.NOT_EXIST.value
        }

    icpperships = Icppership.objects(mentor_user_id=str(user.id)).all()
    icpper_user_id_list = []
    icpper_progress_dict = {}
    for item in icpperships:
        if item.icpper_user_id:
            icpper_user_id_list.append(item.icpper_user_id)
            icpper_progress_dict[item.icpper_user_id] = item.progress
    icpper_users = []
    for icpper in User.objects(id__in=icpper_user_id_list):
        icpper_users.append({
            'nickname': icpper.nickname,
            'github_login': icpper.github_login,
            'github_id': str(icpper.github_user_id),
            'discord_username': icpper.discord_username,
            'discord_id': icpper.discord_user_id,
            'progress': icpper_progress_dict.get(str(icpper.id), 0)
        })
    return {"success": True, "data": icpper_users}


