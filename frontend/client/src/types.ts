/** Tipos de la vista del cliente (móvil). */

export interface PlaylistItem {
  id: number
  youtube_id: string
  title: string
  artist: string
  duration_seconds: number
  thumbnail_url: string
}

export interface QueueItem {
  id: number
  playlist_item: PlaylistItem
  table_number: number | null
  requested_by: string
  status: string
  position: number
  estimated_wait_seconds: number
}

/** Resultado de búsqueda en YouTube (Innertube). */
export interface YouTubeResult {
  youtube_id: string
  title: string
  artist: string
  duration_seconds: number
  thumbnail_url: string
}

/** Snapshot inicial que devuelve el backend al escanear el QR. */
export interface TableSnapshot {
  bar_name: string
  bar_slug: string
  table_number: number
  requests_limit: number
  playing: QueueItem | null
  queue: QueueItem[]
  catalog: PlaylistItem[]
}
