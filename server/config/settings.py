"""Django settings for config project."""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and value in (None, ''):
        raise ImproperlyConfigured(f'{name} is required')
    return value


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY = env('DJANGO_SECRET_KEY', required=True)
DEBUG = env_bool('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = [
    host.strip()
    for host in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'users',
    'user_descriptions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


if env_bool('DJANGO_TEST_USE_SQLITE', default=False):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB', required=True),
            'USER': env('POSTGRES_USER', required=True),
            'PASSWORD': env('POSTGRES_PASSWORD', required=True),
            'HOST': env('POSTGRES_HOST', 'localhost'),
            'PORT': env('POSTGRES_PORT', '5432'),
        }
    }


AUTH_USER_MODEL = 'users.User'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

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


GITHUB_CLIENT_ID = env('GITHUB_CLIENT_ID', required=True)
GITHUB_CLIENT_SECRET = env('GITHUB_CLIENT_SECRET', required=True)
GITHUB_CALLBACK_URL = env('GITHUB_CALLBACK_URL', 'http://localhost:8000/auth/github/callback/')
GITHUB_PRIVATE_KEY_PATH = env('GITHUB_PRIVATE_KEY_PATH')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ('v1',),
    'VERSION_PARAM': 'version',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(env('JWT_ACCESS_TOKEN_MINUTES', '60'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(env('JWT_REFRESH_TOKEN_DAYS', '7'))),
}


LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
