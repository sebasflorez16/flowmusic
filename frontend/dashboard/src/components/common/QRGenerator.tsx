import { QRCodeSVG } from 'qrcode.react'

interface QRGeneratorProps {
  /** Valor a codificar en el QR (p. ej. la URL de la mesa). */
  value: string
  /** Tamaño en píxeles (default 128). */
  size?: number
  /** Color de fondo (default transparente). */
  bgColor?: string
  /** Color del código (default negro). */
  fgColor?: string
}

/**
 * Generador de códigos QR (SVG) usando `qrcode.react`.
 *
 * Se usa en la sección de mesas para renderizar el QR único de cada mesa y
 * permitir descargarlo/imprimirlo.
 */
export function QRGenerator({ value, size = 128, bgColor = 'transparent', fgColor = '#000000' }: QRGeneratorProps) {
  return (
    <div className="inline-block rounded-lg bg-white p-2">
      <QRCodeSVG value={value} size={size} bgColor={bgColor} fgColor={fgColor} level="M" />
    </div>
  )
}
