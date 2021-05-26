from fastapi import Request, APIRouter

from pydantic import BaseModel
from typing import Optional

from app.common.utils.route_helper import get_current_user
from app.common.models.icpdao.user import User
from app.common.models.icpdao.icppership import Icppership, IcppershipStatus


router = APIRouter()


class UpdateProfileItem(BaseModel):
    erc20_address: Optional[str] = None


def _user_profile_dict(user):
    icppership = Icppership.objects(icpper_github_login=user.github_login).first()
    res = {
        "nickname": user.nickname,
        "github_login": user.github_login,
        "avatar": user.avatar,
        "status": user.status,
        "erc20_address": user.erc20_address,
        "icppership": {}
    }
    if icppership:
        mentor = User.objects(github_login=icppership.mentor_github_login).first()

        number_of_instructors = Icppership.objects(
            mentor_github_login=mentor.github_login,
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
            "errorMessage": "ERC20_ADDRESS_FORMAT_INVALID"
        }
    
    if erc20_address:
        user.erc20_address = erc20_address

    user.save()
    return {
        "success": True,
        "data": _user_profile_dict(user)
    }
