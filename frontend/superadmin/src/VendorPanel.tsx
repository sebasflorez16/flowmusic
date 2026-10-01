import { useEffect, useState } from 'react'

import { api } from '@/api'
import { CreateBarForm } from '@/CreateBarForm'
import type { VendorDashboard } from '@/types'

const fmt = (n: number) => '$' + n.toLocaleString('es-CO', { maximumFractionDigits: 0 })

/** Badge del estado de suscripción de un bar. */
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

type VendorTab = 'ventas' | 'bares' | 'crear'

/**
 * Panel del mercaderista (vendedor independiente).
 *
 * Muestra su cálculo mensual (ventas de sus bares, su comisión y si el corte ya
 * fue pagado), el histórico de 12 meses, sus bares y el formulario para crear
 * uno nuevo (que queda asignado a él).
 */
export function VendorPanel({ email, onLogout }: { email: string; onLogout: () => void }) {
  const [data, setData] = useState<VendorDashboard | null>(null)
  const [tab, setTab] = useState<VendorTab>('ventas')

  const load = async () => {
    try {
      setData(await api<VendorDashboard>('/vendor/me/'))
    } catch {
      setData(null)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const current = data?.current
  const rate = data ? Number(data.commission_rate) : 0

  return (
    <div className="layout">
      <div className="glass topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img src="/logo-letra.png" alt="MusicFlow" style={{ height: 26 }} />
          <p style={{ color: 'var(--muted)', fontSize: 13 }}>
            Mercaderista · {email} · comisión {rate}%
          </p>
        </div>
        <button className="btn ghost" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>

      <nav style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {(
          [
            ['ventas', 'Mis ventas'],
            ['bares', 'Mis bares'],
            ['crear', 'Crear bar'],
          ] as [VendorTab, string][]
        ).map(([t, label]) => (
          <button
            key={t}
            className="btn ghost"
            style={tab === t ? { background: 'var(--purple)' } : undefined}
            onClick={() => setTab(t)}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === 'ventas' && (
        <div>
          <div className="cards">
            <div className="glass stat">
              <div className="label">Ventas de mis bares (mes)</div>
              <div className="value">{fmt(current?.sales ?? 0)}</div>
            </div>
            <div className="glass stat">
              <div className="label">Mi comisión ({rate}%)</div>
              <div className="value" style={{ color: 'var(--green)' }}>
                {fmt(current?.commission ?? 0)}
              </div>
            </div>
            <div className="glass stat">
              <div className="label">Estado del corte</div>
              <div
                className="value"
                style={{ color: current?.paid ? 'var(--green)' : 'var(--amber)' }}
              >
                {current?.paid ? 'Pagada ✓' : 'Pendiente'}
              </div>
            </div>
            <div className="glass stat">
              <div className="label">Bares afiliados</div>
              <div className="value">{data?.bars_count ?? 0}</div>
            </div>
          </div>

          <div className="glass panel">
            <h2>Histórico mensual</h2>
            {!data || data.history.length === 0 ? (
              <p style={{ color: 'var(--muted)' }}>Aún no hay ventas registradas.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Mes</th>
                    <th>Ventas</th>
                    <th>Comisión</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {[...data.history].reverse().map((m) => (
                    <tr key={m.period}>
                      <td>{m.period.slice(0, 7)}</td>
                      <td>{fmt(m.sales)}</td>
                      <td>{fmt(m.commission)}</td>
                      <td>
                        {m.paid ? (
                          <span className="badge green">Pagada</span>
                        ) : (
                          <span className="badge amber">Pendiente</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {tab === 'bares' && (
        <div className="glass panel">
          <h2>Mis bares ({data?.bars_count ?? 0})</h2>
          {!data || data.bars.length === 0 ? (
            <p style={{ color: 'var(--muted)' }}>
              Aún no tienes bares. Crea el primero en la pestaña "Crear bar".
            </p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Bar</th>
                  <th>Plan</th>
                  <th>Estado</th>
                  <th>Paga / mes</th>
                </tr>
              </thead>
              <tbody>
                {data.bars.map((b) => (
                  <tr key={b.id}>
                    <td>{b.name}</td>
                    <td>{b.plan}</td>
                    <td>
                      <StatusBadge status={b.subscription_status} />
                    </td>
                    <td>{fmt(b.monthly_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === 'crear' && <CreateBarForm onDone={load} endpoint="/vendor/me/tenants/" />}
    </div>
  )
}
