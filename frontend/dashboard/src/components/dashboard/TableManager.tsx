import { useState } from 'react'

import { Download, Plus } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/stores/auth'
import type { Table } from '@/lib/types'

interface TableManagerProps {
  /** Mesas existentes del tenant. */
  tables: Table[]
  /** Callback para crear una mesa con el número indicado. */
  onCreate: (number: number) => void
}

/** Construye la URL pública que el cliente escanea para abrir su mesa. */
function tableUrl(slug: string, qrHash: string): string {
  const base = import.meta.env.VITE_CLIENT_URL ?? 'https://flowmusic-client.netlify.app'
  return `${base}/bar/${slug}/t/${qrHash}`
}

/**
 * Gestor de mesas y códigos QR.
 *
 * Muestra el QR con el branding de MusicFlow (generado por el backend, listo
 * para imprimir), permite añadir mesas y descargar la imagen de cada QR.
 */
export function TableManager({ tables, onCreate }: TableManagerProps) {
  const [number, setNumber] = useState('')
  const slug = useAuth((s) => s.tenant?.slug ?? '')

  const handleCreate = () => {
    const n = Number(number)
    if (Number.isInteger(n) && n > 0) {
      onCreate(n)
      setNumber('')
    }
  }

  return (
    <div className="space-y-4">
      {/* Formulario para añadir mesa */}
      <div className="glass flex items-end gap-2 rounded-lg p-3">
        <div className="flex-1">
          <label className="mb-1 block text-xs text-muted-foreground" htmlFor="table-number">
            Número de mesa
          </label>
          <Input
            id="table-number"
            type="number"
            min={1}
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            placeholder="Ej. 5"
          />
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4" /> Añadir
        </Button>
      </div>

      {/* Grid de mesas */}
      {tables.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          Aún no hay mesas. Añade la primera para generar su QR.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {tables.map((table) => (
            <div key={table.id} className="glass flex flex-col items-center gap-3 rounded-lg p-4">
              <div className="flex w-full items-center justify-between">
                <span className="text-sm font-semibold">Mesa {table.number}</span>
                <Badge variant={table.is_active ? 'success' : 'muted'}>
                  {table.is_active ? 'Activa' : 'Inactiva'}
                </Badge>
              </div>

              {/* QR con branding generado por el backend (estable e inmutable). */}
              <img
                src={table.qr_image_url}
                alt={`QR Mesa ${table.number}`}
                className="h-28 w-auto rounded bg-white"
              />

              <a
                href={tableUrl(slug, table.qr_hash)}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                {table.qr_hash.slice(0, 10)}…
              </a>

              {table.qr_image_url && (
                <a href={table.qr_image_url} download className="w-full">
                  <Button variant="outline" size="sm" className="w-full">
                    <Download className="h-3 w-3" /> Descargar
                  </Button>
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
