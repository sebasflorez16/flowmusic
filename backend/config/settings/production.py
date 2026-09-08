"""Configuración del entorno de producción.

Deshabilita el debug, restringe hosts y orígenes CORS, y configura el
almacenamiento de archivos en S3/R2 y el envío de errores a Sentry.

Requerimientos de variables de entorno (ver .env.example):
    DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, DATABASE_URL, CORS_ALLOWED_ORIGINS,
    AWS_* (S3/R2), SENTRY_DSN (opcional), REDIS_URL, WOMPI_*.
"""

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401,F403

# ---------------------------------------------------------------------------
# Debug y hosts
# ---------------------------------------------------------------------------
DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # noqa: F405

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Orígenes permitidos explícitos (ej. https://app.musicflow.com). Los subdominios
# dinámicos de tenants se cubren con wildcard solo si el proveedor lo permite;
# en su defecto se añaden explícitamente.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")  # noqa: F405

# ---------------------------------------------------------------------------
# Almacenamiento en S3 / Cloudflare R2
# ---------------------------------------------------------------------------
# Si no hay credenciales S3 se cae al almacenamiento local (útil para deploys
# mínimos o staging sin bucket configurado).
if env("AWS_S3_BUCKET_NAME", default=""):  # noqa: F405
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID")  # noqa: F405
    AWS_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY")  # noqa: F405
    AWS_STORAGE_BUCKET_NAME = env("AWS_S3_BUCKET_NAME")  # noqa: F405
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)  # noqa: F405
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)  # noqa: F405
    AWS_QUERYSTRING_AUTH = False  # URLs públicas (para logos y QR)

# ---------------------------------------------------------------------------
# Caché con Redis (producción)
# ---------------------------------------------------------------------------
# Se usa Redis para cachear búsquedas de YouTube y metadatos, compartiendo la
# instancia con Celery/Channels.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),  # noqa: F405
    }
}

# ---------------------------------------------------------------------------
# Sentry
# ---------------------------------------------------------------------------
if env("SENTRY_DSN", default=""):  # noqa: F405
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),  # noqa: F405
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),  # noqa: F405
        send_default_pii=False,
    )
