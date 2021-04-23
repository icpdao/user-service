# user-service
icpdao backend user-service

# dev
## config
1. need python and nodejs
2. run test
```
npm install
pip install -r requirements.txt
pytest tests
```

# deploy to aws
1. install aws-cli and config by https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html
2. install serverless cli and config by https://www.serverless.com/framework/docs/getting-started/
3. add .env
4. deploy
```
sls deploy --stage dev
sls deploy --stage prod
```
