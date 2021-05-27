import os

from fastapi import Request, APIRouter

from app.common.utils.route_helper import get_current_user
from app.helpers.aws import get_assume_role

from settings import (
    ICPDAO_AWS_UPLOAD_S3_ROLE_ARN
)

router = APIRouter()


@router.get('/aws/sts/upload_s3_assume_role')
async def upload_s3_assume_role(request: Request):
    user = get_current_user(request)

    if os.environ.get('IS_UNITEST') == 'yes':
        credentials = {
            "AccessKeyId": "AccessKeyId",
            "SecretAccessKey": "SecretAccessKey",
            "SessionToken": "SessionToken"
        }
    else:
        session_name = 'session_{}'.format(user.id)
        credentials = get_assume_role(ICPDAO_AWS_UPLOAD_S3_ROLE_ARN, session_name, 900)

    res = {
        'access_key_id': credentials['AccessKeyId'],
        'secret_access_key': credentials['SecretAccessKey'],
        'session_token': credentials['SessionToken']
    }

    return {
        "success": True,
        "data": res
    }
