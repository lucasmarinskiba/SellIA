'use client'

import { ArrowLeft, Clock, MapPin, Truck, CheckCircle, MessageSquare, Edit2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { use, useState } from 'react'

export default function OrderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const [note, setNote] = useState('')

  const order = {
    id,
    date: '2025-01-15',
    status: 'Entregado',
    statusColor: 'bg-green-100 text-green-700',
    customer: {
      name: 'Juan López',
      email: 'juan@example.com',
      phone: '+54 9 11 1234-5678',
    },
    shipping: {
      address: 'Calle Principal 123, CABA, Argentina',
      method: 'Envío express',
      cost: '$50',
      carrier: 'Andreani',
      trackingNumber: 'AR123456789',
    },
    items: [
      { id: 1, name: 'iPhone 15 Pro', sku: 'IPHONE-15-PRO', qty: 1, price: '$999', total: '$999' },
    ],
    timeline: [
      { date: '2025-01-15 14:30', status: 'Entregado', icon: CheckCircle },
      { date: '2025-01-15 10:00', status: 'En tránsito', icon: Truck },
      { date: '2025-01-14 16:00', status: 'Enviado', icon: Truck },
      { date: '2025-01-15 08:00', status: 'Pagado', icon: Clock },
    ],
    subtotal: '$999',
    shipping_cost: '$50',
    tax: '$224.75',
    total: '$1,273.75',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <div>
          <h1 className="text-3xl font-black text-slate-900">Orden #{order.id}</h1>
          <p className="text-slate-600 mt-1">{order.date}</p>
        </div>
        <div className="ml-auto">
          <span className={`px-4 py-2 rounded-full font-medium text-sm ${order.statusColor}`}>
            {order.status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Items */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="font-bold text-slate-900 mb-4">Productos</h2>
            <div className="space-y-3">
              {order.items.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                  <div>
                    <p className="font-medium text-slate-900">{item.name}</p>
                    <p className="text-xs text-slate-500">SKU: {item.sku}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-slate-900">{item.total}</p>
                    <p className="text-xs text-slate-500">Qty: {item.qty}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="font-bold text-slate-900 mb-4">Estado</h2>
            <div className="space-y-4">
              {order.timeline.map((event, idx) => {
                const Icon = event.icon
                return (
                  <div key={idx} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <Icon size={20} className="text-slate-400 mb-2" />
                      {idx < order.timeline.length - 1 && <div className="w-0.5 h-8 bg-slate-200" />}
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{event.status}</p>
                      <p className="text-xs text-slate-500">{event.date}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Shipping */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <MapPin size={20} />
              Envío
            </h2>
            <div className="space-y-2 text-sm">
              <p className="text-slate-900 font-medium">{order.shipping.address}</p>
              <p className="text-slate-600">Método: {order.shipping.method}</p>
              <p className="text-slate-600">Transportista: {order.shipping.carrier}</p>
              <p className="text-slate-600">Tracking: {order.shipping.trackingNumber}</p>
            </div>
          </div>

          {/* Notes */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <MessageSquare size={20} />
              Notas
            </h2>
            <div className="space-y-3">
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="text-xs text-slate-500 mb-1">15 Ene, 14:30</p>
                <p className="text-sm text-slate-900">Cliente confirmó recepción</p>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Agregar nota..."
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm">
                  Guardar
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Customer */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-bold text-slate-900 mb-4">Cliente</h3>
            <div className="space-y-2 text-sm">
              <p className="text-slate-900 font-medium">{order.customer.name}</p>
              <p className="text-slate-600">{order.customer.email}</p>
              <p className="text-slate-600">{order.customer.phone}</p>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-bold text-slate-900 mb-4">Resumen</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span>{order.subtotal}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Envío</span>
                <span>{order.shipping_cost}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Impuestos</span>
                <span>{order.tax}</span>
              </div>
              <div className="border-t border-slate-200 pt-2 mt-2 flex justify-between font-bold text-slate-900">
                <span>Total</span>
                <span>{order.total}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-bold text-slate-900 mb-4">Acciones</h3>
            <div className="space-y-2">
              <button className="w-full px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 font-medium text-sm text-slate-900">
                Reenviar confirmación
              </button>
              <button className="w-full px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 font-medium text-sm text-slate-900 flex items-center justify-center gap-2">
                <Edit2 size={14} />
                Editar orden
              </button>
              <button className="w-full px-4 py-2 rounded-lg border border-red-200 hover:bg-red-50 font-medium text-sm text-red-700">
                Cancelar orden
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
