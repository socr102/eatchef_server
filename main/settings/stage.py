from .common import *
from google.oauth2 import service_account

DEBUG = True

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'stage)(r$zokmzkv)6=jrde6vu)94as0(^&-l%4mya4inm%#b1^_gf+')
SECURE_AUTH_SALT = os.environ.get('SECURE_AUTH_SALT',
                                  'stage1_n=qJO51@GW%kqewWphc-`]*3$@6336H7sxhogE5tSO|aoM|3Q(zD3.+%E}~p<L')

BASE_URL = os.environ.get('BASE_URL', 'https://api.eatchef.goodbit.dev')
BASE_CLIENT_URL = os.environ.get('BASE_CLIENT_URL', 'https://eatchef.goodbit.dev')

# SECURITY WARNING: update this when you have the production host
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'api.eatchef.goodbit.dev,admin.eatchef.goodbit.dev,eatchef.goodbit.dev,localhost').split(',')

# Emails Settings
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'nitsenko94@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'WZEdF9CJ6J')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp-pulse.com')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '587')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', False)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'info@goodbit.dev')

ADMINS = [('Vlad', 'vladislav.levada@goodbit.dev')]

# Emails triggers
SEND_ACTIVATION_EMAIL = True
CHECK_EMAIL_ACTIVATION = False

LOG_PATH = os.path.join(BASE_DIR, '../logs')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout
        },
        'console_errors': {
            'level': 'WARNING',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stderr
        },
        'celery': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/celery.log',
            'formatter': 'verbose',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'root': {
        'handlers': ['console_errors'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'console_errors', 'file', 'mail_admins'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
        'celery': {
            'handlers': ['celery', 'console', 'console_errors'],
            'level': os.getenv('CELERY_LOG_LEVEL', 'INFO'),
        },
        'django.request': {
            'handlers': ['console', 'console_errors'],
            'propagate': False,
            'level': 'DEBUG'
        },
    },
}


STATIC_URL = '/static/'
MEDIA_PATH = 'media'
MEDIA_URL = '%s/%s/' % (BASE_URL, MEDIA_PATH)
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')


# cloud file storage
DEFAULT_FILE_STORAGE = 'main.storage_backends.MediaStorage'
GS_BUCKET_NAME = 'stage-eatchefs'
GS_LOCATION = 'media'
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    os.path.join(BASE_DIR, 'settings', 'atomic-dahlia-316917-740b0b638ed2.json')
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '245264013276-sbkrl06fu1e7d6m0d3724or58hvdmpej.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'T31vo_Y09jfQAuw2tDlzpSml'
SOCIAL_AUTH_FACEBOOK_KEY = '553583208994808'
SOCIAL_AUTH_FACEBOOK_SECRET = 'f47168d1351add4aa34a28d9c15f4fc4'


# payloads debug
MIDDLEWARE = ['request_logging.middleware.LoggingMiddleware'] + MIDDLEWARE

# also pip install ptpython
INSTALLED_APPS += [
    'request_logging',
]
