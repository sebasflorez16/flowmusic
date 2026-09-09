import { useState, type FormEvent } from 'react'

import { register } from './api'

interface RegisterFormProps {
  initialPlan?: 'pro' | 'premium'
  onClose?: () => void
}

/** Formulario de registro de un nuevo bar desde la landing. */
export function RegisterForm({ initialPlan = 'pro', onClose }: RegisterFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [phone, setPhone] = useState('')
  const [plan, setPlan] = useState<'pro' | 'premium'>(initialPlan)
  const [genre, setGenre] = useState('crossover')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await register({
        email,
        password,
        business_name: businessName,
        phone,
        plan,
        genre,
      })
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al registrar el bar')
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="glass panel" style={{ padding: 32, textAlign: 'center' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>🎉</div>
        <h2 style={{ fontSize: 24 }}>¡Tu bar está registrado!</h2>
        <p className="sub" style={{ marginTop: 8, marginBottom: 24 }}>
          Revisa tu correo y entra al panel para configurar tus mesas, tu TV y tu
          música. Nuestro equipo te contactará para activar tu suscripción.
        </p>
        <a
          className="btn"
          href={import.meta.env.VITE_DASHBOARD_URL ?? 'https://flowmusic-dashboard.netlify.app'}
          style={{ marginRight: 12 }}
        >
          Ir al panel →
        </a>
        {onClose && (
          <button className="btn ghost" onClick={onClose}>
            Cerrar
          </button>
        )}
      </div>
    )
  }

  return (
    <form className="glass panel" onSubmit={submit} style={{ padding: 28, textAlign: 'left' }}>
      <h2 style={{ textAlign: 'center', marginBottom: 4 }}>Registra tu bar</h2>
      <p className="sub" style={{ marginBottom: 20 }}>
        Crea tu cuenta en 2 minutos. Sin tarjeta por ahora.
      </p>

      <label htmlFor="business">Nombre de tu bar o negocio</label>
      <input
        id="business"
        value={businessName}
        onChange={(e) => setBusinessName(e.target.value)}
        placeholder="Bar El Faro"
        required
      />

      <div className="row">
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tucorreo@bar.com"
            required
          />
        </div>
        <div>
          <label htmlFor="phone">Teléfono (opcional)</label>
          <input
            id="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="300 123 4567"
          />
        </div>
      </div>

      <label htmlFor="password" style={{ marginTop: 12 }}>
        Contraseña
      </label>
      <input
        id="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Mínimo 8 caracteres"
        minLength={8}
        required
      />

      <div className="row" style={{ marginTop: 12 }}>
        <div>
          <label htmlFor="plan">Plan</label>
          <select id="plan" value={plan} onChange={(e) => setPlan(e.target.value as 'pro' | 'premium')}>
            <option value="pro">Pro — $60.000 / mes</option>
            <option value="premium">Premium — $120.000 / mes</option>
          </select>
        </div>
        <div>
          <label htmlFor="genre">Género principal</label>
          <select id="genre" value={genre} onChange={(e) => setGenre(e.target.value)}>
            <option value="crossover">Variado</option>
            <option value="vallenato">Vallenato</option>
            <option value="reggaeton">Reggaetón</option>
            <option value="salsa">Salsa</option>
            <option value="cumbia">Cumbia</option>
            <option value="ranchera">Ranchera</option>
            <option value="pop_latino">Pop latino</option>
            <option value="rock_espanol">Rock en español</option>
            <option value="electronica">Electrónica</option>
          </select>
        </div>
      </div>

      {error && <p className="msg err" style={{ marginTop: 12 }}>{error}</p>}

      <button className="btn" style={{ width: '100%', marginTop: 16 }} disabled={loading}>
        {loading ? 'Creando tu bar…' : 'Crear mi bar gratis'}
      </button>
      <p style={{ color: 'var(--muted)', fontSize: 12, marginTop: 12, textAlign: 'center' }}>
        Al registrarte aceptas que te contactemos para activar tu suscripción.
      </p>
    </form>
  )
}
