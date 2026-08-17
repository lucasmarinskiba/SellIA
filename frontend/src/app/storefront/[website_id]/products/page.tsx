'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { ShoppingCart, Search, Grid, Loader, AlertCircle } from 'lucide-react'

/* ============================================================
   STOREFRONT PRODUCTS — Customer product listing
   ============================================================ */

interface Product {
  id: string
  name: string
  price: number
  compare_at_price?: number
  featured_image_url?: string
  short_description?: string
  inventory_count: number
}

export default function StorefrontProducts() {
  const params = useParams()
  const websiteId = params.website_id as string

  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    setMounted(true)
    if (websiteId) {
      fetchProducts()
    }
  }, [websiteId])

  const fetchProducts = async () => {
    try {
      setLoading(true)
      const res = await fetch(`/api/v1/businesses/${websiteId}/products?status=PUBLISHED`)
      if (!res.ok) throw new Error('Error cargando productos')

      const data = await res.json()
      setProducts(data.products || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const calculateDiscount = (price: number, compareAt?: number) => {
    if (!compareAt || compareAt <= price) return null
    return Math.round(((compareAt - price) / compareAt) * 100)
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 text-white py-12">
        <div className="max-w-7xl mx-auto px-6">
          <h1 className="text-4xl font-bold mb-2">Tienda Online</h1>
          <p className="text-lg text-slate-300">Descubre nuestros productos</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-12">
        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Search */}
        <div className="mb-8">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar productos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-20 rounded-lg bg-white border border-slate-200">
            <Grid className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Sin productos disponibles</h3>
            <p className="text-slate-600">Vuelve pronto para ver nuestras ofertas</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {filteredProducts.map((product) => {
              const discount = calculateDiscount(product.price, product.compare_at_price)
              return (
                <Link
                  key={product.id}
                  href={`/storefront/${websiteId}/products/${product.id}`}
                  className="rounded-lg bg-white border border-slate-200 shadow-sm hover:shadow-lg transition-all overflow-hidden group"
                >
                  {/* Image */}
                  <div className="relative h-56 bg-slate-100 overflow-hidden">
                    {product.featured_image_url ? (
                      <img
                        src={product.featured_image_url}
                        alt={product.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Grid className="w-12 h-12 text-slate-300" />
                      </div>
                    )}

                    {/* Discount badge */}
                    {discount && (
                      <div className="absolute top-3 right-3 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                        -{discount}%
                      </div>
                    )}

                    {/* Stock status */}
                    {product.inventory_count === 0 && (
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                        <span className="bg-red-500 text-white px-4 py-2 rounded-lg font-semibold">
                          Agotado
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <h3 className="font-bold text-slate-900 mb-2 line-clamp-2 group-hover:text-cyan-600 transition-colors">
                      {product.name}
                    </h3>

                    <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                      {product.short_description}
                    </p>

                    {/* Price */}
                    <div className="flex items-baseline gap-2 mb-4">
                      <p className="text-2xl font-bold text-cyan-600">${product.price.toFixed(2)}</p>
                      {product.compare_at_price && (
                        <p className="text-sm text-slate-500 line-through">
                          ${product.compare_at_price.toFixed(2)}
                        </p>
                      )}
                    </div>

                    {/* Add to cart button */}
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        // Cart logic will be handled on product detail page
                      }}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-cyan-500 text-white font-semibold rounded-lg hover:bg-cyan-600 transition-all disabled:opacity-50"
                      disabled={product.inventory_count === 0}
                    >
                      <ShoppingCart className="w-4 h-4" />
                      {product.inventory_count > 0 ? 'Ver Producto' : 'Agotado'}
                    </button>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
