from enum import Enum
import time
from mongoengine import Document, StringField, IntField


class UserGithubToken(Document):
    meta = {
        'db_alias': 'icpdao',
        'collection': 'user_github_token'
    }

    # github login
    github_login = StringField(required=True, max_length=255)
    # access_token
    access_token = StringField(required=True, max_length=255)
    # expires_in
    expires_in = IntField(required=True)
    # refresh_token
    refresh_token = StringField(required=True, max_length=255)
    # refresh_token_expires_in
    refresh_token_expires_in = IntField(required=True)
