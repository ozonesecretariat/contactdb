"""
Django settings for contactdb project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""
import os
import socket
from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

if os.path.exists(str(BASE_DIR / ".env")):
    env.read_env(str(BASE_DIR / ".env"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

HAS_HTTPS = env.bool("HAS_HTTPS", default=False)
PROTOCOL = "https://" if HAS_HTTPS else "http://"

BACKEND_HOST = env.list("BACKEND_HOST")

REDIS_HOST = env.str("REDIS_HOST")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
REDIS_CACHE_DB = 0
REDIS_TASK_DB = 1

# https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-DEBUG
DEBUG = env.bool("DEBUG", default=False)

# https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY
SECRET_KEY = env.str("SECRET_KEY")

# https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-CSRF_COOKIE_SECURE
CSRF_COOKIE_SECURE = HAS_HTTPS

# https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECURE_SSL_REDIRECT
SECURE_SSL_REDIRECT = HAS_HTTPS

# https://docs.djangoproject.com/en/4.1/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SESSION_COOKIE_SECURE
SESSION_COOKIE_SECURE = HAS_HTTPS

# https://docs.djangoproject.com/en/4.1/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [_host.rsplit(":", 1)[0] for _host in BACKEND_HOST]


# Application definition

INSTALLED_APPS = [
    "django_admin_env_notice",
    # "django.contrib.admin",
    "contactdb.site.ContactDBAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_htmx",
    "django_filters",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "constance",
    "constance.backends.database",
    "two_factor",
    "django_rq",
    "django_task",
    "django_tables2",
    # This app
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "contactdb.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django_admin_env_notice.context_processors.from_settings",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "contactdb.wsgi.application"

# https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-AUTH_USER_MODEL
AUTH_USER_MODEL = "accounts.User"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

POSTGRES_HOST = env.str("POSTGRES_HOST")
POSTGRES_PORT = env.int("POSTGRES_PORT", default=5432)
POSTGRES_DB = env.str("POSTGRES_DB")
POSTGRES_USER = env.str("POSTGRES_USER")
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "CONN_MAX_AGE": None,
        "CONN_HEALTH_CHECKS": True,
    },
}

# Caching
# https://docs.djangoproject.com/en/4.2/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CACHE_DB}",
        "OPTIONS": {
            "SOCKET_TIMEOUT": 5,
            "SOCKET_CONNECT_TIMEOUT": 5,
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "contactdb",
    }
}

# Task Queue (RQ)

RQ_QUEUES = {
    "default": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": REDIS_TASK_DB,
    }
}

# Hide RQ admin, since we are using Django Task models instead
RQ_SHOW_ADMIN_LINK = False


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

USE_L10N = False

# See https://docs.djangoproject.com/en/4.1/ref/templates/builtins/#date
DATETIME_FORMAT = "d N Y, H:i O"
SHORT_DATETIME_FORMAT = "d-m-Y, H:i"
DATE_FORMAT = "d N Y"
SHORT_DATE_FORMAT = "d-m-Y"
TIME_FORMAT = "H:i:s"

# https://docs.djangoproject.com/en/4.0/ref/settings/#login-url
# LOGIN_URL = "/admin/login"
# LOGIN_URL = "two_factor:login"
LOGIN_URL = "/account/login"
LOGOUT_REDIRECT_URL = "/"

FS_DIR = BASE_DIR / ".fs"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = FS_DIR / "static"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files / user uploads
# https://docs.djangoproject.com/en/4.1/howto/static-files/#serving-files-uploaded-by-a-user-during-development
MEDIA_URL = "/media/"
MEDIA_ROOT = FS_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# EMAIL
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-backend
EMAIL_BACKEND = env.str(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host
EMAIL_HOST = env.str("EMAIL_HOST", default="localhost")
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-port
EMAIL_PORT = env.str("EMAIL_PORT", default="25")
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host-user
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host-password
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-email-use-tls
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-timeout
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=30)
# https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-DEFAULT_FROM_EMAIL
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="") or (
    "noreply@" + socket.gethostname()
)

# https://pypi.org/project/django-admin-env-notice/
ENVIRONMENT_NAME = env.str("ENVIRONMENT_NAME", default="")
ENVIRONMENT_COLOR = env.str("ENVIRONMENT_COLOR", default="")
ENVIRONMENT_TEXT_COLOR = env.str("ENVIRONMENT_TEXT_COLOR", default="#ffffff")

# https://django-constance.readthedocs.io/en/latest/
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "REQUIRE_2FA": (
        False,
        "Require two-factor authentication. Users will not be able to use "
        "the application until they complete the 2FA setup.",
    ),
}
CONSTANCE_CONFIG_FIELDSETS = (
    (
        "Security",
        {
            "collapse": False,
            "fields": ("REQUIRE_2FA",),
        },
    ),
)

# Sentry
SENTRY_DSN = env.str("SENTRY_DSN", default="")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT_NAME,
        integrations=[
            DjangoIntegration(),
        ],
    )
