# Dockerfile de producción: instala solo dependencias de producción y expone el
# servidor ASGI (uvicorn + daphne) para soportar WebSockets.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .

# Recoge archivos estáticos en build time.
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
