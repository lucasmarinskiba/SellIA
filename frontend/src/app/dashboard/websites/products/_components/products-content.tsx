'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Plus, Edit2, Trash2, AlertCircle, Loader, Search, Grid } from 'lucide-react'

interface Product {
  id: string
  name: string
  slug: string
  price: number
  featured_image_url?: string
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  inventory_count: number
  created_at: string
}

export default function ProductsContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const businessId = searchParams.get('businessId') || ''

  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    setMounted(true)
    if (businessId) {
      fetchProducts()
    }
  }, [businessId, statusFilter])

  const fetchProducts = async () => {
    try {
      setLoading(true)
      setError('')

      let url = `/api/v1/businesses/${businessId}/products`
      if (statusFilter) {
        url += `?status=${statusFilter}`
      }

      const res = await fetch(url)
      if (!res.ok) throw new Error('Error cargando productos')

      const data = await res.json()
      setProducts(data.products || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (productId: string) => {
    if (!confirm('¿Eliminar este producto?')) return

    setDeleting(productId)
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/products/${productId}`, {
        method: 'DELETE',
      })

      if (!res.ok) throw new Error('Error eliminando producto')

      setProducts(products.filter((p) => p.id !== productId))
    } catch (err: any) {
      setError(err.message)
    } finally {
      setDeleting(null)
    }
  }

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">Productos</h1>
            <p className="text-lg text-slate-600">Gestiona el catálogo de tu tienda</p>
          </div>
          <Link
            href={`/dashboard/websites/products/create?businessId=${businessId}`}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white font-semibold rounded-lg hover:from-cyan-400 hover:to-cyan-500 transition-all shadow-lg shadow-cyan-500/25"
          >
            <Plus className="w-5 h-5" />
            Nuevo Producto
          </Link>
        </div>

        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 flex gap-4 flex-wrap items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar productos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
            />
          </div>

          <div className="flex gap-2">
            {[
              { label: 'Todos', value: null },
              { label: 'Publicados', value: 'PUBLISHED' },
              { label: 'Borradores', value: 'DRAFT' },
            ].map((filter) => (
              <button
                key={filter.label}
                onClick={() => setStatusFilter(filter.value)}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  statusFilter === filter.value
                    ? 'bg-cyan-500 text-white'
                    : 'bg-white border border-slate-200 text-slate-900 hover:bg-slate-50'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {/* Products grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-20 rounded-lg bg-white border border-slate-200">
            <Grid className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Sin productos</h3>
            <p className="text-slate-600 mb-6">Crea tu primer producto para empezar a vender</p>
            <Link
              href={`/dashboard/websites/products/create?businessId=${businessId}`}
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white font-semibold rounded-lg hover:bg-cyan-600 transition-all"
            >
              <Plus className="w-5 h-5" />
              Crear Producto
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProducts.map((product) => (
              <div
                key={product.id}
                className="rounded-lg bg-white border border-slate-200 shadow-sm hover:shadow-md transition-all overflow-hidden group"
              >
                {/* Image */}
                <div className="relative h-48 bg-slate-100 overflow-hidden">
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

                  {/* Status badge */}
                  <div className="absolute top-3 right-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        product.status === 'PUBLISHED'
                          ? 'bg-emerald-100 text-emerald-700'
                          : product.status === 'DRAFT'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {product.status === 'PUBLISHED' ? 'Publicado' : product.status === 'DRAFT' ? 'Borrador' : 'Archivado'}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <h3 className="font-bold text-slate-900 mb-1 line-clamp-2">{product.name}</h3>
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-2xl font-bold text-cyan-600">${product.price.toFixed(2)}</p>
                    <p className="text-sm text-slate-500">{product.inventory_count} en stock</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex gap-2">
                  <button
                    onClick={() => router.push(`/dashboard/websites/products/${product.id}?businessId=${businessId}`)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded hover:bg-slate-50 transition-all"
                  >
                    <Edit2 className="w-4 h-4" />
                    Editar
                  </button>
                  <button
                    onClick={() => handleDelete(product.id)}
                    disabled={deleting === product.id}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-semibold text-red-700 bg-red-50 border border-red-200 rounded hover:bg-red-100 transition-all disabled:opacity-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    {deleting === product.id ? 'Eliminando...' : 'Eliminar'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
