from .common import *
from google.oauth2 import service_account

DEBUG = False

# Удаляем не нужные зависимости для прода
INSTALLED_APPS.remove('drf_yasg')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
SECURE_AUTH_SALT = os.environ.get('SECURE_AUTH_SALT')

BASE_URL = os.environ.get('BASE_URL')
BASE_CLIENT_URL = os.environ.get('BASE_CLIENT_URL')

# cloud file storage
DEFAULT_FILE_STORAGE = 'main.storage_backends.MediaStorage'
GS_BUCKET_NAME = 'stage-eatchefs'
GS_LOCATION = 'media'
GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    os.path.join(BASE_DIR, 'settings', 'atomic-dahlia-316917-740b0b638ed2.json')
)

# SECURITY WARNING: update this when you have the production host
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Emails Settings
EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '587')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', False)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
EMAIL_FROM = os.environ.get('EMAIL_FROM')

# Emails triggers
SEND_ACTIVATION_EMAIL = True
CHECK_EMAIL_ACTIVATION = False

STATIC_URL = '/static/'
MEDIA_PATH = 'media'
MEDIA_URL = '%s/%s/' % (BASE_URL, MEDIA_PATH)
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '245264013276-avgqsj1umm7sc07sk2dtdgkpmqmn0p42.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '27KF4-qS4BgnriYmMVfXfE56'
SOCIAL_AUTH_FACEBOOK_KEY = '161418379213740'
SOCIAL_AUTH_FACEBOOK_SECRET = '9400ca8e8b798c1cf7dde384c4c0cbb2'

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_BROKER_TRANSPORT = 'amqp'

ADMINS = [('Eugene', 'eugene.nitsenko@gmail.com'), ('Vlad', 'vladislav.levada@goodbit.dev')]

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
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout
        },
        'console_errors': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stderr
        },
        'celery': {
            'level': 'INFO',
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
