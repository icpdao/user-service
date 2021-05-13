import os

from flask import request

from app import app
from app.helpers.github_auth import get_github_access_token_by_code, get_github_user_info_by_access_token
from app.helpers.jwt import encode_RS256
from app.models.icpdao.user import User, UserStatus
from app.models.icpdao.user_github_token import UserGithubToken
from app.models.icpdao.icppership import Icppership

from settings import (
    ICPDAO_JWT_RSA_PRIVATE_KEY
)


def create_or_update_user(user_info):
    nickname = user_info.get('name', '')
    if not nickname:
        nickname = user_info['login']
    user = User.objects(github_login=user_info['login']).first()
    if user:
            user.nickname = nickname
            user.avatar = user_info['avatar_url']
            user.save()
    else:
        user = User(
            nickname = nickname,
            github_login = user_info['login'],
            avatar = user_info['avatar_url']
        )
        user.save()
    return user
        

def create_or_update_user_github_token(github_login, access_token_info):
    ugt = UserGithubToken.objects(github_login=github_login).first()
    if ugt:
        ugt.access_token = access_token_info["access_token"]
        ugt.refresh_token = access_token_info["refresh_token"]
        ugt.expires_in = access_token_info["expires_in"]
        ugt.refresh_token_expires_in = access_token_info["refresh_token_expires_in"]
        ugt.save()
    else:
        ugt = UserGithubToken(
            github_login = github_login,
            access_token = access_token_info["access_token"],
            refresh_token = access_token_info["refresh_token"],
            expires_in = access_token_info["expires_in"],
            refresh_token_expires_in = access_token_info["refresh_token_expires_in"]
        )
        ugt.save()
    return ugt


def update_user_status_by_icppership(user):
    if user.status != UserStatus.NORMAL.value:
        return

    if Icppership.objects(icpper_github_login=user.github_login).first():
        user.status = UserStatus.PRE_ICPPER.value
        user.save()


@app.route('/github/auth_callback')
def github_auth_callback():
    code = request.args.get('code')

    if os.environ.get('IS_UNITEST') == 'yes':
        user_info = {
            'name': 'name_{}'.format(code),
            'login': 'login_{}'.format(code),
            'avatar_url': 'avatar_url_{}'.format(code)
        }
        access_token_info = {
            'access_token': 'access_token_{}'.format(code),
            'refresh_token': 'refresh_token_{}'.format(code),
            'expires_in': 3600,
            'refresh_token_expires_in': 3600
        }
    else:
        access_token_info = get_github_access_token_by_code(code)
        access_token = access_token_info['access_token']
        user_info = get_github_user_info_by_access_token(access_token)

    if user_info['login']:
        user = create_or_update_user(user_info)
        create_or_update_user_github_token(user_info['login'], access_token_info)
        update_user_status_by_icppership(user)

        payload = {
            'user_id': str(user.id)
        }
        token = encode_RS256(payload, ICPDAO_JWT_RSA_PRIVATE_KEY)
        return {
            "success": True,
            "data": {'jwt': token}
        }
    else:
        return {
            "success": False,
            "errorCode": "401",
            "errorMessage": 'UNAUTHError',
        }
