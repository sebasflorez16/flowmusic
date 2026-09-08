import { LogOut } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/stores/auth'

interface HeaderProps {
  /** Título de la página actual, mostrado a la izquierda. */
  title: string
}

/**
 * Barra superior del dashboard.
 *
 * Muestra el título de la página, el nombre del bar (tenant) y un botón para
 * cerrar sesión.
 */
export function Header({ title }: HeaderProps) {
  const tenant = useAuth((s) => s.tenant)
  const logout = useAuth((s) => s.logout)

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
        <Button variant="ghost" size="icon" onClick={logout} aria-label="Cerrar sesión">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
