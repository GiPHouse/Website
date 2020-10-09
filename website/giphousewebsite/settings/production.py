import json
import base64

from giphousewebsite.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ['VIRTUAL_HOST'].split(',')

SESSION_COOKIE_SECURE = True

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': int(os.environ.get('POSTGRES_PORT', 5432)),
        'NAME': os.environ.get('POSTGRES_NAME'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
        'brief': {
            'format': '%(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'brief',
        },
        'file': {
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': '/giphouse/log/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'gsuitesync': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
        'github': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
        'automaticteams': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = '/giphouse/static/'
STATIC_URL = '/static/'

MEDIA_ROOT = '/giphouse/media/'
MEDIA_URL = '/media/'

# GitHub App Settings
DJANGO_GITHUB_CLIENT_ID = os.environ['DJANGO_GITHUB_CLIENT_ID']
DJANGO_GITHUB_CLIENT_SECRET = os.environ['DJANGO_GITHUB_CLIENT_SECRET']
DJANGO_GITHUB_SYNC_ORGANIZATION_NAME = os.environ['DJANGO_GITHUB_SYNC_ORGANIZATION_NAME']
DJANGO_GITHUB_SYNC_APP_ID = os.environ['DJANGO_GITHUB_SYNC_APP_ID']
DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64 = os.environ['DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64']
DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY = base64.urlsafe_b64decode(DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64)
DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID = os.environ['DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID']

# GSuite service account credentials
GSUITE_DOMAIN = os.environ['VIRTUAL_HOST']
GSUITE_ADMIN_USER = os.environ["DJANGO_GSUITE_ADMIN_USER"]
GSUITE_ADMIN_CREDENTIALS_BASE64 = os.environ["DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64"]
GSUITE_ADMIN_CREDENTIALS = base64.urlsafe_b64decode(GSUITE_ADMIN_CREDENTIALS_BASE64)
GSUITE_ADMIN_CREDENTIALS = json.loads(GSUITE_ADMIN_CREDENTIALS)
