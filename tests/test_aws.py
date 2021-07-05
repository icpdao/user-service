from .base import Base


class TestAws(Base):
 
    def test_sts_upload_s3_assume_role(self):
        self.clear_db()

        user = self.create_icpper_user('user')

        # mentor 邀请 user1
        res = self.client.get(
            '/aws/sts/upload_s3_assume_role',
            headers={'user_id': str(user.id)}
        )
        assert res.status_code == 200

        assert res.json()['data']['access_key_id'] == 'AccessKeyId'
        assert res.json()['data']['secret_access_key'] == 'SecretAccessKey'
        assert res.json()['data']['session_token'] == 'SessionToken'
