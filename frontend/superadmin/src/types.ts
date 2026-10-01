/** Tipos del panel del superadmin. */

export type Role = 'superadmin' | 'socio' | 'vendedor'

export interface Summary {
  income: number
  expenses: number
  profit: number
  mrr: number
  counts: { active: number; past_due: number; canceled: number }
  by_method: Record<string, number>
}

export interface AdminTenant {
  id: number
  name: string
  slug: string
  phone: string
  plan: string
  subscription_status: string
  next_billing_date: string | null
  last_payment: string | null
  max_tables: number
  included_tables: number
}

export interface OverdueBar {
  id: number
  name: string
  plan: string
  phone: string
  next_billing_date: string
  days_overdue: number
}

export interface Staff {
  id: number
  email: string
  role: string
  is_active: boolean
  date_joined: string
}

/** Bar afiliado por un mercaderista. */
export interface VendorBar {
  id: number
  name: string
  plan: string
  subscription_status: string
  monthly_total: number
}

/** Mes liquidado de un mercaderista (ventas + comisión). */
export interface VendorMonth {
  period: string
  sales: number
  commission: number
  paid: boolean
}

/** Panel completo de un mercaderista. */
export interface VendorDashboard {
  id: number
  email: string
  commission_rate: string
  is_active: boolean
  bars_count: number
  bars: VendorBar[]
  current: VendorMonth | null
  history: VendorMonth[]
}

/** Fila de la lista de mercaderistas (gestión). */
export interface VendorSummary {
  id: number
  email: string
  commission_rate: string
  is_active: boolean
  bars_count: number
  month_sales: number
  month_commission: number
  current_period_paid: boolean
}

export interface LoginResponse {
  access: string
  role: Role
  email: string
}
