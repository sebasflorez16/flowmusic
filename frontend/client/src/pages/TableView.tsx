import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

import { api } from '@/api'
import type { PlaylistItem, TableSnapshot, YouTubeResult } from '@/types'

/** Formatea segundos a MM:SS. */
function formatTime(total: number): string {
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

/**
 * Vista principal del cliente (móvil).
 *
 * Se abre al escanear el QR de la mesa. Muestra el bar, la mesa, la canción
 * actual, la cola con tiempo estimado y el catálogo para pedir canciones.
 */
export function TableView() {
  const { slug = '', hash = '' } = useParams()
  const [snapshot, setSnapshot] = useState<TableSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<YouTubeResult[]>([])
  const [searching, setSearching] = useState(false)
  const [status, setStatus] = useState<{ msg: string; ok: boolean } | null>(null)
  const [requestedIds, setRequestedIds] = useState<Set<string>>(new Set())
  const [messageIndex, setMessageIndex] = useState(0)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  /** Carga el snapshot de la mesa desde el backend. */
  const load = async (silent = false) => {
    if (!silent) setLoading(true)
    setError(null)
    try {
      setSnapshot(await api<TableSnapshot>(`/client/${slug}/table/${hash}/`))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar la mesa')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  useEffect(() => {
    if (slug && hash) void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, hash])

  // Auto-refresco de respaldo (60s) + WebSocket para tiempo real.
  useEffect(() => {
    if (!slug || !hash) return
    const id = setInterval(() => void load(true), 60000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, hash])

  // WebSocket: actualiza la cola y la canción actual en tiempo real.
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
      const msg = data as { type?: string; queue?: TableSnapshot['queue']; playing?: TableSnapshot['playing'] }
      if (msg.type === 'queue.updated') {
        setSnapshot((prev) =>
          prev ? { ...prev, queue: msg.queue ?? [], playing: msg.playing ?? null } : prev,
        )
      }
    }
    return () => socket.close()
  }, [slug])

  // Rotación de mensajes de marketing (uno a la vez, cada 6 segundos).
  const messages = snapshot?.messages ?? []
  useEffect(() => {
    if (messages.length <= 1) return
    setMessageIndex(0)
    const id = setInterval(() => setMessageIndex((prev) => (prev + 1) % messages.length), 6000)
    return () => clearInterval(id)
  }, [messages.length])

  // Búsqueda en YouTube (Innertube) con debounce de 400ms.
  useEffect(() => {
    const q = query.trim()
    if (!q) {
      setResults([])
      return
    }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        setResults(await api<YouTubeResult[]>(`/client/search/?q=${encodeURIComponent(q)}`))
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 400)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  /** Filtra el catálogo local por búsqueda. */
  const catalog = useMemo(() => {
    if (!snapshot) return []
    const q = query.trim().toLowerCase()
    if (!q) return snapshot.catalog
    return snapshot.catalog.filter(
      (item) =>
        item.title.toLowerCase().includes(q) || item.artist.toLowerCase().includes(q),
    )
  }, [snapshot, query])

  /** Pide una canción para esta mesa (desde catálogo o resultado de YouTube). */
  const requestSong = async (item: PlaylistItem | YouTubeResult) => {
    setStatus(null)
    try {
      await api(`/client/${slug}/request/`, {
        method: 'POST',
        body: JSON.stringify({
          qr_hash: hash,
          youtube_id: item.youtube_id,
          title: item.title,
          artist: item.artist,
          duration_seconds: 'duration_seconds' in item ? item.duration_seconds : 0,
          thumbnail_url: item.thumbnail_url,
        }),
      })
      setRequestedIds((prev) => new Set(prev).add(item.youtube_id))
      setStatus({ msg: `✓ "${item.title}" enviada al dueño para aprobar`, ok: true })
    } catch (err) {
      setStatus({ msg: err instanceof Error ? err.message : 'No se pudo pedir', ok: false })
    }
  }

  if (loading) {
    return <div className="loading">Cargando…</div>
  }

  if (error || !snapshot) {
    return (
      <div className="loading">
        <p>{error ?? 'Mesa no encontrada'}</p>
      </div>
    )
  }

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Encabezado */}
      <header className="glass" style={{ padding: 16 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>{snapshot.bar_name}</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginTop: 2 }}>
          Mesa {snapshot.table_number} · Música en vivo
        </p>
      </header>

      {/* Mensaje de marketing rotativo (uno a la vez) */}
      {snapshot.messages.length > 0 && (
        <section className="glass" style={{ padding: 16, borderColor: 'var(--purple)' }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, color: 'var(--pink)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
            Promociones
          </h2>
          <p key={snapshot.messages[messageIndex]?.id} style={{ fontSize: 15, lineHeight: 1.4, fontWeight: 600 }}>
            {snapshot.messages[messageIndex]?.text}
          </p>
        </section>
      )}

      {/* Canción actual */}
      {snapshot.playing && (
        <section className="glass" style={{ padding: 16 }}>
          <p style={{ color: 'var(--pink)', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
            Sonando ahora
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 10 }}>
            <img
              src={snapshot.playing.playlist_item.thumbnail_url}
              alt=""
              style={{ width: 56, height: 56, borderRadius: 10, objectFit: 'cover' }}
            />
            <div style={{ minWidth: 0 }}>
              <p style={{ fontWeight: 600, fontSize: 15 }}>{snapshot.playing.playlist_item.title}</p>
              <p style={{ color: 'var(--muted)', fontSize: 13 }}>{snapshot.playing.playlist_item.artist}</p>
            </div>
          </div>
        </section>
      )}

      {/* Cola */}
      <section className="glass" style={{ padding: 16 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>Cola de reproducción</h2>
        {snapshot.queue.length === 0 ? (
          <p style={{ color: 'var(--muted)', fontSize: 13 }}>La cola está vacía. ¡Pide una canción!</p>
        ) : (
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {snapshot.queue.map((item) => (
              <li key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ color: 'var(--purple)', fontWeight: 700, width: 20 }}>{item.position}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 14, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.playlist_item.title}
                  </p>
                  <p style={{ color: 'var(--muted)', fontSize: 12 }}>
                    {item.playlist_item.artist}
                    {item.table_number ? ` · Mesa ${item.table_number}` : ''}
                  </p>
                </div>
                <span className="mono" style={{ color: 'var(--teal)', fontSize: 13 }}>
                  ~{formatTime(item.estimated_wait_seconds)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Catálogo / búsqueda */}
      <section className="glass" style={{ padding: 16 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>
          {query.trim() ? 'Resultados de YouTube' : 'Catálogo del bar'}
        </h2>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar en YouTube…"
          style={{ marginBottom: 12 }}
        />

        {searching && (
          <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 8 }}>Buscando…</p>
        )}

        {/* Resultados de YouTube cuando hay búsqueda */}
        {query.trim() ? (
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {results.map((item) => (
              <li key={item.youtube_id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <img
                  src={item.thumbnail_url}
                  alt=""
                  style={{ width: 44, height: 44, borderRadius: 8, objectFit: 'cover' }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 14, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.title}
                  </p>
                  <p style={{ color: 'var(--muted)', fontSize: 12 }}>{item.artist}</p>
                </div>
                <button
                  className="btn"
                  style={{
                    padding: '8px 12px',
                    fontSize: 13,
                    background: requestedIds.has(item.youtube_id) ? 'var(--green)' : undefined,
                  }}
                  onClick={() => requestSong(item)}
                  disabled={requestedIds.has(item.youtube_id)}
                >
                  {requestedIds.has(item.youtube_id) ? '✓ Pedida' : 'Pedir'}
                </button>
              </li>
            ))}
            {!searching && results.length === 0 && (
              <p style={{ color: 'var(--muted)', fontSize: 13 }}>Sin resultados. Prueba otra búsqueda.</p>
            )}
          </ul>
        ) : (
          /* Catálogo local aprobado cuando no hay búsqueda */
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {catalog.map((item) => (
              <li key={item.id} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <img
                  src={item.thumbnail_url}
                  alt=""
                  style={{ width: 44, height: 44, borderRadius: 8, objectFit: 'cover' }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 14, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.title}
                  </p>
                  <p style={{ color: 'var(--muted)', fontSize: 12 }}>{item.artist}</p>
                </div>
                <button
                  className="btn"
                  style={{
                    padding: '8px 12px',
                    fontSize: 13,
                    background: requestedIds.has(item.youtube_id) ? 'var(--green)' : undefined,
                  }}
                  onClick={() => requestSong(item)}
                  disabled={requestedIds.has(item.youtube_id)}
                >
                  {requestedIds.has(item.youtube_id) ? '✓ Pedida' : 'Pedir'}
                </button>
              </li>
            ))}
            {catalog.length === 0 && (
              <p style={{ color: 'var(--muted)', fontSize: 13 }}>No hay canciones en el catálogo.</p>
            )}
          </ul>
        )}
      </section>

      {/* Estado (toast fijo arriba, bien visible) */}
      {status && (
        <div
          className="glass"
          style={{
            position: 'fixed',
            top: 16,
            left: 16,
            right: 16,
            maxWidth: 448,
            margin: '0 auto',
            zIndex: 50,
            padding: 14,
            fontSize: 15,
            fontWeight: 600,
            color: status.ok ? 'var(--green)' : 'var(--red)',
            textAlign: 'center',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          }}
        >
          {status.msg}
        </div>
      )}
    </div>
  )
}
