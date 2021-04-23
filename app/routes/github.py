from flask import request

from app import app
from app.helpers.github_auth import get_github_access_token_by_code, get_github_user_info_by_access_token
from app.helpers.jwt import encode_RS256

from settings import (
    ICPDAO_JWT_RSA_PRIVATE_KEY
)

@app.route('/github/auth_callback')
def github_auth_callback():
    code = request.args.get('code')
    access_token_info = get_github_access_token_by_code(code)
    access_token = access_token_info['access_token']
    user_info = get_github_user_info_by_access_token(access_token)

    if user_info['id']:
        # 说明认证成功
        # TODO 1. 根据  user github id 查找获取创建 user
        payload = {
            'user_id': 'usermockid'
        }
        token = encode_RS256(payload, ICPDAO_JWT_RSA_PRIVATE_KEY)
        return {
            'jwt': token
        }
    else:
        return {
            'message': "auth error"
        }, 401
