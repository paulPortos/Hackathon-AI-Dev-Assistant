"""Django settings for config project."""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


# Environment helpers
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


def env_first(names, default=None, required=False):
    for name in names:
        value = os.getenv(name)
        if value not in (None, ''):
            return value
    if required and default in (None, ''):
        raise ImproperlyConfigured(f'One of {", ".join(names)} is required')
    return default


# Environment variables
# Core
SECRET_KEY = env('DJANGO_SECRET_KEY', required=True)
DEBUG = env_bool('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = [
    host.strip()
    for host in env('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]
TIME_ZONE = env('DJANGO_TIME_ZONE', 'UTC')
FRONTEND_URL = env('FRONTEND_URL', 'http://localhost:5173')
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in env('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    if origin.strip()
]

# GitHub
GITHUB_CLIENT_ID = env('GITHUB_CLIENT_ID', required=True)
GITHUB_CLIENT_SECRET = env('GITHUB_CLIENT_SECRET', required=True)
GITHUB_CALLBACK_URL = env('GITHUB_CALLBACK_URL', 'http://localhost:8000/auth/github/callback/')
GITHUB_PRIVATE_KEY_PATH = env('GITHUB_PRIVATE_KEY_PATH')
GITHUB_TOKEN_ENCRYPTION_KEY = env('GITHUB_TOKEN_ENCRYPTION_KEY', required=True)

# Email
TWILLIO_SENDGRID_API_KEY = env('TWILLIO_SENDGRID_API_KEY')
TWILLIO_SENDGRID_FROM_EMAIL = env('TWILLIO_SENDGRID_FROM_EMAIL')
TWILLIO_SENDGRID_FROM_NAME = env('TWILLIO_SENDGRID_FROM_NAME', 'AI Dev Assistant')

# LLM provider
OLLAMA_HOST = env('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_API_KEY = env('OLLAMA_API_KEY', '')
OLLAMA_AGENT_MAX_ATTEMPTS = int(env('OLLAMA_AGENT_MAX_ATTEMPTS', '3'))
OLLAMA_AGENT_RETRY_DELAY_SECONDS = float(env('OLLAMA_AGENT_RETRY_DELAY_SECONDS', '0.75'))

# Agent settings
SR_DEV_AGENT_MODEL = env('SR_DEV_AGENT_MODEL', 'gpt-oss:20b')
SR_DEV_TOOL_CALL_LIMIT = int(env('SR_DEV_TOOL_CALL_LIMIT', '8'))
PROJECT_MANAGER_AGENT_MODEL = env('PROJECT_MANAGER_AGENT_MODEL', 'gpt-oss:20b')
PROJECT_MANAGER_CONFIDENCE_THRESHOLD = int(env('PROJECT_MANAGER_CONFIDENCE_THRESHOLD', '75'))

# Security audit
SECURITY_AUDIT_BODY_MAX_BYTES = int(env('SECURITY_AUDIT_BODY_MAX_BYTES', '8192'))
SECURITY_AUDIT_MAX_SUSPICIOUS_SIGNALS = int(env('SECURITY_AUDIT_MAX_SUSPICIOUS_SIGNALS', '20'))
SECURITY_AUDIT_LOG_LEVEL = env('SECURITY_AUDIT_LOG_LEVEL', 'INFO').upper()

# JWT lifetimes
JWT_ACCESS_TOKEN_MINUTES = int(env('JWT_ACCESS_TOKEN_MINUTES', '60'))
JWT_REFRESH_TOKEN_DAYS = int(env('JWT_REFRESH_TOKEN_DAYS', '7'))
DATABASE_CONN_MAX_AGE = int(env('DATABASE_CONN_MAX_AGE', '600'))
DATABASE_SSL_MODE = env('DATABASE_SSL_MODE', '')
REDIS_URL = env('REDIS_URL')


# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'multi_agent',
    'projects',
    'users',
    'user_descriptions',
    'scrum',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'config.middleware.request_id_middleware.RequestIdMiddleware',
    'config.middleware.security_audit_middleware.SecurityAuditMiddleware',
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
ASGI_APPLICATION = 'config.asgi.application'


CORS_ALLOW_CREDENTIALS = True

# Database
DATABASE_URL = env('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url

    database_config = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=DATABASE_CONN_MAX_AGE,
        ssl_require=env_bool('DATABASE_SSL_REQUIRE', default=False),
    )
    if DATABASE_SSL_MODE:
        database_config.setdefault('OPTIONS', {})['sslmode'] = DATABASE_SSL_MODE
    DATABASES = {'default': database_config}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env_first(('DB_NAME', 'POSTGRES_DB'), required=True),
            'USER': env_first(('DB_USER', 'POSTGRES_USER'), required=True),
            'PASSWORD': env_first(('DB_PASSWORD', 'POSTGRES_PASSWORD'), required=True),
            'HOST': env_first(('DB_HOST', 'POSTGRES_HOST'), 'localhost'),
            'PORT': env_first(('DB_PORT', 'POSTGRES_PORT'), '5432'),
        }
    }

    if DATABASE_SSL_MODE:
        DATABASES['default']['OPTIONS'] = {'sslmode': DATABASE_SSL_MODE}


# Authentication
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

# REST framework
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
    'EXCEPTION_HANDLER': 'config.exception_handlers.friendly_exception_handler.friendly_exception_handler',
}

# Channels
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=JWT_REFRESH_TOKEN_DAYS),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'config.logging.structured_json_formatter.StructuredJsonFormatter',
        },
    },
    'handlers': {
        'console_json': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'api.errors': {
            'handlers': ['console_json'],
            'level': 'ERROR',
            'propagate': False,
        },
        'security.audit': {
            'handlers': ['console_json'],
            'level': SECURITY_AUDIT_LOG_LEVEL,
            'propagate': False,
        },
        'security.suspicious_input': {
            'handlers': ['console_json'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Internationalization
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
