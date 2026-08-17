'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, AlertCircle, Loader, CheckCircle2 } from 'lucide-react'

/* ============================================================
   CHECKOUT — Secure checkout flow
   ============================================================ */

interface CheckoutForm {
  customer_email: string
  customer_phone: string
  shipping_address: {
    street: string
    city: string
    state: string
    zip: string
    country: string
  }
  billing_address: {
    street: string
    city: string
    state: string
    zip: string
    country: string
  }
  notes: string
  same_as_shipping: boolean
}

interface Order {
  id: string
  order_number: string
  total: number
  status: string
}

export default function Checkout() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const websiteId = params.website_id as string
  const sessionId = searchParams.get('session_id') || ''

  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)
  const [order, setOrder] = useState<Order | null>(null)

  const [form, setForm] = useState<CheckoutForm>({
    customer_email: '',
    customer_phone: '',
    shipping_address: {
      street: '',
      city: '',
      state: '',
      zip: '',
      country: '',
    },
    billing_address: {
      street: '',
      city: '',
      state: '',
      zip: '',
      country: '',
    },
    notes: '',
    same_as_shipping: true,
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProcessing(true)
    setError('')

    try {
      const checkoutData = {
        customer_email: form.customer_email,
        customer_phone: form.customer_phone,
        shipping_address: form.shipping_address,
        billing_address: form.same_as_shipping ? form.shipping_address : form.billing_address,
        notes: form.notes,
      }

      const res = await fetch(
        `/api/v1/websites/${websiteId}/checkout?session_id=${sessionId}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(checkoutData),
        }
      )

      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Error procesando orden')
      }

      const orderData = await res.json()
      setOrder(orderData)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setProcessing(false)
    }
  }

  const updateAddress = (
    field: keyof CheckoutForm['shipping_address'],
    value: string
  ) => {
    setForm((prev) => ({
      ...prev,
      shipping_address: {
        ...prev.shipping_address,
        [field]: value,
      },
      billing_address: prev.same_as_shipping
        ? {
            ...prev.shipping_address,
            [field]: value,
          }
        : prev.billing_address,
    }))
  }

  if (!mounted) return null

  // Success screen
  if (order) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-6">
        <div className="rounded-lg bg-white border border-slate-200 p-12 max-w-md text-center">
          <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-slate-900 mb-2">¡Orden Confirmada!</h1>
          <p className="text-slate-600 mb-6">
            Gracias por tu compra. Tu número de orden es{' '}
            <span className="font-mono font-bold text-slate-900">{order.order_number}</span>
          </p>

          <div className="rounded-lg bg-slate-50 p-4 mb-6">
            <p className="text-sm text-slate-600 mb-1">Total</p>
            <p className="text-3xl font-bold text-cyan-600">${order.total.toFixed(2)}</p>
          </div>

          <p className="text-sm text-slate-600 mb-6">
            Te hemos enviado un email de confirmación. El estado de tu orden se actualizará próximamente.
          </p>

          <Link
            href={`/storefront/${websiteId}/products`}
            className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white font-semibold rounded-lg hover:bg-cyan-600 transition-all w-full justify-center"
          >
            Volver a la Tienda
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 text-white py-6">
        <div className="max-w-2xl mx-auto px-6">
          <Link href={`/storefront/${websiteId}/cart`} className="inline-flex items-center gap-2 text-slate-300 hover:text-white mb-4">
            <ArrowLeft className="w-4 h-4" />
            Volver al Carrito
          </Link>
          <h1 className="text-3xl font-bold">Checkout</h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">
        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Info */}
          <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
            <h2 className="text-xl font-bold text-slate-900">Información de Contacto</h2>

            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">Email</label>
              <input
                type="email"
                value={form.customer_email}
                onChange={(e) => setForm({ ...form, customer_email: e.target.value })}
                required
                className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">Teléfono</label>
              <input
                type="tel"
                value={form.customer_phone}
                onChange={(e) => setForm({ ...form, customer_phone: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>
          </div>

          {/* Shipping Address */}
          <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
            <h2 className="text-xl font-bold text-slate-900">Dirección de Envío</h2>

            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">Calle</label>
              <input
                type="text"
                value={form.shipping_address.street}
                onChange={(e) => updateAddress('street', e.target.value)}
                required
                className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">Ciudad</label>
                <input
                  type="text"
                  value={form.shipping_address.city}
                  onChange={(e) => updateAddress('city', e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">Provincia/Estado</label>
                <input
                  type="text"
                  value={form.shipping_address.state}
                  onChange={(e) => updateAddress('state', e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">Código Postal</label>
                <input
                  type="text"
                  value={form.shipping_address.zip}
                  onChange={(e) => updateAddress('zip', e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">País</label>
                <input
                  type="text"
                  value={form.shipping_address.country}
                  onChange={(e) => updateAddress('country', e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                />
              </div>
            </div>
          </div>

          {/* Billing Address */}
          <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.same_as_shipping}
                onChange={(e) => setForm({ ...form, same_as_shipping: e.target.checked })}
                className="w-4 h-4"
              />
              <span className="font-semibold text-slate-900">La dirección de facturación es igual a la de envío</span>
            </label>

            {!form.same_as_shipping && (
              <div className="space-y-5 pt-4">
                <h2 className="text-lg font-bold text-slate-900">Dirección de Facturación</h2>
                {/* Billing address form would go here */}
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="rounded-lg bg-white border border-slate-200 p-6">
            <label className="block text-sm font-semibold text-slate-900 mb-2">Notas (opcional)</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Instrucciones de entrega, etc."
              className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 resize-none h-20"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={processing}
            className="w-full px-6 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white font-bold text-lg rounded-lg hover:from-cyan-400 hover:to-cyan-500 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {processing ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Procesando...
              </>
            ) : (
              'Completar Orden'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
