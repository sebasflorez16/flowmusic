#!/bin/sh
# Entrypoint del backend en producción (Railway).
#
# Railway ejecuta este script como comando de inicio del servicio web. Antes de
# arrancar el servidor ASGI, aplica las migraciones (esquema público + tenants)
# y recoge los estáticos. Luego arranca uvicorn en $PORT (Railway inyecta esta
# variable; por defecto 8000 para uso local con docker).
set -e

echo ">> Aplicando migraciones del esquema público..."
python manage.py migrate_schemas --shared --noinput

echo ">> Aplicando migraciones de los tenants..."
python manage.py migrate_schemas --noinput

echo ">> Recogiendo archivos estáticos..."
python manage.py collectstatic --noinput

echo ">> Arrancando servidor ASGI (uvicorn)..."
exec uvicorn config.asgi:application \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --proxy-headers \
    --forwarded-allow-ips "*"
