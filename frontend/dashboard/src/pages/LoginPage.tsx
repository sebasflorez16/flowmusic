import { useState, type FormEvent } from 'react'

import { Disc3 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Tenant } from '@/lib/types'
import { useAuth } from '@/stores/auth'

/**
 * Página de inicio de sesión del dueño.
 *
 * Envía email/contraseña al backend, guarda el JWT y el tenant en el estado
 * global y redirige al dashboard.
 */
export function LoginPage() {
  const navigate = useNavigate()
  const login = useAuth((s) => s.login)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const data = await api<{ access: string; refresh: string; tenant: Tenant }>(
        '/auth/login/',
        { method: 'POST', body: JSON.stringify({ email, password }) },
      )
      login(data.tenant, data.access, data.refresh)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-screen place-items-center p-6">
      <form onSubmit={handleSubmit} className="glass w-full max-w-sm space-y-4 rounded-2xl p-8 shadow-glass">
        {/* Logo */}
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br from-primary to-secondary">
            <Disc3 className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-xl font-bold">MusicFlow</h1>
          <p className="text-sm text-muted-foreground">Panel del dueño</p>
        </div>

        <div className="space-y-2">
          <label className="text-xs text-muted-foreground" htmlFor="email">
            Email
          </label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs text-muted-foreground" htmlFor="password">
            Contraseña
          </label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? 'Ingresando…' : 'Iniciar sesión'}
        </Button>
      </form>
    </div>
  )
}
