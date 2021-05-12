from flask import request

from app import app
from app.helpers.route_helper import get_current_user
from app.models.icpdao.user import User, UserStatus
from app.models.icpdao.icppership import Icppership, IcppershipStatus


def to_icppership_dict(icppership, icpper=None):
    if icpper:
        nickname = icpper.nickname
        github_login = icpper.github_login
    else:
        nickname = ""
        github_login = icppership.icpper_github_login
    return {
        "id":                  str(icppership.id),
        "progress":            icppership.progress,
        "status":              icppership.status, 
        "mentor_github_login": icppership.mentor_github_login,
        "icpper": {
            "nickname":        nickname,
            "github_login":    github_login,
        },
        "create_at":           icppership.create_at,
        "accept_at":           icppership.accept_at, 
        "icpper_at":           icppership.icpper_at, 
    }


@app.route('/icpperships/<icppership_id>/accept', methods=['PUT'])
def accept(icppership_id):
    user = get_current_user()

    icppership = Icppership.objects(id=icppership_id).first()
    if not icppership:
        return {
            "success": True,
            "errorCode": "404",
            "errorMessage": "NOT_FOUND"
        }

    if icppership.icpper_github_login != user.github_login:
        return {
            "success": True,
            "errorCode": "403",
            "errorMessage": "NO_ROLE"
        }

    icppership.accept()

    icppership_mentor = User.objects(github_login=icppership.mentor_github_login).first()
    if icppership_mentor.status == UserStatus.PRE_ICPPER.value:
        icppership_mentor.update_to_icpper()
        user_is = Icppership.objects(icpper_github_login=icppership_mentor.github_login).first()
        user_is.update_to_icpper()

    return {
        "success": True,
        "data": to_icppership_dict(icppership, user)
    }


@app.route('/icpperships', methods=['POST'])
def create():
    user = get_current_user()

    if user.status == UserStatus.NORMAL.value:
        return {
            "success": True,
            "errorCode": "403",
            "errorMessage": "NO_ROLE"
        }

    if Icppership.objects(mentor_github_login = user.github_login).count() >= 2:
        return {
            "success": True,
            "errorCode": "403",
            "errorMessage": "ALREADY_TWO_PRE_ICPPER"
        }

    icpper_github_login = request.json.get('icpper_github_login')
    if Icppership.objects(icpper_github_login = icpper_github_login).count() > 0:
        return {
            "success": True,
            "errorCode": "403",
            "errorMessage": "ALREADY_MENTOR"
        }

    icppership = Icppership(
        mentor_github_login = user.github_login,
        icpper_github_login = icpper_github_login
    )
    icppership.save()

    icpper = User.objects(github_login=icpper_github_login).first()
    icpper.update_to_pre_icpper()

    return {
        "success": True,
        "data": to_icppership_dict(icppership, icpper)
    }


@app.route('/icpperships/<icppership_id>', methods=['DELETE'])
def delete(icppership_id):
    user = get_current_user()

    icppership = Icppership.objects(id=icppership_id).first()
    if not icppership:
        return {
            "success": True,
            "errorCode": "404",
            "errorMessage": "NOT_FOUND"
        }

    if icppership.mentor_github_login != user.github_login:
        return {
            "success": True,
            "errorCode": "403",
            "errorMessage": "NO_ROLE"
        }

    Icppership.objects(id=icppership_id).delete()

    if icppership.status == IcppershipStatus.PRE_ICPPER.value:
        pre_icpper = User.objects(github_login=icppership.icpper_github_login).first()
        pre_icpper.update_to_normal()

    return {
        "success": True,
        "data": {}
    }


@app.route('/icpperships', methods=['GET'])
def get_list():
    user = get_current_user()

    is_list = [item for item in Icppership.objects(mentor_github_login=str(user.github_login))]

    icpper_login_list = [item.icpper_github_login for item in is_list]
    login_2_icpper = {}
    for icpper in User.objects(github_login__in=icpper_login_list):
        login_2_icpper[icpper.github_login] = icpper

    res = [to_icppership_dict(item, login_2_icpper.get(item.icpper_github_login, None)) for item in is_list]

    return {
        "success": True,
        "data": res
    }
