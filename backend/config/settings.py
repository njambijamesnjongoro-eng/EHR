import os
from datetime import timedelta
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="insecure-change-in-production")

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,.onrender.com,.vercel.app", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Local
    "core",
    "api.authentication",
    "api.patients",
    "api.audit",
    "api.clinical",
    "api.labs",
    "api.timeline",
    "api.admissions",
    "api.billing",
    "api.imaging",
    "api.notifications",
    "api.reports",
    "api.hospitals",
    "api.referrals",
    "api.sync",
    "api.analytics",
    "api.insurance",
    "api.telemedicine",
    "api.security",
    "api.monitoring",
    "api.compliance",
    "api.interop",
    "api.ai_assist",
    "api.public_health",
    "api.wearable",
    "api.biometric",
    "api.smart_hospital",
    "api.citizen_portal",
    # Phase 7
    "api.ai_orchestrator",
    "api.epidemic",
    "api.precision_health",
    "api.health_data_fabric",
    # Phase 8
    "api.digital_twin",
    "api.emergency_response",
    "api.population_health",
    "api.ai_orchestration",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "middleware.audit_log.AuditLogMiddleware",
    "middleware.rate_limit.EnterpriseRateLimitMiddleware",
    "middleware.zero_trust.ZeroTrustMiddleware",
    "middleware.zero_trust.SecurityHeadersMiddleware",
    "middleware.hospital_isolation.HospitalIsolationMiddleware",
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

DATABASES = {
    "default": (
        dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    )
}

AUTH_USER_MODEL = "core.User"

AUTH_PASSWORD_VALIDATORS = [
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

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── CORS ───
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:3001,https://*.vercel.app",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ─── REST FRAMEWORK ───
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("LOGIN_RATE_LIMIT", default="10/minute"),
        "user": config("API_RATE_LIMIT", default="100/minute"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "COERCE_DECIMAL_TO_STRING": True,
}

# ─── SIMPLE JWT ───
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=1, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
}

# ─── SECURITY ───
SECURE_SSL_REDIRECT = config("HTTPS_ONLY", default=True, cast=bool)
SESSION_COOKIE_SECURE = config("HTTPS_ONLY", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("HTTPS_ONLY", default=True, cast=bool)
SECURE_HSTS_SECONDS = 31536000 if config("HTTPS_ONLY", default=True, cast=bool) else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# ─── AUDIT ───
AUDIT_LOG_ENABLED = config("AUDIT_LOG_ENABLED", default=True, cast=bool)
AUDIT_LOG_RETENTION_DAYS = config("AUDIT_LOG_RETENTION_DAYS", default=365, cast=int)

# ─── DRF SPECTACULAR ───
SPECTACULAR_SETTINGS = {
    "TITLE": "EHR Hospital API",
    "DESCRIPTION": "Hospital Electronic Health Record System API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ─── CELERY ───
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ─── REDIS ───
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/2")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ehr-cache",
        "KEY_PREFIX": "ehr",
    }
}

# Use Redis in production (when REDIS_URL is set)
import os
if os.environ.get("USE_REDIS"):
    CACHES["default"] = {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "ehr",
    }

# ─── STORAGE ───
STORAGE_BACKEND = config("STORAGE_BACKEND", default="local")
if STORAGE_BACKEND == "s3":
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="ehr-media")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = True
    AWS_S3_VERIFY = True

# ─── SENTRY ───
SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=False,
        traces_sample_rate=0.1,
        environment=config("ENVIRONMENT", default="production"),
    )

# ─── WHITENOISE ───
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ─── ENTERPRISE CONFIG ───
ENABLE_HOSPITAL_ISOLATION = config("ENABLE_HOSPITAL_ISOLATION", default=True, cast=bool)
SYNC_BATCH_SIZE = config("SYNC_BATCH_SIZE", default=50, cast=int)
MAX_SYNC_RETRIES = config("MAX_SYNC_RETRIES", default=3, cast=int)
