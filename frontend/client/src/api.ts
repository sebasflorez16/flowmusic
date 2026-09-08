/** Cliente HTTP para la vista del cliente (pública, sin login). */

const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

/**
 * Realiza una petición JSON y devuelve el cuerpo parseado.
 * @throws ApiError si la respuesta no es exitosa.
 */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message =
      (body as { detail?: string }).detail ?? response.statusText
    throw new ApiError(message, response.status)
  }

  return (await response.json()) as T
}
