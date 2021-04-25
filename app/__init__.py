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
