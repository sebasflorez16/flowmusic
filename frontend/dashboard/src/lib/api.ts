/**
 * Cliente HTTP para el API REST del backend (Django + DRF).
 *
 * Centraliza la URL base, el manejo del token JWT y el refresco automático de
 * sesión. En desarrollo el proxy de Vite reenvía `/api` al backend; en
 * producción se usa `VITE_API_URL`.
 */

const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

/** Token de acceso JWT, persistido en memoria + localStorage. */
const ACCESS_TOKEN_KEY = 'musicflow.access'
const REFRESH_TOKEN_KEY = 'musicflow.refresh'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, access)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

/** Error tipado para respuestas del API con cuerpo de error. */
export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Realiza una petición autenticada al backend.
 *
 * @param path - Ruta relativa (ej. `'/tables/'`).
 * @param options - Opciones de fetch (método, body, etc.).
 * @returns El cuerpo JSON de la respuesta.
 * @throws ApiError si la respuesta no es exitosa.
 */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')

  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (response.status === 401) {
    // Intento único de refrescar el token antes de fallar.
    const refreshed = await tryRefresh()
    if (refreshed) {
      return api<T>(path, options)
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message = (body as { detail?: string }).detail ?? response.statusText
    throw new ApiError(message, response.status)
  }

  // 204 No Content no tiene cuerpo.
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

/**
 * Intenta renovar el token de acceso usando el refresh token.
 *
 * @returns `true` si el refresco fue exitoso.
 */
async function tryRefresh(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) {
    clearTokens()
    return false
  }
  try {
    const response = await fetch(`${API_URL}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })
    if (!response.ok) {
      clearTokens()
      return false
    }
    const data = (await response.json()) as { access?: string; refresh?: string }
    if (data.access) {
      setTokens(data.access, data.refresh ?? refresh)
      return true
    }
    return false
  } catch {
    return false
  }
}
