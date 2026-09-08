import { Outlet, useLocation } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

/** Títulos por ruta para el header. */
const TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/queue': 'Cola de reproducción',
  '/tables': 'Mesas y códigos QR',
  '/playlist': 'Playlist',
  '/marketing': 'Marketing',
  '/stats': 'Estadísticas',
  '/settings': 'Configuración',
}

/**
 * Layout principal del dashboard: sidebar fija + header + contenido.
 *
 * Usa `<Outlet/>` de React Router para renderizar la página activa dentro del
 * área de contenido.
 */
export function DashboardLayout() {
  const { pathname } = useLocation()
  const title = TITLES[pathname] ?? 'Dashboard'

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header title={title} />
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
