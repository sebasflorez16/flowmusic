import type { HTMLAttributes, ReactNode } from 'react'

import { cn } from '@/lib/utils'

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Icono o contenido decorativo opcional en la esquina. */
  icon?: ReactNode
  /** Habilita el efecto hover de elevación (default: true). */
  hover?: boolean
}

/**
 * Contenedor "Liquid Glass" reutilizable.
 *
 * Envuelve contenido con el efecto de cristal (blur + borde + brillo) y una
 * elevación sutil al hacer hover.
 */
export function GlassCard({ icon, hover = true, className, children, ...props }: GlassCardProps) {
  return (
    <div
      className={cn('glass rounded-lg p-5 shadow-glass-sm', hover && 'hover-glow', className)}
      {...props}
    >
      {icon && <div className="mb-3 text-primary">{icon}</div>}
      {children}
    </div>
  )
}
