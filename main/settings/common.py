"""
Django settings for main.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import sys
from datetime import timedelta

from corsheaders.defaults import default_headers

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:4096')
BASE_CLIENT_URL = os.environ.get('BASE_CLIENT_URL', 'http://localhost:8030')
# Build paths inside the main like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'q2*_*ek4!_lg_8iq8v4o(*e=i4(cn)uju5x_c!98r&hvbiayf3')
SECURE_AUTH_SALT = '1_n=qJO51@GW%kqewWphc-`]*3$@6336H7sxhogE5tSO|aoM|3Q(zD3.+%E}~p<L'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get('DJANGO_DEBUG', True))

ALLOWED_HOSTS = ['0.0.0.0', 'localhost', '127.0.0.1', 'main']

# Application definition
INSTALLED_APPS = [
    # system apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'storages',
    'social_django',
    'channels',
    'django.contrib.postgres',
    # 'request_logging',
    'djcelery_email',
    # User apps
    'users',
    'recipe',
    'social',
    'site_settings',
    'chef_pencils',
    'stats',
    'notifications',
]

MIDDLEWARE = [
    'main.middleware.RequestTimeLoggingMiddleware',
    # 'request_logging.middleware.LoggingMiddleware',
    'main.middleware.TimezoneMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


AUTH_USER_MODEL = 'users.User'

CORS_ALLOW_ALL_ORIGINS = True
CORS_EXPOSE_HEADERS = ['Content-Range']
CORS_ALLOW_HEADERS = default_headers + (
    'Range',
    'Content-Range'
)


# social-auth config url
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'main.social.pipeline.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_USER_MODEL = 'users.User'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '245264013276-sbkrl06fu1e7d6m0d3724or58hvdmpej.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'T31vo_Y09jfQAuw2tDlzpSml'

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {  # add this
    'fields': 'id, name, email'
}

# FB
SOCIAL_AUTH_LOGIN_REDIRECT_URL = f'{BASE_CLIENT_URL}/auth/login/social'

# Translation settings
USE_I18N = True
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English')
]

ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.base_url',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

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
    },
    'root': {
        'handlers': ['console_errors'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'console_errors', 'file'],
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

WSGI_APPLICATION = 'main.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': os.environ.get('DB_HOST', 'localhost,eatchef-postgres'),
        'NAME': os.environ.get('DB_NAME', 'main'),
        'USER': os.environ.get('DB_USER', 'main'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 's5yrbJ'),
        'PORT': os.environ.get('DB_PORT', 5432),
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(PROJECT_DIR, 'app-messages')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '2525')
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', False)
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', False)
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'info@gmail.com')

CELERY_EMAIL_TASK_CONFIG = {
    'queue': 'email',
    'rate_limit': '50/m',  # * CELERY_EMAIL_CHUNK_SIZE (default: 10)
}

CELERY_EMAIL_TASK_CONFIG = {
    'name': 'djcelery_email_send',
    'ignore_result': True,
}

# Emails triggers
SEND_ACTIVATION_EMAIL = False
CHECK_EMAIL_ACTIVATION = False

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# https://www.django-rest-framework.org/api-guide/permissions/#setting-the-permission-policy
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.tokens.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

AUTHENTICATION_BACKENDS = [
    # Default user authentication with jwt
    'main.backends.UserAuthenticationBackend',
    # Needed to login by username in Django admin, regardless of allauth
    'django.contrib.auth.backends.ModelBackend',
    # Social authentications
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
]

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
MEDIA_PATH = 'media'
MEDIA_URL = '%s/%s/' % (BASE_URL, MEDIA_PATH)
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')
TEST_FILES_ROOT = os.path.join(PROJECT_DIR, 'test_files')
TEMPLATES_ROOT = os.path.join(PROJECT_DIR, 'templates')

REDIS = {
    'host': 'eatchef-redis',
    'port': '6379',
    'db': '1',
}

# Channels
ASGI_APPLICATION = "main.websocket_routing.application"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS['host'], REDIS['port'])],
        },
    },
}

CELERY_ENABLE_UTC = True
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://main:BWgxXi6AoAM5VJwW@eatchef-rabbit'),
CELERY_BROKER_TRANSPORT = 'amqp'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

TESTS_VCR_FOR_REQUESTS_ENABLED = os.environ.get(
    'TESTS_VCR_FOR_REQUESTS_ENABLED', False)

RAPID_API_KEY = '9ff8cc9c40mshe718d4cddf8e1a2p177c01jsn6436b0355864'

EATCHEFS_ACCOUNT_NAME = 'Skinner'

DATA_UPLOAD_MAX_MEMORY_SIZE = 200 * 1024 * 1024