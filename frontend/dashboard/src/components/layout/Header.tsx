import { LogOut, MonitorPlay } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/stores/auth'

interface HeaderProps {
  /** Título de la página actual, mostrado a la izquierda. */
  title: string
}

/**
 * Barra superior del dashboard.
 *
 * Muestra el título de la página, el nombre del bar (tenant), un botón para
 * abrir la segunda pantalla (vista TV en una pestaña nueva) y cerrar sesión.
 */
export function Header({ title }: HeaderProps) {
  const tenant = useAuth((s) => s.tenant)
  const logout = useAuth((s) => s.logout)

  // URL de la segunda pantalla (vista TV) para este bar.
  const tvUrl = tenant?.slug
    ? `${import.meta.env.VITE_TV_URL ?? 'http://localhost:5175'}/tv/${tenant.slug}`
    : null

  return (
    <header className="glass sticky top-0 z-10 flex items-center justify-between border-b px-6 py-3">
      <div>
        <h1 className="text-lg font-semibold">{title}</h1>
        {tenant && <p className="text-xs text-muted-foreground">{tenant.name}</p>}
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium">{tenant?.owner_email ?? '—'}</p>
          <p className="text-xs capitalize text-muted-foreground">{tenant?.plan ?? ''}</p>
        </div>

        {tvUrl && (
          <Button variant="secondary" size="sm" asChild>
            <a href={tvUrl} target="_blank" rel="noopener noreferrer">
              <MonitorPlay className="h-4 w-4" /> Segunda pantalla
            </a>
          </Button>
        )}

        <Button variant="ghost" size="icon" onClick={logout} aria-label="Cerrar sesión">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
