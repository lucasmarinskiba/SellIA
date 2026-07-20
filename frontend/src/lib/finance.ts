import { api } from './api'

export interface SalesInvoice {
  id: string
  business_id: string
  order_id: string | null
  conversation_id: string | null
  invoice_number: string
  status: string
  amount: number
  tax_amount: number
  total_amount: number
  currency: string
  due_date: string
  paid_at: string | null
  paid_amount: number
  customer_name: string | null
  customer_email: string | null
  customer_phone: string | null
  items: any[]
  created_at: string
}

export interface PaymentReminder {
  id: string
  business_id: string
  order_id: string
  invoice_id: string | null
  conversation_id: string | null
  reminder_level: number
  status: string
  scheduled_at: string
  sent_at: string | null
  message_content: string | null
  channel_platform: string
  response_received: boolean
  created_at: string
}

export interface ARSnapshot {
  id: string
  business_id: string
  snapshot_date: string
  total_outstanding: number
  total_overdue: number
  invoice_count: number
  overdue_count: number
  customer_breakdown: any[]
  created_at: string
}

export interface TaxConfig {
  id: string
  business_id: string
  country_code: string
  tax_name: string
  tax_rate: number
  tax_id_number: string | null
  is_tax_exempt: boolean
  extra_data: Record<string, any>
  created_at: string
}

export interface FinanceAutopilotStatus {
  business_id: string
  is_active: boolean
  is_paused: boolean
  paused_reason: string | null
  auto_deliver_invoices: boolean
  auto_run_dunning: boolean
  auto_reconcile_payments: boolean
  auto_generate_tax_reports: boolean
  dunning_channel: string
  max_dunning_level: number
}

export interface TaxReport {
  period: string
  total_invoiced: number
  total_net: number
  iva_debito: number
  iva_credito: number
  saldo: number
  tax_rate: number
  invoice_count: number
  currency: string
}

export interface CashFlowForecast {
  days: number
  total_receivables: number
  pipeline_weighted: number
  daily_projection: Array<{
    date: string
    projected_inflow: number
    confidence_low: number
    confidence_high: number
  }>
  currency: string
}

export interface DunningPipeline {
  level_1: { label: string; count: number; amount: number }
  level_2: { label: string; count: number; amount: number }
  level_3: { label: string; count: number; amount: number }
  level_4: { label: string; count: number; amount: number }
}

export interface FinanceDashboard {
  business_id: string
  total_receivables: number
  overdue_amount: number
  invoice_count: number
  overdue_count: number
  dunning_active: number
  forecast_summary: {
    date: string
    projected_inflow: number
    confidence_low: number
    confidence_high: number
  } | null
  tax_status: {
    period: string
    saldo: number
    invoice_count: number
  }
  collection_rate: number
  autopilot_active: boolean
  currency: string
}

export const financeApi = {
  getInvoices: (businessId: string, status?: string) =>
    api.get<SalesInvoice[]>(`/businesses/${businessId}/finance/invoices`, { params: { status } }).then(r => r.data),

  createInvoice: (businessId: string, data: Partial<SalesInvoice>) =>
    api.post<SalesInvoice>(`/businesses/${businessId}/finance/invoices`, data).then(r => r.data),

  getPendingReminders: (businessId: string) =>
    api.get<PaymentReminder[]>(`/businesses/${businessId}/finance/reminders/pending`).then(r => r.data),

  generateARSnapshot: (businessId: string) =>
    api.post<ARSnapshot>(`/businesses/${businessId}/finance/ar-snapshot`).then(r => r.data),

  getTaxConfig: (businessId: string) =>
    api.get<TaxConfig | null>(`/businesses/${businessId}/finance/tax-config`).then(r => r.data),

  // Autopilot
  getAutopilotStatus: (businessId: string) =>
    api.get<FinanceAutopilotStatus>(`/businesses/${businessId}/finance/autopilot/status`).then(r => r.data),

  toggleAutopilot: (businessId: string) =>
    api.post<{ is_active: boolean; message: string }>(`/businesses/${businessId}/finance/autopilot/toggle`).then(r => r.data),

  triggerDelivery: (businessId: string) =>
    api.post<{ delivered: number }>(`/businesses/${businessId}/finance/autopilot/trigger-delivery`).then(r => r.data),

  triggerDunning: (businessId: string) =>
    api.post<{ reminders_sent: number }>(`/businesses/${businessId}/finance/autopilot/trigger-dunning`).then(r => r.data),

  getDashboard: (businessId: string) =>
    api.get<FinanceDashboard>(`/businesses/${businessId}/finance/autopilot/dashboard`).then(r => r.data),

  getCashFlow: (businessId: string, days?: number) =>
    api.get<CashFlowForecast>(`/businesses/${businessId}/finance/autopilot/cash-flow`, { params: { days } }).then(r => r.data),

  getTaxReport: (businessId: string, month?: number, year?: number) =>
    api.get<TaxReport>(`/businesses/${businessId}/finance/autopilot/tax-report`, { params: { month, year } }).then(r => r.data),

  getDunningPipeline: (businessId: string) =>
    api.get<DunningPipeline>(`/businesses/${businessId}/finance/autopilot/dunning-pipeline`).then(r => r.data),
}
