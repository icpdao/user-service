from flask import request

from app import app
from app.helpers.route_helper import get_current_user
from app.models.icpdao.user import User
from app.models.icpdao.icppership import Icppership, IcppershipStatus


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


@app.route('/profile')
def profile():
    user = get_current_user()

    return {
        "success": True,
        "data": _user_profile_dict(user)
    }
