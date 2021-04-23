import time
import jwt

"""
# 1. 生成 2048 位的 RSA 密钥
openssl genrsa -out rsa-private-key.pem 2048

# 2. 通过密钥生成公钥
openssl rsa -in rsa-private-key.pem -pubout -out rsa-public-key.pem
"""
def encode_RS256(payload, private_key, exp=86400):
    exp = int(time.time() + exp)
    payload['exp'] = exp

    token = jwt.encode(payload=payload, key=private_key, algorithm='RS256')
    return token

def decode_RS256(token, public_key):
    try:
        decoded = jwt.decode(token, public_key, algorithms=["RS256"])
    except jwt.exceptions.ExpiredSignatureError:
        return None
    return decoded
