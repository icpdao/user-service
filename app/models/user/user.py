from mongoengine import Document, StringField


class User(Document):
    meta = {
        'db_alias': 'user',
        'collection': 'user'
    }

    # 昵称
    nickname = StringField(max_length=255)
 