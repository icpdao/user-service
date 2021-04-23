import requests
import json

from settings import (
    ICPDAO_GITHUB_APP_CLIENT_ID,
    ICPDAO_GITHUB_APP_CLIENT_SECRET
)


def get_github_access_token_by_code(code):
    """
    result:
    {
        "access_token": "ghu_16C7e42F292c6912E7710c838347Ae178B4a",
        "expires_in": 28800,
        "refresh_token": "ghr_1B4a2e77838347a7E420ce178F2E7c6912E169246c34E1ccbF66C46812d16D5B1A9Dc86A1498",
        "refresh_token_expires_in": 15811200,
        "scope": "",
        "token_type": "bearer"
    }
    """
    url = "https://github.com/login/oauth/access_token?client_id={}&client_secret={}&code={}".format(
        ICPDAO_GITHUB_APP_CLIENT_ID,
        ICPDAO_GITHUB_APP_CLIENT_SECRET,
        code
    )
    headers = {
        "Accept": "application/json"
    }

    res = requests.post(url=url, headers=headers, timeout=10)
    return json.loads(res.text)


def get_github_user_info_by_access_token(access_token):
    url = "https://api.github.com/user"
    headers = {
        "Authorization": "token {}".format(access_token)
    }

    res = requests.get(url=url, headers=headers, timeout=10)
    return json.loads(res.text)
