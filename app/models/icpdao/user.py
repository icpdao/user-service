from enum import Enum
import time
from mongoengine import Document, StringField, IntField


class UserStatus(Enum):
    NORMAL     = 0
    PRE_ICPPER = 1
    ICPPER     = 2


class User(Document):
    meta = {
        'db_alias': 'icpdao',
        'collection': 'user'
    }

    # 昵称
    nickname = StringField(required=True, max_length=255)
    # github login
    github_login = StringField(required=True, max_length=255)
    # avatar
    avatar = StringField(required=True, max_length=255)
    # 用户类型
    status = IntField(required=True,
        default=UserStatus.NORMAL.value,
        choices=[i.value for i in list(UserStatus)])
    # 用户钱包地址
    erc20_address = StringField(max_length=42)
    # 创建时间
    create_at = IntField(required=True, default=time.time)

    def update_to_normal(self):
        self.status = UserStatus.NORMAL.value
        self.save()

    def update_to_pre_icpper(self):
        self.status = UserStatus.PRE_ICPPER.value
        self.save()

    def update_to_icpper(self):
        self.status = UserStatus.ICPPER.value
        self.save()
