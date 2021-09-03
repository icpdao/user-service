import time

import redis
from redis.exceptions import LockNotOwnedError, LockError

from .base import Base
from settings import ICPDAO_REDIS_LOCK_DB_URL


class TestRedis(Base):
    def test_1(self):
        conn = redis.Redis.from_url(ICPDAO_REDIS_LOCK_DB_URL)
        try:
            with conn.lock('my-lock-key', timeout=5, blocking_timeout=5) as lock:
                print(1111)
                time.sleep(6)
                print(2222)
        except LockNotOwnedError:
            # 使用锁超时了
            print(3333)
        except LockError:
            # 没有获取到锁
            print(4444)


