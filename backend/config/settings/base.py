import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from decouple import Csv, config


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-your-secret-key")


def _env_bool(name, default=False):
    value = str(config(name, default=str(default))).strip().lower()
    if value in {"1", "true", "yes", "on", "debug", "development", "local"}:
        return True
    if value in {"0", "false", "no", "off", "release", "production", "prod"}:
        return False
    return bool(default)


DEBUG = _env_bool("DEBUG", True)


def _get_allowed_domains():
    """Read allowed email domains from env; add new domains without code changes."""
    env_domains = os.getenv(
        "ALLOWED_EMAIL_DOMAINS",
        "gmail.com,yahoo.com,outlook.com,hotmail.com",
    )
    return [domain.strip().lower() for domain in env_domains.split(",") if domain.strip()]


ALLOWED_EMAIL_DOMAINS = _get_allowed_domains()

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,zyrunbackend.onrender.com",
    cast=Csv(),
)
RENDER_EXTERNAL_HOSTNAME = config("RENDER_EXTERNAL_HOSTNAME", default="")
DEPLOYMENT_HOSTS = ["zyrunbackend.onrender.com"]

for host in [RENDER_EXTERNAL_HOSTNAME, *DEPLOYMENT_HOSTS]:
    if host and host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "backend.users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = config("DATABASE_URL", default=None)
DATABASE_NAME = config("DATABASE_NAME", default=None)
DATABASE_USER = config("DATABASE_USER", default=None)
DATABASE_PASSWORD = config("DATABASE_PASSWORD", default="")
DATABASE_HOST = config("DATABASE_HOST", default="127.0.0.1")
DATABASE_PORT = config("DATABASE_PORT", default="5432")

if DATABASE_URL:
    parsed_url = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_url.path.lstrip("/"),
            "USER": parsed_url.username or DATABASE_USER,
            "PASSWORD": parsed_url.password or DATABASE_PASSWORD,
            "HOST": parsed_url.hostname or DATABASE_HOST,
            "PORT": parsed_url.port or DATABASE_PORT,
        }
    }
elif DATABASE_NAME and DATABASE_USER:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DATABASE_NAME,
            "USER": DATABASE_USER,
            "PASSWORD": DATABASE_PASSWORD,
            "HOST": DATABASE_HOST,
            "PORT": DATABASE_PORT,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000,https://zyrunfrontend.onrender.com",
    cast=Csv(),
)
DEPLOYMENT_ORIGINS = ["https://zyrunfrontend.onrender.com"]

for origin in DEPLOYMENT_ORIGINS:
    if origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000,https://zyrunfrontend.onrender.com",
    cast=Csv(),
)

for origin in DEPLOYMENT_ORIGINS:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=config("JWT_ACCESS_MINUTES", default=15, cast=int)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=config("JWT_REFRESH_DAYS", default=7, cast=int)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

GOOGLE_OAUTH_CLIENT_ID = config("GOOGLE_OAUTH_ID", default="")

USER_PHONE_MAX_LENGTH = config("USER_PHONE_MAX_LENGTH", default=15, cast=int)
USER_NAME_MAX_LENGTH = config("USER_NAME_MAX_LENGTH", default=150, cast=int)
USER_PASSWORD_HASH_MAX_LENGTH = config("USER_PASSWORD_HASH_MAX_LENGTH", default=128, cast=int)
USER_PROFILE_PICTURE_UPLOAD_TO = config("USER_PROFILE_PICTURE_UPLOAD_TO", default="profile_pictures/")
USER_DEFAULT_ORDERING = ["-created_at"]
USER_VERBOSE_NAME_PLURAL = "Users"

OTP_CODE_LENGTH = config("OTP_CODE_LENGTH", default=6, cast=int)
OTP_PURPOSE_MAX_LENGTH = config("OTP_PURPOSE_MAX_LENGTH", default=20, cast=int)

SOCIAL_PROVIDER_GOOGLE = config("SOCIAL_PROVIDER_GOOGLE", default="google")
SOCIAL_PROVIDER_MAX_LENGTH = config("SOCIAL_PROVIDER_MAX_LENGTH", default=20, cast=int)
SOCIAL_PROVIDER_ID_MAX_LENGTH = config("SOCIAL_PROVIDER_ID_MAX_LENGTH", default=255, cast=int)
SOCIAL_PROVIDER_CHOICES = [
    (SOCIAL_PROVIDER_GOOGLE, "Google"),
]

EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=1025, cast=int)
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", default=10, cast=int)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@example.com")

AUTH_USER_MODEL = "users.CustomUser"
