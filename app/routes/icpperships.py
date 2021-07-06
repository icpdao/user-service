from fastapi import Request, APIRouter

from pydantic import BaseModel

from app.common.utils.route_helper import get_current_user
from app.common.models.icpdao.user import User, UserStatus
from app.common.models.icpdao.icppership import Icppership, IcppershipStatus, IcppershipProgress


router = APIRouter()


class CreateItem(BaseModel):
    icpper_github_login: str


def to_icppership_dict(icppership, icpper=None):
    if icpper:
        nickname = icpper.nickname
        github_login = icpper.github_login
    else:
        nickname = ""
        github_login = icppership.icpper_github_login
    mentor = User.objects(id=str(icppership.mentor_user_id)).first()
    return {
        "id":                  str(icppership.id),
        "progress":            icppership.progress,
        "status":              icppership.status, 
        "mentor_github_login": mentor.github_login,
        "icpper": {
            "nickname":        nickname,
            "github_login":    github_login,
        },
        "create_at":           icppership.create_at,
        "accept_at":           icppership.accept_at, 
        "icpper_at":           icppership.icpper_at, 
    }


@router.put('/icpperships/{icppership_id}/accept')
async def accept(icppership_id, request: Request):
    user = get_current_user(request)

    icppership = Icppership.objects(id=icppership_id).first()
    if not icppership:
        return {
            "success": False,
            "errorCode": "404",
            "errorMessage": "NOT_FOUND"
        }

    if icppership.icpper_github_login != user.github_login:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": "NO_ROLE"
        }

    if icppership.progress != IcppershipProgress.PENDING.value:
        return {
            "success": True,
            "data": to_icppership_dict(icppership, user)
        }

    icppership.accept(str(user.id))
    if user.status == UserStatus.NORMAL.value:
        user.update_to_pre_icpper()
    elif user.status == UserStatus.ICPPER.value:
        icppership.update_to_icpper()

    icppership_mentor = User.objects(id=icppership.mentor_user_id).first()
    if icppership_mentor.status == UserStatus.PRE_ICPPER.value:
        icppership_mentor.update_to_icpper()
        user_is = Icppership.objects(icpper_user_id=str(icppership_mentor.id)).first()
        user_is.update_to_icpper()

    return {
        "success": True,
        "data": to_icppership_dict(icppership, user)
    }


@router.post('/icpperships')
async def create(request: Request, item: CreateItem):
    user = get_current_user(request)

    if user.status == UserStatus.NORMAL.value:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": "NO_ROLE"
        }

    if Icppership.objects(mentor_user_id=str(user.id)).count() >= 2:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": "ALREADY_TWO_PRE_ICPPER"
        }

    icpper_github_login = item.icpper_github_login
    if Icppership.objects(icpper_github_login=icpper_github_login).count() > 0:
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": "ALREADY_MENTOR"
        }

    icppership = Icppership(
        mentor_user_id=str(user.id),
        icpper_github_login=icpper_github_login
    )
    icppership.save()

    icpper = User.objects(github_login=icpper_github_login).first()
    return {
        "success": True,
        "data": to_icppership_dict(icppership, icpper)
    }


@router.delete('/icpperships/{icppership_id}')
async def delete(icppership_id, request: Request):
    user = get_current_user(request)

    icppership = Icppership.objects(id=icppership_id).first()
    if not icppership:
        return {
            "success": False,
            "errorCode": "404",
            "errorMessage": "NOT_FOUND"
        }

    if icppership.mentor_user_id != str(user.id):
        return {
            "success": False,
            "errorCode": "403",
            "errorMessage": "NO_ROLE"
        }

    Icppership.objects(id=icppership_id).delete()

    if icppership.progress == IcppershipProgress.ACCEPT.value:
        pre_icpper = User.objects(id=icppership.icpper_user_id).first()
        if pre_icpper and pre_icpper.status == UserStatus.PRE_ICPPER.value:
            pre_icpper.update_to_normal()

    return {
        "success": True,
        "data": {}
    }


@router.get('/icpperships')
async def get_list(request: Request):
    user = get_current_user(request)

    is_list = Icppership.objects(mentor_user_id=str(user.id)).all()

    icpper_user_id_list = []
    for item in is_list:
        if item.icpper_user_id:
            icpper_user_id_list.append(item.icpper_user_id)
    user_id_2_icpper = {}
    for icpper in User.objects(id__in=icpper_user_id_list):
        user_id_2_icpper[str(icpper.id)] = icpper

    res = [to_icppership_dict(item, user_id_2_icpper.get(item.icpper_user_id, None)) for item in is_list]

    return {
        "success": True,
        "data": res
    }
