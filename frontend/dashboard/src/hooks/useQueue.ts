import { useEffect } from 'react'

import { useQueue } from '@/stores/queue'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { QueueItem, SongRequest } from '@/lib/types'

/**
 * Hook de la cola en tiempo real.
 *
 * Al montarse, carga la cola y las peticiones desde el API y se suscribe al
 * WebSocket de la cola. Los eventos `queue.updated` y `request.created`
 * actualizan el estado global de forma reactiva.
 *
 * @returns El estado de la cola (items, peticiones, loading) y las acciones.
 */
export function useQueueSync() {
  const { fetchQueue, setQueue, setPendingRequests, ...actions } = useQueue()
  const state = useQueue()

  useEffect(() => {
    void fetchQueue()
  }, [fetchQueue])

  useWebSocket('/ws/queue/', (data) => {
    const event = data as { type?: string; queue?: QueueItem[]; pending?: SongRequest[] }
    if (event.type === 'queue.updated' && event.queue) {
      setQueue(event.queue)
    }
    if (event.type === 'request.created' && event.pending) {
      setPendingRequests(event.pending)
    }
  })

  return { ...state, ...actions }
}
