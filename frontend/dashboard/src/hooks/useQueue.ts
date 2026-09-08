import { useEffect } from 'react'

import { useQueue } from '@/stores/queue'

/**
 * Hook de la cola con actualización automática.
 *
 * Al montarse, carga la cola y las peticiones desde el API y las refresca cada
 * 5 segundos (polling). Esto sustituye temporalmente a los WebSockets, que se
 * habilitarán en la Fase 3 para actualización en tiempo real.
 *
 * @returns El estado de la cola (items, peticiones, loading) y las acciones.
 */
export function useQueueSync() {
  const state = useQueue()

  useEffect(() => {
    void state.fetchQueue()
    const interval = setInterval(() => void state.fetchQueue(), 5000)
    return () => clearInterval(interval)
  }, [state.fetchQueue])

  return state
}
