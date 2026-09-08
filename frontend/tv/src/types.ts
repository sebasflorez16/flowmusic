/** Tipos de la vista TV. */

export interface QueueItem {
  id: number
  playlist_item: {
    youtube_id: string
    title: string
    artist: string
    thumbnail_url: string
    duration_seconds: number
  }
  table_number: number | null
  status: string
  position: number
}

export interface DisplayMessage {
  id: number
  text: string
  message_type: string
}

export interface TVSnapshot {
  bar_name: string
  playing: QueueItem | null
  queue: QueueItem[]
  messages: DisplayMessage[]
}

