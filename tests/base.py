from fastapi.testclient import TestClient

from app.main import app
from app.models.icpdao.user import User
from app.models.icpdao.user_github_token import UserGithubToken
from app.models.icpdao.icppership import Icppership


class Base():
    client = TestClient(app)

    def clear_db(self):
        User.drop_collection()
        UserGithubToken.drop_collection()
        Icppership.drop_collection()

    def create_icpper_user(self, code='user'):
        assert self.client.get('/github/auth_callback?code={}'.format(code)).status_code == 200
        user = User.objects(github_login='login_{}'.format(code)).first()
        user.update_to_icpper()
        return user

    def create_normal_user(self, code='user'):
        assert self.client.get('/github/auth_callback?code={}'.format(code)).status_code == 200
        user = User.objects(github_login='login_{}'.format(code)).first()
        return user
