'use client'

/**
 * Órdenes — las órdenes reales del negocio.
 *
 * Antes listaba cinco órdenes inventadas (iPhone 15 Pro para "Juan López",
 * AirPods para "María García"…) escritas en el propio componente: clientes
 * que no existen, montos que nadie cobró, iguales para cualquier cuenta.
 * Ahora lee GET /businesses/{id}/orders del negocio del usuario.
 */

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { Search, Loader2, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot, formatMoney } from '@/lib/businessSnapshot'

interface OrderRow {
  id: string
  order_number: string | null
  status: string
  payment_status: string
  total: number | string
  customer_email: string | null
  customer_phone: string | null
  created_at: string
}

const STATUS_STYLE: Record<string, string> = {
  delivered: 'bg-green-100 text-green-700',
  shipped: 'bg-blue-100 text-blue-700',
  paid: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  cancelled: 'bg-red-100 text-red-700',
  refunded: 'bg-slate-100 text-slate-700',
}

export default function OrdersPage() {
  const { snapshot, loading: snapLoading } = useBusinessSnapshot()
  const [orders, setOrders] = useState<OrderRow[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const businessId = snapshot?.business.id ?? null

  useEffect(() => {
    if (snapLoading) return
    if (!businessId) { setLoading(false); return }
    let alive = true
    api.get<{ orders: OrderRow[] }>(`/businesses/${businessId}/orders?limit=100`)
      .then(res => { if (alive) setOrders(res.data.orders ?? []) })
      .catch(() => { /* sin tienda / sin órdenes -> lista vacía real */ })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [businessId, snapLoading])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return orders
    return orders.filter(o =>
      (o.order_number ?? o.id).toLowerCase().includes(q) ||
      (o.customer_email ?? '').toLowerCase().includes(q) ||
      o.status.toLowerCase().includes(q)
    )
  }, [orders, search])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Órdenes</h1>
        <p className="text-slate-600 mt-2">
          {snapshot?.business.name
            ? `Órdenes reales de ${snapshot.business.name}`
            : 'Órdenes reales de tu negocio'}
        </p>
      </div>

      {(snapLoading || loading) && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tus órdenes…
        </div>
      )}

      {!snapLoading && !loading && !businessId && (
        <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
          <p className="font-semibold text-slate-900 mb-1">Todavía no tenés un negocio creado</p>
          <p className="text-slate-600 text-sm mb-5">Las órdenes aparecen acá una vez que tengas tu negocio y tu tienda.</p>
          <Link
            href="/sellia-onboarding"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
          >
            Configurar mi negocio <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      )}

      {!snapLoading && !loading && businessId && (
        <>
          <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-4 py-2 max-w-md">
            <Search size={18} className="text-slate-400" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Buscar por número, cliente o estado…"
              className="flex-1 outline-none text-sm text-slate-900"
            />
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-6">
            {orders.length === 0 ? (
              <p className="text-sm text-slate-600">
                No hay órdenes registradas todavía. Cuando entre una venta real, aparece acá con su
                número, cliente, monto y estado — nada de ejemplos.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Orden</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Fecha</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Cliente</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Monto</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Pago</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map(order => (
                      <tr key={order.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-2 font-mono text-slate-900">{order.order_number ?? order.id.slice(0, 8)}</td>
                        <td className="py-3 px-2 text-slate-600">{new Date(order.created_at).toLocaleDateString('es-AR')}</td>
                        <td className="py-3 px-2 text-slate-600">{order.customer_email ?? order.customer_phone ?? '—'}</td>
                        <td className="py-3 px-2 font-semibold text-slate-900">
                          {formatMoney(Number(order.total), snapshot?.revenue.currency ?? null)}
                        </td>
                        <td className="py-3 px-2 text-slate-600">{order.payment_status}</td>
                        <td className="py-3 px-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            STATUS_STYLE[order.status] ?? 'bg-slate-100 text-slate-700'
                          }`}>
                            {order.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filtered.length === 0 && (
                  <p className="text-sm text-slate-500 mt-4">Ninguna orden coincide con la búsqueda.</p>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
