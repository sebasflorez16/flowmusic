# Dockerfile de producción (Railway).
#
# Railway construye la imagen y ejecuta `entrypoint.sh`, que aplica migraciones,
# recoge estáticos y arranca uvicorn en $PORT. La imagen usa solo dependencias
# de producción y sirve HTTP + WebSockets (ASGI) en un único proceso.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# Dependencias del sistema para compilar psycopg y otras extensiones.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Instala primero las dependencias para aprovechar la caché de capas de Docker.
COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/production.txt

# Copia el código y el entrypoint.
COPY . .

# Railway usa un usuario no-root por defecto; damos permisos sobre /app.
RUN useradd -m musicflow && chown -R musicflow:musicflow /app
USER musicflow

EXPOSE 8000

CMD ["./entrypoint.sh"]
