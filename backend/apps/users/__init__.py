"""App ``users``: autenticación, perfiles y roles (esquema público).

La autenticación usa el modelo ``User`` de Django (vía allauth) en el esquema
público. Aquí se define el perfil que vincula a cada usuario con su tenant y su
rol (dueño o superadministrador del sistema).
"""
