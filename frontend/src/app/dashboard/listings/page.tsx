'use client'

/**
 * Listings — el catálogo real del negocio (agentes/servicios/productos).
 *
 * Antes mostraba tres productos inventados (iPhone 15 Pro con 12 de stock y
 * 1234 vistas, AirPods, MacBook) escritos a mano en el componente, luego se
 * cambió a leer GET /businesses/{id}/products -- pero ese modelo (storefront
 * de /dashboard/websites/products) no tiene clasificación de tipo. Ahora lee
 * GET /catalog/{id}/items, el catálogo real (CatalogItemType: service/good/
 * digital) que también alimenta el contexto de negocio del SellIA Assistant.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus, Loader2, Package, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot, formatMoney } from '@/lib/businessSnapshot'

type CatalogItemType = 'service' | 'good' | 'digital'

interface CatalogItemRow {
  id: string
  type: CatalogItemType
  name: string
  price: number | string
  currency: string
  stock: number | null
  is_available: boolean
  extra_data: Record<string, unknown>
}

const TYPE_LABEL: Record<CatalogItemType, string> = { service: 'Servicio', good: 'Físico', digital: 'Digital' }
const TYPE_COLOR: Record<CatalogItemType, string> = {
  service: 'bg-purple-100 text-purple-700',
  good: 'bg-blue-100 text-blue-700',
  digital: 'bg-emerald-100 text-emerald-700',
}

export default function ListingsPage() {
  const { snapshot, loading: snapLoading } = useBusinessSnapshot()
  const [items, setItems] = useState<CatalogItemRow[]>([])
  const [loading, setLoading] = useState(true)

  const businessId = snapshot?.business.id ?? null

  useEffect(() => {
    if (snapLoading) return
    if (!businessId) { setLoading(false); return }
    let alive = true
    api.get<CatalogItemRow[]>(`/catalog/${businessId}/items`)
      .then(res => { if (alive) setItems(res.data ?? []) })
      .catch(() => { /* sin negocio / sin catálogo -> lista vacía real */ })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [businessId, snapLoading])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Listings</h1>
          <p className="text-slate-600 mt-2">
            {items.length > 0
              ? `${items.length} producto(s)/servicio(s) en tu catálogo`
              : 'Tu catálogo de productos y servicios'}
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
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tu catálogo…
        </div>
      )}

      {!snapLoading && !loading && !businessId && (
        <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
          <p className="font-semibold text-slate-900 mb-1">Todavía no tenés un negocio creado</p>
          <p className="text-slate-600 text-sm mb-5">Creá tu negocio para publicar productos y servicios.</p>
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
          {items.length === 0 ? (
            <div className="text-center py-6">
              <Package className="w-8 h-8 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-900 mb-1">Todavía no cargaste nada en tu catálogo</p>
              <p className="text-slate-600 text-sm">
                Cuando cargues un producto o servicio, aparece acá con su precio, tipo y plataforma reales.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Producto/Servicio</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Tipo</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Plataforma</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Precio</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Stock</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(it => (
                    <tr key={it.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-2 text-slate-900 font-medium">{it.name}</td>
                      <td className="py-3 px-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${TYPE_COLOR[it.type]}`}>
                          {TYPE_LABEL[it.type]}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-slate-600">
                        {typeof it.extra_data?.source_platform === 'string' ? it.extra_data.source_platform : 'Sin especificar'}
                      </td>
                      <td className="py-3 px-2 font-semibold text-slate-900">
                        {formatMoney(Number(it.price), it.currency)}
                      </td>
                      <td className="py-3 px-2 text-slate-600">
                        {it.type === 'good' ? (it.stock ?? 0) : '—'}
                      </td>
                      <td className="py-3 px-2">
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                          {it.is_available ? 'Disponible' : 'Pausado'}
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
