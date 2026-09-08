"""Generación de códigos QR con branding de MusicFlow.

Produce una imagen PNG lista para imprimir y pegar en las mesas. Además del
código en sí (en los colores de la marca), incluye el nombre del bar, el número
de mesa y el mensaje de escaneo. Como el dueño la imprime, funciona como pieza
de publicidad de la plataforma.
"""

from __future__ import annotations

import io
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

# Colores de marca (Liquid Glass): púrpura neón, rosa vibrante y turquesa.
BRAND_PURPLE = (139, 92, 246)
BRAND_DARK = (24, 22, 38)
BRAND_TEXT = (51, 51, 68)
WHITE = (255, 255, 255)


def _font(size: int) -> ImageFont.ImageFont:
    """Devuelve una fuente TrueType o la por defecto si no está disponible."""
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def generate_branded_qr(
    *,
    value: str,
    bar_name: str,
    table_number: int,
) -> bytes:
    """Genera un QR con branding como imagen PNG (bytes).

    Args:
        value: contenido del QR (URL de la mesa).
        bar_name: nombre del bar (se imprime en la tarjeta).
        table_number: número de mesa (se imprime en la tarjeta).

    Returns:
        Bytes del archivo PNG generado.
    """
    # 1. QR con módulos redondeados en el púrpura de la marca.
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(value)
    qr.make(fit=True)
    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(front_color=BRAND_PURPLE, back_color=WHITE),
    ).convert("RGB")

    # 2. Composición de la tarjeta (fondo blanco + borde de marca + texto).
    qr_size = qr_img.size[0]
    padding = 40
    header = 90
    footer = 90
    card_width = qr_size + padding * 2
    card_height = qr_size + padding + header + footer

    card = Image.new("RGB", (card_width, card_height), WHITE)
    draw = ImageDraw.Draw(card)

    # Borde superior con degradado de marca (banda púrpura -> rosa).
    for i in range(header):
        ratio = i / header
        color = (
            int(BRAND_PURPLE[0] * (1 - ratio) + (236, 72, 153)[0] * ratio),
            int(BRAND_PURPLE[1] * (1 - ratio) + (236, 72, 153)[1] * ratio),
            int(BRAND_PURPLE[2] * (1 - ratio) + (236, 72, 153)[2] * ratio),
        )
        draw.line([(0, i), (card_width, i)], fill=color)

    # Nombre de la marca en la banda.
    brand_font = _font(30)
    draw.text((padding, 26), "MusicFlow", font=brand_font, fill=WHITE)

    # Pegar el QR.
    qr_x = padding
    qr_y = header + 30
    card.paste(qr_img, (qr_x, qr_y))

    # Pie: nombre del bar y número de mesa.
    bar_font = _font(26)
    sub_font = _font(18)
    draw.text((padding, header + qr_size + 50), bar_name, font=bar_font, fill=BRAND_DARK)
    draw.text(
        (padding, header + qr_size + 82),
        f"Mesa {table_number} · Escanea y pide tu canción",
        font=sub_font,
        fill=BRAND_TEXT,
    )

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    return buffer.getvalue()


def save_branded_qr(value: str, bar_name: str, table_number: int, media_dir: Path, slug: str) -> str:
    """Guarda el QR con branding en el directorio de media y devuelve su ruta.

    Args:
        value: contenido del QR.
        bar_name: nombre del bar.
        table_number: número de mesa.
        media_dir: raíz de media (settings.MEDIA_ROOT).
        slug: slug del tenant (se usa como subcarpeta).

    Returns:
        Ruta relativa (relativa a media) del archivo PNG guardado.
    """
    png_bytes = generate_branded_qr(
        value=value, bar_name=bar_name, table_number=table_number
    )
    folder = Path(media_dir) / "qr" / slug
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"mesa_{table_number}.png"
    (folder / filename).write_bytes(png_bytes)
    return f"qr/{slug}/{filename}"
