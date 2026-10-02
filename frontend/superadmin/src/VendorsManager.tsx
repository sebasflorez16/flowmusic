import { useEffect, useState, type FormEvent } from 'react'

import { api } from '@/api'
import type { VendorSummary } from '@/types'

const fmt = (n: number) => '$' + n.toLocaleString('es-CO', { maximumFractionDigits: 0 })

/**
 * URL del portal de mercaderistas.
 *
 * Si el panel está en un subdominio `admin.<dominio>` usa `vendedores.<dominio>`;
 * en cualquier otro caso, la ruta `/vendedor` del mismo dominio.
 */
function vendorPortalUrl(): string {
  const { protocol, host, origin } = window.location
  if (host.startsWith('admin.')) {
    return `${protocol}//vendedores.${host.slice('admin.'.length)}`
  }
  return `${origin}/vendedor`
}

/** Primer día del mes actual en formato YYYY-MM-01. */
function currentMonthFirstDay(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

/** Input inline para editar el % de comisión de un mercaderista. */
function RateInput({
  vendor,
  onSave,
}: {
  vendor: VendorSummary
  onSave: (vendor: VendorSummary, value: string) => Promise<void>
}) {
  const [value, setValue] = useState(vendor.commission_rate)
  const [saving, setSaving] = useState(false)

  const save = async () => {
    if (value === vendor.commission_rate) return
    setSaving(true)
    try {
      await onSave(vendor, value)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
      <input
        type="number"
        step="0.5"
        min="0"
        max="100"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        style={{ width: 64 }}
      />
      <button
        className="btn ghost"
        style={{ width: 'auto', padding: '6px 10px' }}
        onClick={() => void save()}
        disabled={saving || value === vendor.commission_rate}
      >
        {saving ? '…' : 'ok'}
      </button>
    </div>
  )
}

/**
 * Gestión de mercaderistas (vendedores independientes).
 *
 * Lista a los vendedores con sus ventas/comisión del mes, permite crearlos y
 * marcar el corte mensual como pagado. Solo cambia el % para ventas nuevas: las
 * ventas ya registradas conservan el porcentaje vigente al momento del cobro.
 */
export function VendorsManager() {
  const [vendors, setVendors] = useState<VendorSummary[]>([])
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [rate, setRate] = useState('5')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const load = async () => {
    try {
      setVendors(await api<VendorSummary[]>('/admin/vendors/'))
    } catch {
      setVendors([])
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const create = async (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    try {
      await api('/admin/vendors/', {
        method: 'POST',
        body: JSON.stringify({ email, password, commission_rate: rate }),
      })
      setMsg({ ok: true, text: `✓ Mercaderista ${email} creado` })
      setEmail('')
      setPassword('')
      await load()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  const markPaid = async (vendor: VendorSummary) => {
    setMsg(null)
    try {
      await api(`/admin/vendors/${vendor.id}/payouts/`, {
        method: 'POST',
        body: JSON.stringify({ period: currentMonthFirstDay() }),
      })
      setMsg({ ok: true, text: `✓ Corte de ${vendor.email} marcado como pagado` })
      await load()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  const changeRate = async (vendor: VendorSummary, value: string) => {
    setMsg(null)
    try {
      await api(`/admin/vendors/${vendor.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ commission_rate: value }),
      })
      setMsg({ ok: true, text: `✓ Comisión actualizada (rige para ventas nuevas)` })
      await load()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="glass panel">
        <h2>Acceso de mercaderistas</h2>
        <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 8 }}>
          Comparte este enlace con tus vendedores. Entran con su cuenta y ven solo lo suyo
          (sus bares y su comisión).
        </p>
        <input
          readOnly
          value={vendorPortalUrl()}
          onFocus={(e) => e.currentTarget.select()}
        />
      </div>

      <form className="glass panel" onSubmit={create}>
        <h2>Crear mercaderista</h2>
        <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>
          El vendedor tendrá su propio panel para crear bares y ver su comisión. El
          porcentaje rige para las ventas nuevas.
        </p>
        <div className="row">
          <div>
            <label>Email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
          </div>
          <div>
            <label>Contraseña</label>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
            />
          </div>
          <div>
            <label>Comisión (%)</label>
            <input
              value={rate}
              onChange={(e) => setRate(e.target.value)}
              type="number"
              step="0.5"
              min="0"
              max="100"
            />
          </div>
        </div>
        {msg && <p className={`msg ${msg.ok ? 'ok' : 'err'}`}>{msg.text}</p>}
        <button className="btn" style={{ marginTop: 12 }}>
          Crear mercaderista
        </button>
      </form>

      <div className="glass panel">
        <h2>Mercaderistas ({vendors.length})</h2>
        {vendors.length === 0 ? (
          <p style={{ color: 'var(--muted)' }}>Aún no hay mercaderistas.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Comisión %</th>
                <th>Bares</th>
                <th>Ventas del mes</th>
                <th>Comisión del mes</th>
                <th>Corte</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {vendors.map((v) => (
                <tr key={v.id}>
                  <td>{v.email}</td>
                  <td>
                    <RateInput vendor={v} onSave={changeRate} />
                  </td>
                  <td>{v.bars_count}</td>
                  <td>{fmt(v.month_sales)}</td>
                  <td style={{ color: 'var(--green)' }}>{fmt(v.month_commission)}</td>
                  <td>
                    {v.current_period_paid ? (
                      <span className="badge green">Pagada</span>
                    ) : (
                      <span className="badge amber">Pendiente</span>
                    )}
                  </td>
                  <td>
                    {!v.current_period_paid && (
                      <button
                        className="btn ghost"
                        style={{ width: 'auto', padding: '6px 10px' }}
                        onClick={() => void markPaid(v)}
                      >
                        Marcar pagado
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
