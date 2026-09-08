import { useEffect, useState } from 'react'

import { StatsWidget } from '@/components/dashboard/StatsWidget'
import { api } from '@/lib/api'
import type { RequestsByDay, StatsSummary } from '@/lib/types'

const EMPTY_SUMMARY: StatsSummary = {
  total_requests: 0,
  approved_requests: 0,
  songs_played: 0,
  avg_wait_seconds: 0,
  estimated_sales: 0,
}

/**
 * Página de estadísticas.
 *
 * Vista ampliada de las analíticas del bar: métricas agregadas y serie temporal
 * de peticiones. En el futuro añadirá filtros por rango de fechas.
 */
export function StatsPage() {
  const [summary, setSummary] = useState<StatsSummary>(EMPTY_SUMMARY)
  const [requestsByDay, setRequestsByDay] = useState<RequestsByDay[]>([])

  useEffect(() => {
    void api<StatsSummary>('/analytics/summary/')
      .then(setSummary)
      .catch(() => setSummary(EMPTY_SUMMARY))
    void api<RequestsByDay[]>('/analytics/requests-by-day/')
      .then(setRequestsByDay)
      .catch(() => setRequestsByDay([]))
  }, [])

  return <StatsWidget summary={summary} requestsByDay={requestsByDay} />
}
