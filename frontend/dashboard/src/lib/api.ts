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

  // Timeout de red: si el backend no responde en 20s, se falla en vez de
  // dejar el botón "Ingresando…" colgado indefinidamente.
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 20000)

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    })
  } catch (err) {
    clearTimeout(timer)
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('El servidor tardó demasiado. Intenta de nuevo.', 0)
    }
    throw new ApiError('No se pudo conectar con el servidor.', 0)
  }
  clearTimeout(timer)

  if (response.status === 401) {
    // Intento único de refrescar el token antes de fallar.
    const refreshed = await tryRefresh()
    if (refreshed) {
      return api<T>(path, options)
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message = extractErrorMessage(body) ?? response.statusText
    throw new ApiError(message, response.status)
  }

  // 204 No Content no tiene cuerpo.
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

/**
 * Extrae un mensaje legible de un error de DRF.
 *
 * DRF devuelve errores en varios formatos:
 * - `{ detail: "..." }` (errores genéricos de APIView)
 * - `{ non_field_errors: ["..."] }` (errores de serializer)
 * - `{ campo: ["..."] }` (errores de validación por campo)
 */
function extractErrorMessage(body: unknown): string | null {
  if (typeof body !== 'object' || body === null) return null
  const data = body as Record<string, unknown>

  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
    return String(data.non_field_errors[0])
  }
  for (const value of Object.values(data)) {
    if (Array.isArray(value) && value.length > 0) {
      return `${String(value[0])}`
    }
  }
  return null
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
