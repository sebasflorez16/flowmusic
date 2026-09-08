import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Tenant } from '@/lib/types'
import { useAuth } from '@/stores/auth'

/**
 * Página de configuración del tenant.
 *
 * Permite editar los datos del bar y la configuración de reproducción
 * (AutoDJ, crossfade y límite de peticiones). Guarda vía PATCH al backend.
 */
export function SettingsPage() {
  const tenant = useAuth((s) => s.tenant)
  const setTenant = useAuth((s) => s.setTenant)
  const [form, setForm] = useState<Tenant | null>(tenant)

  useEffect(() => {
    setForm(tenant)
  }, [tenant])

  if (!form) {
    return <p className="text-sm text-muted-foreground">Cargando configuración…</p>
  }

  const update = <K extends keyof Tenant>(key: K, value: Tenant[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      const updated = await api<Tenant>('/settings/tenant/', {
        method: 'PATCH',
        body: JSON.stringify(form),
      })
      setTenant(updated)
    } catch {
      // El error ya se maneja en el cliente api.
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Datos del negocio</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground" htmlFor="name">Nombre</label>
            <Input id="name" value={form.name} onChange={(e) => update('name', e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground" htmlFor="phone">Teléfono</label>
            <Input id="phone" value={form.phone} onChange={(e) => update('phone', e.target.value)} />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <label className="text-xs text-muted-foreground" htmlFor="address">Dirección</label>
            <Input id="address" value={form.address} onChange={(e) => update('address', e.target.value)} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Reproducción</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <label className="flex items-center justify-between gap-2 text-sm">
            AutoDJ activado
            <input
              type="checkbox"
              checked={form.autodj_enabled}
              onChange={(e) => update('autodj_enabled', e.target.checked)}
            />
          </label>
          <label className="flex items-center justify-between gap-2 text-sm">
            Crossfade activado
            <input
              type="checkbox"
              checked={form.crossfade_enabled}
              onChange={(e) => update('crossfade_enabled', e.target.checked)}
            />
          </label>
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground" htmlFor="limit">
              Límite de peticiones por mesa/hora
            </label>
            <Input
              id="limit"
              type="number"
              min={1}
              value={form.requests_per_hour_limit}
              onChange={(e) => update('requests_per_hour_limit', Number(e.target.value))}
            />
          </div>
        </CardContent>
      </Card>

      <Button type="submit">Guardar cambios</Button>
    </form>
  )
}
