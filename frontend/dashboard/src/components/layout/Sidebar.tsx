import {
  BarChart3,
  Disc3,
  ListMusic,
  Megaphone,
  Music2,
  Settings,
  Table2,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { cn } from '@/lib/utils'

/** Elementos de navegación del dashboard. */
const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: BarChart3, end: true },
  { to: '/queue', label: 'Cola', icon: ListMusic, end: false },
  { to: '/tables', label: 'Mesas', icon: Table2, end: false },
  { to: '/playlist', label: 'Playlist', icon: Music2, end: false },
  { to: '/marketing', label: 'Marketing', icon: Megaphone, end: false },
  { to: '/stats', label: 'Estadísticas', icon: BarChart3, end: false },
  { to: '/settings', label: 'Configuración', icon: Settings, end: false },
]

/**
 * Barra lateral del dashboard con el logo y la navegación principal.
 *
 * Usa `NavLink` para resaltar la ruta activa y un estilo coherente con el
 * Liquid Glass (fondo translúcido con blur).
 */
export function Sidebar() {
  return (
    <aside className="glass sticky top-0 flex h-screen w-64 flex-col border-r p-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2 px-2 pt-2">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary">
          <Disc3 className="h-5 w-5 text-white" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-bold">MusicFlow</p>
          <p className="text-xs text-muted-foreground">Panel del dueño</p>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary/20 text-primary shadow-glow'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Estado de conexión / pie */}
      <div className="mt-4 px-3 text-xs text-muted-foreground">
        <p className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
          Multi-tenant activo
        </p>
      </div>
    </aside>
  )
}
