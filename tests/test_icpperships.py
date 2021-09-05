
from app.common.models.icpdao.user import User, UserStatus
from app.common.models.icpdao.icppership import Icppership, IcppershipStatus, IcppershipProgress
from app.common.utils.errors import ICPPER_ALREADY_MENTOR_ERROR, ICPPER_PRE_MENTOR_MAX_ERROR, \
    COMMON_NOT_PERMISSION_ERROR, ICPPER_LOOP_BACK_ERROR
from app.routes.icpperships import PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT

from .base import Base


class TestIcpperships(Base):

    def test_create_and_accept(self):
        self.clear_db()

        # 创建 mentor user1 两个用户
        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')

        # mentor 邀请 user1
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        isp = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user1.github_login
        ).first()

        assert res.json()['data']['id'] == str(isp.id)
        assert res.json()['data']['progress'] == IcppershipProgress.PENDING.value
        assert res.json()['data']['status'] == IcppershipStatus.NORMAL.value
        assert res.json()['data']['mentor_github_login'] == mentor.github_login
        assert res.json()['data']['icpper']['github_login'] == isp.icpper_github_login
        assert res.json()['data']['icpper']['nickname'] == user1.nickname

        res = self.client.get('/profile', headers={'user_id': str(user1.id)})
        assert res.json()['data']['status'] == UserStatus.NORMAL.value
        assert res.json()['data']['icppership']['progress'] == IcppershipProgress.PENDING.value
        assert res.json()['data']['icppership']['status'] == IcppershipStatus.NORMAL.value
        assert res.json()['data']['icppership']['id'] == str(isp.id)
        assert res.json()['data']['icppership']['mentor']['github_login'] == mentor.github_login
        assert res.json()['data']['icppership']['mentor']['nickname'] == mentor.nickname
        assert res.json()['data']['icppership']['mentor']['avatar'] == mentor.avatar
        assert res.json()['data']['icppership']['mentor']['number_of_instructors'] == 0

        # user1 接受 mentor 邀请
        res = self.client.put(
            '/icpperships/{}/accept'.format(isp.id),
            headers={'user_id': str(user1.id)}
        )
        assert res.status_code == 200
        assert res.json()['data']['id'] == str(isp.id)
        assert res.json()['data']['progress'] == IcppershipProgress.ACCEPT.value
        assert res.json()['data']['status'] == IcppershipStatus.PRE_ICPPER.value
        assert res.json()['data']['mentor_github_login'] == mentor.github_login
        assert res.json()['data']['icpper']['github_login'] == isp.icpper_github_login
        assert res.json()['data']['icpper']['nickname'] == user1.nickname

        res = self.client.get('/profile', headers={'user_id': str(user1.id)})
        assert res.json()['data']['status'] == UserStatus.PRE_ICPPER.value
        assert res.json()['data']['icppership']['progress'] == IcppershipProgress.ACCEPT.value
        assert res.json()['data']['icppership']['status'] == IcppershipStatus.PRE_ICPPER.value
        assert res.json()['data']['icppership']['id'] == str(isp.id)
        assert res.json()['data']['icppership']['mentor']['github_login'] == mentor.github_login
        assert res.json()['data']['icppership']['mentor']['nickname'] == mentor.nickname
        assert res.json()['data']['icppership']['mentor']['avatar'] == mentor.avatar
        assert res.json()['data']['icppership']['mentor']['number_of_instructors'] == 0

        # 创建 user2 user3 两个用户
        user2 = self.create_normal_user('user2')
        user3 = self.create_normal_user('user3')

        # user1 邀请 user2
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(user1.id)},
            json={
                'icpper_github_login': user2.github_login
            }
        )
        assert res.status_code == 200
        # mentor 邀请 user3
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user3.github_login
            }
        )
        assert res.status_code == 200

        # user2 接受 user1 邀请
        isp = Icppership.objects(
            mentor_user_id=str(user1.id),
            icpper_github_login=user2.github_login
        ).first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(isp.id),
            headers={'user_id': str(user2.id)}
        )
        assert res.status_code == 200

        res = self.client.get('/profile', headers={'user_id': str(user1.id)})
        assert res.json()['data']['status'] == UserStatus.ICPPER.value
        assert res.json()['data']['icppership']['mentor']['number_of_instructors'] == 1

        res = self.client.get('/profile', headers={'user_id': str(user2.id)})
        assert res.json()['data']['icppership']['progress'] == IcppershipProgress.ACCEPT.value

        # 查询 mentor 的所有 icpperships
        res = self.client.get(
            '/icpperships',
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200
        assert len(res.json()['data']) == 2

        isp1 = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user1.github_login
        ).first()
        isp3 = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user3.github_login
        ).first()
        for item in res.json()['data']:
            if item['id'] not in [str(isp1.id), str(isp3.id)]:
                assert False
            if item['id'] == str(isp1.id):
                assert item['id'] == str(isp1.id)
                assert item['progress'] == IcppershipProgress.ACCEPT.value
                assert item['status'] == IcppershipStatus.ICPPER.value
                assert item['mentor_github_login'] == mentor.github_login
                assert item['icpper']['github_login'] == isp1.icpper_github_login
                assert item['icpper']['nickname'] == user1.nickname

        # mentor 删除邀请 user3
        res = self.client.get('/profile', headers={'user_id': str(user3.id)})
        assert res.json()['data']['status'] == UserStatus.NORMAL.value

        isp = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user3.github_login
        ).first()
        res = self.client.delete(
            '/icpperships/{}'.format(isp.id),
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200

        res = self.client.get('/profile', headers={'user_id': str(user3.id)})
        assert res.json()['data']['status'] == UserStatus.NORMAL.value

        assert Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user3.github_login
        ).first() == None

    def test_create_and_accept_no_user(self):
        self.clear_db()

        # 创建 mentor
        mentor = self.create_icpper_user('mentor')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': 'login_user1'
            }
        )
        assert res.status_code == 200
        assert not not res.json()['data']

        # 创建 user1
        user1 = self.create_normal_user('user1')
        assert user1.status == UserStatus.PRE_ICPPER.value

        # 接受邀请
        isp = Icppership.objects().first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(user1.id)}
        )
        assert res.status_code == 200
        assert not not res.json()['data']

        isp = Icppership.objects().first()
        assert isp.status == IcppershipStatus.PRE_ICPPER.value
        assert isp.progress == IcppershipProgress.ACCEPT.value

    def test_get_list_empty(self):
        self.clear_db()
        user = self.create_icpper_user()

        res = self.client.get(
            '/icpperships',
            headers={'user_id': str(user.id)}
        )
        assert res.status_code == 200
        assert len(res.json()['data']) == 0

    def test_create_normal_user(self):
        # 发送邀请 当前用户是普通用户，没有权限
        self.clear_db()

        user1 = self.create_normal_user('user1')
        user2 = self.create_normal_user('user2')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(user1.id)},
            json={
                'icpper_github_login': user2.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '403'

    def test_create_have_mentor(self):
        # 发送邀请 对方已经有 mentor
        self.clear_db()

        mentor1 = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')
        mentor2 = self.create_icpper_user('mentor2')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor1.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor2.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '403'
        assert res.json()['errorMessage'] == ICPPER_ALREADY_MENTOR_ERROR

    def test_create_with_mentor_limit(self):
        # 发送邀请 已经有PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT个邀请了
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user = self.create_normal_user('user')

        if PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT == -1:
            return

        for index in range(0, PRE_MENTOR_ICPPERSHIP_COUNT_LIMIT):
            user_index = self.create_normal_user('user{}'.format(index))
            res = self.client.post(
                '/icpperships',
                headers={'user_id': str(mentor.id)},
                json={
                    'icpper_github_login': user_index.github_login
                }
            )
            assert res.status_code == 200
            assert res.json()['success'] == True

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '403'
        assert res.json()['errorMessage'] == ICPPER_PRE_MENTOR_MAX_ERROR

    def test_create_icpper(self):
        # 邀请一个 没有 mentor 的 icpper
        # 创建 mentor icpper
        # 创建邀请
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        icpper = self.create_icpper_user('icpper')

        assert icpper.status == UserStatus.ICPPER.value
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': icpper.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] == True

        icpper = User.objects(github_login=icpper.github_login).first()
        assert icpper.status == UserStatus.ICPPER.value

        isp = Icppership.objects().first()

        assert isp.mentor_user_id == str(mentor.id)
        assert isp.icpper_github_login == icpper.github_login
        assert isp.icpper_user_id is None
        assert isp.progress == IcppershipProgress.PENDING.value
        assert isp.status == IcppershipStatus.ICPPER.value

        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(icpper.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        isp = Icppership.objects().first()

        assert isp.mentor_user_id == str(mentor.id)
        assert isp.icpper_user_id == str(icpper.id)
        assert isp.icpper_github_login == icpper.github_login
        assert isp.progress == IcppershipProgress.ACCEPT.value
        assert isp.status == IcppershipStatus.ICPPER.value

        icpper = User.objects(github_login=icpper.github_login).first()
        assert icpper.status == UserStatus.ICPPER.value

    def test_create_no_role(self):
        # 一个被邀请，但是还没有接收成为 pre icpper 的用户，不能邀请别人
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user = self.create_normal_user('user')
        user2 = self.create_normal_user('user2')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        user = User.objects(github_login=user.github_login).first()
        assert user.status == UserStatus.NORMAL.value

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(user.id)},
            json={
                'icpper_github_login': user2.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] == False
        assert res.json()['errorCode'] == '403'
        assert res.json()['errorMessage'] == COMMON_NOT_PERMISSION_ERROR

    def _link_mentor_and_icpper(self, mentor, icpper):
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': icpper.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        isp = Icppership.objects(
            icpper_github_login=icpper.github_login,
            mentor_user_id=str(mentor.id)
        ).first()

        assert isp.icpper_user_id is None
        assert isp.progress == IcppershipProgress.PENDING.value

        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(icpper.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        isp = Icppership.objects(
            icpper_github_login=icpper.github_login,
            mentor_user_id=str(mentor.id)
        ).first()

        assert isp.mentor_user_id == str(mentor.id)
        assert isp.icpper_user_id == str(icpper.id)
        assert isp.icpper_github_login == icpper.github_login
        assert isp.progress == IcppershipProgress.ACCEPT.value
        assert isp.status == IcppershipStatus.ICPPER.value

    def test_create_parent_mentor(self):
        self.clear_db()

        mentor_parent_2 = self.create_icpper_user('mentor_parent_2')
        mentor_parent_1 = self.create_icpper_user('mentor_parent_1')
        mentor = self.create_icpper_user('mentor')

        self._link_mentor_and_icpper(mentor_parent_1, mentor)
        self._link_mentor_and_icpper(mentor_parent_2, mentor_parent_1)

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': mentor_parent_2.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is False
        assert res.json()['errorMessage'] == ICPPER_LOOP_BACK_ERROR

    def test_accept_404(self):
        # 接收邀请 404
        self.clear_db()

        user = self.create_normal_user('user')

        res = self.client.put(
            '/icpperships/{}/accept'.format('0'*24),
            headers={'user_id': str(user.id)}
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '404'

    def test_accept_no_role(self):
        # 接收邀请 没有权限
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')
        user2 = self.create_normal_user('user2')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        isp = Icppership.objects().first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(user2.id)}
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '403'
        assert res.json()['errorMessage'] == COMMON_NOT_PERMISSION_ERROR

    def test_accept_parent_mentor(self):
        self.clear_db()

        mentor_parent_2 = self.create_icpper_user('mentor_parent_2')
        mentor_parent_1 = self.create_icpper_user('mentor_parent_1')
        mentor = self.create_icpper_user('mentor')

        self._link_mentor_and_icpper(mentor_parent_1, mentor)
        self._link_mentor_and_icpper(mentor_parent_2, mentor_parent_1)

        icppership = Icppership(
            mentor_user_id=str(mentor.id),
            icpper_github_login=mentor_parent_2.github_login
        )
        icppership.save()

        res = self.client.put(
            '/icpperships/{}/accept'.format(str(icppership.id)),
            headers={'user_id': str(mentor_parent_2.id)}
        )

        assert res.status_code == 200
        assert res.json()['success'] is False
        assert res.json()['errorMessage'] == ICPPER_LOOP_BACK_ERROR

    def test_access_repeat(self):
        # 接收邀请 重复调用
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')
        
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        isp = Icppership.objects().first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(user1.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        isp = Icppership.objects().first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(user1.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] == True
        assert not not res.json()['data']

    def test_delete_404(self):
        # 删除邀请 404
        self.clear_db()

        user = self.create_normal_user('user')

        res = self.client.delete(
            '/icpperships/{}'.format('0'*24),
            headers={'user_id': str(user.id)}
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '404'

    def test_delete_no_role(self):
        # 删除邀请 没有权限
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        isp = Icppership.objects().first()
        res = self.client.delete(
            '/icpperships/{}'.format(str(isp.id)),
            headers={'user_id': str(user1.id)}
        )
        assert res.status_code == 200
        assert res.json()['errorCode'] == '403'
        assert res.json()['errorMessage'] == COMMON_NOT_PERMISSION_ERROR

    def test_delete_pending(self):
        # 删除 pending 的邀请 对方从 pre 变成 normal
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')

        assert user1.status == UserStatus.NORMAL.value
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.NORMAL.value

        isp = Icppership.objects().first()
        res = self.client.delete(
            '/icpperships/{}'.format(str(isp.id)),
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.NORMAL.value

    def test_delete_no_user(self):
        self.clear_db()

        mentor = self.create_icpper_user('mentor')

        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': 'login_user1'
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        isp = Icppership.objects().first()
        res = self.client.delete(
            '/icpperships/{}'.format(str(isp.id)),
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

    def test_delete_accept(self):
        # 删除 已经 accept 的邀请 对方从 pre 变成 normal
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')

        assert user1.status == UserStatus.NORMAL.value
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.NORMAL.value

        isp = Icppership.objects().first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(isp.id),
            headers={'user_id': str(user1.id)}
        )

        isp = Icppership.objects().first()
        assert isp.progress == IcppershipProgress.ACCEPT.value

        isp = Icppership.objects().first()
        res = self.client.delete(
            '/icpperships/{}'.format(str(isp.id)),
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.NORMAL.value

    def test_delete_icpper(self):
        # mentor 邀请 user1, user1 成为 pre_icpper
        # user1 邀请 user2
        # user2 接收邀请，user1 成为 icpper
        # mentor 删除 user1 的邀请，user1 仍然是 icpper
        self.clear_db()

        mentor = self.create_icpper_user('mentor')
        user1 = self.create_normal_user('user1')
        user2 = self.create_normal_user('user2')

        assert user1.status == UserStatus.NORMAL.value
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': user1.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.NORMAL.value
        ########################
        isp = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user1.github_login
        ).first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(isp.id),
            headers={'user_id': str(user1.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']
        ########################
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(user1.id)},
            json={
                'icpper_github_login': user2.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.PRE_ICPPER.value

        user2 = User.objects(id=str(user2.id)).first()
        assert user2.status == UserStatus.NORMAL.value
        ########################
        isp = Icppership.objects(
            mentor_user_id=str(user1.id),
            icpper_github_login=user2.github_login
        ).first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(isp.id),
            headers={'user_id': str(user2.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        isp = Icppership.objects(
            mentor_user_id=str(user1.id),
            icpper_github_login=user2.github_login
        ).first()
        assert isp.progress == IcppershipProgress.ACCEPT.value
        assert isp.status == IcppershipStatus.PRE_ICPPER.value
        user2 = User.objects(id=str(user2.id)).first()
        assert user2.status == UserStatus.PRE_ICPPER.value

        isp1 = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user1.github_login
        ).first()
        assert isp1.progress == IcppershipProgress.ACCEPT.value
        assert isp1.status == IcppershipStatus.ICPPER.value
        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.ICPPER.value

        #######################
        isp1 = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=user1.github_login
        ).first()
        res = self.client.delete(
            '/icpperships/{}'.format(str(isp1.id)),
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

        user1 = User.objects(id=str(user1.id)).first()
        assert user1.status == UserStatus.ICPPER.value
