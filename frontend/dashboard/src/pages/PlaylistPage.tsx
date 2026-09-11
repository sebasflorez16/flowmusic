import { useCallback, useEffect, useState } from 'react'

import { Play, Plus } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { PlaylistItem } from '@/lib/types'
import { useQueue } from '@/stores/queue'

/**
 * Página de gestión de la playlist (catálogo de canciones aprobadas).
 *
 * Permite buscar, ver y agregar canciones desde YouTube (por URL o ID). El
 * backend extrae el ID y autocompleta título/artista vía oEmbed.
 */
export function PlaylistPage() {
  const [items, setItems] = useState<PlaylistItem[]>([])
  const [query, setQuery] = useState('')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const enqueuePlaylist = useQueue((s) => s.enqueuePlaylist)

  const fetchItems = useCallback(async () => {
    try {
      setItems(await api<PlaylistItem[]>('/music/playlist/'))
    } catch {
      setItems([])
    }
  }, [])

  useEffect(() => {
    void fetchItems()
  }, [fetchItems])

  /** Agrega una canción a partir de una URL o ID de YouTube. */
  const handleAdd = async () => {
    const value = youtubeUrl.trim()
    if (!value) return

    setAdding(true)
    setError(null)
    try {
      await api<PlaylistItem>('/music/playlist/', {
        method: 'POST',
        body: JSON.stringify({ url: value }),
      })
      setYoutubeUrl('')
      await fetchItems()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo agregar la canción')
    } finally {
      setAdding(false)
    }
  }

  const filtered = items.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.artist.toLowerCase().includes(query.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      {/* Agregar canción desde YouTube */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Agregar canción desde YouTube</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="Pega una URL o ID de YouTube"
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
          />
          <Button onClick={handleAdd} disabled={adding}>
            <Plus className="h-4 w-4" /> {adding ? 'Agregando…' : 'Agregar'}
          </Button>
        </CardContent>
        {error && <CardContent className="pt-0 text-sm text-destructive">{error}</CardContent>}
      </Card>

      {/* Catálogo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Catálogo de canciones</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar por título o artista…"
            className="mb-4"
          />

          {filtered.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No hay canciones en el catálogo
            </p>
          ) : (
            <ul className="space-y-2">
              {filtered.map((item) => (
                <li key={item.id} className="glass flex items-center gap-3 rounded-lg p-3">
                  <img
                    src={item.thumbnail_url}
                    alt=""
                    className="h-10 w-10 shrink-0 rounded object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{item.title}</p>
                    <p className="truncate text-xs text-muted-foreground">{item.artist}</p>
                  </div>
                  <Badge variant="muted">{item.duration_seconds}s</Badge>
                  <Badge variant={item.autodj_approved ? 'accent' : 'muted'}>
                    {item.autodj_approved ? 'AutoDJ' : 'Manual'}
                  </Badge>
                  <Button
                    variant="default"
                    size="icon"
                    onClick={() => void enqueuePlaylist(item.id)}
                    aria-label="Reproducir ahora"
                    title="Reproducir ahora"
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
