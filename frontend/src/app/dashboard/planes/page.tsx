'use client'

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { isSafeRedirectUrl } from '@/lib/security'
import {
  subscriptionsApi, SubscriptionPlan, Subscription, UsageReport,
  CheckoutRequest, CryptoPaymentRequest, RegionDetectResponse,
  bankTransferApi, BankTransferOrder, cancellationApi, CancellationRequest,
  preapprovalApi,
} from '@/lib/subscriptions'
import {
  Zap, Crown, Rocket, Building2, Check, Loader2, AlertCircle,
  ExternalLink, BarChart3, Globe, CreditCard, Bitcoin, Calendar,
  ChevronDown, ChevronUp, MapPin, Wallet, Landmark, Building,
  Copy, X, MessageSquare, ThumbsDown, HelpCircle, Clock,
} from 'lucide-react'

const planIcons: Record<string, typeof Zap> = {
  free: Zap,
  starter: Crown,
  pro: Rocket,
  enterprise: Building2,
}

const planColors: Record<string, string> = {
  free: 'text-white/60',
  starter: 'text-brand-orange',
  pro: 'text-brand-violet',
  enterprise: 'text-brand-teal',
}

const REGION_NAMES: Record<string, string> = {
  AR: 'Argentina',
  LATAM: 'Latinoamérica',
  INTL: 'Internacional',
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  ARS: '$',
  USD: 'USD ',
}

export default function PlanesPage() {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [usage, setUsage] = useState<UsageReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [region, setRegion] = useState<string>('AR')
  const [detectedRegion, setDetectedRegion] = useState<RegionDetectResponse | null>(null)
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly')
  const [checkingOut, setCheckingOut] = useState<string | null>(null)
  const [showPaymentModal, setShowPaymentModal] = useState<string | null>(null)
  const [showCryptoModal, setShowCryptoModal] = useState<{
    plan: SubscriptionPlan
    network: 'trc20' | 'bep20'
  } | null>(null)
  const [cryptoPayment, setCryptoPayment] = useState<any>(null)
  const [expandedPlan, setExpandedPlan] = useState<string | null>(null)
  const [showBankTransferModal, setShowBankTransferModal] = useState<SubscriptionPlan | null>(null)
  const [bankTransferOrder, setBankTransferOrder] = useState<BankTransferOrder | null>(null)
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [cancelSubmitting, setCancelSubmitting] = useState(false)
  const [mpRecurring, setMpRecurring] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [plansData, subData, usageData, regionData] = await Promise.all([
        subscriptionsApi.listPlans(),
        subscriptionsApi.getMySubscription(),
        subscriptionsApi.getMyUsage().catch(() => null),
        subscriptionsApi.detectRegion().catch(() => null),
      ])
      setPlans(plansData.sort((a, b) => a.display_order - b.display_order))
      setSubscription(subData)
      setUsage(usageData)
      if (regionData) {
        setDetectedRegion(regionData)
        setRegion(regionData.detected_region)
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar planes')
    } finally {
      setLoading(false)
    }
  }

  const getPlanPrice = useCallback((plan: SubscriptionPlan) => {
    if (region === 'AR') {
      return billingCycle === 'monthly'
        ? plan.price_monthly_ars
        : plan.price_yearly_ars
    }
    if (region === 'LATAM') {
      return billingCycle === 'monthly'
        ? plan.price_monthly_latam_usd
        : plan.price_yearly_latam_usd
    }
    return billingCycle === 'monthly'
      ? plan.price_monthly_usd
      : plan.price_yearly_usd
  }, [region, billingCycle])

  const getCurrency = useCallback(() => {
    return region === 'AR' ? 'ARS' : 'USD'
  }, [region])

  const formatPrice = (plan: SubscriptionPlan) => {
    const price = getPlanPrice(plan)
    if (!price || price === 0) return 'Gratis'
    const symbol = CURRENCY_SYMBOLS[getCurrency()]
    return `${symbol}${Number(price).toLocaleString()}`
  }

  const getMonthlyPrice = (plan: SubscriptionPlan) => {
    if (region === 'AR') return plan.price_monthly_ars
    if (region === 'LATAM') return plan.price_monthly_latam_usd
    return plan.price_monthly_usd
  }

  const handleCheckout = async (planSlug: string, provider: 'mercadopago' | 'bank_transfer') => {
    if (provider === 'bank_transfer') {
      const plan = plans.find(p => p.slug === planSlug)
      if (plan) setShowBankTransferModal(plan)
      return
    }
    setCheckingOut(planSlug)
    try {
      const checkout = await subscriptionsApi.createCheckout({
        plan_slug: planSlug,
        billing_cycle: billingCycle,
        payment_provider: provider,
      })

      if (provider === 'mercadopago' && checkout.init_point && isSafeRedirectUrl(checkout.init_point)) {
        window.location.href = checkout.init_point
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al crear checkout')
    } finally {
      setCheckingOut(null)
      setShowPaymentModal(null)
    }
  }

  const handleCreateBankTransfer = async (plan: SubscriptionPlan) => {
    setCheckingOut(plan.slug)
    try {
      const order = await bankTransferApi.createOrder({
        plan_slug: plan.slug,
        billing_cycle: billingCycle,
        currency: getCurrency(),
      })
      setBankTransferOrder(order)
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al crear orden de transferencia')
    } finally {
      setCheckingOut(null)
    }
  }

  const handleConfirmTransfer = async () => {
    if (!bankTransferOrder) return
    try {
      const updated = await bankTransferApi.confirmOrder(bankTransferOrder.id, {})
      setBankTransferOrder(updated)
      setTimeout(() => {
        setShowBankTransferModal(null)
        setBankTransferOrder(null)
        loadData()
      }, 2000)
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al confirmar')
    }
  }

  const handleCancel = async (data: CancellationRequest) => {
    setCancelSubmitting(true)
    try {
      await cancellationApi.cancel(data)
      setShowCancelModal(false)
      loadData()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al cancelar')
    } finally {
      setCancelSubmitting(false)
    }
  }

  const handleCryptoPayment = async (plan: SubscriptionPlan, network: 'trc20' | 'bep20') => {
    setCheckingOut(plan.slug)
    try {
      const payment = await subscriptionsApi.createCryptoPayment({
        plan_slug: plan.slug,
        billing_cycle: billingCycle,
        crypto_network: network,
      })
      setCryptoPayment(payment)
      setShowCryptoModal({ plan, network })
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al crear pago crypto')
    } finally {
      setCheckingOut(null)
      setShowPaymentModal(null)
    }
  }

  const pollCryptoStatus = useCallback(async () => {
    if (!cryptoPayment) return
    try {
      const status = await subscriptionsApi.getCryptoPaymentStatus(cryptoPayment.transaction_id)
      setCryptoPayment((prev: any) => ({ ...prev, ...status }))
      if (status.status === 'completed') {
        setTimeout(() => {
          setShowCryptoModal(null)
          loadData()
        }, 3000)
      }
    } catch (e) {
      // Silently fail polling
    }
  }, [cryptoPayment])

  useEffect(() => {
    if (!cryptoPayment || cryptoPayment.status === 'completed') return
    const interval = setInterval(pollCryptoStatus, 10000)
    return () => clearInterval(interval)
  }, [cryptoPayment, pollCryptoStatus])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-3">Elige tu plan</h1>
        <p className="text-white/40 max-w-xl mx-auto">
          Empieza gratis y escala según necesites. Precios adaptados a tu región.
        </p>

        {/* Region & Cycle Selectors */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-6">
          {/* Region Badge */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 text-white/60 text-sm">
            <MapPin className="w-4 h-4" />
            <span>{REGION_NAMES[region] || region}</span>
            {detectedRegion && (
              <button
                onClick={() => {
                  if (detectedRegion) {
                    setRegion(detectedRegion.detected_region)
                  }
                }}
                className="text-brand-orange hover:underline text-xs ml-1"
              >
                (auto)
              </button>
            )}
          </div>

          {/* Region Override */}
          <div className="flex items-center gap-1 rounded-xl bg-white/5 p-1">
            {(['AR', 'LATAM', 'INTL'] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRegion(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  region === r ? 'bg-brand-orange text-white' : 'text-white/40 hover:text-white/60'
                }`}
              >
                {r === 'AR' ? '🇦🇷 AR' : r === 'LATAM' ? '🌎 LATAM' : '🌍 INTL'}
              </button>
            ))}
          </div>

          {/* Billing Cycle */}
          <div className="flex items-center gap-1 rounded-xl bg-white/5 p-1">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                billingCycle === 'monthly' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white/60'
              }`}
            >
              Mensual
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
                billingCycle === 'yearly' ? 'bg-brand-orange text-white' : 'text-white/40 hover:text-white/60'
              }`}
            >
              Anual
              <span className="text-[10px] bg-white/20 px-1 rounded">-17%</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Current Plan & Usage */}
      {subscription && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5"
        >
          <div className="flex items-center gap-3 mb-4">
            <BarChart3 className="w-5 h-5 text-brand-orange" />
            <h2 className="text-lg font-semibold text-white">Tu plan actual</h2>
            <span className="ml-auto text-sm font-medium text-brand-orange">{subscription.plan.name}</span>
          </div>
          {usage ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {usage.usage.map((u) => (
                <div key={u.metric} className="p-3 rounded-xl bg-white/5">
                  <p className="text-[10px] text-white/30 uppercase">{u.metric.replace(/_/g, ' ')}</p>
                  <p className="text-sm font-bold text-white mt-1">
                    {u.unlimited ? '∞' : `${u.used} / ${u.limit}`}
                  </p>
                  {!u.unlimited && u.limit > 0 && (
                    <div className="h-1 bg-white/5 rounded-full mt-2 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand-orange transition-all"
                        style={{ width: `${Math.min((u.used / u.limit) * 100, 100)}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-white/30">Sin datos de uso aún</p>
          )}
        </motion.div>
      )}

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {plans.map((plan) => {
          const Icon = planIcons[plan.slug] || Zap
          const isCurrent = subscription?.plan.slug === plan.slug
          const isCheckingOut = checkingOut === plan.slug
          const monthlyPrice = getMonthlyPrice(plan)
          const isExpanded = expandedPlan === plan.slug

          return (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`glass-card p-6 flex flex-col relative ${
                plan.slug === 'starter' ? 'ring-1 ring-brand-orange' : ''
              }`}
            >
              {plan.slug === 'starter' && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-brand-orange text-white text-[10px] font-bold">
                  Más popular
                </div>
              )}

              <div className={`w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-4 ${planColors[plan.slug]}`}>
                <Icon className="w-6 h-6" />
              </div>

              <h3 className="text-xl font-bold text-white">{plan.name}</h3>
              <p className="text-sm text-white/30 mb-4">{plan.description}</p>

              <div className="mb-6">
                <span className="text-3xl font-bold text-white">{formatPrice(plan)}</span>
                <span className="text-white/30 text-sm">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                {billingCycle === 'yearly' && monthlyPrice && (
                  <p className="text-xs text-white/20 mt-1">
                    ${Number(monthlyPrice).toLocaleString()}/mes antes
                  </p>
                )}
              </div>

              <ul className="space-y-3 mb-6 flex-1">
                {plan.features.slice(0, 5).map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm text-white/50">
                    <Check className="w-4 h-4 text-brand-teal shrink-0 mt-0.5" />
                    <span>{feature.replace(/_/g, ' ')}</span>
                  </li>
                ))}
                {plan.features.length > 5 && (
                  <li>
                    <button
                      onClick={() => setExpandedPlan(isExpanded ? null : plan.slug)}
                      className="flex items-center gap-1 text-xs text-white/30 hover:text-white/50 transition-colors"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="w-3 h-3" /> Ver menos
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-3 h-3" /> Ver {plan.features.length - 5} más
                        </>
                      )}
                    </button>
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.ul
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-2 mt-2 overflow-hidden"
                        >
                          {plan.features.slice(5).map((feature) => (
                            <li key={feature} className="flex items-start gap-2.5 text-sm text-white/50">
                              <Check className="w-4 h-4 text-brand-teal shrink-0 mt-0.5" />
                              <span>{feature.replace(/_/g, ' ')}</span>
                            </li>
                          ))}
                        </motion.ul>
                      )}
                    </AnimatePresence>
                  </li>
                )}
              </ul>

              {isCurrent ? (
                <button
                  disabled
                  className="w-full py-2.5 rounded-xl bg-white/10 text-white/40 text-sm font-medium cursor-default"
                >
                  Plan actual
                </button>
              ) : (
                <button
                  onClick={() => {
                    if (plan.price_monthly_ars === 0 && plan.price_monthly_usd === 0) {
                      // Free plan - just select it
                      return
                    }
                    setShowPaymentModal(plan.slug)
                  }}
                  disabled={isCheckingOut}
                  className={`w-full py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    plan.slug === 'starter'
                      ? 'bg-brand-orange text-white hover:bg-brand-orange/90'
                      : 'bg-white/5 text-white hover:bg-white/10'
                  } disabled:opacity-50`}
                >
                  {isCheckingOut ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Procesando...
                    </span>
                  ) : plan.price_monthly_ars === 0 && plan.price_monthly_usd === 0 ? (
                    'Gratis'
                  ) : (
                    'Elegir plan'
                  )}
                </button>
              )}

              {/* Payment Method Modal */}
              <AnimatePresence>
                {showPaymentModal === plan.slug && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                    onClick={() => setShowPaymentModal(null)}
                  >
                    <motion.div
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.95, opacity: 0 }}
                      className="glass-card p-6 w-full max-w-sm mx-4"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <h3 className="text-lg font-bold text-white mb-1">{plan.name}</h3>
                      <p className="text-2xl font-bold text-white mb-4">{formatPrice(plan)}<span className="text-sm text-white/30 font-normal">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span></p>

                      <div className="space-y-2">
                        {region === 'AR' && (
                          <>
                            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5">
                              <button
                                onClick={() => setMpRecurring(false)}
                                className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${!mpRecurring ? 'bg-brand-orange text-white' : 'text-white/40 hover:text-white/60'}`}
                              >
                                Pago único
                              </button>
                              <button
                                onClick={() => setMpRecurring(true)}
                                className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${mpRecurring ? 'bg-brand-orange text-white' : 'text-white/40 hover:text-white/60'}`}
                              >
                                Cobro automático
                              </button>
                            </div>
                            <button
                              onClick={async () => {
                                if (mpRecurring) {
                                  setCheckingOut(plan.slug)
                                  try {
                                    const pre = await preapprovalApi.create({ plan_slug: plan.slug, billing_cycle: billingCycle })
                                    if (pre.init_point && isSafeRedirectUrl(pre.init_point)) window.location.href = pre.init_point
                                  } catch (e: any) {
                                    alert(e.response?.data?.detail || 'Error al crear preapproval')
                                  } finally {
                                    setCheckingOut(null)
                                  }
                                } else {
                                  handleCheckout(plan.slug, 'mercadopago')
                                }
                              }}
                              disabled={checkingOut === plan.slug}
                              className="w-full flex items-center gap-3 p-3 rounded-xl bg-brand-orange/10 hover:bg-brand-orange/20 border border-brand-orange/20 text-white transition-colors"
                            >
                              <Wallet className="w-5 h-5 text-brand-orange" />
                              <span className="text-sm font-medium">
                                {mpRecurring ? 'MercadoPago — Suscripción' : 'MercadoPago'}
                              </span>
                              <span className="ml-auto text-xs text-white/40">ARS</span>
                            </button>
                          </>
                        )}

                        <button
                          onClick={() => handleCheckout(plan.slug, 'bank_transfer')}
                          disabled={isCheckingOut}
                          className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors"
                        >
                          <Building className="w-5 h-5 text-brand-teal" />
                          <span className="text-sm font-medium">Transferencia bancaria</span>
                          <span className="ml-auto text-xs text-white/40">ARS</span>
                        </button>

                        <button
                          onClick={() => handleCryptoPayment(plan, 'trc20')}
                          disabled={isCheckingOut}
                          className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors"
                        >
                          <Bitcoin className="w-5 h-5 text-brand-teal" />
                          <span className="text-sm font-medium">USDT (TRC-20)</span>
                          <span className="ml-auto text-xs text-white/40">Crypto</span>
                        </button>

                        <button
                          onClick={() => handleCryptoPayment(plan, 'bep20')}
                          disabled={isCheckingOut}
                          className="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors"
                        >
                          <Bitcoin className="w-5 h-5 text-brand-violet" />
                          <span className="text-sm font-medium">USDT (BEP-20)</span>
                          <span className="ml-auto text-xs text-white/40">Crypto</span>
                        </button>
                      </div>

                      <button
                        onClick={() => setShowPaymentModal(null)}
                        className="w-full mt-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors"
                      >
                        Cancelar
                      </button>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </div>

      {/* Crypto Payment Modal */}
      <AnimatePresence>
        {showCryptoModal && cryptoPayment && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowCryptoModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card p-6 w-full max-w-md mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-bold text-white mb-1">Pagar con USDT</h3>
              <p className="text-sm text-white/40 mb-4">
                Red: {showCryptoModal.network === 'trc20' ? 'TRC-20 (Tron)' : 'BEP-20 (BNB Smart Chain)'}
              </p>

              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-white/5">
                  <p className="text-xs text-white/30 uppercase mb-1">Monto a enviar</p>
                  <p className="text-2xl font-bold text-white">{cryptoPayment.amount_usdt} USDT</p>
                </div>

                <div className="p-4 rounded-xl bg-white/5">
                  <p className="text-xs text-white/30 uppercase mb-1">Dirección de wallet</p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs text-white/60 break-all font-mono">{cryptoPayment.wallet_address}</code>
                    <button
                      onClick={() => navigator.clipboard.writeText(cryptoPayment.wallet_address)}
                      className="shrink-0 text-xs text-brand-orange hover:underline"
                    >
                      Copiar
                    </button>
                  </div>
                </div>

                {cryptoPayment.status === 'pending' && (
                  <div className="flex items-center gap-2 text-sm text-white/40">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Esperando confirmación de pago...
                  </div>
                )}

                {cryptoPayment.status === 'completed' && (
                  <div className="flex items-center gap-2 text-sm text-brand-teal">
                    <Check className="w-4 h-4" />
                    ¡Pago confirmado! Activando tu plan...
                  </div>
                )}

                <div className="text-xs text-white/20 text-center">
                  Este pago expira en 30 minutos. No cierres esta ventana.
                </div>
              </div>

              <button
                onClick={() => setShowCryptoModal(null)}
                className="w-full mt-4 py-2 text-sm text-white/40 hover:text-white/60 transition-colors"
              >
                Cerrar
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bank Transfer Modal */}
      <AnimatePresence>
        {showBankTransferModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => { setShowBankTransferModal(null); setBankTransferOrder(null) }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="glass-card p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Transferencia bancaria</h3>
                <button onClick={() => { setShowBankTransferModal(null); setBankTransferOrder(null) }} className="text-white/40 hover:text-white/60">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {!bankTransferOrder ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-white/5">
                    <p className="text-sm text-white/40 mb-1">Plan</p>
                    <p className="text-white font-medium">{showBankTransferModal.name}</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {formatPrice(showBankTransferModal)}<span className="text-sm text-white/30 font-normal">/{billingCycle === 'monthly' ? 'mes' : 'año'}</span>
                    </p>
                  </div>
                  <div className="p-4 rounded-xl bg-brand-orange/10 border border-brand-orange/20">
                    <p className="text-sm text-white/60 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Tu orden tiene 48 horas de validez.
                    </p>
                  </div>
                  <button
                    onClick={() => handleCreateBankTransfer(showBankTransferModal)}
                    disabled={checkingOut === showBankTransferModal.slug}
                    className="w-full py-2.5 rounded-xl bg-brand-orange text-white font-medium hover:bg-brand-orange/90 disabled:opacity-50"
                  >
                    {checkingOut === showBankTransferModal.slug ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generando...
                      </span>
                    ) : (
                      'Generar orden de pago'
                    )}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 p-3 rounded-xl bg-brand-teal/10 border border-brand-teal/20">
                    <Check className="w-5 h-5 text-brand-teal" />
                    <div>
                      <p className="text-sm font-medium text-white">Orden generada</p>
                      <p className="text-xs text-white/40">#{bankTransferOrder.order_number}</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="p-3 rounded-xl bg-white/5">
                      <p className="text-xs text-white/30 uppercase">Alias</p>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="text-white font-mono">{bankTransferOrder.alias}</code>
                        <button
                          onClick={() => bankTransferOrder.alias && navigator.clipboard.writeText(bankTransferOrder.alias)}
                          className="text-brand-orange hover:underline text-xs"
                        >
                          Copiar
                        </button>
                      </div>
                    </div>

                    {bankTransferOrder.cbu && (
                      <div className="p-3 rounded-xl bg-white/5">
                        <p className="text-xs text-white/30 uppercase">CBU</p>
                        <div className="flex items-center gap-2 mt-1">
                          <code className="text-white font-mono text-xs">{bankTransferOrder.cbu}</code>
                          <button
                            onClick={() => navigator.clipboard.writeText(bankTransferOrder.cbu!)}
                            className="text-brand-orange hover:underline text-xs"
                          >
                            Copiar
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="p-3 rounded-xl bg-white/5">
                      <p className="text-xs text-white/30 uppercase">Titular</p>
                      <p className="text-white text-sm mt-1">Lucas Daniel Marin</p>
                      <p className="text-white/40 text-xs">CUIL 20-41941012-9</p>
                    </div>

                    <div className="p-3 rounded-xl bg-white/5">
                      <p className="text-xs text-white/30 uppercase">Monto</p>
                      <p className="text-2xl font-bold text-white mt-1">
                        {CURRENCY_SYMBOLS[bankTransferOrder.currency]}{Number(bankTransferOrder.amount).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-brand-orange/5 border border-brand-orange/10">
                    <p className="text-xs text-white/40">
                      <strong className="text-white/60">Importante:</strong> Enviá el comprobante por email a 
                      <a href="mailto:ventas@sellia.com" className="text-brand-orange ml-1">ventas@sellia.com</a>.
                      Activaremos tu plan en 24-48h hábiles.
                    </p>
                  </div>

                  {bankTransferOrder.status === 'pending' && (
                    <button
                      onClick={handleConfirmTransfer}
                      className="w-full py-2.5 rounded-xl bg-white/10 text-white font-medium hover:bg-white/20 transition-colors"
                    >
                      Ya realicé la transferencia
                    </button>
                  )}

                  {bankTransferOrder.status === 'paid' && (
                    <div className="flex items-center gap-2 text-sm text-brand-teal">
                      <Check className="w-4 h-4" />
                      Transferencia confirmada. Pendiente de activación.
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Cancel Subscription Modal */}
      <AnimatePresence>
        {showCancelModal && (
          <CancelModal
            onClose={() => setShowCancelModal(false)}
            onSubmit={handleCancel}
            submitting={cancelSubmitting}
          />
        )}
      </AnimatePresence>

      {/* Cancel Plan -->
      {subscription && subscription.plan.slug !== 'free' && (
        <div className="flex justify-center">
          <button
            onClick={() => setShowCancelModal(true)}
            className="text-sm text-white/20 hover:text-red-400 transition-colors"
          >
            Cancelar suscripción
          </button>
        </div>
      )}

      {/* Enterprise CTA */}
      <div className="glass-card p-8 bg-gradient-to-br from-brand-orange/10 to-brand-violet/10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-xl font-bold text-white mb-2">¿Necesitas algo personalizado?</h3>
            <p className="text-white/40 text-sm">
              Podemos adaptar SellIA a tu empresa con funcionalidades exclusivas, onboarding dedicado y SLA garantizado.
            </p>
          </div>
          <a
            href="mailto:ventas@sellia.com"
            className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/10 text-white text-sm font-medium hover:bg-white/20 transition-colors"
          >
            Hablar con ventas
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  )
}

/* ─── Cancel Subscription Modal ─── */

const CANCEL_REASONS: { value: CancellationRequest['reason_category']; label: string; icon: typeof MessageSquare }[] = [
  { value: 'price', label: 'Es muy caro', icon: CreditCard },
  { value: 'competitor', label: 'Encontré una alternativa', icon: Building2 },
  { value: 'no_usage', label: 'No lo uso lo suficiente', icon: Clock },
  { value: 'bugs', label: 'Problemas técnicos', icon: AlertCircle },
  { value: 'missing_feature', label: 'Me falta una función', icon: HelpCircle },
  { value: 'support', label: 'Soporte insuficiente', icon: MessageSquare },
  { value: 'trial', label: 'Solo quería probarlo', icon: Calendar },
  { value: 'other', label: 'Otro', icon: HelpCircle },
]

function CancelModal({
  onClose,
  onSubmit,
  submitting,
}: {
  onClose: () => void
  onSubmit: (data: CancellationRequest) => void
  submitting: boolean
}) {
  const [reason, setReason] = useState<CancellationRequest['reason_category'] | ''>('')
  const [reasonText, setReasonText] = useState('')
  const [competitor, setCompetitor] = useState('')
  const [improvement, setImprovement] = useState('')
  const [nps, setNps] = useState<number | null>(null)
  const [step, setStep] = useState<1 | 2>(1)

  const canSubmit = reason.length > 0

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="glass-card p-6 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">
            {step === 1 ? '¿Por qué te vas?' : 'Un último paso'}
          </h3>
          <button onClick={onClose} className="text-white/40 hover:text-white/60">
            <X className="w-5 h-5" />
          </button>
        </div>

        {step === 1 ? (
          <div className="space-y-4">
            <p className="text-sm text-white/40">
              Tu suscripción seguirá activa hasta el final del período. Tu feedback nos ayuda a mejorar.
            </p>

            <div className="space-y-2">
              {CANCEL_REASONS.map((r) => {
                const Icon = r.icon
                return (
                  <button
                    key={r.value}
                    onClick={() => setReason(r.value)}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-colors ${
                      reason === r.value
                        ? 'bg-brand-orange/10 border-brand-orange/40 text-white'
                        : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="text-sm">{r.label}</span>
                  </button>
                )
              })}
            </div>

            <textarea
              value={reasonText}
              onChange={(e) => setReasonText(e.target.value)}
              placeholder="Contanos más (opcional)..."
              className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-brand-orange/40 resize-none h-20"
            />

            <button
              onClick={() => setStep(2)}
              disabled={!reason}
              className="w-full py-2.5 rounded-xl bg-brand-orange text-white font-medium hover:bg-brand-orange/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Continuar
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <p className="text-sm text-white/60 mb-2">¿Recomendarías SellIA? (0-10)</p>
              <div className="flex items-center gap-1">
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => (
                  <button
                    key={score}
                    onClick={() => setNps(score)}
                    className={`w-8 h-8 rounded-lg text-xs font-bold transition-colors ${
                      nps === score
                        ? score >= 7
                          ? 'bg-brand-teal text-white'
                          : score >= 4
                          ? 'bg-brand-orange text-white'
                          : 'bg-red-500 text-white'
                        : 'bg-white/5 text-white/40 hover:bg-white/10'
                    }`}
                  >
                    {score}
                  </button>
                ))}
              </div>
            </div>

            {(reason === 'competitor') && (
              <div>
                <p className="text-sm text-white/60 mb-1">¿Qué otra herramienta usás?</p>
                <input
                  value={competitor}
                  onChange={(e) => setCompetitor(e.target.value)}
                  placeholder="Nombre del producto/servicio"
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-brand-orange/40"
                />
              </div>
            )}

            <div>
              <p className="text-sm text-white/60 mb-1">¿Qué podemos mejorar? (opcional)</p>
              <textarea
                value={improvement}
                onChange={(e) => setImprovement(e.target.value)}
                placeholder="Tu sugerencia..."
                className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white text-sm placeholder:text-white/20 focus:outline-none focus:border-brand-orange/40 resize-none h-20"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setStep(1)}
                className="flex-1 py-2.5 rounded-xl bg-white/5 text-white text-sm font-medium hover:bg-white/10 transition-colors"
              >
                Atrás
              </button>
              <button
                onClick={() =>
                  onSubmit({
                    reason_category: reason as CancellationRequest['reason_category'],
                    reason_text: reasonText || undefined,
                    competitor_name: competitor || undefined,
                    improvement_suggestion: improvement || undefined,
                    rating_nps: nps ?? undefined,
                  })
                }
                disabled={submitting}
                className="flex-1 py-2.5 rounded-xl bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                {submitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Cancelando...
                  </span>
                ) : (
                  'Confirmar cancelación'
                )}
              </button>
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}
