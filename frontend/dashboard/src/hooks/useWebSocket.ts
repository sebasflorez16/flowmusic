import { useEffect, useRef, useState } from 'react'

import { getAccessToken } from '@/lib/api'

/**
 * Estado de una conexión WebSocket.
 */
export type WebSocketStatus = 'connecting' | 'open' | 'closed'

/**
 * Hook genérico para suscribirse a un endpoint WebSocket del backend.
 *
 * Al reconectar, dispara el callback `onMessage` para que el consumidor pueda
 * re-sincronizar su estado (el backend envía un snapshot al conectar).
 *
 * @param path - Ruta relativa del socket (ej. `/ws/queue/`).
 * @param onMessage - Callback invocado con cada mensaje parseado.
 * @returns El estado actual de la conexión.
 */
export function useWebSocket(
  path: string,
  onMessage: (data: unknown) => void,
): WebSocketStatus {
  const [status, setStatus] = useState<WebSocketStatus>('connecting')
  const onMessageRef = useRef(onMessage)

  // Mantiene el callback más reciente sin reiniciar el socket.
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL ?? '/ws'
    const token = getAccessToken()
    const url = `${wsUrl}${path}${path.includes('?') ? '&' : '?'}token=${token ?? ''}`

    const socket = new WebSocket(url)
    setStatus('connecting')

    socket.onopen = () => setStatus('open')
    socket.onclose = () => setStatus('closed')
    socket.onerror = () => setStatus('closed')
    socket.onmessage = (event) => {
      try {
        onMessageRef.current(JSON.parse(event.data))
      } catch {
        onMessageRef.current(event.data)
      }
    }

    return () => socket.close()
  }, [path])

  return status
}
