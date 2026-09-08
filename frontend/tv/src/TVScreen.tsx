import { useEffect, useRef, useState } from 'react'

import { api } from '@/api'
import type { QueueItem, TVSnapshot } from '@/types'

/** Duración por defecto (seg) si la canción no trae duración. */
const DEFAULT_DURATION = 180

/**
 * Vista TV: reproduce la cola de YouTube en pantalla completa.
 *
 * Usa un <iframe> normal de YouTube (sin la IFrame API, que da problemas con
 * orígenes locales). Avanza a la siguiente canción usando la duración de cada
 * video, y hace polling para recibir canciones nuevas aprobadas por el dueño.
 */
export function TVScreen() {
  const [snapshot, setSnapshot] = useState<TVSnapshot | null>(null)
  const [currentId, setCurrentId] = useState<number | null>(null)

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const currentIdRef = useRef<number | null>(null)
  const queueRef = useRef<QueueItem[]>([])

  // Extrae el slug de la URL: /tv/<slug>
  const slug = window.location.pathname.split('/')[2] ?? ''

  useEffect(() => {
    currentIdRef.current = currentId
  }, [currentId])

  useEffect(() => {
    queueRef.current = snapshot?.queue ?? []
  }, [snapshot])

  /** Programa el avance a la siguiente canción según la duración de la actual. */
  const scheduleAdvance = (item: QueueItem) => {
    if (timerRef.current) clearTimeout(timerRef.current)
    const duration = (item.playlist_item.duration_seconds || DEFAULT_DURATION) * 1000
    timerRef.current = setTimeout(() => advance(), duration)
  }

  /** Marca una canción como reproduciendo y programa el avance. */
  const playItem = (item: QueueItem) => {
    setCurrentId(item.id)
    void api(`/client/${slug}/playing/${item.id}/`, { method: 'POST' }).catch(() => {})
    scheduleAdvance(item)
  }

  /** Avanza a la siguiente canción de la cola. */
  const advance = () => {
    const queue = queueRef.current
    const idx = queue.findIndex((item) => item.id === currentIdRef.current)
    const next = idx >= 0 ? queue[idx + 1] : undefined
    if (next) {
      playItem(next)
    } else {
      setCurrentId(null)
    }
  }

  /** Carga la cola desde el backend. */
  const load = async (initial: boolean) => {
    try {
      const data = await api<TVSnapshot>(`/client/${slug}/tv/`)
      setSnapshot(data)

      if (initial) {
        if (data.playing) {
          setCurrentId(data.playing.id)
          scheduleAdvance(data.playing)
        } else if (data.queue.length > 0) {
          playItem(data.queue[0])
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

  const current = snapshot?.queue.find((item) => item.id === currentId) ?? snapshot?.playing ?? null
  const upcoming = snapshot?.queue.filter((item) => item.id !== currentId) ?? []
  const videoId = current?.playlist_item.youtube_id
  const embedUrl = videoId
    ? `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&playsinline=1&rel=0&controls=1`
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

      {/* Mensajes promocionales */}
      {snapshot && snapshot.messages.length > 0 && (
        <div className="messages">
          {snapshot.messages.map((m) => (
            <div key={m.id} className="message">
              {m.text}
            </div>
          ))}
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
