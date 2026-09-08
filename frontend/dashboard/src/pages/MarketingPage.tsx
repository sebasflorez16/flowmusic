import { useEffect, useState } from 'react'

import { CouponManager } from '@/components/dashboard/CouponManager'
import { MessageManager } from '@/components/dashboard/MessageManager'
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

  useEffect(() => {
    void api<Coupon[]>('/marketing/coupons/')
      .then(setCoupons)
      .catch(() => setCoupons([]))
    void api<DisplayMessage[]>('/marketing/messages/')
      .then(setMessages)
      .catch(() => setMessages([]))
  }, [])

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cupones de descuento</CardTitle>
        </CardHeader>
        <CardContent>
          <CouponManager coupons={coupons} onCreate={() => { /* TODO: abrir formulario */ }} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Mensajes en pantalla</CardTitle>
        </CardHeader>
        <CardContent>
          <MessageManager messages={messages} onCreate={() => { /* TODO: abrir formulario */ }} />
        </CardContent>
      </Card>
    </div>
  )
}
