from .common import *

DEBUG = True

SECRET_KEY = 'test)(r$zokmzkv)6=jrwe6vu)94as0(^&-l%4mya4inm%#b1^_gf+'

BASE_URL = os.environ.get('BASE_CLIENT_URL', 'http://localhost:4096')
BASE_CLIENT_URL = os.environ.get('BASE_CLIENT_URL', 'http://localhost:3000')

# SECURITY WARNING: update this when you have the production host
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'NAME': os.environ.get('DB_NAME', 'eatchef'),
        'USER': os.environ.get('DB_USER', 'eatchef'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 's5yrbJ'),
        'PORT': os.environ.get('DB_PORT', 5432),
    }
}

REDIS = {
    'host': 'host.docker.internal',
    'port': '6379',
    'db': '1',
}

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS['host'], REDIS['port'])],
        },
    },
}

# AWS_STORAGE_BUCKET_NAME = 'test-robin-stage'
# MEDIA_URL = '%s//%s/%s/' % (AWS_S3_URL_PROTOCOL, AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
# DEFAULT_FILE_STORAGE = 'main.storage_backends.MediaStorage'
