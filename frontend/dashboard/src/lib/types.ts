/**
 * Tipos de dominio que reflejan los modelos del backend (DRF serializers).
 *
 * Mantenerlos sincronizados con `backend/apps/**​/models.py` a medida que se
 * implementa el API REST.
 */

/** Estados de suscripción de un tenant. */
export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'canceled'

/** Planes disponibles. */
export type Plan = 'pro' | 'premium'

/** Géneros musicales del bar (usados por el AutoDJ). */
export type Genre =
  | 'vallenato'
  | 'reggaeton'
  | 'salsa'
  | 'cumbia'
  | 'ranchera'
  | 'pop_latino'
  | 'rock_espanol'
  | 'electronica'
  | 'crossover'

/** Mesa del bar. */
export interface Table {
  id: number
  number: number
  qr_hash: string
  qr_image_url: string
  is_active: boolean
  created_at: string
}

/** Canción en el catálogo aprobado. */
export interface PlaylistItem {
  id: number
  youtube_id: string
  title: string
  artist: string
  duration_seconds: number
  thumbnail_url: string
  autodj_approved: boolean
  play_count: number
  created_at: string
}

/** Estado de un ítem en la cola de reproducción. */
export type QueueItemStatus =
  | 'pending'
  | 'approved'
  | 'playing'
  | 'played'
  | 'skipped'
  | 'rejected'

/** Canción en la cola de reproducción. */
export interface QueueItem {
  id: number
  playlist_item: PlaylistItem
  table: Table | null
  requested_by: string
  status: QueueItemStatus
  position: number
  estimated_wait_seconds: number
  started_at: string | null
  played_at: string | null
}

/** Estado de una petición de canción. */
export type SongRequestStatus = 'pending' | 'approved' | 'rejected'

/** Petición de canción de un cliente. */
export interface SongRequest {
  id: number
  table: Table
  playlist_item: PlaylistItem
  status: SongRequestStatus
  requested_at: string
  approved_at: string | null
}

/** Cupón de descuento. */
export interface Coupon {
  id: number
  code: string
  description: string
  discount_type: 'percentage' | 'fixed'
  value: string
  valid_from: string
  valid_until: string
  is_active: boolean
  max_uses: number | null
  used_count: number
}

/** Mensaje que se muestra en la TV. */
export interface DisplayMessage {
  id: number
  text: string
  message_type: 'promotion' | 'birthday' | 'anniversary' | 'custom' | 'happy_hour'
  valid_from: string
  valid_until: string
  is_active: boolean
}

/** Datos del tenant (bar) del dueño logueado. */
export interface Tenant {
  id: number
  name: string
  slug: string
  owner_email: string
  phone: string
  address: string
  logo_url: string
  plan: Plan
  subscription_status: SubscriptionStatus
  max_tables: number
  requests_per_hour_limit: number
  crossfade_enabled: boolean
  autodj_enabled: boolean
  genre: Genre
}

/** Estadísticas agregadas para el dashboard. */
export interface StatsSummary {
  total_requests: number
  approved_requests: number
  songs_played: number
  avg_wait_seconds: number
  estimated_sales: number
}

/** Punto de la serie temporal de peticiones por día. */
export interface RequestsByDay {
  date: string
  requests: number
}
