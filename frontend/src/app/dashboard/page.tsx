'use client'

/**
 * Dashboard — números reales de la cuenta.
 *
 * Antes esta pantalla saludaba "Bienvenido de vuelta, Juan" y mostraba
 * "$47,300 de ingresos (+12%) · 234 órdenes · 89 listings · 4.2% conversión"
 * junto a órdenes inventadas (iPhone 15 Pro, AirPods, MacBook) — constantes
 * en el código, idénticas para cualquiera que abriera la página. Todo lo que
 * se ve acá ahora sale del snapshot real de la cuenta y de sus órdenes reales.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { DollarSign, ShoppingCart, MessageSquare, Bot, Loader2, ExternalLink } from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot, formatMoney } from '@/lib/businessSnapshot'

interface StorefrontOrder {
  id: string
  order_number: string | null
  status: string
  payment_status: string
  total: number | string
  customer_email: string | null
  created_at: string
}

const STATUS_STYLE: Record<string, string> = {
  delivered: 'bg-green-100 text-green-700',
  shipped: 'bg-blue-100 text-blue-700',
  paid: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  cancelled: 'bg-red-100 text-red-700',
}

export default function DashboardHome() {
  const { snapshot, loading, unavailable } = useBusinessSnapshot()
  const [orders, setOrders] = useState<StorefrontOrder[]>([])
  const [ordersLoaded, setOrdersLoaded] = useState(false)

  const businessId = snapshot?.business.id ?? null

  useEffect(() => {
    if (!businessId) { setOrdersLoaded(true); return }
    let alive = true
    api.get<{ orders: StorefrontOrder[] }>(`/businesses/${businessId}/orders?limit=5`)
      .then(res => { if (alive) setOrders(res.data.orders ?? []) })
      .catch(() => { /* sin órdenes o sin tienda -> tabla vacía, nunca inventada */ })
      .finally(() => { if (alive) setOrdersLoaded(true) })
    return () => { alive = false }
  }, [businessId])

  const rev = snapshot?.revenue
  const conv = snapshot?.conversations

  const stats = [
    {
      label: 'Cobrado (órdenes pagadas)',
      value: rev ? formatMoney(rev.paid_amount, rev.currency) : '—',
      hint: rev ? `${rev.orders_paid} de ${rev.orders_total} órdenes` : '',
      icon: DollarSign,
    },
    {
      label: 'Órdenes registradas',
      value: rev ? String(rev.orders_total) : '—',
      hint: rev ? `${formatMoney(rev.gross_amount, rev.currency)} facturados` : '',
      icon: ShoppingCart,
    },
    {
      label: 'Conversaciones',
      value: conv ? String(conv.total) : '—',
      hint: conv && conv.inbound > 0 ? `${conv.response_rate}% respondidas` : 'sin consultas todavía',
      icon: MessageSquare,
    },
    {
      label: 'Respondidas por la IA',
      value: conv ? String(conv.ai_answered) : '—',
      hint: conv && conv.answered > 0 ? `${conv.ai_share}% de las respuestas` : 'la IA todavía no respondió',
      icon: Bot,
    },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-2">
          {snapshot?.business.name
            ? `Estado real de ${snapshot.business.name}`
            : 'Estado real de tu cuenta'}
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tus datos…
        </div>
      )}

      {!loading && unavailable && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
          <p className="text-sm text-slate-600 mt-1">
            Iniciá sesión para ver tus números. No se muestran cifras de ejemplo.
          </p>
        </div>
      )}

      {!loading && !unavailable && snapshot && (
        <>
          {!snapshot.verification.has_business && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="font-semibold text-slate-900">Todavía no configuraste tu negocio</p>
                <p className="text-sm text-slate-600 mt-1">
                  Hasta entonces todos los números son cero de verdad, no un ejemplo.
                </p>
              </div>
              <Link
                href="/sellia-onboarding"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
              >
                Configurar <ExternalLink className="w-4 h-4" />
              </Link>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => {
              const Icon = stat.icon
              return (
                <div key={stat.label} className="bg-white rounded-lg border border-slate-200 p-6">
                  <Icon className="text-slate-400 mb-4" size={24} />
                  <p className="text-slate-600 text-sm mb-1">{stat.label}</p>
                  <p className="text-2xl font-black text-slate-900">{stat.value}</p>
                  {stat.hint && <p className="text-xs text-slate-500 mt-1">{stat.hint}</p>}
                </div>
              )
            })}
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Órdenes recientes</h2>
            {!ordersLoaded ? (
              <p className="text-sm text-slate-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Leyendo órdenes…
              </p>
            ) : orders.length === 0 ? (
              <p className="text-sm text-slate-600">
                No hay órdenes registradas todavía. Cuando entre una venta real por tu tienda o por un
                canal conectado, aparece acá con su número, monto y estado.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Orden</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Cliente</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Fecha</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Monto</th>
                      <th className="text-left py-2 px-2 text-slate-600 font-medium">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((order) => (
                      <tr key={order.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-2 font-mono text-slate-900">{order.order_number ?? order.id.slice(0, 8)}</td>
                        <td className="py-3 px-2 text-slate-600">{order.customer_email ?? '—'}</td>
                        <td className="py-3 px-2 text-slate-600">
                          {new Date(order.created_at).toLocaleDateString('es-AR')}
                        </td>
                        <td className="py-3 px-2 font-semibold text-slate-900">
                          {formatMoney(Number(order.total), snapshot.revenue.currency)}
                        </td>
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
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
