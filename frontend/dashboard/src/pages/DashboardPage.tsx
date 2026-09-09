import { useEffect, useState } from 'react'

import { QueueList } from '@/components/dashboard/QueueList'
import { RequestManager } from '@/components/dashboard/RequestManager'
import { StatsWidget } from '@/components/dashboard/StatsWidget'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useQueueSync } from '@/hooks/useQueue'
import { api } from '@/lib/api'
import type { RequestsByDay, StatsSummary } from '@/lib/types'

/** Estado vacío por defecto mientras no hay datos del backend. */
const EMPTY_SUMMARY: StatsSummary = {
  total_requests: 0,
  approved_requests: 0,
  songs_played: 0,
  avg_wait_seconds: 0,
  estimated_sales: 0,
}

/**
 * Página principal del dashboard del dueño.
 *
 * Combina las estadísticas rápidas con una vista de la cola y las peticiones
 * pendientes en tiempo real.
 */
export function DashboardPage() {
  const { queue, pendingRequests, approveRequest, rejectRequest, skipItem, playItem } = useQueueSync()
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

  return (
    <div className="space-y-6">
      <StatsWidget summary={summary} requestsByDay={requestsByDay} />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Peticiones pendientes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Peticiones pendientes</CardTitle>
          </CardHeader>
          <CardContent>
            <RequestManager requests={pendingRequests} onApprove={approveRequest} onReject={rejectRequest} />
          </CardContent>
        </Card>

        {/* Cola actual */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cola de reproducción</CardTitle>
          </CardHeader>
          <CardContent>
            <QueueList items={queue} onSkip={skipItem} onPlay={playItem} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
