import pytest

from app.models.icpdao.user import User
from app.models.icpdao.user_github_token import UserGithubToken

@pytest.mark.usefixtures('client_class')
class TestUsers():
    def test_profile_no_login(self):
        res = self.client.get('/profile')
        assert res.status_code == 200
        assert res.json['errorCode'] == '401'

    def test_profile_login(self):
        User.drop_collection()
        UserGithubToken.drop_collection()

        assert self.client.get('/github/auth_callback?code=hello').status_code == 200

        user = User.objects.first()
        assert user.nickname == 'name_hello'

        res = self.client.get('/profile', headers={'user_id': str(user.id)})
        
        assert res.json['data']['nickname'] == 'name_hello'
        assert res.json['data']['github_login'] == 'login_hello'
        assert res.json['data']['avatar'] == 'avatar_url_hello'
        assert res.json['data']['status'] == 0
        assert res.json['data']['erc20_address'] == None
        assert res.json['data']['icppership'] == {}
