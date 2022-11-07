"""
Django settings for giphousewebsite project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

# Application definition

INSTALLED_APPS = [
    'giphousewebsite',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'sass_processor',
    'django_bootstrap5',
    'admin_auto_filters',
    'admin_totals',
    'django_easy_admin_object_actions',

    'questionnaires.apps.QuestionnairesConfig',
    'github_oauth.apps.GithubConfig',
    'registrations.apps.RegistrationsConfig',
    'courses.apps.CoursesConfig',
    'projects.apps.ProjectsConfig',
    'room_reservation.apps.RoomReservationConfig',
    'mailing_lists.apps.MailingListsConfig',
    'tasks.apps.TasksConfig',
    'lecture_registrations.apps.LectureRegistrationsConfig'
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'giphousewebsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'giphousewebsite.context_processors.source_commit',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'giphousewebsite.context_processors.add_menu_objects_to_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'giphousewebsite.wsgi.application'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

AUTH_USER_MODEL = 'registrations.Employee'

# SASS processor variables
SASS_PROCESSOR_INCLUDE_DIRS = [
    os.path.join(BASE_DIR, 'giphousewebsite/static/scss'),
    os.path.join(BASE_DIR, 'projects/static/scss'),
    os.path.join(BASE_DIR, 'mailing_lists/static/scss')
]

SASS_PRECISION = 8
SASS_PROCESSOR_ENABLED = True
SASS_OUTPUT_STYLE = 'compressed'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

AUTHENTICATION_BACKENDS = [
    'github_oauth.backends.GithubOAuthBackend',
]

LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/'

DATE_FORMAT = '%d-%b-%y'

BOOTSTRAP5 = {
    'error_css_class': '',
    'success_css_class': '',
}

GSUITE_DOMAIN = "giphouse.nl"
GSUITE_SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.group",
    "https://www.googleapis.com/auth/apps.groups.settings",
]
