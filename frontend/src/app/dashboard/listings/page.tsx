'use client'

/**
 * Listings — los productos reales publicados por el negocio.
 *
 * Antes mostraba tres productos inventados (iPhone 15 Pro con 12 de stock y
 * 1234 vistas, AirPods, MacBook) escritos a mano en el componente, con
 * ratings y visitas que nadie midió. Ahora lee
 * GET /businesses/{id}/products del negocio del usuario.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus, Loader2, Package, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot, formatMoney } from '@/lib/businessSnapshot'

interface ProductRow {
  id: string
  name: string
  sku: string | null
  price: number | string
  stock_quantity: number | null
  status: string
  track_inventory?: boolean
}

export default function ListingsPage() {
  const { snapshot, loading: snapLoading } = useBusinessSnapshot()
  const [products, setProducts] = useState<ProductRow[]>([])
  const [loading, setLoading] = useState(true)

  const businessId = snapshot?.business.id ?? null

  useEffect(() => {
    if (snapLoading) return
    if (!businessId) { setLoading(false); return }
    let alive = true
    api.get<{ products: ProductRow[] }>(`/businesses/${businessId}/products?limit=100`)
      .then(res => { if (alive) setProducts(res.data.products ?? []) })
      .catch(() => { /* sin tienda / sin productos -> lista vacía real */ })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [businessId, snapLoading])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Listings</h1>
          <p className="text-slate-600 mt-2">
            {products.length > 0
              ? `${products.length} producto(s) publicados en tu tienda`
              : 'Tus productos publicados'}
          </p>
        </div>
        {businessId && (
          <Link href="/dashboard/listings/create" className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">
            <Plus size={18} />
            Nuevo listing
          </Link>
        )}
      </div>

      {(snapLoading || loading) && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tus productos…
        </div>
      )}

      {!snapLoading && !loading && !businessId && (
        <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
          <p className="font-semibold text-slate-900 mb-1">Todavía no tenés un negocio creado</p>
          <p className="text-slate-600 text-sm mb-5">Creá tu negocio para publicar productos.</p>
          <Link
            href="/sellia-onboarding"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
          >
            Configurar mi negocio <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      )}

      {!snapLoading && !loading && businessId && (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          {products.length === 0 ? (
            <div className="text-center py-6">
              <Package className="w-8 h-8 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-900 mb-1">Todavía no publicaste productos</p>
              <p className="text-slate-600 text-sm">
                Cuando cargues uno, aparece acá con su precio y stock reales.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Producto</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">SKU</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Precio</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Stock</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map(p => (
                    <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-2 text-slate-900 font-medium">{p.name}</td>
                      <td className="py-3 px-2 font-mono text-slate-600">{p.sku ?? '—'}</td>
                      <td className="py-3 px-2 font-semibold text-slate-900">
                        {formatMoney(Number(p.price), snapshot?.revenue.currency ?? null)}
                      </td>
                      <td className="py-3 px-2 text-slate-600">
                        {p.track_inventory === false ? 'sin control' : (p.stock_quantity ?? 0)}
                      </td>
                      <td className="py-3 px-2">
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
