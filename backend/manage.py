#!/usr/bin/env python
"""Punto de entrada de Django.

Este script se ejecuta tanto en desarrollo (`python manage.py runserver`) como
en los comandos de administración de producción. Establece la variable de
entorno ``DJANGO_SETTINGS_MODULE`` por defecto y delega en Django.
"""

import os
import sys


def main() -> None:
    """Ejecuta las tareas administrativas de Django.

    Raises:
        ImportError: si Django no está instalado o no es importable.
    """
    # El módulo de settings por defecto es el de desarrollo. En producción se
    # sobrescribe con la variable de entorno DJANGO_SETTINGS_MODULE.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegúrate de que está instalado y "
            "que el virtualenv está activo."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
