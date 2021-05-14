import os
from flask import request

from fastapi import Request
from app.models.icpdao.user import User


def get_user_id(request: Request):
    try:
        if os.environ.get('IS_UNITEST') == 'yes':
            return request.headers.get('user_id')
        else:
            authorizer = request.scope['aws.event']['requestContext']['authorizer']
            return authorizer['user_id']
    except:
        return None


def find_current_user(request: Request):
    user_id = get_user_id(request)
    if user_id:
        user = User.objects(id=user_id).first()
        if user:
            request.scope['icpdao.user'] = user
            return user
    else:
        return None


def get_current_user(request: Request):
    try:
        return request.scope['icpdao.user']
    except:
        return None
