import { useEffect, useRef, useState } from 'react'

import { api } from '@/api'
import type { QueueItem, TVSnapshot } from '@/types'

/** Estado "finalizado" del reproductor de YouTube. */
const PLAYER_ENDED = 0
/** Duración por defecto (seg) si la canción no trae duración. */
const DEFAULT_DURATION = 180
/** Clave de localStorage para recordar la preferencia de sonido. */
const MUTE_KEY = 'musicflow.tv.muted'

/**
 * Vista TV: reproduce la cola de YouTube en pantalla completa.
 *
 * Robustez frente a pestañas en segundo plano: el avance no depende de un único
 * ``setTimeout`` (que el navegador puede retrasar), sino de un "heartbeat" que
 * compara el tiempo real transcurrido con la duración de la canción. Al volver
 * a la pestaña se re-sincroniza. Además detecta errores de YouTube (video no
 * reproducible) y salta automáticamente a la siguiente del AutoDJ.
 */
export function TVScreen() {
  const [snapshot, setSnapshot] = useState<TVSnapshot | null>(null)
  const [currentId, setCurrentId] = useState<number | null>(null)
  const [messageIndex, setMessageIndex] = useState(0)
  const [muted, setMuted] = useState<boolean>(
    () => localStorage.getItem(MUTE_KEY) !== 'false',
  )

  const currentIdRef = useRef<number | null>(null)
  const queueRef = useRef<QueueItem[]>([])
  const advancingRef = useRef(false)
  const autodjRef = useRef(false)
  const iframeRef = useRef<HTMLIFrameElement | null>(null)
  const mutedRef = useRef(muted)
  // Timestamp real en que empezó la canción actual (para el heartbeat).
  const startedAtRef = useRef<number>(Date.now())
  const durationRef = useRef<number>(DEFAULT_DURATION * 1000)

  // Extrae el slug de la URL: /tv/<slug>
  const slug = window.location.pathname.split('/')[2] ?? ''

  useEffect(() => {
    queueRef.current = snapshot?.queue ?? []
  }, [snapshot])

  useEffect(() => {
    mutedRef.current = muted
    localStorage.setItem(MUTE_KEY, String(muted))
  }, [muted])

  /** Envía un comando al reproductor de YouTube vía postMessage. */
  const sendCommand = (func: string, args: unknown[] = []) => {
    const iframe = iframeRef.current
    if (iframe?.contentWindow) {
      iframe.contentWindow.postMessage(
        JSON.stringify({ event: 'command', func, args }),
        '*',
      )
    }
  }

  /** Activa o silencia el sonido (persiste entre canciones y recargas). */
  const toggleMute = () => {
    if (muted) {
      sendCommand('unMute')
      setMuted(false)
    } else {
      sendCommand('mute')
      setMuted(true)
    }
  }

  /** Al cargar un video nuevo, restaura el estado de sonido que había. */
  const handleIframeLoad = () => {
    if (!mutedRef.current) {
      // Reintenta el unmute unas pocas veces (el player puede tardar en estar listo).
      for (const delay of [400, 900, 1500]) {
        setTimeout(() => sendCommand('unMute'), delay)
      }
    }
  }

  /** Marca el inicio de la canción actual para el heartbeat. */
  const markStart = (item: QueueItem) => {
    startedAtRef.current = Date.now()
    durationRef.current = (item.playlist_item.duration_seconds || DEFAULT_DURATION) * 1000
  }

  /** Pide al AutoDJ una canción del género del bar cuando la cola queda vacía. */
  const triggerAutoDJ = () => {
    if (autodjRef.current) return
    autodjRef.current = true
    void api<TVSnapshot>(`/client/${slug}/autodj/`, { method: 'POST' })
      .then((generated) => {
        autodjRef.current = false
        setSnapshot(generated)
        if (generated.playing) {
          currentIdRef.current = generated.playing.id
          setCurrentId(generated.playing.id)
          markStart(generated.playing)
        }
      })
      .catch(() => {
        autodjRef.current = false
      })
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
      markStart(next)
    } else {
      // Fin de la cola: marca la canción como reproducida y deja que el AutoDJ
      // continúe con el género del bar.
      const endedId = currentIdRef.current
      if (endedId) {
        void api(`/client/${slug}/played/${endedId}/`, { method: 'POST' }).catch(() => {})
      }
      currentIdRef.current = null
      setCurrentId(null)
      triggerAutoDJ()
    }
  }

  const advanceRef = useRef(advance)
  advanceRef.current = advance

  const triggerAutoDJRef = useRef(triggerAutoDJ)
  triggerAutoDJRef.current = triggerAutoDJ

  // Detecta fin del video y errores de YouTube (postMessage).
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
        data as {
          info?: {
            eventType?: string
            eventArgs?: { playerState?: number; data?: number }
          }
        }
      )?.info

      if (info?.eventType === 'onStateChange' && info.eventArgs?.playerState === PLAYER_ENDED) {
        advanceRef.current()
      }

      // Error de YouTube (video no reproducible / embed bloqueado / eliminado):
      // salta a la siguiente o pide otra al AutoDJ.
      if (info?.eventType === 'onError') {
        const endedId = currentIdRef.current
        if (endedId) {
          void api(`/client/${slug}/played/${endedId}/`, { method: 'POST' }).catch(() => {})
        }
        currentIdRef.current = null
        setCurrentId(null)
        triggerAutoDJRef.current()
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug])

  // Heartbeat: avanza según el tiempo real transcurrido, robusto al throttling
  // de pestañas en segundo plano (setInterval en background se limita a ~1/min,
  // pero al volver a primer plano se dispara de inmediato y corrige el avance).
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentIdRef.current === null) return
      if (Date.now() - startedAtRef.current >= durationRef.current) {
        advanceRef.current()
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // Al volver a la pestaña (visibilitychange), re-sincroniza: si la canción ya
  // terminó mientras la pestaña estaba en segundo plano, avanza de inmediato.
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState !== 'visible') return
      if (currentIdRef.current !== null && Date.now() - startedAtRef.current >= durationRef.current) {
        advanceRef.current()
      }
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
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
          markStart(data.playing)
        } else if (data.queue.length > 0) {
          const first = data.queue[0]
          currentIdRef.current = first.id
          setCurrentId(first.id)
          void api(`/client/${slug}/playing/${first.id}/`, { method: 'POST' }).catch(() => {})
          markStart(first)
        }
      }

      if (!data.playing && data.queue.length === 0) {
        triggerAutoDJ()
      } else if (data.queue.length > 0) {
        autodjRef.current = false
      }
    } catch {
      // El endpoint no está listo o el bar no existe.
    }
  }

  useEffect(() => {
    void load(true)
    // Polling de respaldo (60s); la actualización en tiempo real es por WS.
    const interval = setInterval(() => void load(false), 60000)
    return () => {
      clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // WebSocket: actualiza cola y canción actual en tiempo real.
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
      const msg = data as { type?: string; queue?: TVSnapshot['queue']; playing?: TVSnapshot['playing'] }
      if (msg.type !== 'queue.updated') return

      setSnapshot((prev) =>
        prev ? { ...prev, queue: msg.queue ?? [], playing: msg.playing ?? null } : prev,
      )

      const queue = msg.queue ?? []
      const stillInQueue = queue.some((q) => q.id === currentIdRef.current)

      if (msg.playing && msg.playing.id !== currentIdRef.current) {
        currentIdRef.current = msg.playing.id
        setCurrentId(msg.playing.id)
        markStart(msg.playing)
      } else if (!msg.playing && queue.length > 0 && !stillInQueue) {
        const first = queue[0]
        currentIdRef.current = first.id
        setCurrentId(first.id)
        void api(`/client/${slug}/playing/${first.id}/`, { method: 'POST' }).catch(() => {})
        markStart(first)
      } else if (!msg.playing && queue.length === 0) {
        triggerAutoDJRef.current()
      }
    }
    return () => socket.close()
  }, [slug])

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
            key={current?.id}
            ref={iframeRef}
            src={embedUrl}
            title="YouTube player"
            allow="autoplay; encrypted-media; fullscreen"
            allowFullScreen
            onLoad={handleIframeLoad}
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
