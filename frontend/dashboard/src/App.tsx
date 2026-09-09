import type { ReactNode } from 'react'

import { Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { DashboardPage } from '@/pages/DashboardPage'
import { LoginPage } from '@/pages/LoginPage'
import { MarketingPage } from '@/pages/MarketingPage'
import { PlaylistPage } from '@/pages/PlaylistPage'
import { QueuePage } from '@/pages/QueuePage'
import { SettingsPage } from '@/pages/SettingsPage'
import { StatsPage } from '@/pages/StatsPage'
import { TablesPage } from '@/pages/TablesPage'
import { useAuth } from '@/stores/auth'

/**
 * Protege las rutas del dashboard.
 *
 * Si no hay un tenant logueado (sesión real), redirige al login.
 */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const tenant = useAuth((s) => s.tenant)

  if (!tenant) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

/**
 * Componente raíz de la aplicación.
 *
 * Define las rutas: login y el área protegida del dashboard (con layout).
 */
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="queue" element={<QueuePage />} />
        <Route path="tables" element={<TablesPage />} />
        <Route path="playlist" element={<PlaylistPage />} />
        <Route path="marketing" element={<MarketingPage />} />
        <Route path="stats" element={<StatsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
