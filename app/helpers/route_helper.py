import os
from flask import request

from app.models.icpdao.user import User


def get_user_id():
    try:
        if os.environ.get('IS_UNITEST') == 'yes':
            return request.headers.get('user_id')
        else:
            authorizer = request.environ['serverless.event']['requestContext']['authorizer']
            return authorizer['user_id']
    except:
        return None


def find_current_user():
    user_id = get_user_id()
    if user_id:
        user = User.objects(id=user_id).first()
        if user:
            request.environ['icpdao.user'] = user
            return user
    else:
        return None


def get_current_user():
    try:
        return request.environ['icpdao.user']
    except:
        return None
