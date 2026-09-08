"""App ``core``: modelos base del multi-tenant (Tenant y Domain).

Estos modelos viven en el esquema público (``SHARED_APPS``) y son la puerta de
entrada del sistema: cada bar es un ``Tenant`` con su propio esquema de base de
datos, y cada ``Domain`` mapea un subdominio a un tenant.
"""
