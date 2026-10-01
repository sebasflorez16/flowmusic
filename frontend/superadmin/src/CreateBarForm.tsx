import { useState, type FormEvent } from 'react'

import { api } from '@/api'

/**
 * Formulario para crear un bar manualmente (flujo de pago en efectivo).
 *
 * Se reutiliza tanto en la gestión del superadmin/socio (`/admin/tenants/`)
 * como en el panel del mercaderista (`/vendor/me/tenants/`), donde el bar queda
 * asignado automáticamente al vendedor.
 */
export function CreateBarForm({
  onDone,
  endpoint = '/admin/tenants/',
}: {
  onDone: () => void
  endpoint?: string
}) {
  const [name, setName] = useState('')
  const [ownerEmail, setOwnerEmail] = useState('')
  const [ownerPassword, setOwnerPassword] = useState('')
  const [phone, setPhone] = useState('')
  const [plan, setPlan] = useState('pro')
  const [maxTables, setMaxTables] = useState('8')
  const [genre, setGenre] = useState('crossover')
  const [customGenre, setCustomGenre] = useState('')
  const [withPayment, setWithPayment] = useState(true)
  const [amount, setAmount] = useState('60000')
  const [method, setMethod] = useState('cash')
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [created, setCreated] = useState<{ name: string; password: string } | null>(null)

  // Mesas incluidas y precio base por plan (sincronizado con el backend).
  const PLAN_INFO: Record<string, { included: number; base: number }> = {
    pro: { included: 8, base: 60000 },
    plus: { included: 12, base: 90000 },
    premium: { included: 16, base: 120000 },
  }
  const EXTRA_TABLE_PRICE = 10000
  const planInfo = PLAN_INFO[plan] ?? PLAN_INFO.pro
  const tables = Math.max(planInfo.included, Number(maxTables) || planInfo.included)
  const extra = Math.max(0, tables - planInfo.included)
  const computedAmount = planInfo.base + extra * EXTRA_TABLE_PRICE

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    setCreated(null)
    try {
      const data = await api<{ name: string; owner_password?: string; payment_registered: boolean }>(
        endpoint,
        {
          method: 'POST',
          body: JSON.stringify({
            name,
            owner_email: ownerEmail,
            owner_password: ownerPassword || undefined,
            phone,
            plan,
            genre,
            custom_genre: genre === 'custom' ? customGenre : undefined,
            max_tables: tables,
            initial_amount: withPayment ? computedAmount : null,
            initial_method: method,
          }),
        },
      )
      setCreated({ name: data.name, password: data.owner_password ?? ownerPassword })
      setMsg({
        ok: true,
        text: `✓ Bar "${data.name}" creado${data.payment_registered ? ' y activado' : ''}`,
      })
      setName('')
      setOwnerEmail('')
      setOwnerPassword('')
      setPhone('')
      setMaxTables('8')
      onDone()
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : 'Error' })
    }
  }

  return (
    <form className="glass panel" onSubmit={submit}>
      <h2>Crear bar manualmente</h2>
      <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>
        Para el flujo de pago en efectivo mano a mano: registras el bar y, si cobras
        ahora, queda activo al instante. El mínimo son 8 mesas.
      </p>

      <div className="row">
        <div>
          <label>Nombre del bar</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <label>Email del dueño</label>
          <input value={ownerEmail} onChange={(e) => setOwnerEmail(e.target.value)} type="email" required />
        </div>
      </div>

      <div className="row" style={{ marginTop: 8 }}>
        <div>
          <label>Contraseña del dueño (opcional)</label>
          <input
            value={ownerPassword}
            onChange={(e) => setOwnerPassword(e.target.value)}
            type="password"
            placeholder="Se genera automáticamente si vacío"
          />
        </div>
        <div>
          <label>Teléfono</label>
          <input value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
      </div>

      <div className="row" style={{ marginTop: 8 }}>
        <div>
          <label>Plan</label>
          <select value={plan} onChange={(e) => setPlan(e.target.value)}>
            <option value="pro">Pro — 8 mesas · $60.000</option>
            <option value="plus">Plus — 12 mesas · $90.000</option>
            <option value="premium">Premium — 16 mesas · $120.000</option>
          </select>
        </div>
        <div>
          <label>Número de mesas (mín. {planInfo.included})</label>
          <input
            value={maxTables}
            onChange={(e) => setMaxTables(e.target.value)}
            type="number"
            min={planInfo.included}
          />
        </div>
      </div>

      <div className="row" style={{ marginTop: 8 }}>
        <div>
          <label>Género</label>
          <select value={genre} onChange={(e) => setGenre(e.target.value)}>
            <option value="crossover">Variado</option>
            <option value="vallenato">Vallenato</option>
            <option value="reggaeton">Reggaetón</option>
            <option value="salsa">Salsa</option>
            <option value="cumbia">Cumbia</option>
            <option value="ranchera">Ranchera</option>
            <option value="pop_latino">Pop latino</option>
            <option value="rock_espanol">Rock en español</option>
            <option value="electronica">Electrónica</option>
            <option value="popular">Música popular</option>
            <option value="banda">Banda</option>
            <option value="nortena">Norteña</option>
            <option value="bachata">Bachata</option>
            <option value="merengue">Merengue</option>
            <option value="tropical">Tropical</option>
            <option value="champeta">Champeta</option>
            <option value="corridos">Corridos</option>
            <option value="custom">Otro (personalizado)</option>
          </select>
        </div>
        <div>
          <label>Total mensual (calculado)</label>
          <div className="msg ok" style={{ marginTop: 8, fontSize: 16 }}>
            <b>${computedAmount.toLocaleString('es-CO')}</b>
            {extra > 0 && (
              <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                {' '}
                = {planInfo.base.toLocaleString('es-CO')} base + {extra} mesa(s) extra × $10.000
              </span>
            )}
          </div>
        </div>
      </div>

      {genre === 'custom' && (
        <label style={{ marginTop: 12 }}>Género personalizado</label>
      )}
      {genre === 'custom' && (
        <input
          value={customGenre}
          onChange={(e) => setCustomGenre(e.target.value)}
          placeholder="Ej. baladas románticas, norteño sax…"
        />
      )}

      <label style={{ marginTop: 12 }}>
        <input
          type="checkbox"
          checked={withPayment}
          onChange={(e) => setWithPayment(e.target.checked)}
          style={{ width: 'auto', marginRight: 8 }}
        />
        Registrar pago en efectivo ahora y activar el bar
      </label>

      {withPayment && (
        <div className="row" style={{ marginTop: 8 }}>
          <div>
            <label>Monto a cobrar (COP)</label>
            <input
              value={withPayment ? String(computedAmount) : amount}
              onChange={(e) => setAmount(e.target.value)}
              type="number"
            />
          </div>
          <div>
            <label>Método</label>
            <select value={method} onChange={(e) => setMethod(e.target.value)}>
              <option value="cash">Efectivo</option>
              <option value="transfer">Transferencia</option>
            </select>
          </div>
        </div>
      )}

      {msg && <p className={`msg ${msg.ok ? 'ok' : 'err'}`}>{msg.text}</p>}
      {created && (
        <div className="msg ok" style={{ marginTop: 8 }}>
          Acceso del dueño: {created.name} — contraseña: <b>{created.password || 'la que definiste'}</b>
        </div>
      )}

      <button className="btn" style={{ marginTop: 12 }}>
        Crear bar
      </button>
    </form>
  )
}
