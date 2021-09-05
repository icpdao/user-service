import os
import random
import time

from fastapi import Request, APIRouter

from app.common.utils.errors import COMMON_NOT_AUTH_ERROR
from app.common.utils.github_rest_api import get_github_user_info_by_access_token, get_expires_at_by_access_token_info, \
    get_github_access_token_by_code
from app.helpers.jwt import encode_RS256
from app.common.models.icpdao.user import User, UserStatus
from app.common.models.icpdao.user_github_token import UserGithubToken
from app.common.models.icpdao.icppership import Icppership

from settings import (
    ICPDAO_JWT_RSA_PRIVATE_KEY,
    ICPDAO_GITHUB_APP_CLIENT_ID,
    ICPDAO_GITHUB_APP_CLIENT_SECRET
)

router = APIRouter()


def create_or_update_user(user_info):
    github_login = user_info.get('login')
    github_user_id = user_info.get('id')
    nickname = user_info.get('name', '')
    avatar_url = user_info.get('avatar_url', '')
    if not nickname:
        nickname = github_login
    user = User.objects(github_user_id=github_user_id).first()
    if user:
        user.nickname = nickname
        user.github_login = github_login
        user.avatar = avatar_url
        user.save()
    else:
        user = User(
            nickname=nickname,
            github_login=github_login,
            github_user_id=github_user_id,
            avatar=avatar_url
        )
        user.save()
    return user
        

def create_or_update_user_github_token(github_user_id, github_login, access_token_info):
    ugt = UserGithubToken.objects(github_user_id=github_user_id).first()
    if ugt:
        ugt.github_login = github_login
        ugt.access_token = access_token_info["access_token"]
        ugt.refresh_token = access_token_info["refresh_token"]
        ugt.expires_in = access_token_info["expires_in"]
        ugt.refresh_token_expires_in = access_token_info["refresh_token_expires_in"]
        ugt.token_at = access_token_info["token_at"]
        ugt.save()
    else:
        ugt = UserGithubToken(
            github_user_id=github_user_id,
            github_login=github_login,
            access_token=access_token_info["access_token"],
            refresh_token=access_token_info["refresh_token"],
            expires_in=access_token_info["expires_in"],
            refresh_token_expires_in=access_token_info["refresh_token_expires_in"],
            token_at=access_token_info["token_at"]
        )
        ugt.save()
    return ugt


def update_user_status_by_icppership(user):
    if user.status != UserStatus.NORMAL.value:
        return

    if Icppership.objects(icpper_github_login=user.github_login).first():
        user.status = UserStatus.PRE_ICPPER.value
        user.save()


@router.get('/github/auth_callback')
async def github_auth_callback(request: Request):
    code = request.query_params.get('code')

    if os.environ.get('IS_UNITEST') == 'yes':
        random.seed(code)
        github_user_id = int(random.random() * 10000)
        random.seed()
        user_info = {
            'id': github_user_id,
            'name': 'name_{}'.format(code),
            'login': 'login_{}'.format(code),
            'avatar_url': 'avatar_url_{}'.format(code)
        }
        access_token_info = {
            'access_token': 'access_token_{}'.format(code),
            'refresh_token': 'refresh_token_{}'.format(code),
            'expires_in': 3600,
            'refresh_token_expires_in': 3600,
            'token_at': int(time.time()) - 5
        }
    else:
        access_token_info = get_github_access_token_by_code(
            ICPDAO_GITHUB_APP_CLIENT_ID,
            ICPDAO_GITHUB_APP_CLIENT_SECRET,
            code
        )
        access_token = access_token_info['access_token']
        user_info = get_github_user_info_by_access_token(access_token)

    if user_info['login']:
        expires_at = get_expires_at_by_access_token_info(access_token_info)
        user = create_or_update_user(user_info)
        create_or_update_user_github_token(user_info['id'], user_info['login'], access_token_info)
        update_user_status_by_icppership(user)

        payload = {
            'user_id': str(user.id)
        }
        token = encode_RS256(payload, ICPDAO_JWT_RSA_PRIVATE_KEY)

        return {
            "success": True,
            "data": {'jwt': token, 'expires_at': expires_at}
        }
    else:
        return {
            "success": False,
            "errorCode": "401",
            "errorMessage": COMMON_NOT_AUTH_ERROR,
        }
