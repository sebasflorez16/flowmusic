import { useCallback, useEffect, useState } from 'react'

import { Plus } from 'lucide-react'

import { CouponManager } from '@/components/dashboard/CouponManager'
import { MessageManager } from '@/components/dashboard/MessageManager'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { Coupon, DisplayMessage } from '@/lib/types'

/**
 * Página de marketing: cupones de descuento y mensajes en pantalla.
 *
 * Centraliza la gestión de promociones que ven los clientes en la vista móvil
 * y de los mensajes que aparecen como overlay en la TV.
 */
export function MarketingPage() {
  const [coupons, setCoupons] = useState<Coupon[]>([])
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [messageText, setMessageText] = useState('')
  const [messageType, setMessageType] = useState<DisplayMessage['message_type']>('promotion')

  const fetchData = useCallback(async () => {
    try {
      setCoupons(await api<Coupon[]>('/marketing/coupons/'))
    } catch {
      setCoupons([])
    }
    try {
      setMessages(await api<DisplayMessage[]>('/marketing/messages/'))
    } catch {
      setMessages([])
    }
  }, [])

  useEffect(() => {
    void fetchData()
  }, [fetchData])

  /** Crea un mensaje en pantalla (aparece en el celular y la TV). */
  const handleCreateMessage = async () => {
    const text = messageText.trim()
    if (!text) return
    const now = new Date()
    const until = new Date(now.getTime() + 6 * 3600 * 1000) // +6 horas
    try {
      await api<DisplayMessage>('/marketing/messages/', {
        method: 'POST',
        body: JSON.stringify({
          text,
          message_type: messageType,
          valid_from: now.toISOString(),
          valid_until: until.toISOString(),
          is_active: true,
        }),
      })
      setMessageText('')
      await fetchData()
    } catch {
      // El error ya se maneja en el cliente api.
    }
  }

  /** Activa/desactiva un mensaje (para elegir cuáles rotan en pantalla). */
  const handleToggleMessage = async (message: DisplayMessage) => {
    try {
      await api<DisplayMessage>(`/marketing/messages/${message.id}/`, {
        method: 'PATCH',
        body: JSON.stringify({ is_active: !message.is_active }),
      })
      await fetchData()
    } catch {
      // El error ya se maneja en el cliente api.
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cupones de descuento</CardTitle>
        </CardHeader>
        <CardContent>
          <CouponManager coupons={coupons} onCreate={() => { /* TODO: formulario de cupones */ }} />
        </CardContent>
      </Card>

      <div className="space-y-6">
        {/* Formulario para crear mensaje */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Nuevo mensaje en pantalla</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Input
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              placeholder="Ej. 2x1 en cervezas hasta las 9PM"
            />
            <div className="flex items-center gap-2">
              <select
                value={messageType}
                onChange={(e) => setMessageType(e.target.value as DisplayMessage['message_type'])}
                className="neumorphic-inset h-10 flex-1 rounded-md px-3 text-sm"
              >
                <option value="promotion">Promoción</option>
                <option value="birthday">Cumpleaños</option>
                <option value="anniversary">Aniversario</option>
                <option value="happy_hour">Happy Hour</option>
                <option value="custom">Personalizado</option>
              </select>
              <Button onClick={handleCreateMessage}>
                <Plus className="h-4 w-4" /> Crear
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Lista de mensajes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Mensajes activos</CardTitle>
          </CardHeader>
          <CardContent>
            <MessageManager messages={messages} onCreate={() => {}} onToggle={handleToggleMessage} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
