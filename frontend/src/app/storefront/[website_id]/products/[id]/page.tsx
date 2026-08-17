'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, ShoppingCart, AlertCircle, Loader, Heart } from 'lucide-react'

/* ============================================================
   PRODUCT DETAIL — Customer product page with add-to-cart
   ============================================================ */

interface Product {
  id: string
  name: string
  price: number
  compare_at_price?: number
  description: string
  short_description?: string
  sku?: string
  featured_image_url?: string
  images: string[]
  inventory_count: number
}

export default function ProductDetail() {
  const params = useParams()
  const websiteId = params.website_id as string
  const productId = params.id as string

  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)
  const [quantity, setQuantity] = useState(1)
  const [adding, setAdding] = useState(false)
  const [imageIndex, setImageIndex] = useState(0)

  useEffect(() => {
    setMounted(true)
    if (websiteId && productId) {
      fetchProduct()
    }
  }, [websiteId, productId])

  const fetchProduct = async () => {
    try {
      setLoading(true)
      const res = await fetch(`/api/v1/businesses/${websiteId}/products/${productId}`)
      if (!res.ok) throw new Error('Producto no encontrado')

      const data = await res.json()
      setProduct(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = async () => {
    if (!product) return

    setAdding(true)
    try {
      // Get or create session ID
      let sessionId = localStorage.getItem('session_id')
      if (!sessionId) {
        sessionId = `session-${Date.now()}`
        localStorage.setItem('session_id', sessionId)
      }

      const res = await fetch(`/api/v1/websites/${websiteId}/cart/add?session_id=${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: product.id,
          quantity: quantity,
        }),
      })

      if (!res.ok) throw new Error('Error agregando al carrito')

      // Show success toast/message
      alert('Producto agregado al carrito')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setAdding(false)
    }
  }

  const calculateDiscount = () => {
    if (!product || !product.compare_at_price || product.compare_at_price <= product.price) {
      return null
    }
    return Math.round(((product.compare_at_price - product.price) / product.compare_at_price) * 100)
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 text-white py-6">
        <div className="max-w-7xl mx-auto px-6">
          <Link href={`/storefront/${websiteId}/products`} className="inline-flex items-center gap-2 text-slate-300 hover:text-white mb-4">
            <ArrowLeft className="w-4 h-4" />
            Volver a Productos
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
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
        ) : product ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {/* Images */}
            <div>
              <div className="mb-4 rounded-lg bg-slate-100 overflow-hidden aspect-square flex items-center justify-center">
                {product.featured_image_url ? (
                  <img
                    src={product.featured_image_url}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-slate-300">Sin imagen</div>
                )}
              </div>

              {/* Thumbnail gallery */}
              {product.images && product.images.length > 0 && (
                <div className="grid grid-cols-4 gap-2">
                  {product.images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => setImageIndex(idx)}
                      className={`aspect-square rounded-lg overflow-hidden border-2 transition-all ${
                        imageIndex === idx ? 'border-cyan-500' : 'border-slate-200'
                      }`}
                    >
                      <img src={img} alt={`${product.name} ${idx}`} className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Info */}
            <div className="space-y-6">
              <div>
                <h1 className="text-4xl font-bold text-slate-900 mb-2">{product.name}</h1>
                <p className="text-slate-600">{product.short_description}</p>
              </div>

              {/* Pricing */}
              <div className="space-y-2">
                <div className="flex items-baseline gap-3">
                  <p className="text-4xl font-bold text-cyan-600">${product.price.toFixed(2)}</p>
                  {product.compare_at_price && (
                    <p className="text-xl text-slate-500 line-through">${product.compare_at_price.toFixed(2)}</p>
                  )}
                </div>

                {calculateDiscount() && (
                  <p className="text-lg font-semibold text-red-600">Ahorras ${(product.compare_at_price! - product.price).toFixed(2)} ({calculateDiscount()}%)</p>
                )}
              </div>

              {/* Stock */}
              <div className="p-4 rounded-lg bg-slate-100">
                {product.inventory_count > 0 ? (
                  <p className="text-sm text-emerald-700 font-semibold">
                    ✓ {product.inventory_count} disponibles
                  </p>
                ) : (
                  <p className="text-sm text-red-700 font-semibold">✗ Producto Agotado</p>
                )}
              </div>

              {/* SKU */}
              {product.sku && (
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                  <p className="text-xs text-slate-600 uppercase mb-1">Código SKU</p>
                  <p className="font-mono text-sm text-slate-900">{product.sku}</p>
                </div>
              )}

              {/* Description */}
              <div className="p-6 rounded-lg bg-white border border-slate-200">
                <h3 className="text-lg font-bold text-slate-900 mb-3">Descripción</h3>
                <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">{product.description}</p>
              </div>

              {/* Add to cart */}
              {product.inventory_count > 0 ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-4">
                    <label className="text-sm font-semibold text-slate-900">Cantidad:</label>
                    <div className="flex items-center gap-2 border border-slate-200 rounded-lg">
                      <button
                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                        className="px-3 py-2 hover:bg-slate-50"
                      >
                        −
                      </button>
                      <span className="px-4 py-2 font-semibold text-slate-900">{quantity}</span>
                      <button
                        onClick={() => setQuantity(Math.min(product.inventory_count, quantity + 1))}
                        className="px-3 py-2 hover:bg-slate-50"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  <button
                    onClick={handleAddToCart}
                    disabled={adding}
                    className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white font-bold text-lg rounded-lg hover:from-cyan-400 hover:to-cyan-500 transition-all disabled:opacity-50"
                  >
                    <ShoppingCart className="w-5 h-5" />
                    {adding ? 'Agregando...' : 'Agregar al Carrito'}
                  </button>
                </div>
              ) : (
                <button
                  disabled
                  className="w-full px-6 py-4 bg-slate-300 text-slate-600 font-bold text-lg rounded-lg cursor-not-allowed"
                >
                  Producto Agotado
                </button>
              )}

              {/* Wishlist */}
              <button className="w-full flex items-center justify-center gap-2 px-6 py-3 border-2 border-slate-200 text-slate-900 font-semibold rounded-lg hover:border-slate-300 transition-all">
                <Heart className="w-5 h-5" />
                Agregar a Favoritos
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-20">
            <p className="text-slate-600">Producto no encontrado</p>
          </div>
        )}
      </div>
    </div>
  )
}
