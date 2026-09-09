import { useEffect } from 'react'

import { useAuth } from '@/stores/auth'
import { useQueue } from '@/stores/queue'
import type { QueueItem } from '@/lib/types'

/**
 * Hook de la cola con actualización en tiempo real vía WebSocket.
 *
 * Al montarse carga la cola y se suscribe al WebSocket del tenant
 * (``ws/queue/<slug>/``). Los eventos ``queue.updated`` y ``request.created``
 * actualizan el estado de forma reactiva, sin necesidad de polling.
 */
export function useQueueSync() {
  const state = useQueue()
  const slug = useAuth((s) => s.tenant?.slug)

  useEffect(() => {
    void state.fetchQueue()
  }, [state.fetchQueue])

  useEffect(() => {
    if (!slug) return

    const wsUrl = import.meta.env.VITE_WS_URL ?? '/ws'
    const socket = new WebSocket(`${wsUrl}/queue/${slug}/`)

    socket.onmessage = (event) => {
      let data: unknown
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }
      const msg = data as { type?: string; queue?: QueueItem[] }
      if (msg.type === 'queue.updated' && msg.queue) {
        state.setQueue(msg.queue)
      }
      if (msg.type === 'request.created') {
        void state.fetchQueue()
      }
    }

    return () => socket.close()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug])

  return state
}
