/** Tipos de la vista TV. */

export interface QueueItem {
  id: number
  playlist_item: {
    youtube_id: string
    title: string
    artist: string
    thumbnail_url: string
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

/** Declaración mínima del API de YouTube IFrame. */
export interface YTPlayer {
  loadVideoById: (videoId: string) => void
  destroy: () => void
}

export interface YTEvent {
  target: YTPlayer
  data: number
}

export interface YouTubeAPI {
  Player: new (
    element: HTMLElement,
    options: {
      videoId?: string
      playerVars?: Record<string, number | string>
      events?: {
        onStateChange?: (event: YTEvent) => void
        onReady?: () => void
      }
    },
  ) => YTPlayer
}
