import json
import base64

from giphousewebsite.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['staging.giphouse.nl', 'giphouse.nl']

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
    'handlers': {
        'file': {
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'class': 'logging.FileHandler',
            'filename': '/giphouse/log/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': True,
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
GITHUB_CLIENT_ID = os.environ['GITHUB_CLIENT_ID']
GITHUB_CLIENT_SECRET = os.environ['GITHUB_CLIENT_SECRET']
GITHUB_ORGANIZATION_NAME = os.environ['GITHUB_ORGANIZATION_NAME']
GITHUB_APP_ID = os.environ['GITHUB_APP_ID']
GITHUB_APP_PRIVATE_KEY_BASE64 = os.environ['GITHUB_APP_PRIVATE_KEY_BASE64']
GITHUB_APP_PRIVATE_KEY = base64.urlsafe_b64decode(GITHUB_APP_PRIVATE_KEY_BASE64)
GITHUB_APP_INSTALLATION_ID = os.environ['GITHUB_APP_INSTALLATION_ID']
GITHUB_REPO_PRIVATE = os.environ.get('GITHUB_REPO_PRIVATE', 'False') == 'True'

# GSuite service account credentials
GSUITE_ADMIN_USER = os.environ["DJANGO_GSUITE_ADMIN_USER"]
GSUITE_ADMIN_CREDENTIALS_BASE64 = os.environ["DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64"]
GSUITE_ADMIN_CREDENTIALS = base64.urlsafe_b64decode(GSUITE_ADMIN_CREDENTIALS_BASE64)
GSUITE_ADMIN_CREDENTIALS = json.loads(GSUITE_ADMIN_CREDENTIALS)
