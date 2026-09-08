import { forwardRef, type InputHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'

/**
 * Campo de texto de entrada (shadcn/ui).
 *
 * Usa el efecto "neumorphic-inset" para simular un campo hundido, coherente con
 * la estética Neumorfismo del proyecto.
 */
const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'neumorphic-inset flex h-10 w-full rounded-md px-3 py-2 text-sm',
          'placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className,
        )}
        ref={ref}
        {...props}
      />
    )
  },
)
Input.displayName = 'Input'

export { Input }
