import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { api } from '@/api'
import type { PlaylistItem, TableSnapshot } from '@/types'

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
  const [status, setStatus] = useState<{ msg: string; ok: boolean } | null>(null)

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

  // Auto-refresco silencioso cada 8 segundos para reflejar cambios en la cola.
  useEffect(() => {
    if (!slug || !hash) return
    const id = setInterval(() => void load(true), 8000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, hash])

  /** Filtra el catálogo por búsqueda. */
  const catalog = useMemo(() => {
    if (!snapshot) return []
    const q = query.trim().toLowerCase()
    if (!q) return snapshot.catalog
    return snapshot.catalog.filter(
      (item) =>
        item.title.toLowerCase().includes(q) || item.artist.toLowerCase().includes(q),
    )
  }, [snapshot, query])

  /** Pide una canción para esta mesa. */
  const requestSong = async (item: PlaylistItem) => {
    setStatus(null)
    try {
      await api(`/client/${slug}/request/`, {
        method: 'POST',
        body: JSON.stringify({ qr_hash: hash, youtube_id: item.youtube_id }),
      })
      setStatus({ msg: `"${item.title}" pedida. ¡El dueño la aprobará!`, ok: true })
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

      {/* Catálogo */}
      <section className="glass" style={{ padding: 16 }}>
        <h2 style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>Pide tu canción</h2>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar canción…"
          style={{ marginBottom: 12 }}
        />
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
              <button className="btn" style={{ padding: '8px 12px', fontSize: 13 }} onClick={() => requestSong(item)}>
                Pedir
              </button>
            </li>
          ))}
          {catalog.length === 0 && (
            <p style={{ color: 'var(--muted)', fontSize: 13 }}>No hay canciones para esa búsqueda.</p>
          )}
        </ul>
      </section>

      {/* Estado */}
      {status && (
        <div
          className="glass"
          style={{
            padding: 12,
            fontSize: 14,
            color: status.ok ? 'var(--green)' : 'var(--red)',
            textAlign: 'center',
          }}
        >
          {status.msg}
        </div>
      )}
    </div>
  )
}
