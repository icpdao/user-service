from flask import Flask, make_response
app = Flask('user-service')

from . import routes

@app.after_request
def set_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
    response.headers["Access-Control-Allow-Methods"] = "OPTIONS,DELETE,GET,HEAD,PATCH,POST,PUT"
    return response

@app.errorhandler(Exception)
def internal_error(error):
    response = make_response({'error': str(error)})
    return response, 500


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
        'user': {
            'host': self.settings.ICPDAO_MONGODB_USER_HOST,
            'alias': 'user',
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
    'user': {
        'host': settings.ICPDAO_MONGODB_USER_HOST,
        'alias': 'user',
    }
})
