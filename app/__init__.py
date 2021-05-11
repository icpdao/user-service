import os

from flask import Flask, make_response, request
from app.helpers.route_helper import find_current_user

app = Flask('user-service')

from . import routes

UN_NEED_AUTH_PATH = [
    '/github/auth_callback'
]

class UNAUTHError(Exception):
    pass

@app.before_request
def before():
    if request.path not in UN_NEED_AUTH_PATH:
        print(request.path)
        if not find_current_user():
            raise UNAUTHError


@app.after_request
def set_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
    response.headers["Access-Control-Allow-Methods"] = "OPTIONS,DELETE,GET,HEAD,PATCH,POST,PUT"
    return response

@app.errorhandler(Exception)
def internal_error(error):
    if type(error) == UNAUTHError:
        return {
            "success": True,
            "errorCode": "401",
            "errorMessage": 'UNAUTHError',
        }

    if os.environ.get('IS_UNITEST') == 'yes':
        raise error
    return {
        "success": True,
        "errorCode": "500",
        "errorMessage": str(error),
    }


# mongodb
from mongoengine import connect, connection
import logging
import settings

dbs = {}

def init_mongo(mongo_config):
    """
    Connect to mongo database
    mongo_config:
    {
        'icpdao': {
            'host': self.settings.ICPDAO_MONGODB_ICPDAO_HOST,
            'alias': 'icpdao',
        },
        'xxx': {
            'host': self.settings.ICPDAO_MONGODB_XXX_HOST,
            'alias': 'xxx',
        }
    }
    """
    global dbs
    for dbname, conn_config in mongo_config.items():
        alias = conn_config['alias']
        host = conn_config['host']
        logging.info('connect mongo {}'.format(alias))
        dbs[alias] = connect(alias=alias, host=host)

def disconnect_mongo():
    for dbalias, con in dbs.items():
        connection.disconnect(dbalias)

init_mongo({
    'icpdao': {
        'host': settings.ICPDAO_MONGODB_ICPDAO_HOST,
        'alias': 'icpdao',
    }
})
