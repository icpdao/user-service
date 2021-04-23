from flask import Flask
app = Flask('user-service')

from . import routes
