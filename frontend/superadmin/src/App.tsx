import { useEffect, useState, type FormEvent } from 'react'

import { api, clearToken, getEmail, getRole, getToken, setEmail, setRole, setToken } from '@/api'
import type { AdminTenant, LoginResponse, OverdueBar, Role, Staff, Summary } from '@/types'

type Tab = 'resumen' | 'bares' | 'cobrar' | 'cobros' | 'gastos' | 'socios'

const fmt = (n: number) =>
  '$' + n.toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 })

/** Página principal del superadmin. */
export default function App() {
  const [token, setTok] = useState(getToken())
  const [role, setRoleState] = useState<Role | null>(getRole())
  const [email, setEmailState] = useState<string | null>(getEmail())
  const [tab, setTab] = useState<Tab>('resumen')
  const [summary, setSummary] = useState<Summary | null>(null)
  const [tenants, setTenants] = useState<AdminTenant[]>([])
  const [overdue, setOverdue] = useState<OverdueBar[]>([])

  const load = async () => {
    try {
      setSummary(await api<Summary>('/admin/summary/'))
    } catch {
      setSummary(null)
    }
    try {
      setTenants(await api<AdminTenant[]>('/admin/tenants/'))
    } catch {
      setTenants([])
    }
    try {
      setOverdue(await api<OverdueBar[]>('/admin/overdue/'))
    } catch {
      setOverdue([])
    }
  }

  useEffect(() => {
    if (token) void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const onLogin = (data: LoginResponse) => {
    setToken(data.access)
    setRole(data.role)
    setEmail(data.email)
    setRoleState(data.role)
    setEmailState(data.email)
    setTok(data.access)
    setTab('resumen')
  }

  if (!token) {
    return <Login onLogin={onLogin} />
  }

  const isSuperadmin = role === 'superadmin'

  return (
    <div className="layout">
      <div className="glass topbar">
        <div>
          <h1 style={{ fontSize: 18 }}>MusicFlow · {isSuperadmin ? 'Superadmin' : 'Socio'}</h1>
          <p style={{ color: 'var(--muted)', fontSize: 13 }}>
            {isSuperadmin ? 'Dueños del negocio' : 'Gestión de bares y cobros'} · {email}
          </p>
        </div>
        <button
          className="btn ghost"
          onClick={() => {
            clearToken()
            setTok(null)
            setRoleState(null)
          }}
        >
          Cerrar sesión
        </button>
      </div>

      <nav style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {(
          [
            ['resumen', 'Resumen'],
            ['bares', 'Bares'],
            ['cobrar', 'Por cobrar'],
            ['cobros', 'Cobros'],
            ['gastos', 'Gastos'],
            ...(isSuperadmin ? ([['socios', 'Socios']] as [Tab, string][]) : []),
          ] as [Tab, string][]
        ).map(([t, label]) => (
          <button
            key={t}
            className="btn ghost"
            style={tab === t ? { background: 'var(--purple)' } : undefined}
            onClick={() => setTab(t)}
          >
            {label}
            {t === 'cobrar' && overdue.length > 0 && (
              <span style={{ background: 'var(--red)', borderRadius: 999, padding: '0 6px', fontSize: 11 }}>
                {overdue.length}
              </span>
            )}
          </button>
        ))}
      </nav>

      {tab === 'resumen' && summary && (
        <div>
          <div className="cards">
            <Stat label="Ingresos del mes" value={fmt(summary.income)} color="var(--green)" />
            <Stat label="Gastos del mes" value={fmt(summary.expenses)} color="var(--red)" />
            <Stat label="Utilidad" value={fmt(summary.profit)} color="var(--teal)" />
            <Stat label="MRR" value={fmt(summary.mrr)} color="var(--purple)" />
            <Stat label="Bares activos" value={String(summary.counts.active)} color="var(--text)" />
          </div>
          <div className="glass panel">
            <h2>Ingresos por método</h2>
            <table>
              <thead>
                <tr>
                  <th>Método</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Efectivo</td>
                  <td>{fmt(summary.by_method.cash ?? 0)}</td>
                </tr>
                <tr>
                  <td>Tarjeta</td>
                  <td>{fmt(summary.by_method.card ?? 0)}</td>
                </tr>
                <tr>
                  <td>Transferencia</td>
                  <td>{fmt(summary.by_method.transfer ?? 0)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'bares' && (
        <div className="glass panel">
          <h2>Bares ({tenants.length})</h2>
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Plan</th>
                <th>Estado</th>
                <th>Próxima facturación</th>
                <th>Último pago</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td>{t.plan}</td>
                  <td>
                    <StatusBadge status={t.subscription_status} />
                  </td>
                  <td>{t.next_billing_date ?? '—'}</td>
                  <td>{t.last_payment ? new Date(t.last_payment).toLocaleDateString('es-CO') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'cobrar' && (
        <div className="glass panel">
          <h2>Bares por cobrar ({overdue.length})</h2>
          {overdue.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>No hay bares vencidos. Todo al día.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Bar</th>
                  <th>Teléfono</th>
                  <th>Venció el</th>
                  <th>Días de atraso</th>
                </tr>
              </thead>
              <tbody>
                {overdue.map((b) => (
                  <tr key={b.id}>
                    <td>{b.name}</td>
                    <td>{b.phone || '—'}</td>
                    <td>{b.next_billing_date}</td>
                    <td style={{ color: 'var(--red)', fontWeight: 700 }}>{b.days_overdue} días</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'cobros' && <PaymentForm tenants={tenants} onDone={load} />}
      {tab === 'gastos' && <ExpenseForm onDone={load} />}
      {tab === 'socios' && <StaffForm onDone={load} />}
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="glass stat">
      <div className="label">{label}</div>
      <div className="value" style={{ color }}>
        {value}
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, [string, string]> = {
    active: ['Activo', 'green'],
    past_due: ['Vencido', 'red'],
    canceled: ['Cancelado', 'amber'],
    trialing: ['En registro', 'amber'],
  }
  const [label, color] = map[status] ?? [status, 'amber']
  return <span className={`badge ${color}`}>{label}</span>
}

function Login({ onLogin }: { onLogin: (data: LoginResponse) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await api<LoginResponse>('/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      if (data.role !== 'superadmin' && data.role !== 'socio') {
        setError('Esta cuenta no tiene acceso al panel de administración.')
        return
      }
      onLogin(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout" style={{ maxWidth: 400, paddingTop: 60 }}>
      <form className="glass panel" onSubmit={submit}>
        <h1 style={{ fontSize: 20, marginBottom: 4 }}>MusicFlow Superadmin</h1>
        <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 16 }}>Acceso de dueños del negocio</p>
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required autoFocus />
        <label style={{ marginTop: 12 }}>Contraseña</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        {error && <p className="msg err">{error}</p>}
        <button className="btn" style={{ width: '100%', marginTop: 16 }} disabled={loading}>
          {loading ? 'Ingresando…' : 'Ingresar'}
        </button>
      </form>
    </div>
  )
}

function PaymentForm({ tenants, onDone }: { tenants: AdminTenant[]; onDone: () => void }) {
  const [tenant, setTenant] = useState('')
  const [amount, setAmount] = useState('60000')
  const [method, setMethod] = useState('cash')
  const [period, setPeriod] = useState('')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    try {
      await api('/admin/payments/', {
        method: 'POST',
        body: JSON.stringify({
          tenant: Number(tenant),
          amount: Number(amount),
          method,
          billing_period: period,
        }),
      })
      setMsg({ ok: true, text: '✓ Pago registrado y bar activado' })
      onDone()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  return (
    <form className="glass panel" onSubmit={submit}>
      <h2>Registrar cobro</h2>
      <label>Bar</label>
      <select value={tenant} onChange={(e) => setTenant(e.target.value)} required>
        <option value="">Selecciona un bar…</option>
        {tenants.map((t) => (
          <option key={t.id} value={t.id}>
            {t.name}
          </option>
        ))}
      </select>
      <div className="row" style={{ marginTop: 12 }}>
        <div>
          <label>Monto (COP)</label>
          <input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" required />
        </div>
        <div>
          <label>Método</label>
          <select value={method} onChange={(e) => setMethod(e.target.value)}>
            <option value="cash">Efectivo</option>
            <option value="transfer">Transferencia</option>
          </select>
        </div>
        <div>
          <label>Período (mes)</label>
          <input value={period} onChange={(e) => setPeriod(e.target.value)} type="date" required />
        </div>
      </div>
      {msg && <p className={`msg ${msg.ok ? 'ok' : 'err'}`}>{msg.text}</p>}
      <button className="btn" style={{ marginTop: 12 }}>
        Registrar cobro
      </button>
    </form>
  )
}

function ExpenseForm({ onDone }: { onDone: () => void }) {
  const [category, setCategory] = useState('hosting')
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState('')
  const [description, setDescription] = useState('')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    try {
      await api('/admin/expenses/', {
        method: 'POST',
        body: JSON.stringify({ category, amount: Number(amount), date, description }),
      })
      setMsg({ ok: true, text: '✓ Gasto registrado' })
      onDone()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  return (
    <form className="glass panel" onSubmit={submit}>
      <h2>Registrar gasto</h2>
      <div className="row">
        <div>
          <label>Categoría</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="hosting">Hosting / Infraestructura</option>
            <option value="marketing">Marketing</option>
            <option value="salaries">Salarios</option>
            <option value="software">Software</option>
            <option value="other">Otros</option>
          </select>
        </div>
        <div>
          <label>Monto (COP)</label>
          <input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" required />
        </div>
        <div>
          <label>Fecha</label>
          <input value={date} onChange={(e) => setDate(e.target.value)} type="date" required />
        </div>
      </div>
      <label style={{ marginTop: 12 }}>Descripción</label>
      <input value={description} onChange={(e) => setDescription(e.target.value)} />
      {msg && <p className={`msg ${msg.ok ? 'ok' : 'err'}`}>{msg.text}</p>}
      <button className="btn" style={{ marginTop: 12 }}>
        Registrar gasto
      </button>
    </form>
  )
}

function StaffForm({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [staff, setStaff] = useState<Staff[]>([])

  const loadStaff = async () => {
    try {
      setStaff(await api<Staff[]>('/admin/staff/list/'))
    } catch {
      setStaff([])
    }
  }

  useEffect(() => {
    void loadStaff()
  }, [])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    try {
      await api('/admin/staff/', {
        method: 'POST',
        body: JSON.stringify({ email, password, confirm_password: confirm }),
      })
      setMsg({ ok: true, text: `✓ Socio ${email} creado` })
      setEmail('')
      setPassword('')
      setConfirm('')
      void loadStaff()
      onDone()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <form className="glass panel" onSubmit={submit}>
        <h2>Crear socio</h2>
        <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>
          El socio podrá activar bares y registrar cobros en efectivo. Se requiere tu
          contraseña de dueño para confirmar.
        </p>
        <label>Email del socio</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label style={{ marginTop: 12 }}>Contraseña del socio</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        <label style={{ marginTop: 12 }}>Tu contraseña (verificación de dueño)</label>
        <input value={confirm} onChange={(e) => setConfirm(e.target.value)} type="password" required />
        {msg && <p className={`msg ${msg.ok ? 'ok' : 'err'}`}>{msg.text}</p>}
        <button className="btn" style={{ marginTop: 12 }}>
          Crear socio
        </button>
      </form>

      <div className="glass panel">
        <h2>Socios ({staff.length})</h2>
        {staff.length === 0 ? (
          <p style={{ color: 'var(--muted)' }}>No hay socios registrados todavía.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Estado</th>
                <th>Desde</th>
              </tr>
            </thead>
            <tbody>
              {staff.map((s) => (
                <tr key={s.id}>
                  <td>{s.email}</td>
                  <td>
                    <span className={`badge ${s.is_active ? 'green' : 'red'}`}>
                      {s.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>{new Date(s.date_joined).toLocaleDateString('es-CO')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
