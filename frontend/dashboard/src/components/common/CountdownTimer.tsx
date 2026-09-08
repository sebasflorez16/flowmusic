import { useEffect, useState } from 'react'

import { cn } from '@/lib/utils'

interface CountdownTimerProps {
  /** Tiempo total en segundos. */
  seconds: number
  /** Tamaño del texto (sm | md | lg). */
  size?: 'sm' | 'md' | 'lg'
  /** Si es true, usa el color de "urgencia" (rosa/rojo) para estrés positivo. */
  urgent?: boolean
}

const SIZES = {
  sm: 'text-sm',
  md: 'text-2xl',
  lg: 'text-4xl',
}

/**
 * Formatea un número de segundos a `MM:SS` o `HH:MM:SS`.
 */
function formatTime(total: number): string {
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const pad = (n: number) => String(n).padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`
}

/**
 * Contador regresivo en vivo.
 *
 * Decrementa el tiempo cada segundo. Se usa para mostrar el tiempo estimado de
 * espera de una canción en la cola; con `urgent` adopta el color de "estrés
 * positivo" que incentiva al cliente a pedir otra bebida.
 */
export function CountdownTimer({ seconds, size = 'md', urgent = false }: CountdownTimerProps) {
  const [remaining, setRemaining] = useState(Math.max(0, seconds))

  useEffect(() => {
    setRemaining(Math.max(0, seconds))
  }, [seconds])

  useEffect(() => {
    if (remaining <= 0) return
    const id = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000)
    return () => clearInterval(id)
  }, [remaining])

  return (
    <span
      className={cn(
        'font-mono font-semibold tabular-nums',
        SIZES[size],
        urgent ? 'text-secondary animate-pulse' : 'text-foreground',
      )}
    >
      {formatTime(remaining)}
    </span>
  )
}
