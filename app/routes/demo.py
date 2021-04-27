from flask import request

from app import app
from app.models.user.user import User

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
    user = User.objects(nickname=name).first()
    if not user:
        user = User(nickname=name).save()

    return user.to_json()

@app.route("/test", methods = ['POST', 'GET'])
def test():
    headers = []
    for k,v in request.headers.items():
        headers.append("{}:{}".format(k, v))
    # response += "\n=================================================================="
    # response += "\nserverless.event.requestContext.authorizer:{}".format(request.environ['serverless.event']['requestContext']['authorizer'])
    return {
        'data': request.get_json(),
        'headers': headers
    }
