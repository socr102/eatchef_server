from django.conf import settings
from redis import Redis


def get_redis_instance(db='1') -> Redis:
    return Redis(
        host=settings.REDIS['host'],
        port=settings.REDIS['port'],
        db=db,
    )
