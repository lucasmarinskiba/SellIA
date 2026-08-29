'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Trash2, ArrowLeft, Loader, AlertCircle } from 'lucide-react'

/* ============================================================
   SHOPPING CART — Customer shopping cart review
   ============================================================ */

interface CartItem {
  id: string
  product_id: string
  product_name: string
  variant_name?: string
  quantity: number
  unit_price: number
  line_total: number
}

interface Cart {
  id: string
  items: CartItem[]
  subtotal: number
  tax: number
  shipping: number
  discount: number
  total: number
}

export default function ShoppingCart() {
  const params = useParams()
  const router = useRouter()
  const websiteId = params?.website_id as string

  const [cart, setCart] = useState<Cart | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)

  useEffect(() => {
    setMounted(true)
    if (websiteId) {
      fetchCart()
    }
  }, [websiteId])

  const fetchCart = async () => {
    try {
      setLoading(true)
      const sessionId = localStorage.getItem('session_id')
      if (!sessionId) {
        throw new Error('Carrito vacío')
      }

      const res = await fetch(`/api/v1/websites/${websiteId}/cart?session_id=${sessionId}`)
      if (!res.ok) throw new Error('Error cargando carrito')

      const data = await res.json()
      setCart(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveItem = async (itemId: string) => {
    const sessionId = localStorage.getItem('session_id')
    if (!sessionId) return

    setRemoving(itemId)
    try {
      const res = await fetch(
        `/api/v1/websites/${websiteId}/cart/remove/${itemId}?session_id=${sessionId}`,
        { method: 'POST' }
      )

      if (!res.ok) throw new Error('Error removiendo item')

      const updated = await res.json()
      setCart(updated)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setRemoving(null)
    }
  }

  const handleCheckout = () => {
    const sessionId = localStorage.getItem('session_id')
    router.push(`/storefront/${websiteId}/checkout?session_id=${sessionId}`)
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 text-white py-6">
        <div className="max-w-7xl mx-auto px-6">
          <Link href={`/storefront/${websiteId}/products`} className="inline-flex items-center gap-2 text-slate-300 hover:text-white mb-4">
            <ArrowLeft className="w-4 h-4" />
            Continuar Comprando
          </Link>
          <h1 className="text-3xl font-bold">Carrito de Compras</h1>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : !cart || cart.items.length === 0 ? (
          <div className="text-center py-20 rounded-lg bg-white border border-slate-200">
            <p className="text-lg text-slate-600 mb-6">Tu carrito está vacío</p>
            <Link
              href={`/storefront/${websiteId}/products`}
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white font-semibold rounded-lg hover:bg-cyan-600 transition-all"
            >
              <ArrowLeft className="w-4 h-4" />
              Ver Productos
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Items */}
            <div className="lg:col-span-2">
              <div className="rounded-lg bg-white border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
                  <h2 className="font-bold text-slate-900">{cart.items.length} artículos</h2>
                </div>

                <div className="divide-y divide-slate-200">
                  {cart.items.map((item) => (
                    <div key={item.id} className="px-6 py-6 flex gap-4 hover:bg-slate-50 transition-colors">
                      {/* Product info */}
                      <div className="flex-1">
                        <h3 className="font-bold text-slate-900 mb-1">{item.product_name}</h3>
                        {item.variant_name && (
                          <p className="text-sm text-slate-600 mb-2">{item.variant_name}</p>
                        )}
                        <p className="text-sm text-slate-600">
                          {item.quantity}x ${item.unit_price.toFixed(2)}
                        </p>
                      </div>

                      {/* Price & Actions */}
                      <div className="text-right space-y-2">
                        <p className="font-bold text-lg text-slate-900">
                          ${item.line_total.toFixed(2)}
                        </p>
                        <button
                          onClick={() => handleRemoveItem(item.id)}
                          disabled={removing === item.id}
                          className="flex items-center justify-center gap-2 px-3 py-1 text-sm text-red-700 bg-red-50 border border-red-200 rounded hover:bg-red-100 transition-all disabled:opacity-50"
                        >
                          <Trash2 className="w-4 h-4" />
                          {removing === item.id ? 'Removiendo...' : 'Remover'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="h-fit">
              <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-4">
                <h3 className="font-bold text-lg text-slate-900">Resumen</h3>

                <div className="space-y-2 border-b border-slate-200 pb-4">
                  <div className="flex justify-between text-slate-600">
                    <span>Subtotal</span>
                    <span>${cart.subtotal.toFixed(2)}</span>
                  </div>
                  {cart.discount > 0 && (
                    <div className="flex justify-between text-emerald-600 font-semibold">
                      <span>Descuento</span>
                      <span>-${cart.discount.toFixed(2)}</span>
                    </div>
                  )}
                  {cart.shipping > 0 && (
                    <div className="flex justify-between text-slate-600">
                      <span>Envío</span>
                      <span>${cart.shipping.toFixed(2)}</span>
                    </div>
                  )}
                  {cart.tax > 0 && (
                    <div className="flex justify-between text-slate-600">
                      <span>Impuestos</span>
                      <span>${cart.tax.toFixed(2)}</span>
                    </div>
                  )}
                </div>

                <div className="flex justify-between text-xl font-bold text-slate-900">
                  <span>Total</span>
                  <span className="text-cyan-600">${cart.total.toFixed(2)}</span>
                </div>

                <button
                  onClick={handleCheckout}
                  className="w-full px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white font-bold rounded-lg hover:from-cyan-400 hover:to-cyan-500 transition-all"
                >
                  Proceder al Pago
                </button>

                <Link
                  href={`/storefront/${websiteId}/products`}
                  className="w-full text-center px-6 py-2 border border-slate-200 text-slate-900 font-semibold rounded-lg hover:bg-slate-50 transition-all"
                >
                  Continuar Comprando
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
