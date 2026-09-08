"""Aplicación Celery para tareas asíncronas.

Se usa para: webhooks de Wompi, cobros recurrentes mensuales, envío de emails y
cualquier actualización pesada que no deba bloquear la petición HTTP.
"""

import os

from celery import Celery

# Celery necesita saber qué settings usar para cargar las configuraciones de
# broker y backend (CELERY_BROKER_URL, CELERY_RESULT_BACKEND, etc.).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("musicflow")

# Carga la configuración de Celery desde los settings de Django usando el
# prefijo "CELERY_". Esto evita duplicar la configuración.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descubre automáticamente las tareas definidas en tasks.py de cada app.
app.autodiscover_tasks()
