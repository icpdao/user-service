import os

from fastapi import FastAPI, Request
from mangum import Mangum
from fastapi.responses import JSONResponse

app = FastAPI()

from app.helpers.route_helper import find_current_user

from app import routes

UN_NEED_AUTH_PATH = [
    '/github/auth_callback'
]

class UNAUTHError(Exception):
    pass


def set_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
    response.headers["Access-Control-Allow-Methods"] = "OPTIONS,DELETE,GET,HEAD,PATCH,POST,PUT"


def build_response(status_code, content):
    response = JSONResponse(
        status_code=status_code,
        content=content
    )
    set_cors(response)
    return response


@app.middleware("http")
async def add_global_process(request: Request, call_next):
    if request.url.path not in UN_NEED_AUTH_PATH:
        if not find_current_user(request):
            return build_response(200, {
                "success": False,
                "errorCode": "401",
                "errorMessage": 'UNAUTHError',
            })
        
    try:
        response = await call_next(request)
    except Exception as ex:
        if os.environ.get('IS_UNITEST') == 'yes':
            raise ex

        return build_response(200, {
            "success": False,
            "errorCode": "500",
            "errorMessage": str(ex),
        })

    set_cors(response)
    return response

handler = Mangum(app)
