import { BarChart3, Clock, Music2, TrendingUp, Users } from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { GlassCard } from '@/components/layout/GlassCard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { RequestsByDay, StatsSummary } from '@/lib/types'

interface StatsWidgetProps {
  /** Resumen de métricas agregadas. */
  summary: StatsSummary
  /** Serie temporal de peticiones por día para el gráfico. */
  requestsByDay: RequestsByDay[]
}

/**
 * Widget de estadísticas rápidas del dashboard.
 *
 * Muestra tarjetas de métricas clave (peticiones, canciones, tiempo de espera y
 * ventas estimadas) y un gráfico de barras con las peticiones por día usando
 * Recharts.
 */
export function StatsWidget({ summary, requestsByDay }: StatsWidgetProps) {
  const metrics = [
    { label: 'Peticiones totales', value: summary.total_requests, icon: Users },
    { label: 'Aprobadas', value: summary.approved_requests, icon: Music2 },
    { label: 'Canciones reproducidas', value: summary.songs_played, icon: BarChart3 },
    { label: 'Espera promedio', value: `${summary.avg_wait_seconds}s`, icon: Clock },
  ]

  return (
    <div className="space-y-4">
      {/* Tarjetas de métricas */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {metrics.map(({ label, value, icon: Icon }) => (
          <GlassCard key={label} icon={<Icon className="h-5 w-5" />}>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-1 text-2xl font-bold tabular-nums">{value}</p>
          </GlassCard>
        ))}

        {/* Ventas estimadas */}
        <GlassCard icon={<TrendingUp className="h-5 w-5 text-secondary" />}>
          <p className="text-sm text-muted-foreground">Ventas estimadas</p>
          <p className="mt-1 text-2xl font-bold tabular-nums text-gradient">
            ${Number(summary.estimated_sales).toLocaleString('es-CO')}
          </p>
        </GlassCard>
      </div>

      {/* Gráfico de peticiones por día */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Peticiones por día</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          {requestsByDay.length === 0 ? (
            <div className="grid h-full place-items-center text-sm text-muted-foreground">
              Sin datos todavía
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={requestsByDay} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} allowDecimals={false} />
                <Tooltip
                  cursor={{ fill: 'hsla(var(--primary) / 0.08)' }}
                  contentStyle={{
                    background: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: 'var(--radius)',
                  }}
                />
                <Bar dataKey="requests" name="Peticiones" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
