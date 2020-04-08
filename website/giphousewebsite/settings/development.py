import base64
import json
import os

import github

from giphousewebsite.settings.base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'fnm1xg4jbokf^=x9m6covu2o5)qc0txurb6@k*u3$u9u$@v)7-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# GitHub App Settings
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
GITHUB_ORGANIZATION_NAME = os.environ.get('GITHUB_ORGANIZATION_NAME', '')
GITHUB_APP_ID = os.environ.get('GITHUB_APP_ID', '')
GITHUB_APP_PRIVATE_KEY_BASE64 = os.environ.get('GITHUB_APP_PRIVATE_KEY_BASE64', '')
GITHUB_APP_PRIVATE_KEY = base64.urlsafe_b64decode(GITHUB_APP_PRIVATE_KEY_BASE64)
GITHUB_APP_INSTALLATION_ID = os.environ.get('GITHUB_APP_INSTALLATION_ID', '')
GITHUB_REPO_PRIVATE = os.environ.get('GITHUB_REPO_PRIVATE', 'False') == 'True'

# Use debug-level logging for GitHub synchronisation
github.enable_console_debug_logging()

# GSuite service account credentials
GSUITE_ADMIN_USER = os.environ.get("DJANGO_GSUITE_ADMIN_USER", "giphouse2020@staging.giphouse.nl")
GSUITE_ADMIN_CREDENTIALS_BASE64 = os.environ.get("DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64", base64.urlsafe_b64encode(b"{}"))
GSUITE_ADMIN_CREDENTIALS = base64.urlsafe_b64decode(GSUITE_ADMIN_CREDENTIALS_BASE64)
GSUITE_ADMIN_CREDENTIALS = json.loads(GSUITE_ADMIN_CREDENTIALS)
