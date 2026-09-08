import { MessageSquare } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { DisplayMessage } from '@/lib/types'

interface MessageManagerProps {
  /** Mensajes de pantalla del tenant. */
  messages: DisplayMessage[]
  /** Callback para crear un mensaje nuevo. */
  onCreate: () => void
  /** Callback para activar/desactivar un mensaje. */
  onToggle: (message: DisplayMessage) => void
}

/** Etiqueta legible para cada tipo de mensaje. */
const TYPE_LABEL: Record<DisplayMessage['message_type'], string> = {
  promotion: 'Promoción',
  birthday: 'Cumpleaños',
  anniversary: 'Aniversario',
  custom: 'Personalizado',
  happy_hour: 'Happy Hour',
}

/**
 * Lista de mensajes que aparecen como overlay en la TV.
 *
 * Muestra texto, tipo y estado de cada mensaje, con un interruptor para
 * activar/desactivar cuáles rotan en pantalla.
 */
export function MessageManager({ messages, onCreate, onToggle }: MessageManagerProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{messages.length} mensajes</p>
        <Button size="sm" onClick={onCreate}>
          Crear mensaje
        </Button>
      </div>

      {messages.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">No hay mensajes en pantalla</p>
      ) : (
        <ul className="space-y-2">
          {messages.map((message) => (
            <li key={message.id} className="glass flex items-center gap-3 rounded-lg p-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-accent/20 text-accent">
                <MessageSquare className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{message.text}</p>
                <p className="text-xs text-muted-foreground">{TYPE_LABEL[message.message_type]}</p>
              </div>
              <button
                type="button"
                onClick={() => onToggle(message)}
                className="flex items-center gap-2 rounded-full border border-border px-2 py-1 text-xs transition-colors"
                aria-label={message.is_active ? 'Desactivar mensaje' : 'Activar mensaje'}
              >
                <span
                  className={`h-3 w-3 rounded-full ${message.is_active ? 'bg-success' : 'bg-muted-foreground'}`}
                />
                {message.is_active ? 'Activo' : 'Inactivo'}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
