import { useEffect, useRef, useState } from 'react'

import { api } from '@/api'
import type { QueueItem, TVSnapshot } from '@/types'

/** Estado "finalizado" del reproductor de YouTube. */
const PLAYER_ENDED = 0
/** Duración por defecto (seg) si la canción no trae duración. */
const DEFAULT_DURATION = 180

/**
 * Vista TV: reproduce la cola de YouTube en pantalla completa.
 *
 * Avanza a la siguiente canción usando un temporizador con la duración de cada
 * video (refuerza con la detección del fin real vía postMessage). Los mensajes
 * de marketing rotan uno a uno.
 */
export function TVScreen() {
  const [snapshot, setSnapshot] = useState<TVSnapshot | null>(null)
  const [currentId, setCurrentId] = useState<number | null>(null)
  const [messageIndex, setMessageIndex] = useState(0)

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const currentIdRef = useRef<number | null>(null)
  const queueRef = useRef<QueueItem[]>([])
  const advancingRef = useRef(false)

  // Extrae el slug de la URL: /tv/<slug>
  const slug = window.location.pathname.split('/')[2] ?? ''

  useEffect(() => {
    queueRef.current = snapshot?.queue ?? []
  }, [snapshot])

  /** Programa el avance automático según la duración de la canción actual. */
  const scheduleAdvance = (item: QueueItem) => {
    if (timerRef.current) clearTimeout(timerRef.current)
    const duration = (item.playlist_item.duration_seconds || DEFAULT_DURATION) * 1000
    timerRef.current = setTimeout(() => advance(), duration)
  }

  /** Avanza a la siguiente canción de la cola (con guarda anti-doble). */
  const advance = () => {
    if (advancingRef.current) return
    advancingRef.current = true
    setTimeout(() => {
      advancingRef.current = false
    }, 1500)

    const queue = queueRef.current
    const idx = queue.findIndex((item) => item.id === currentIdRef.current)
    const next = idx >= 0 ? queue[idx + 1] : undefined

    if (next) {
      currentIdRef.current = next.id
      setCurrentId(next.id)
      void api(`/client/${slug}/playing/${next.id}/`, { method: 'POST' }).catch(() => {})
      scheduleAdvance(next)
    } else {
      currentIdRef.current = null
      setCurrentId(null)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }

  const advanceRef = useRef(advance)
  advanceRef.current = advance

  // Detecta el fin del video (postMessage) como refuerzo del temporizador.
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (typeof event.data !== 'string') return
      let data: unknown
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }
      const info = (
        data as { info?: { eventType?: string; eventArgs?: { playerState?: number } } }
      )?.info
      if (info?.eventType === 'onStateChange' && info.eventArgs?.playerState === PLAYER_ENDED) {
        advanceRef.current()
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  /** Carga la cola desde el backend. */
  const load = async (initial: boolean) => {
    try {
      const data = await api<TVSnapshot>(`/client/${slug}/tv/`)
      setSnapshot(data)

      if (initial) {
        if (data.playing) {
          currentIdRef.current = data.playing.id
          setCurrentId(data.playing.id)
          scheduleAdvance(data.playing)
        } else if (data.queue.length > 0) {
          const first = data.queue[0]
          currentIdRef.current = first.id
          setCurrentId(first.id)
          void api(`/client/${slug}/playing/${first.id}/`, { method: 'POST' }).catch(() => {})
          scheduleAdvance(first)
        }
      }
    } catch {
      // El endpoint no está listo o el bar no existe.
    }
  }

  useEffect(() => {
    void load(true)
    const interval = setInterval(() => void load(false), 5000)
    return () => {
      clearInterval(interval)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Rotación de mensajes de marketing (uno a la vez, cada 6 segundos).
  const messages = snapshot?.messages ?? []
  useEffect(() => {
    if (messages.length <= 1) return
    setMessageIndex(0)
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length)
    }, 6000)
    return () => clearInterval(interval)
  }, [messages.length])

  const current = snapshot?.queue.find((item) => item.id === currentId) ?? snapshot?.playing ?? null
  const upcoming = snapshot?.queue.filter((item) => item.id !== currentId) ?? []
  const videoId = current?.playlist_item.youtube_id
  const embedUrl = videoId
    ? `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&playsinline=1&rel=0&controls=1&enablejsapi=1&origin=${encodeURIComponent(window.location.origin)}`
    : null

  return (
    <div className="tv">
      <div className="player">
        {embedUrl ? (
          <iframe
            key={videoId}
            src={embedUrl}
            title="YouTube player"
            allow="autoplay; encrypted-media; fullscreen"
            allowFullScreen
          />
        ) : (
          <div className="empty-tv">Cola vacía · esperando canciones…</div>
        )}
      </div>

      {/* Mensaje de marketing rotativo (uno a la vez) */}
      {messages.length > 0 && (
        <div className="messages">
          <div key={messages[messageIndex]?.id} className="message">
            {messages[messageIndex]?.text}
          </div>
        </div>
      )}

      {/* Overlay inferior */}
      <div className="overlay">
        <div className="now-playing">
          {current ? (
            <>
              <div className="label">Sonando ahora</div>
              <div className="title">{current.playlist_item.title}</div>
              <div className="meta">
                {current.playlist_item.artist}
                {current.table_number ? ` · Mesa ${current.table_number}` : ''}
              </div>
            </>
          ) : (
            <div className="label">Cola vacía · esperando canciones…</div>
          )}
        </div>

        {upcoming.length > 0 && (
          <div className="next">
            <h3>Próximas</h3>
            {upcoming.slice(0, 4).map((item) => (
              <div key={item.id} className="next-item">
                <span className="pos">{item.position}</span>
                <span className="name">{item.playlist_item.title}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
