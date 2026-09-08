import { create } from 'zustand'

import { clearTokens, setTokens as persistTokens } from '@/lib/api'
import type { Tenant } from '@/lib/types'

/**
 * Estado global de autenticación (Zustand).
 *
 * Guarda el tenant del dueño logueado y expone acciones de login/logout. El
 * token JWT se persiste en localStorage vía `lib/api`.
 */
interface AuthState {
  /** Tenant del dueño logueado (null si no hay sesión). */
  tenant: Tenant | null
  /** Indica si se está autenticando. */
  loading: boolean
  /** Inicia sesión guardando tokens y el tenant. */
  login: (tenant: Tenant, access: string, refresh: string) => void
  /** Cierra sesión y limpia tokens + estado. */
  logout: () => void
  /** Actualiza los datos del tenant (p. ej. tras editar settings). */
  setTenant: (tenant: Tenant) => void
}

export const useAuth = create<AuthState>((set) => ({
  tenant: null,
  loading: false,
  login: (tenant, access, refresh) => {
    persistTokens(access, refresh)
    set({ tenant, loading: false })
  },
  logout: () => {
    clearTokens()
    set({ tenant: null })
  },
  setTenant: (tenant) => set({ tenant }),
}))
