import { create } from 'zustand'

import { api } from '@/lib/api'
import type { QueueItem, SongRequest } from '@/lib/types'

/**
 * Estado global de la cola de reproducción y las peticiones (Zustand).
 *
 * Centraliza la fuente de verdad del lado del cliente y expone acciones para
 * cargar, aprobar, rechazar, saltar y reordenar. Se sincroniza en tiempo real
 * vía WebSocket (ver `hooks/useQueue`).
 */
interface QueueState {
  /** Ítems activos de la cola. */
  queue: QueueItem[]
  /** Peticiones pendientes de aprobación. */
  pendingRequests: SongRequest[]
  /** Indica si se está cargando la cola. */
  loading: boolean
  /** Carga la cola y las peticiones pendientes desde el API. */
  fetchQueue: () => Promise<void>
  /** Aprueba una petición (la añade a la cola). */
  approveRequest: (requestId: number) => Promise<void>
  /** Rechaza una petición. */
  rejectRequest: (requestId: number) => Promise<void>
  /** Salta un ítem de la cola. */
  skipItem: (queueItemId: number) => Promise<void>
  /** Reproduce un ítem de la cola (lo marca como "reproduciendo"). */
  playItem: (queueItemId: number) => Promise<void>
  /** Reemplaza la cola con un snapshot recibido por WebSocket. */
  setQueue: (queue: QueueItem[]) => void
  /** Reemplaza las peticiones pendientes con un snapshot. */
  setPendingRequests: (requests: SongRequest[]) => void
}

export const useQueue = create<QueueState>((set, get) => ({
  queue: [],
  pendingRequests: [],
  loading: false,

  fetchQueue: async () => {
    set({ loading: true })
    try {
      const [queue, requests] = await Promise.all([
        api<QueueItem[]>('/music/queue/'),
        api<SongRequest[]>('/requests/?status=pending'),
      ])
      set({ queue, pendingRequests: requests, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  approveRequest: async (requestId) => {
    await api(`/requests/${requestId}/approve/`, { method: 'POST' })
    await get().fetchQueue()
  },

  rejectRequest: async (requestId) => {
    await api(`/requests/${requestId}/reject/`, { method: 'POST' })
    await get().fetchQueue()
  },

  skipItem: async (queueItemId) => {
    await api(`/music/queue/${queueItemId}/skip/`, { method: 'POST' })
    await get().fetchQueue()
  },

  playItem: async (queueItemId) => {
    await api(`/music/queue/${queueItemId}/play/`, { method: 'POST' })
    await get().fetchQueue()
  },

  setQueue: (queue) => set({ queue }),
  setPendingRequests: (pendingRequests) => set({ pendingRequests }),
}))
