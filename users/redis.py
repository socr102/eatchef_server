from redis import Redis

from utils.redis import get_redis_instance


class NewMailCache:
    redis: Redis

    def __init__(self):
        self.redis = get_redis_instance()

    @staticmethod
    def _gen_key(activation_email_code):
        return f'new_email:{activation_email_code}'

    def set_new_email(self, activation_email_code, new_email: str):
        self.redis.set(self._gen_key(activation_email_code), new_email, ex=24 * 600 * 600)

    def get_new_email(self, activation_email_code):
        value = self.redis.get(self._gen_key(activation_email_code))
        if value is None:
            return None
        return value.decode('utf-8')
