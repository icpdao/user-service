import os
import pytest
from app.helpers.jwt import encode_RS256, decode_RS256

TESTS_ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

@pytest.mark.usefixtures('client_class')
class TestJWT():
    def test_jwt(self):
        public_key = open('{}/rs256/rsa-public-key.pem'.format(TESTS_ROOT_DIR), 'r').read()
        private_key = open('{}/rs256/rsa-private-key.pem'.format(TESTS_ROOT_DIR), 'r').read()
        
        payload = {
            "user_id": "mockid"
        }
        token = encode_RS256(payload, private_key)

        content = decode_RS256(token, public_key)
        assert content['user_id'] == 'mockid'

        token = encode_RS256(payload, private_key, exp=-1)

        content = decode_RS256(token, public_key)
        assert content == None
