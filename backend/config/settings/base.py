"""Configuración base de Django compartida por desarrollo y producción.

Este módulo centraliza la configuración multi-tenant con django-tenants, la API
REST (DRF + JWT), el tiempo real (Channels), las tareas asíncronas (Celery), el
CORS para los frontends separados y la autenticación con allauth.

Arquitectura multi-tenant:
    Cada bar es un ``Tenant`` con su propio esquema de PostgreSQL. Las apps
    compartidas (core, users, payments, admin) viven en el esquema ``public``;
    las apps de negocio (tables, music, marketing, analytics) viven en el
    esquema propio de cada tenant.
"""

from datetime import timedelta
from pathlib import Path

import environ

# ---------------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------------
# BASE_DIR apunta a ``backend/`` (el directorio que contiene manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Inicializa django-environ para leer variables desde el entorno y un archivo .env.
env = environ.Env(
    DEBUG=(bool, False),
)

# Carga las variables desde un archivo .env si existe. No falla si está ausente
# (en producción las variables vienen del entorno del contenedor).
if (BASE_DIR / ".env").exists():
    env.read_env(str(BASE_DIR / ".env"))

# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-only-key")
DEBUG = env("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
# Las apps están agrupadas bajo ``apps/`` y ``apps/tenants/``. Django resuelve
# su ``app_label`` a partir del último componente del dotted path.
INSTALLED_APPS = [
    # django-tenants debe ir antes que django.contrib.admin para que el admin
    # funcione correctamente con los esquemas por tenant.
    "django_tenants",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "corsheaders",
    "channels",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Apps propias (compartidas)
    "apps.core",
    "apps.users",
    "apps.payments",
    # Apps propias (por tenant)
    "apps.tenants.tables",
    "apps.tenants.music",
    "apps.tenants.marketing",
    "apps.tenants.analytics",
]

# Apps que viven en el esquema público (compartido entre todos los tenants).
# IMPORTANTE: deben usar la ruta completa (``appconfig.name``), no la etiqueta
# corta, porque el router de django-tenants compara contra ``appconfig.name``.
SHARED_APPS = [
    "django_tenants",
    "apps.core",
    "apps.users",
    "apps.payments",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

# Apps que viven en el esquema individual de cada tenant.
# ``contenttypes`` se repite aquí porque cada esquema necesita su propia tabla
# de content types para las relaciones genéricas (si se usan).
TENANT_APPS = [
    "django.contrib.contenttypes",
    "apps.tenants.tables",
    "apps.tenants.music",
    "apps.tenants.marketing",
    "apps.tenants.analytics",
]

# Modelo que representa cada tenant (bar) y su modelo de dominio (subdominio).
TENANT_MODEL = "core.Tenant"
TENANT_DOMAIN_MODEL = "core.Domain"

# Enruta las migraciones al esquema correcto (público vs. por tenant).
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# Si un hostname no coincide con ningún dominio de tenant, se sirve el esquema
# público (donde viven auth, superadmin y la landing). En desarrollo, `localhost`
# cae aquí; en producción, el dominio principal (musicflow.com) también.
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    # Resuelve el tenant actual a partir del subdominio de la petición.
    "django_tenants.middleware.main.TenantMainMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

# ASGI (requerido por Channels para WebSockets). Daphne/uvicorn lo sirven.
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------
# La URL viene de DATABASE_URL (formato postgres://usuario:pass@host:puerto/db).
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://musicflow:musicflow@localhost:5432/musicflow"),
}
DATABASES["default"]["ENGINE"] = "django_tenants.postgresql_backend"

# ---------------------------------------------------------------------------
# Validación de contraseñas
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internacionalización
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Archivos estáticos y media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework + JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.users.authentication.TenantJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
}

# Configuración de tokens JWT (acceso de corta duración + refresh).
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=30)),
}

# ---------------------------------------------------------------------------
# CORS (frontends separados)
# ---------------------------------------------------------------------------
# En producción CORS_ALLOWED_ORIGINS se define explícitamente. En desarrollo se
# permite todo (ver development.py).
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Autenticación (allauth)
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_VERIFICATION = "optional"

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ---------------------------------------------------------------------------
# Channels (WebSockets)
# ---------------------------------------------------------------------------
# Redis es obligatorio (no usar in-memory) para que las notificaciones lleguen
# a todos los clientes aunque Django corra en múltiples instancias.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [CELERY_BROKER_URL],
        },
    },
}

# ---------------------------------------------------------------------------
# URLs públicas de los frontends
# ---------------------------------------------------------------------------
# Base de la vista del cliente (PWA móvil) para construir los QR de las mesas.
CLIENT_BASE_URL = env("CLIENT_BASE_URL", default="http://localhost:5174")

# ---------------------------------------------------------------------------
# Wompi (pagos)
# ---------------------------------------------------------------------------
WOMPI_PUBLIC_KEY = env("WOMPI_PUBLIC_KEY", default="")
WOMPI_PRIVATE_KEY = env("WOMPI_PRIVATE_KEY", default="")
# Clave para verificar la firma de los webhooks (checksum SHA256).
WOMPI_EVENTS_SECRET_KEY = env("WOMPI_EVENTS_SECRET_KEY", default="")
WOMPI_INTEGRITY_KEY = env("WOMPI_INTEGRITY_KEY", default="")
# Entorno de Wompi: "sandbox" (pruebas) o "production".
WOMPI_ENV = env("WOMPI_ENV", default="sandbox")
