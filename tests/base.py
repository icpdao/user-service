from fastapi.testclient import TestClient

from mongoengine.connection import get_db

from app import app
from app.common.models.icpdao.user import User, UserStatus


class Base:
    client = TestClient(app)

    def clear_db(self):
        get_db('icpdao').client.drop_database('icpdao')

    def create_icpper_user(self, code='user'):
        assert self.client.get('/github/auth_callback?code={}'.format(code)).status_code == 200
        user = User.objects(github_login='login_{}'.format(code)).first()
        user.status = UserStatus.ICPPER.value
        user.save()
        return user

    def create_normal_user(self, code='user'):
        assert self.client.get('/github/auth_callback?code={}'.format(code)).status_code == 200
        user = User.objects(github_login='login_{}'.format(code)).first()
        return user
