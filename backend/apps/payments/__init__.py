"""App ``payments``: integración con Wompi (esquema público).

Gestiona la tokenización de tarjetas, los cobros/suscripciones y la recepción
de webhooks. Nunca se almacenan datos de tarjeta: Wompi tokeniza la tarjeta y
solo guardamos el token.
"""
