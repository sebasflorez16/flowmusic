import { QueueList } from '@/components/dashboard/QueueList'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useQueueSync } from '@/hooks/useQueue'

/**
 * Página de gestión de la cola de reproducción.
 *
 * Vista completa de la cola con acciones para aprobar/saltar ítems. Los datos
 * se sincronizan en tiempo real vía WebSocket.
 */
export function QueuePage() {
  const { queue, skipItem, playItem, moveItem } = useQueueSync()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Cola de reproducción</CardTitle>
      </CardHeader>
      <CardContent>
        <QueueList items={queue} onSkip={skipItem} onPlay={playItem} onMove={moveItem} />
      </CardContent>
    </Card>
  )
}
