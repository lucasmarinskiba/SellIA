'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Ticket, Tag, Check, X, Loader2, Percent, Clock, Copy, CheckCheck } from 'lucide-react'

interface Coupon {
  id: string
  code: string
  discount_percent: number
  description: string
  valid_until: string
  status: 'active' | 'applied' | 'expired'
  plan?: string
  min_amount?: number
}

interface AppliedCoupon extends Coupon {
  applied_at: string
  applied_to?: string
}

const mockAvailableCoupons: Coupon[] = [
  {
    id: 'c1',
    code: 'START50',
    discount_percent: 50,
    description: '50% de descuento en tu primer mes Pro',
    valid_until: '2024-12-31',
    status: 'active',
    plan: 'Pro',
    min_amount: 29.99,
  },
  {
    id: 'c2',
    code: 'UPGRADE25',
    discount_percent: 25,
    description: '25% off al hacer upgrade a Business',
    valid_until: '2024-11-30',
    status: 'active',
    plan: 'Business',
    min_amount: 79.99,
  },
  {
    id: 'c3',
    code: 'FRIEND20',
    discount_percent: 20,
    description: '20% de descuento por referido',
    valid_until: '2025-01-15',
    status: 'active',
  },
]

const mockAppliedCoupons: AppliedCoupon[] = [
  {
    id: 'a1',
    code: 'BIENVENIDO10',
    discount_percent: 10,
    description: '10% de descuento de bienvenida',
    valid_until: '2024-10-01',
    status: 'applied',
    applied_at: '2024-05-15',
    applied_to: 'Plan Starter',
  },
]

function formatCurrency(value: number) {
  return `$${value.toFixed(2)}`
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: 'short', year: 'numeric' })
}

export default function CouponsPage() {
  const [code, setCode] = useState('')
  const [validating, setValidating] = useState(false)
  const [validateResult, setValidateResult] = useState<{
    valid: boolean
    coupon?: Coupon
    newPrice?: number
    originalPrice?: number
    error?: string
  } | null>(null)
  const [appliedCoupons, setAppliedCoupons] = useState<AppliedCoupon[]>(mockAppliedCoupons)
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const handleValidate = async () => {
    if (!code.trim()) return
    setValidating(true)
    setValidateResult(null)
    try {
      const res = await api.post('/coupons/validate', { code: code.trim() })
      const data = res.data
      setValidateResult({
        valid: true,
        coupon: data.coupon,
        newPrice: data.new_price,
        originalPrice: data.original_price,
      })
    } catch (err: any) {
      setValidateResult({
        valid: false,
        error: err.response?.data?.detail || 'Cupón inválido o expirado.',
      })
    } finally {
      setValidating(false)
    }
  }

  const copyCode = (couponCode: string) => {
    navigator.clipboard.writeText(couponCode)
    setCopiedCode(couponCode)
    setTimeout(() => setCopiedCode(null), 2000)
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-pink-500/10">
            <Ticket className="w-6 h-6 text-pink-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Cupones</h1>
            <p className="text-sm text-white/50">Aplicá cupones y ahorrá en tus planes</p>
          </div>
        </div>

        <div className="space-y-8">
          {/* Apply Coupon */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-lg font-semibold text-white mb-4">Aplicar cupón</h2>
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleValidate()}
                  placeholder="Ingresá el código de cupón"
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-pink-500/40 focus:border-pink-500/30 transition-all text-sm"
                />
              </div>
              <button
                onClick={handleValidate}
                disabled={validating || !code.trim()}
                className="px-6 py-3 rounded-xl bg-pink-500/20 text-pink-300 hover:bg-pink-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium inline-flex items-center justify-center gap-2"
              >
                {validating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Aplicar
              </button>
            </div>

            {validateResult && (
              <div className={`mt-4 p-4 rounded-xl border ${
                validateResult.valid
                  ? 'bg-emerald-500/10 border-emerald-500/20'
                  : 'bg-red-500/10 border-red-500/20'
              }`}>
                {validateResult.valid ? (
                  <div className="flex items-start gap-3">
                    <CheckCheck className="w-5 h-5 text-emerald-400 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-emerald-300">¡Cupón válido!</p>
                      {validateResult.coupon && (
                        <p className="text-sm text-white/60 mt-1">
                          {validateResult.coupon.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2">
                        {validateResult.coupon && (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-300 bg-emerald-500/10 px-2 py-1 rounded-lg">
                            <Percent className="w-3 h-3" />
                            {validateResult.coupon.discount_percent}% OFF
                          </span>
                        )}
                        {validateResult.originalPrice !== undefined && validateResult.newPrice !== undefined && (
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-white/40 line-through">{formatCurrency(validateResult.originalPrice)}</span>
                            <span className="text-white font-bold">{formatCurrency(validateResult.newPrice)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-3">
                    <X className="w-5 h-5 text-red-400 mt-0.5" />
                    <p className="text-sm text-red-300">{validateResult.error}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Applied Coupons */}
          <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-lg font-semibold text-white mb-4">Mis cupones aplicados</h2>
            {appliedCoupons.length === 0 ? (
              <div className="text-center py-10 text-white/30 text-sm">
                <Ticket className="w-8 h-8 mx-auto mb-2 opacity-40" />
                <p>No tenés cupones aplicados aún.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {appliedCoupons.map((c) => (
                  <div
                    key={c.id}
                    className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="p-2.5 rounded-lg bg-emerald-500/10">
                        <Check className="w-4 h-4 text-emerald-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{c.code}</p>
                        <p className="text-xs text-white/40">{c.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 sm:justify-end">
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-300 bg-emerald-500/10 px-2 py-1 rounded-lg">
                        <Percent className="w-3 h-3" />
                        {c.discount_percent}% OFF
                      </span>
                      {c.applied_to && (
                        <span className="text-xs text-white/30">{c.applied_to}</span>
                      )}
                      <span className="text-xs text-white/30">{formatDate(c.applied_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Available Coupons */}
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Cupones disponibles</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {mockAvailableCoupons.map((c) => (
                <div
                  key={c.id}
                  className="p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.10] transition-colors group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2.5 rounded-lg bg-pink-500/10">
                      <Tag className="w-4 h-4 text-pink-400" />
                    </div>
                    <button
                      onClick={() => copyCode(c.code)}
                      className="p-2 rounded-lg bg-white/[0.04] text-white/40 hover:text-white/70 hover:bg-white/[0.08] transition-colors"
                      title="Copiar código"
                    >
                      {copiedCode === c.code ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  <p className="text-sm font-medium text-white mb-1">{c.code}</p>
                  <p className="text-xs text-white/50 mb-4">{c.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-pink-300 bg-pink-500/10 px-2 py-1 rounded-lg">
                      <Percent className="w-3 h-3" />
                      {c.discount_percent}% OFF
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] text-white/30">
                      <Clock className="w-3 h-3" />
                      Vence {formatDate(c.valid_until)}
                    </span>
                  </div>
                  {c.plan && (
                    <p className="mt-3 text-[10px] text-white/30">Válido para plan {c.plan}{c.min_amount ? ` · mínimo ${formatCurrency(c.min_amount)}` : ''}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
