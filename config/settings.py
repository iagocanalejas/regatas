import os
from pathlib import Path

from corsheaders.defaults import default_methods
from environs import Env

from config import version
from config.common import load_env
from config.patch import patch_unaccent

load_env()
patch_unaccent()
env = Env()

# WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", False)
VERSION = version.__version__

SERVICE_NAME = "rowing"
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = os.path.join(BASE_DIR, "static")
TEMPLATES_ROOT = os.path.join(STATIC_ROOT, "templates")
LOG_ROOT = os.path.join(BASE_DIR, "logs")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = "/media/"
STATIC_URL = "/static/"

INTERNAL_DATE_FORMAT = "%Y%m%d_%H%M%S"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY", "what-a-fake-secret-key-lol")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DATABASE_NAME"),
        "USER": env.str("DATABASE_USERNAME"),
        "PASSWORD": env.str("DATABASE_PASSWORD"),
        "HOST": env.str("DATABASE_HOST"),
        "PORT": "5432",
    },
    "OPTIONS": {"client_encoding": "UTF8", "timezone": "UTC"},
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "corsheaders",
    "stdimage",
    "prettyjson",
    "rest_framework",
    "drf_spectacular",
    # Self
    "djutils",
    "apps.entities",
    "apps.races",
    "apps.participants",
    "apps.actions",
]

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar", "django_extensions"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATES_ROOT],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

if DEBUG:
    MIDDLEWARE += [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

INTERNAL_IPS = [
    "127.0.0.1",
]
"""
** Cross-Origin-Resource-Sharing: CORS is a mechanism that allows restricted resources (e.g. fonts) on a web page to be
** requested from another domain outside the domain from which the first resource was served. A web page may freely
** embed cross-origin images, stylesheets, scripts, iframes, and videos. Certain 'cross-domain' requests, notably
** Ajax requests, are forbidden by default by the same-origin security policy.

# Control Cross-Origin-Resource-Sharing to allow access to our service from other sites, it's value depends on
# https://github.com/ottoyiu/django-cors-headers
"""
ALLOWED_HOSTS = ["*"] if DEBUG else [".tiempostraineras.com", "54.73.193.48", "localhost", "127.0.0.1"]

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_METHODS = default_methods
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "accept-language",
    "pragma",
    "cache-control",
    "accept-encoding",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CORS_ALLOWED_ORIGINS = (
    []
    if DEBUG
    else [
        "https://tiempostraineras.com",
        "https://*.tiempostraineras.com",
        "https://54.73.193.48",
        "http://localhost",
        "http://127.0.0.1",
    ]
)
"""
** Cross-Site-Request-Forgery: A CSRF hole is when a malicious site can cause a visitor's browser to make a
** request to your server that causes a change on the server. The server thinks that because the request comes with the
** user's cookies, the user wanted to submit that form.

# To use CORS and CSRF at the same time we need to include in CSRF_TRUSTED_ORIGINS all the valid domains that can
# send requests to our service.
# https://docs.djangoproject.com/en/dev/ref/csrf/
"""
CSRF_TRUSTED_ORIGINS = (
    []
    if DEBUG
    else [
        "https://tiempostraineras.com",
        "https://*.tiempostraineras.com",
        "https://54.73.193.48",
        "http://localhost",
        "http://127.0.0.1",
    ]
)

if DEBUG:
    ADMIN_HONEYPOT_EMAIL_ADMINS = False
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = os.path.join(LOG_ROOT, "emails")
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
else:
    # SSL
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    """
    ** HTTP-Strict-Transport-Security: Web security policy mechanism which helps to protect websites against protocol
    ** downgrade attacks and cookie hijacking. It allows web servers to declare that web browsers (or other complying
    ** user agents) should only interact with it using secure HTTPS connections, and never via the insecure HTTP
    ** protocol.

    # Force HSTS header in all the requests
    # https://docs.djangoproject.com/en/2.0/ref/middleware/#http-strict-transport-security
    """
    SECURE_HSTS_SECONDS = 31536000  # One year
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", "")

MAIN_ADMIN = ("AndIag", "andiag.dev@gmail.com")
ADMINS = [("AndIag", "andiag.dev@gmail.com")]

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

SWAGGER_SETTINGS = {
    "API_VERSION": VERSION,
    "TITLE": SERVICE_NAME,
    "DESCRIPTION": "Servicio de regatas",
    "VERSION": VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {process:d} {thread:d} {module} {filename} {funcName} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_all": {
            "level": "DEBUG" if DEBUG else os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "filename": os.path.join(LOG_ROOT, "django_debug.log"),
            "formatter": "verbose",
        },
        "file": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "ERROR"),
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "filename": os.path.join(LOG_ROOT, "django_errors.log"),
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "simple",
            "include_html": True,
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file", "file_all", "mail_admins"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        # Handling of requests
        "django.request": {
            "handlers": ["console", "file", "file_all", "mail_admins"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        # MRendering of templates
        "django.template": {
            "handlers": ["console", "file", "file_all", "mail_admins"],
            "level": "INFO",
            "propagate": True,
        },
        # Interaction of code with the database
        "django.db.backends": {
            "handlers": ["file_all"],
            "level": "DEBUG",
            "propagate": False,
        },
        # SuspiciousOperation error as DisallowedHost call
        "django.security.DisallowedHost": {
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
