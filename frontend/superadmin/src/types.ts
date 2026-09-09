/** Tipos del panel del superadmin. */

export type Role = 'superadmin' | 'socio'

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

export interface LoginResponse {
  access: string
  role: Role
  email: string
}
