"""Cliente del API de Wompi.

Encapsula las llamadas HTTP a Wompi (tokenización, cobros, suscripciones) y la
verificación de la firma de los webhooks. Centralizar aquí el cliente permite
aislar al resto del sistema de los cambios de la API de Wompi.

Referencia: https://docs.wompi.co
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any, Optional

import requests
from django.conf import settings


class WompiError(Exception):
    """Error base de la integración con Wompi."""


class WompiClient:
    """Cliente HTTP para interactuar con la API de Wompi.

    Elige el entorno (sandbox o production) según ``settings.WOMPI_ENV`` y usa
    la clave privada para las operaciones que crean recursos y la clave de
    eventos para verificar webhooks.
    """

    SANDBOX_URL = "https://sandbox.wompi.co/v1"
    PRODUCTION_URL = "https://production.wompi.co/v1"

    def __init__(self) -> None:
        """Configura la URL base y las credenciales desde los settings."""
        self.base_url = (
            self.SANDBOX_URL if settings.WOMPI_ENV == "sandbox" else self.PRODUCTION_URL
        )
        self.private_key = settings.WOMPI_PRIVATE_KEY
        self.events_secret_key = settings.WOMPI_EVENTS_SECRET_KEY

    @property
    def _headers(self) -> dict[str, str]:
        """Cabeceras de autenticación para las llamadas privadas."""
        return {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Realiza una petición POST y devuelve el JSON de respuesta.

        Args:
            path: ruta relativa del endpoint (sin la URL base).
            payload: cuerpo JSON de la petición.

        Returns:
            Diccionario con la respuesta de Wompi.

        Raises:
            WompiError: si la petición falla o Wompi devuelve un error.
        """
        url = f"{self.base_url}{path}"
        response = requests.post(url, json=payload, headers=self._headers, timeout=30)
        data = response.json() if response.content else {}

        if response.status_code >= 400:
            error = data.get("error", {})
            raise WompiError(
                f"Wompi error {response.status_code}: {error.get('type')} - {error.get('messages')}"
            )
        return data

    # ------------------------------------------------------------------
    # Tokenización y cobros
    # ------------------------------------------------------------------
    def tokenize_card(self, card_data: dict[str, Any]) -> dict[str, Any]:
        """Tokeniza una tarjeta y devuelve el token.

        Args:
            card_data: datos de la tarjeta (number, cvc, exp_month, exp_year,
                card_holder). Nunca se persisten; solo viajan a Wompi.

        Returns:
            Respuesta de Wompi incluyendo ``data.id`` (el token de la tarjeta).
        """
        return self._post("/tokens/cards", card_data)

    def create_payment(
        self,
        amount_cents: int,
        currency: str,
        card_token: str,
        reference: str,
        customer_email: str,
    ) -> dict[str, Any]:
        """Crea un cobro único con una tarjeta tokenizada.

        Args:
            amount_cents: monto en centavos (ej. 6000000 = $60.000 COP).
            currency: código ISO de la moneda (por defecto COP).
            card_token: token de la tarjeta devuelto por ``tokenize_card``.
            reference: referencia única del negocio (para reconciliación).
            customer_email: email del dueño/pagador.

        Returns:
            Respuesta de Wompi con la transacción creada.
        """
        payload = {
            "amount_in_cents": amount_cents,
            "currency": currency,
            "customer_email": customer_email,
            "payment_method": {"type": "CARD", "token": card_token},
            "reference": reference,
            "payment_description": "Suscripción MusicFlow",
        }
        return self._post("/transactions", payload)

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------
    def verify_webhook_signature(self, checksum: Optional[str], raw_body: str) -> bool:
        """Verifica la firma de un webhook de Wompi.

        Wompi envía un checksum SHA256 de ``reference + amount + currency +
        events_secret_key`` en la cabecera ``X-Event-Checksum``. Verificamos
        ese checksum para evitar suplantaciones.

        Args:
            checksum: valor de la cabecera ``X-Event-Checksum``.
            raw_body: cuerpo crudo del webhook (bytes/str).

        Returns:
            ``True`` si la firma es válida, ``False`` en caso contrario.
        """
        if not checksum or not self.events_secret_key:
            return False

        try:
            # Se reconstruye el checksum a partir de los campos del evento.
            payload = __import__("json").loads(raw_body)
            data = payload.get("data", {}).get("transaction", {})
            signature_string = (
                f"{data.get('reference', '')}"
                f"{data.get('amount_in_cents', '')}"
                f"{data.get('currency', '')}"
                f"{self.events_secret_key}"
            )
            computed = hashlib.sha256(signature_string.encode("utf-8")).hexdigest()
            return hmac.compare_digest(computed, checksum)
        except (ValueError, AttributeError):
            return False


def get_wompi_client() -> WompiClient:
    """Devuelve una instancia compartida del cliente de Wompi.

    Returns:
        Instancia de ``WompiClient`` configurada con los settings actuales.
    """
    return WompiClient()
