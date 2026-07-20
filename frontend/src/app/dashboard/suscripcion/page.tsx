'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import {
  subscriptionsApi, Subscription, Invoice,
  preapprovalApi, PreapprovalStatusResponse,
} from '@/lib/subscriptions'
import {
  CreditCard, Calendar, Loader2, AlertCircle, CheckCircle2,
  XCircle, RefreshCcw, FileText, Zap,
} from 'lucide-react'

export default function SuscripcionPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [preapproval, setPreapproval] = useState<PreapprovalStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
      return
    }
    if (user) {
      loadData()
    }
  }, [authLoading, user, router])

  const loadData = async () => {
    setLoading(true)
    try {
      const [subData, invData] = await Promise.all([
        subscriptionsApi.getMySubscription(),
        subscriptionsApi.getInvoices().catch(() => []),
      ])
      setSubscription(subData)
      setInvoices(invData)

      // Fetch preapproval status if exists
      if (subData.mercadopago_preapproval_id) {
        try {
          const pa = await preapprovalApi.getStatus(subData.mercadopago_preapproval_id)
          setPreapproval(pa)
        } catch {
          setPreapproval(null)
        }
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar suscripción')
    } finally {
      setLoading(false)
    }
  }

  const handleCancelPreapproval = async () => {
    if (!subscription?.mercadopago_preapproval_id) return
    if (!confirm('¿Cancelar el cobro automático? Tu suscripción seguirá activa hasta el final del período.')) return

    setCancelling(true)
    try {
      await preapprovalApi.cancel(subscription.mercadopago_preapproval_id)
      loadData()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al cancelar')
    } finally {
      setCancelling(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  if (!subscription) {
    return (
      <div className="text-center py-20">
        <AlertCircle className="w-12 h-12 text-white/20 mx-auto mb-4" />
        <p className="text-white/40">No se encontró información de suscripción</p>
      </div>
    )
  }

  const plan = subscription.plan
  const isMpRecurring = subscription.payment_provider === 'mercadopago' && subscription.auto_renew && subscription.mercadopago_preapproval_id

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Tu suscripción</h1>
        <p className="text-white/40">Gestioná tu plan y métodos de pago</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Current Plan Card */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
            <Zap className="w-6 h-6 text-brand-orange" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{plan.name}</h2>
            <p className="text-sm text-white/40">
              {subscription.status === 'active' ? 'Activa' : subscription.status}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-3 rounded-xl bg-white/5">
            <p className="text-xs text-white/30 uppercase">Ciclo de facturación</p>
            <p className="text-white font-medium capitalize">{subscription.billing_cycle === 'monthly' ? 'Mensual' : 'Anual'}</p>
          </div>
          <div className="p-3 rounded-xl bg-white/5">
            <p className="text-xs text-white/30 uppercase">Método de pago</p>
            <p className="text-white font-medium">
              {subscription.payment_provider === 'mercadopago' ? 'MercadoPago' :
               subscription.payment_provider === 'bank_transfer' ? 'Transferencia bancaria' :
               subscription.payment_provider === 'crypto' ? 'USDT Crypto' : '—'}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-white/5">
            <p className="text-xs text-white/30 uppercase">Período actual</p>
            <p className="text-white font-medium">
              {subscription.current_period_start ? new Date(subscription.current_period_start).toLocaleDateString('es-AR') : '—'}
              {' → '}
              {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString('es-AR') : '—'}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-white/5">
            <p className="text-xs text-white/30 uppercase">Renovación automática</p>
            <p className="text-white font-medium flex items-center gap-1.5">
              {subscription.auto_renew ? (
                <><CheckCircle2 className="w-3.5 h-3.5 text-brand-teal" /> Activada</>
              ) : (
                <><XCircle className="w-3.5 h-3.5 text-red-400" /> Desactivada</>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Preapproval Status */}
      {isMpRecurring && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-4">
            <CreditCard className="w-5 h-5 text-brand-orange" />
            <h3 className="text-base font-semibold text-white">Cobro automático MercadoPago</h3>
          </div>

          {preapproval ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <span className="text-sm text-white/40">Estado</span>
                <span className={`text-sm font-medium ${
                  preapproval.status === 'authorized' ? 'text-brand-teal' : 'text-amber-400'
                }`}>
                  {preapproval.status === 'authorized' ? 'Activo' : preapproval.status}
                </span>
              </div>
              {preapproval.next_payment_date && (
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                  <span className="text-sm text-white/40">Próximo cobro</span>
                  <span className="text-sm text-white font-medium">
                    {new Date(preapproval.next_payment_date).toLocaleDateString('es-AR')}
                  </span>
                </div>
              )}
              <button
                onClick={handleCancelPreapproval}
                disabled={cancelling}
                className="w-full py-2.5 rounded-xl bg-white/5 text-white/60 text-sm font-medium hover:bg-red-500/10 hover:text-red-400 transition-colors disabled:opacity-50"
              >
                {cancelling ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Cancelando...
                  </span>
                ) : (
                  'Cancelar cobro automático'
                )}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-white/40">
              <Loader2 className="w-4 h-4 animate-spin" />
              Cargando estado...
            </div>
          )}
        </div>
      )}

      {/* Invoices */}
      {invoices.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center gap-3 mb-4">
            <FileText className="w-5 h-5 text-brand-teal" />
            <h3 className="text-base font-semibold text-white">Facturas</h3>
          </div>
          <div className="space-y-2">
            {invoices.map((inv) => (
              <div key={inv.id} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                <div>
                  <p className="text-sm text-white font-medium">{inv.invoice_number}</p>
                  <p className="text-xs text-white/40">{inv.plan_name || 'SellIA'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-white font-medium">{inv.currency === 'ARS' ? '$' : 'USD '}{inv.total_amount.toLocaleString()}</p>
                  <p className="text-xs text-white/40">{new Date(inv.created_at).toLocaleDateString('es-AR')}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cancel at period end indicator */}
      {subscription.cancel_at_period_end && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm text-center">
          <RefreshCcw className="w-4 h-4 inline mr-1" />
          Tu suscripción no se renovará al final del período actual.
        </div>
      )}
    </div>
  )
}
