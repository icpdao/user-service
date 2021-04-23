from flask import request

from app import app


@app.route('/hello')
def hello():
    return 'hello'

@app.route('/hello_json')
def hello_json():
    return {"message": "hello_json"}, 401

@app.route('/user/login')
def login():
    return 'login'

@app.route('/user/info/<name>')
def info(name):
    return 'user: ' + name + '!'

@app.route("/head", methods = ['POST', 'GET'])
def bbbb():
    headers = request.headers
    response = ""
    for k,v in headers.items():
        response += "\n{}:{}".format(k, v)
    response += "\n=================================================================="
    response += "\nserverless.event.requestContext.authorizer:{}".format(request.environ['serverless.event']['requestContext']['authorizer'])
    return response
