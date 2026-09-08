import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Combina clases CSS condicionalmente y resuelve conflictos de Tailwind.
 *
 * Utilidad base de shadcn/ui: permite escribir clases condicionales limpias y
 * deja que `tailwind-merge` elimine duplicados/conflictos.
 *
 * @param inputs - Lista de clases o expresiones condicionales.
 * @returns Cadena de clases lista para el atributo `className`.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
