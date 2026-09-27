"""Notificaciones por WhatsApp vía Twilio.

Centraliza el envío de mensajes de WhatsApp (cobros, bares nuevos, etc.) para
mantener aislada la integración. Si las credenciales de Twilio no están
configuradas, los envíos se omiten silenciosamente (no rompen el flujo).
"""

from __future__ import annotations

import requests
from django.conf import settings


def _send_whatsapp(to: str, body: str) -> bool:
    """Envía un mensaje de WhatsApp a ``to`` (E.164 sin '+') y devuelve éxito."""
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_FROM_WHATSAPP

    if not (sid and token and from_number):
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    try:
        response = requests.post(
            url,
            data={
                "From": from_number,
                "To": f"whatsapp:+{to}",
                "Body": body,
            },
            auth=(sid, token),
            timeout=15,
        )
        return response.status_code < 400
    except requests.RequestException:
        return False


def notify_new_bar(tenant) -> None:
    """Avisa a los dueños del negocio que se registró un bar nuevo."""
    body = (
        "🎵 MusicFlow — Nuevo bar registrado\n"
        f"Nombre: {tenant.name}\n"
        f"Dueño: {tenant.owner_email}\n"
        f"Plan: {tenant.get_plan_display()}"
    )
    for to in settings.NEW_BAR_ALERT_RECIPIENTS:
        _send_whatsapp(to, body)


def notify_billing_due(tenants) -> None:
    """Avisa que hay bares a punto de facturar (a N días)."""
    for tenant in tenants:
        body = (
            "⚠️ MusicFlow — Facturación próxima\n"
            f"Bar: {tenant.name}\n"
            f"Plan: {tenant.get_plan_display()}\n"
            f"Vence el: {tenant.next_billing_date}"
        )
        for to in settings.BILLING_ALERT_RECIPIENTS:
            _send_whatsapp(to, body)
