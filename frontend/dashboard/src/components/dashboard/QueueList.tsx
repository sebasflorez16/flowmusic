import { SkipForward } from 'lucide-react'

import { CountdownTimer } from '@/components/common/CountdownTimer'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { QueueItem } from '@/lib/types'

interface QueueListProps {
  /** Ítems de la cola, ordenados por posición. */
  items: QueueItem[]
  /** Callback para saltar un ítem. */
  onSkip: (id: number) => void
}

/** Mapea el estado de un ítem a la variante visual del badge. */
const STATUS_VARIANT: Record<QueueItem['status'], 'default' | 'accent' | 'success' | 'muted' | 'destructive'> = {
  pending: 'muted',
  approved: 'accent',
  playing: 'success',
  played: 'muted',
  skipped: 'muted',
  rejected: 'destructive',
}

/**
 * Lista de la cola de reproducción.
 *
 * Muestra posición, título/artista, mesa que lo pidió, estado y tiempo estimado
 * de espera. Permite saltar un ítem directamente.
 */
export function QueueList({ items, onSkip }: QueueListProps) {
  if (items.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">La cola está vacía</p>
  }

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="glass flex items-center gap-3 rounded-lg p-3 transition-colors hover:bg-muted/40"
        >
          {/* Posición */}
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-muted text-sm font-semibold tabular-nums">
            {item.position}
          </span>

          {/* Info de la canción */}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{item.playlist_item.title}</p>
            <p className="truncate text-xs text-muted-foreground">
              {item.playlist_item.artist}
              {item.table ? ` · Mesa ${item.table.number}` : ''}
            </p>
          </div>

          {/* Estado */}
          <Badge variant={STATUS_VARIANT[item.status]} className="hidden sm:inline-flex">
            {item.status}
          </Badge>

          {/* Tiempo estimado */}
          <div className="w-16 text-right">
            <CountdownTimer seconds={item.estimated_wait_seconds} size="sm" />
          </div>

          {/* Acción */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onSkip(item.id)}
            aria-label="Saltar canción"
          >
            <SkipForward className="h-4 w-4" />
          </Button>
        </li>
      ))}
    </ul>
  )
}
