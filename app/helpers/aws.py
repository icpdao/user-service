import os
import boto3


def get_assume_role(role_arn, session_name, duration_seconds=900):
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
        DurationSeconds=duration_seconds
    )
    credentials = assumed_role_object['Credentials']
    return credentials

# 普通上传
def verson_1():
    aws_access_key_id = "XXXX"
    aws_secret_access_key = "XXXXX"

    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './jwt.py')
    data = open(path, 'rb')
    s3.put_object(Bucket='xxxx', Key='jwt.py', Body=data)


# 使用 STS 临时凭证上传
def verson_2():
    sts_client = boto3.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn="arn:aws:iam::xxxx:role/s3_files_upload",
        RoleSessionName="AssumeRoleSession1",
        DurationSeconds=900
    )
    credentials = assumed_role_object['Credentials']
    print(credentials)
    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './jwt.py')
    data = open(path, 'rb')
    s3.put_object(Bucket='xxxx', Key='jwt.py', Body=data)
