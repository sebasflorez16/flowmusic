import { useEffect, type ReactNode } from 'react'

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
import type { Tenant } from '@/lib/types'

/** Tenant de demostración para previsualizar el dashboard sin backend. */
const DEMO_TENANT: Tenant = {
  id: 1,
  name: 'Bar El Faro',
  slug: 'bar-el-faro',
  owner_email: 'juansebastianflorezescobar@gmail.com',
  phone: '',
  address: '',
  logo_url: '',
  plan: 'pro',
  subscription_status: 'active',
  max_tables: 20,
  requests_per_hour_limit: 2,
  crossfade_enabled: true,
  autodj_enabled: true,
}

/**
 * Protege las rutas del dashboard.
 *
 * Si no hay un tenant logueado, redirige al login. En desarrollo, si no hay
 * sesión, se inyecta un tenant de demostración para poder previsualizar la
 * interfaz sin backend (se elimina al conectar el API real).
 */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const tenant = useAuth((s) => s.tenant)
  const setTenant = useAuth((s) => s.setTenant)

  useEffect(() => {
    if (import.meta.env.DEV && !tenant) {
      setTenant(DEMO_TENANT)
    }
  }, [tenant, setTenant])

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
