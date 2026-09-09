/** Cliente HTTP con JWT para el panel del superadmin. */

const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1'
const TOKEN_KEY = 'musicflow.superadmin.token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function extractError(body: unknown): string | null {
  if (typeof body !== 'object' || body === null) return null
  const d = body as Record<string, unknown>
  if (typeof d.detail === 'string') return d.detail
  if (Array.isArray(d.non_field_errors) && d.non_field_errors.length) {
    return String(d.non_field_errors[0])
  }
  for (const v of Object.values(d)) {
    if (Array.isArray(v) && v.length) return String(v[0])
  }
  return null
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(extractError(body) ?? response.statusText, response.status)
  }
  return (await response.json()) as T
}
