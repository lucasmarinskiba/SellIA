'use client'

import { logger } from '@/lib/logger';
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { ordersApi, Order } from '@/lib/orders'
import { shipmentsApi } from '@/lib/shipments'
import { servicesApi } from '@/lib/services'
import Button from '@/components/ui/Button'
import {
  ShoppingCart, Plus, Search, Loader2, Package, Truck, CheckCircle2,
  XCircle, Clock, CreditCard, AlertCircle, Filter, ChevronDown, Calendar
} from 'lucide-react'

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  pending: { label: 'Pendiente', color: '#F59E0B', icon: Clock },
  paid: { label: 'Pagado', color: '#22C55E', icon: CreditCard },
  shipped: { label: 'Enviado', color: '#3B82F6', icon: Truck },
  delivered: { label: 'Entregado', color: '#00D4AA', icon: CheckCircle2 },
  cancelled: { label: 'Cancelado', color: '#EF4444', icon: XCircle },
  refunded: { label: 'Reembolsado', color: '#64748B', icon: AlertCircle },
}

export default function OrdenesPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadOrders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId, statusFilter])

  const loadOrders = async () => {
    setLoading(true)
    try {
      const data = await ordersApi.getOrders(selectedBusinessId, statusFilter ? { status: statusFilter } : undefined)
      setOrders(data)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
    }
  }

  const filteredOrders = orders.filter(o =>
    !search ||
    (o.order_number && o.order_number.toLowerCase().includes(search.toLowerCase())) ||
    (o.customer_name && o.customer_name.toLowerCase().includes(search.toLowerCase())) ||
    (o.customer_email && o.customer_email.toLowerCase().includes(search.toLowerCase()))
  )

  const handleUpdateStatus = async (orderId: string, newStatus: string) => {
    try {
      await ordersApi.updateOrder(orderId, { status: newStatus })
      loadOrders()
    } catch (e) {
      logger.error(String(e))
    }
  }

  const handleCreateShipment = async (order: Order) => {
    try {
      await shipmentsApi.createShipment({
        order_id: order.id,
        carrier: order.shipping_provider || 'local',
        service_type: 'standard',
        package: {
          weight_kg: 1,
          items: order.items?.map((item: any) => ({ name: item.name, qty: item.qty || 1, sku: item.sku })) || [],
        },
        auto_generate_label: true,
        notify_customer: true,
        notification_channel: 'whatsapp',
      })
      alert('Envío creado correctamente')
      loadOrders()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al crear envío')
    }
  }

  const handleScheduleService = async (order: Order) => {
    try {
      // Create service delivery + appointment
      const now = new Date()
      const startTime = new Date(now.getTime() + 24 * 60 * 60 * 1000) // tomorrow
      startTime.setHours(10, 0, 0, 0)
      const endTime = new Date(startTime.getTime() + 60 * 60 * 1000)

      await servicesApi.createDelivery({
        order_id: order.id,
        scheduled_at: startTime.toISOString(),
        modality: 'remote',
        estimated_duration_minutes: 60,
      })

      await servicesApi.createAppointment({
        order_id: order.id,
        client_name: order.customer_name || '',
        client_email: order.customer_email || '',
        client_phone: order.customer_phone || '',
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        service_name: order.items?.[0]?.name || 'Servicio',
        modality: 'remote',
      })

      // Update order status
      await ordersApi.updateOrder(order.id, { status: 'shipped' })

      alert('Servicio agendado correctamente. Revisa la Agenda para ajustar la fecha/hora.')
      loadOrders()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al agendar servicio')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShoppingCart className="w-6 h-6 text-brand-orange" />
            Órdenes
          </h1>
          <p className="text-sm text-white/40 mt-1">Gestiona tus ventas, pagos y envíos.</p>
        </div>
        <div className="flex items-center gap-2">
          {businesses.length > 0 && (
            <select
              value={selectedBusinessId}
              onChange={e => setSelectedBusinessId(e.target.value)}
              className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
            >
              {businesses.map(b => (
                <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar por número, cliente, email..."
            className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
        >
          <option value="" className="bg-[#0A0E1A]">Todos los estados</option>
          {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
            <option key={key} value={key} className="bg-[#0A0E1A]">{cfg.label}</option>
          ))}
        </select>
      </div>

      {/* Orders Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-white/30">
          <Loader2 className="w-6 h-6 animate-spin mr-2" />
          Cargando órdenes...
        </div>
      ) : (
        <div className="border border-white/[0.06] rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Orden</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Cliente</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Items</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Total</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Estado</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Pago</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Canal</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Fecha</th>
                  <th className="text-left px-4 py-3 text-white/30 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((order) => {
                  const statusCfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.pending
                  const StatusIcon = statusCfg.icon
                  return (
                    <motion.tr
                      key={order.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                    >
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">{order.order_number || `#${order.id.slice(0, 8)}`}</p>
                        {order.external_platform && (
                          <p className="text-[10px] text-white/30 uppercase">{order.external_platform}</p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white/70">{order.customer_name || '—'}</p>
                        <p className="text-[10px] text-white/30">{order.customer_email || ''}</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white/70">{order.items?.length || 0} items</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white font-medium">${Number(order.total_amount).toLocaleString()}</p>
                        <p className="text-[10px] text-white/30">{order.currency}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium"
                          style={{ background: `${statusCfg.color}15`, color: statusCfg.color }}
                        >
                          <StatusIcon className="w-3 h-3" />
                          {statusCfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${order.payment_status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : order.payment_status === 'pending' ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400'}`}>
                          {order.payment_status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[10px] text-white/40 uppercase">{order.source_channel || 'manual'}</span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white/40 text-xs">{new Date(order.created_at).toLocaleDateString('es-AR')}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {order.status === 'pending' && (
                            <button onClick={() => handleUpdateStatus(order.id, 'paid')} className="px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-[10px] hover:bg-emerald-500/20 transition-colors">Pagar</button>
                          )}
                          {order.status === 'paid' && (
                            <>
                              <button onClick={() => handleUpdateStatus(order.id, 'shipped')} className="px-2 py-1 rounded-lg bg-blue-500/10 text-blue-400 text-[10px] hover:bg-blue-500/20 transition-colors">Enviar</button>
                              <button onClick={() => handleCreateShipment(order)} className="px-2 py-1 rounded-lg bg-orange-500/10 text-orange-400 text-[10px] hover:bg-orange-500/20 transition-colors flex items-center gap-1">
                                <Truck className="w-3 h-3" /> Crear envío
                              </button>
                              <button onClick={() => handleScheduleService(order)} className="px-2 py-1 rounded-lg bg-violet-500/10 text-violet-400 text-[10px] hover:bg-violet-500/20 transition-colors flex items-center gap-1">
                                <Calendar className="w-3 h-3" /> Agendar servicio
                              </button>
                            </>
                          )}
                          {order.status === 'shipped' && (
                            <button onClick={() => handleUpdateStatus(order.id, 'delivered')} className="px-2 py-1 rounded-lg bg-teal-500/10 text-teal-400 text-[10px] hover:bg-teal-500/20 transition-colors">Entregar</button>
                          )}
                          {(order.status === 'pending' || order.status === 'paid') && (
                            <button onClick={() => handleUpdateStatus(order.id, 'cancelled')} className="px-2 py-1 rounded-lg bg-red-500/10 text-red-400 text-[10px] hover:bg-red-500/20 transition-colors">Cancelar</button>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {filteredOrders.length === 0 && (
            <div className="text-center py-12">
              <Package className="w-10 h-10 text-white/10 mx-auto mb-3" />
              <p className="text-sm text-white/30">No hay órdenes aún</p>
              <p className="text-xs text-white/20 mt-1">Las órdenes aparecerán cuando se registren ventas</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
