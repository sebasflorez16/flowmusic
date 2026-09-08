import { Ticket } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Coupon } from '@/lib/types'

interface CouponManagerProps {
  /** Cupones del tenant. */
  coupons: Coupon[]
  /** Callback para crear un cupón nuevo (abre un formulario en la página). */
  onCreate: () => void
}

/**
 * Lista de cupones de descuento.
 *
 * Muestra código, descripción, descuento, vigencia y usos de cada cupón. El
 * botón "Crear cupón" delega en la página de Marketing para abrir el formulario.
 */
export function CouponManager({ coupons, onCreate }: CouponManagerProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{coupons.length} cupones</p>
        <Button size="sm" onClick={onCreate}>
          Crear cupón
        </Button>
      </div>

      {coupons.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">No hay cupones creados</p>
      ) : (
        <ul className="space-y-2">
          {coupons.map((coupon) => (
            <li key={coupon.id} className="glass flex items-center gap-3 rounded-lg p-3">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-secondary/20 text-secondary">
                <Ticket className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold">{coupon.code}</p>
                <p className="truncate text-xs text-muted-foreground">{coupon.description}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-gradient">
                  {coupon.discount_type === 'percentage'
                    ? `${coupon.value}%`
                    : `$${Number(coupon.value).toLocaleString('es-CO')}`}
                </p>
                <p className="text-xs text-muted-foreground">
                  {coupon.used_count}/{coupon.max_uses ?? '∞'} usos
                </p>
              </div>
              <Badge variant={coupon.is_active ? 'success' : 'muted'}>
                {coupon.is_active ? 'Activo' : 'Inactivo'}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
