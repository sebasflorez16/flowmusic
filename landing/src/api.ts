/** Cliente HTTP para el registro de nuevos bares desde la landing. */

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

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
  for (const [key, value] of Object.entries(d)) {
    if (Array.isArray(value) && value.length) return `${key}: ${String(value[0])}`
  }
  return null
}

export async function register(data: {
  email: string
  password: string
  business_name: string
  phone?: string
  plan?: string
  genre?: string
}): Promise<{ email: string; role: string }> {
  const response = await fetch(`${API_URL}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(extractError(body) ?? 'Error al registrar el bar', response.status)
  }

  return (await response.json()) as { email: string; role: string }
}
