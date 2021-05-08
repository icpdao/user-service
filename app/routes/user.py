from flask import request

from app import app
from app.models.icpdao.user import User


def get_user_id():
    authorizer = request.environ['serverless.event']['requestContext']['authorizer']
    


@app.route('/profile')
def profile():
    # response += "\n=================================================================="
    # response += "\nserverless.event.requestContext.authorizer:{}".format(request.environ['serverless.event']['requestContext']['authorizer'])


    if user_info['login']:
        user = create_or_update_user(user_info)
        create_or_update_user_github_token(user_info['login'], access_token_info)

        payload = {
            'user_id': str(user.id)
        }
        token = encode_RS256(payload, ICPDAO_JWT_RSA_PRIVATE_KEY)
        return {
            'jwt': token
        }
    else:
        return {
            'message': "auth error"
        }, 401
