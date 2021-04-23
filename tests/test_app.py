import pytest

@pytest.mark.usefixtures('client_class')
class TestApp():
    def test_app(self):
        assert self.client.get('/hello').status_code == 200
        assert self.client.get('/hello').data == b'hello'
        assert self.client.get('/hello_json').get_json()['message'] == 'hello_json' 
        assert self.client.get('/hello_json').status_code == 401
    # def test_github(self):
    #     assert self.client.get('/github/auth_callback?code=359b7211dd5662065436').get_json()['jwt'] == '359b7211dd5662065436'
