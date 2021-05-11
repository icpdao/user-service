import os

ICPDAO_GITHUB_APP_CLIENT_ID = os.environ['ICPDAO_GITHUB_APP_CLIENT_ID']
ICPDAO_GITHUB_APP_CLIENT_SECRET = os.environ['ICPDAO_GITHUB_APP_CLIENT_SECRET']
ICPDAO_JWT_RSA_PRIVATE_KEY = os.environ['ICPDAO_JWT_RSA_PRIVATE_KEY'].replace('\\n', '\n')
API_GATEWAY_BASE_PATH = os.environ['API_GATEWAY_BASE_PATH']
AWS_AUTHORIZER_ARN = os.environ['AWS_AUTHORIZER_ARN']

ICPDAO_MONGODB_ICPDAO_HOST = os.environ['ICPDAO_MONGODB_ICPDAO_HOST']
