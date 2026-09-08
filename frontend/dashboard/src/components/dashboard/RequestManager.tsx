import { Check, X } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { SongRequest } from '@/lib/types'

interface RequestManagerProps {
  /** Peticiones pendientes de aprobación. */
  requests: SongRequest[]
  /** Callback para aprobar una petición. */
  onApprove: (id: number) => void
  /** Callback para rechazar una petición. */
  onReject: (id: number) => void
}

/**
 * Gestor de peticiones pendientes de los clientes.
 *
 * Muestra cada petición con su mesa, canción y hora, y botones de
 * aprobar/rechazar. Las notificaciones llegan en tiempo real por WebSocket.
 */
export function RequestManager({ requests, onApprove, onReject }: RequestManagerProps) {
  if (requests.length === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">No hay peticiones pendientes</p>
  }

  return (
    <ul className="space-y-2">
      {requests.map((request) => (
        <li key={request.id} className="glass flex items-center gap-3 rounded-lg p-3">
          <img
            src={request.playlist_item.thumbnail_url}
            alt=""
            className="h-10 w-10 shrink-0 rounded object-cover"
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{request.playlist_item.title}</p>
            <p className="truncate text-xs text-muted-foreground">
              {request.playlist_item.artist} · Mesa {request.table.number}
            </p>
          </div>
          <Badge variant="muted">{new Date(request.requested_at).toLocaleTimeString('es-CO')}</Badge>
          <div className="flex gap-1">
            <Button variant="default" size="icon" onClick={() => onApprove(request.id)} aria-label="Aprobar">
              <Check className="h-4 w-4" />
            </Button>
            <Button variant="destructive" size="icon" onClick={() => onReject(request.id)} aria-label="Rechazar">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </li>
      ))}
    </ul>
  )
}
