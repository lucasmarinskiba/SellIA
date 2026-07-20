import { api } from './api'

export interface SubscriptionPlan {
  id: string
  name: string
  slug: string
  description: string | null
  price_monthly_ars: number | null
  price_yearly_ars: number | null
  price_monthly_usd: number | null
  price_yearly_usd: number | null
  price_monthly_latam_usd: number | null
  price_yearly_latam_usd: number | null
  limits: Record<string, any>
  features: string[]
  is_active: boolean
  display_order: number
  billing_cycle_options: string[]
  target_regions: string[]
  trial_days: number
}

export interface Subscription {
  id: string
  user_id: string
  plan_id: string
  status: string
  current_period_start: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  billing_cycle: string
  payment_provider: string | null
  next_billing_date: string | null
  auto_renew: boolean
  trial_ends_at: string | null
  mercadopago_preapproval_id: string | null
  plan: SubscriptionPlan
}

export interface UsageReport {
  period_month: string
  plan_slug: string
  usage: {
    metric: string
    used: number
    limit: number
    unlimited: boolean
    remaining: number | string
  }[]
}

export interface CheckoutRequest {
  plan_slug: string
  billing_cycle: 'monthly' | 'yearly'
  payment_provider: 'mercadopago' | 'bank_transfer' | 'crypto'
  crypto_network?: 'trc20' | 'bep20'
}

export interface BankTransferOrder {
  id: string
  user_id: string
  order_number: string
  amount: number
  currency: string
  alias: string | null
  cbu: string | null
  account_holder: string | null
  instructions: string | null
  status: string
  expires_at: string
  created_at: string
}

export interface CancellationRequest {
  reason_category: 'price' | 'competitor' | 'no_usage' | 'bugs' | 'missing_feature' | 'support' | 'trial' | 'other'
  reason_text?: string
  competitor_name?: string
  improvement_suggestion?: string
  rating_nps?: number
}

export interface CancellationFeedback {
  id: string
  user_id: string
  reason_category: string
  reason_text: string | null
  competitor_name: string | null
  improvement_suggestion: string | null
  rating_nps: number | null
  cancelled_at: string
}

export interface PreapprovalResponse {
  preapproval_id: string | null
  init_point: string | null
  sandbox_init_point: string | null
  status: string
}

export interface PreapprovalStatusResponse {
  preapproval_id: string
  status: string
  plan_slug: string
  billing_cycle: string
  next_payment_date: string | null
}

export interface RetentionSummary {
  total_cancellations: number
  cancellations_this_month: number
  churn_rate_percent: number
  avg_nps: number | null
  top_reasons: { reason: string; count: number }[]
  top_competitors: { name: string; count: number }[]
}

export interface RevenueSummary {
  mrr: number
  arr: number
  revenue_this_month: number
  revenue_by_provider: Record<string, number>
  pending_transfers_count: number
  active_subscriptions_count: number
}

export interface AdminSubscription {
  id: string
  user_id: string
  user_email: string | null
  user_full_name: string | null
  plan_id: string
  plan_name: string
  plan_slug: string
  status: string
  billing_cycle: string
  payment_provider: string | null
  next_billing_date: string | null
  current_period_end: string | null
  auto_renew: boolean
  created_at: string
}

export interface CheckoutResponse {
  preference_id?: string
  init_point?: string
  sandbox_init_point?: string
  session_id?: string
  client_secret?: string
  public_key?: string
}

export interface CryptoPaymentRequest {
  plan_slug: string
  billing_cycle: 'monthly' | 'yearly'
  crypto_network: 'trc20' | 'bep20'
}

export interface CryptoPaymentResponse {
  transaction_id: string
  wallet_address: string
  amount_usdt: number
  network: string
  qr_code_url: string | null
  expires_at: string
  status: string
}

export interface CryptoPaymentStatusResponse {
  transaction_id: string
  status: string
  confirmations: number
  tx_hash: string | null
  completed_at: string | null
  amount_received: number | null
}

export interface RegionDetectResponse {
  detected_country: string | null
  detected_region: string
  suggested_currency: string
}

export interface Invoice {
  id: string
  invoice_number: string
  invoice_type: string
  amount: number
  currency: string
  total_amount: number
  plan_name: string | null
  status: string
  pdf_url: string | null
  created_at: string
}

export const subscriptionsApi = {
  listPlans: (region?: string, cycle?: string) =>
    api.get<SubscriptionPlan[]>('/subscriptions/plans', { params: { region, cycle } }).then(r => r.data),

  getMySubscription: () =>
    api.get<Subscription>('/subscriptions/my-subscription').then(r => r.data),

  getMyUsage: () =>
    api.get<UsageReport>('/subscriptions/my-usage').then(r => r.data),

  createCheckout: (data: CheckoutRequest) =>
    api.post<CheckoutResponse>('/subscriptions/create-checkout', data).then(r => r.data),

  createCryptoPayment: (data: CryptoPaymentRequest) =>
    api.post<CryptoPaymentResponse>('/subscriptions/create-crypto-payment', data).then(r => r.data),

  getCryptoPaymentStatus: (transactionId: string) =>
    api.get<CryptoPaymentStatusResponse>(`/subscriptions/crypto-payment/${transactionId}/status`).then(r => r.data),

  detectRegion: () =>
    api.get<RegionDetectResponse>('/subscriptions/region-detect').then(r => r.data),

  updateUserRegion: (data: { country_code: string; preferred_currency: string; timezone?: string }) =>
    api.put('/subscriptions/user-region', data).then(r => r.data),

  getInvoices: () =>
    api.get<Invoice[]>('/subscriptions/invoices').then(r => r.data),

  downloadInvoice: (invoiceId: string) =>
    api.get(`/subscriptions/invoices/${invoiceId}/download`).then(r => r.data),

  updateBillingDetails: (data: { tax_id?: string; billing_address?: Record<string, any>; full_name?: string }) =>
    api.put('/subscriptions/billing-details', data).then(r => r.data),
}


export const bankTransferApi = {
  createOrder: (data: { plan_slug: string; billing_cycle: string; currency: string }) =>
    api.post<BankTransferOrder>('/subscriptions/create-bank-transfer', data).then(r => r.data),

  confirmOrder: (orderId: string, data: { proof_image_url?: string }) =>
    api.post<BankTransferOrder>(`/subscriptions/confirm-bank-transfer/${orderId}`, data).then(r => r.data),
}

export const preapprovalApi = {
  create: (data: { plan_slug: string; billing_cycle: string }) =>
    api.post<PreapprovalResponse>('/subscriptions/preapproval', data).then(r => r.data),

  getStatus: (preapprovalId: string) =>
    api.get<PreapprovalStatusResponse>(`/subscriptions/preapproval/${preapprovalId}/status`).then(r => r.data),

  cancel: (preapprovalId: string) =>
    api.delete(`/subscriptions/preapproval/${preapprovalId}`).then(r => r.data),
}

export const cancellationApi = {
  cancel: (data: CancellationRequest) =>
    api.post<CancellationFeedback>('/subscriptions/cancel', data).then(r => r.data),
}

export const adminApi = {
  getRevenue: () =>
    api.get<RevenueSummary>('/subscriptions/admin/revenue').then(r => r.data),

  getBankTransfers: (params?: { status?: string; date_from?: string; date_to?: string; page?: number; limit?: number }) =>
    api.get<BankTransferOrder[]>('/subscriptions/admin/bank-transfers', { params }).then(r => r.data),

  getSubscriptions: (params?: { plan_slug?: string; provider?: string; status?: string; page?: number; limit?: number }) =>
    api.get<AdminSubscription[]>('/subscriptions/admin/subscriptions', { params }).then(r => r.data),

  approveTransfer: (orderId: string, data: { approved: boolean; notes?: string }) =>
    api.post(`/subscriptions/admin/approve-bank-transfer/${orderId}`, data).then(r => r.data),

  getFeedbacks: () =>
    api.get<CancellationFeedback[]>('/subscriptions/admin/feedbacks').then(r => r.data),

  getRetention: () =>
    api.get<RetentionSummary>('/subscriptions/admin/retention').then(r => r.data),
}
