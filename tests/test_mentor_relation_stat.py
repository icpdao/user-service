from app.common.models.icpdao.icppership import Icppership, MentorRelationStat, MentorLevel7IcpperCountStat
from tests.base import Base


class TestMentorRelationStat(Base):
    def _link_relation(self, mentor, icpper):
        res = self.client.post(
            '/icpperships',
            headers={'user_id': str(mentor.id)},
            json={
                'icpper_github_login': icpper.github_login
            }
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

        isp = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=icpper.github_login
        ).first()
        res = self.client.put(
            '/icpperships/{}/accept'.format(str(isp.id)),
            headers={'user_id': str(icpper.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True
        assert not not res.json()['data']

    def _delete_link_relation(self, mentor, icpper):
        isp = Icppership.objects(
            mentor_user_id=str(mentor.id),
            icpper_github_login=icpper.github_login
        ).first()
        res = self.client.delete(
            '/icpperships/{}'.format(str(isp.id)),
            headers={'user_id': str(mentor.id)}
        )
        assert res.status_code == 200
        assert res.json()['success'] is True

    def _assert_has_reward_icpper_count(self, mentor, icpper, has_reward_icpper_count, relation=True):
        stat = MentorRelationStat.objects(
            mentor_id=str(mentor.id),
            icpper_id=str(icpper.id)
        ).first()
        assert stat.has_reward_icpper_count == has_reward_icpper_count
        assert stat.relation == relation

    def _assert_level_7(self, mentor, level_1_count, level_2_count, level_3_count, level_4_count, level_5_count, level_6_count, level_7_count):
        stat = MentorLevel7IcpperCountStat.objects(
            mentor_id=str(mentor.id)
        ).first()
        assert stat.level_1_count == level_1_count
        assert stat.level_2_count == level_2_count
        assert stat.level_3_count == level_3_count
        assert stat.level_4_count == level_4_count
        assert stat.level_5_count == level_5_count
        assert stat.level_6_count == level_6_count
        assert stat.level_7_count == level_7_count

    def test_1(self):
        self.clear_db()
        user_zu = self.create_icpper_user("user_zu")
        user_a = self.create_normal_user("user_a")
        self._link_relation(user_zu, user_a)
        self._assert_has_reward_icpper_count(user_zu, user_a, 1)
        self._assert_level_7(user_zu, 1, 1, 1, 1, 1, 1, 1)

        user_b1 = self.create_normal_user("user_b1")
        user_b2 = self.create_normal_user("user_b2")

        self._link_relation(user_a, user_b1)
        self._assert_has_reward_icpper_count(user_zu, user_a, 2)
        self._assert_level_7(user_zu, 1, 2, 2, 2, 2, 2, 2)
        self._assert_has_reward_icpper_count(user_a, user_b1, 1)
        self._assert_level_7(user_a, 1, 1, 1, 1, 1, 1, 1)

        self._link_relation(user_a, user_b2)
        self._assert_has_reward_icpper_count(user_zu, user_a, 3)
        self._assert_level_7(user_zu, 1, 3, 3, 3, 3, 3, 3)
        self._assert_has_reward_icpper_count(user_a, user_b2, 1)
        self._assert_level_7(user_a, 2, 2, 2, 2, 2, 2, 2)

        user_c1 = self.create_normal_user("user_c1")
        user_c2 = self.create_normal_user("user_c2")
        self._link_relation(user_b1, user_c1)
        self._link_relation(user_b1, user_c2)
        self._assert_has_reward_icpper_count(user_zu, user_a, 5)
        self._assert_level_7(user_zu, 1, 3, 5, 5, 5, 5, 5)

        user_c3 = self.create_normal_user("user_c3")
        user_c4 = self.create_normal_user("user_c4")
        self._link_relation(user_b2, user_c3)
        self._link_relation(user_b2, user_c4)
        self._assert_has_reward_icpper_count(user_zu, user_a, 7)
        self._assert_level_7(user_zu, 1, 3, 7, 7, 7, 7, 7)
        self._assert_has_reward_icpper_count(user_a, user_b1, 3)

        user_d1 = self.create_normal_user("user_d1")
        user_d2 = self.create_normal_user("user_d2")
        user_d3 = self.create_normal_user("user_d3")
        user_d4 = self.create_normal_user("user_d4")
        user_d5 = self.create_normal_user("user_d5")
        user_d6 = self.create_normal_user("user_d6")
        user_d7 = self.create_normal_user("user_d7")
        user_d8 = self.create_normal_user("user_d8")

        self._link_relation(user_c1, user_d1)
        self._link_relation(user_c1, user_d2)
        self._link_relation(user_c2, user_d3)
        self._link_relation(user_c2, user_d4)
        self._link_relation(user_c3, user_d5)
        self._link_relation(user_c3, user_d6)
        self._link_relation(user_c4, user_d7)
        self._link_relation(user_c4, user_d8)

        self._assert_has_reward_icpper_count(user_zu, user_a, 15)
        self._assert_level_7(user_zu, 1, 3, 7, 15, 15, 15, 15)
        self._assert_has_reward_icpper_count(user_a, user_b1, 7)
        self._assert_level_7(user_a, 2, 6, 14, 14, 14, 14, 14)
        self._assert_level_7(user_b1, 2, 6, 6, 6, 6, 6, 6)

        user_e1 = self.create_normal_user("user_e1")
        user_e2 = self.create_normal_user("user_e2")
        user_f1 = self.create_normal_user("user_f1")
        user_f2 = self.create_normal_user("user_f2")
        user_g1 = self.create_normal_user("user_g1")
        user_g2 = self.create_normal_user("user_g2")
        user_h1 = self.create_normal_user("user_h1")
        user_h2 = self.create_normal_user("user_h2")
        user_i1 = self.create_normal_user("user_i1")
        user_i2 = self.create_normal_user("user_i2")
        user_j1 = self.create_normal_user("user_j1")
        user_j2 = self.create_normal_user("user_j2")

        self._link_relation(user_d1, user_e1)
        self._link_relation(user_d1, user_e2)

        self._link_relation(user_e1, user_f1)
        self._link_relation(user_e1, user_f2)

        self._link_relation(user_f1, user_g1)
        self._link_relation(user_f1, user_g2)

        self._link_relation(user_g1, user_h1)
        self._link_relation(user_g1, user_h2)

        self._link_relation(user_h1, user_i1)
        self._link_relation(user_h1, user_i2)

        self._link_relation(user_i1, user_j1)
        self._link_relation(user_i1, user_j2)

        self._assert_has_reward_icpper_count(user_zu, user_a, 21)
        self._assert_level_7(user_zu, 1, 3, 7, 15, 17, 19, 21)

        self._delete_link_relation(user_a, user_b2)
        self._assert_has_reward_icpper_count(user_zu, user_a, 14)
        self._assert_level_7(user_zu, 1, 2, 4, 8, 10, 12, 14)
        self._assert_has_reward_icpper_count(user_a, user_b2, 7, False)

        self._delete_link_relation(user_a, user_b1)
        self._assert_has_reward_icpper_count(user_zu, user_a, 1)
        self._assert_level_7(user_zu, 1, 1, 1, 1, 1, 1, 1)
        self._assert_has_reward_icpper_count(user_a, user_b1, 15, False)

        self._link_relation(user_a, user_b1)
        self._assert_has_reward_icpper_count(user_zu, user_a, 14)
        self._assert_level_7(user_zu, 1, 2, 4, 8, 10, 12, 14)
        self._assert_has_reward_icpper_count(user_a, user_b1, 15, True)

        self._link_relation(user_a, user_b2)
        self._assert_has_reward_icpper_count(user_zu, user_a, 21)
        self._assert_level_7(user_zu, 1, 3, 7, 15, 17, 19, 21)
        self._assert_has_reward_icpper_count(user_a, user_b2, 7, True)

        self._assert_has_reward_icpper_count(user_b2, user_c3, 3)
        self._assert_level_7(user_b2, 2, 6, 6, 6, 6, 6, 6)

        self._delete_link_relation(user_b2, user_c3)
        self._assert_has_reward_icpper_count(user_b2, user_c3, 3, False)
        self._assert_level_7(user_b2, 1, 3, 3, 3, 3, 3, 3)
        self._assert_has_reward_icpper_count(user_zu, user_a, 18)
        self._assert_level_7(user_zu, 1, 3, 6, 12, 14, 16, 18)

        self._delete_link_relation(user_a, user_b2)
        self._assert_has_reward_icpper_count(user_zu, user_a, 14)
        self._assert_level_7(user_zu, 1, 2, 4, 8, 10, 12, 14)
        self._assert_has_reward_icpper_count(user_a, user_b2, 4, False)

        self._link_relation(user_b2, user_c3)
        self._assert_has_reward_icpper_count(user_b2, user_c3, 3)
        self._assert_level_7(user_b2, 2, 6, 6, 6, 6, 6, 6)

        self._link_relation(user_a, user_b2)
        self._assert_has_reward_icpper_count(user_zu, user_a, 21)
        self._assert_level_7(user_zu, 1, 3, 7, 15, 17, 19, 21)
        self._assert_has_reward_icpper_count(user_a, user_b2, 7, True)
