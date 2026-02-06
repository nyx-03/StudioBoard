from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core security / runtime
# -----------------------------------------------------------------------------
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

def _split_env_list(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]

# Hosts
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    # LAN (dev)
    "192.168.1.140",
    "192.168.1.82",
]
ALLOWED_HOSTS += _split_env_list("DJANGO_ALLOWED_HOSTS")

# When behind a reverse proxy (Nginx/Caddy) in HTTPS, set DJANGO_BEHIND_PROXY=1
BEHIND_PROXY = os.environ.get("DJANGO_BEHIND_PROXY", "0") == "1"
if BEHIND_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -----------------------------------------------------------------------------
# Application definition
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "board",
]

MIDDLEWARE = [
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
        "DIRS": [],
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

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# API-first setup (Next.js frontend)
# -----------------------------------------------------------------------------
# Cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # doit rester lisible côté JS pour le fetch Next.js

# En LAN (IP + port), Lax fonctionne et évite les soucis de "SameSite=None + Secure"
SESSION_COOKIE_SAMESITE = os.environ.get("DJANGO_SESSION_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.environ.get("DJANGO_CSRF_SAMESITE", "Lax")

# En prod HTTPS, on passera automatiquement en Secure via DEBUG=False (ou env)
_force_secure = os.environ.get("DJANGO_FORCE_SECURE_COOKIES", "")
if _force_secure:
    SECURE_COOKIES = _force_secure == "1"
else:
    SECURE_COOKIES = not DEBUG

CSRF_COOKIE_SECURE = SECURE_COOKIES
SESSION_COOKIE_SECURE = SECURE_COOKIES

# CSRF trusted origins (Next.js dev + LAN). Ajout possible via env.
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.140:3000",
    "http://192.168.1.82:3000",
    "http://192.168.1.140",
    "http://192.168.1.82",
]
CSRF_TRUSTED_ORIGINS += _split_env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# -----------------------------------------------------------------------------
# Static files (Django admin en a besoin, même en API-only)
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("DJANGO_STATIC_ROOT", str(BASE_DIR / "staticfiles"))

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL = "DEBUG" if DEBUG else os.environ.get("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "formatters": {
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
        "formatter": "simple",
    },
    "loggers": {
        # pratique pour isoler les logs API
        "board": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "board.api": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# -----------------------------------------------------------------------------
# Default primary key field type
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = False