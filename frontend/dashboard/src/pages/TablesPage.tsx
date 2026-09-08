import { useCallback, useEffect, useState } from 'react'

import { TableManager } from '@/components/dashboard/TableManager'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { Table } from '@/lib/types'

/**
 * Página de gestión de mesas y códigos QR.
 *
 * Permite crear mesas, ver su QR único y gestionarlas. Cada QR enlaza a la
 * vista móvil del cliente para esa mesa.
 */
export function TablesPage() {
  const [tables, setTables] = useState<Table[]>([])
  const [error, setError] = useState<string | null>(null)

  const fetchTables = useCallback(async () => {
    try {
      setTables(await api<Table[]>('/tables/'))
    } catch {
      setTables([])
    }
  }, [])

  useEffect(() => {
    void fetchTables()
  }, [fetchTables])

  const handleCreate = async (number: number) => {
    setError(null)
    try {
      await api<Table>('/tables/', { method: 'POST', body: JSON.stringify({ number }) })
      await fetchTables()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la mesa')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Mesas y códigos QR</CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-3 text-sm text-destructive">{error}</p>}
        <TableManager tables={tables} onCreate={handleCreate} />
      </CardContent>
    </Card>
  )
}
