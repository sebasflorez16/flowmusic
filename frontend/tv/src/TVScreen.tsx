import { useEffect, useRef, useState } from 'react'

import { api } from '@/api'
import type { QueueItem, TVSnapshot, YouTubeAPI, YTPlayer } from '@/types'

/** Estado finalizado de un video en la API de YouTube IFrame. */
const YT_ENDED = 0

/** Carga el script del API de YouTube IFrame y devuelve el objeto YT. */
function loadYouTubeAPI(): Promise<YouTubeAPI> {
  return new Promise((resolve, reject) => {
    const existing = (window as unknown as { YT?: YouTubeAPI }).YT
    if (existing?.Player) {
      resolve(existing)
      return
    }
    const onReady = () => {
      const yt = (window as unknown as { YT?: YouTubeAPI }).YT
      if (yt?.Player) resolve(yt)
      else reject(new Error('YT no disponible'))
    }
    ;(window as unknown as { onYouTubeIframeAPIReady?: () => void }).onYouTubeIframeAPIReady = onReady

    const script = document.createElement('script')
    script.src = 'https://www.youtube.com/iframe_api'
    script.async = true
    script.onerror = () => reject(new Error('No se pudo cargar el API de YouTube'))
    document.head.appendChild(script)
  })
}

/**
 * Vista TV: reproduce la cola de YouTube en pantalla completa.
 *
 * Reproduce la cola una por una: al terminar una canción, avanza a la siguiente
 * y avisa al backend para que actualice el estado. Hace polling para recibir
 * canciones nuevas aprobadas por el dueño.
 */
export function TVScreen() {
  const [snapshot, setSnapshot] = useState<TVSnapshot | null>(null)
  const [currentId, setCurrentId] = useState<number | null>(null)
  const [muted, setMuted] = useState(true)
  const playerRef = useRef<YTPlayer | null>(null)
  const currentIdRef = useRef<number | null>(null)
  const queueRef = useRef<QueueItem[]>([])

  // Extrae el slug de la URL: /tv/<slug>
  const slug = window.location.pathname.split('/')[2] ?? ''

  // Mantiene refs sincronizados para usarlos dentro de los callbacks del player.
  useEffect(() => {
    currentIdRef.current = currentId
  }, [currentId])

  useEffect(() => {
    queueRef.current = snapshot?.queue ?? []
  }, [snapshot])

  /** Activa o silencia el sonido del reproductor. */
  const toggleMute = () => {
    const player = playerRef.current
    if (!player) return
    if (muted) {
      player.unmute()
      setMuted(false)
    } else {
      player.mute()
      setMuted(true)
    }
  }

  /** Marca una canción como reproduciendo y la carga en el player. */
  const playItem = (item: QueueItem) => {
    setCurrentId(item.id)
    playerRef.current?.loadVideoById(item.playlist_item.youtube_id)
    void api(`/client/${slug}/playing/${item.id}/`, { method: 'POST' }).catch(() => {})
  }

  /** Avanza a la siguiente canción de la cola (tras terminar una). */
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

      // Si no hay nada sonando aún, arranca con la primera de la cola.
      if (initial && !data.playing && data.queue.length > 0) {
        playItem(data.queue[0])
      } else if (initial && data.playing) {
        setCurrentId(data.playing.id)
        playerRef.current?.loadVideoById(data.playing.playlist_item.youtube_id)
      }
    } catch {
      // El endpoint no está listo o el bar no existe.
    }
  }

  // Inicialización: carga el API de YouTube, crea el player y arranca.
  useEffect(() => {
    let disposed = false

    void loadYouTubeAPI().then((yt) => {
      if (disposed) return
      const el = document.getElementById('player')
      if (!el) return
      playerRef.current = new yt.Player(el, {
        playerVars: {
          autoplay: 1,
          controls: 1,
          rel: 0,
          origin: window.location.origin,
          playsinline: 1,
          mute: 1, // autoplay con sonido lo bloquea el navegador; se arranca silenciado
        },
        events: {
          onStateChange: (event) => {
            if (event.data === YT_ENDED) advance()
          },
        },
      })
      void load(true)
    })

    // Polling: refresca la cola cada 5 segundos (recibe canciones nuevas).
    const interval = setInterval(() => void load(false), 5000)

    return () => {
      disposed = true
      clearInterval(interval)
      playerRef.current?.destroy()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const current = snapshot?.queue.find((item) => item.id === currentId) ?? snapshot?.playing ?? null
  const upcoming = snapshot?.queue.filter((item) => item.id !== currentId) ?? []

  return (
    <div className="tv">
      <div className="player">
        <div id="player" />
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
          <button className="mute-btn" onClick={toggleMute}>
            {muted ? '🔇 Activar sonido' : '🔊 Sonido activado'}
          </button>
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
