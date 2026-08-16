'use client'

import { Search, Filter, Download } from 'lucide-react'
import { useState } from 'react'

export default function OrdersPage() {
  const [search, setSearch] = useState('')

  const orders = [
    { id: 'ORD-001', date: '2025-01-15', product: 'iPhone 15 Pro', customer: 'Juan López', platform: 'Mercado Libre', amount: '$999', status: 'Entregado' },
    { id: 'ORD-002', date: '2025-01-14', product: 'AirPods Pro', customer: 'María García', platform: 'Amazon', amount: '$249', status: 'En tránsito' },
    { id: 'ORD-003', date: '2025-01-13', product: 'MacBook Air M3', customer: 'Carlos Rodríguez', platform: 'Hotmart', amount: '$1,299', status: 'Pendiente' },
    { id: 'ORD-004', date: '2025-01-12', product: 'iPad Pro 12.9"', customer: 'Ana Martínez', platform: 'Mercado Libre', amount: '$799', status: 'Entregado' },
    { id: 'ORD-005', date: '2025-01-11', product: 'Apple Watch S9', customer: 'Pedro Sánchez', platform: 'Amazon', amount: '$399', status: 'Entregado' },
  ]

  const filteredOrders = orders.filter(order =>
    order.id.toLowerCase().includes(search.toLowerCase()) ||
    order.product.toLowerCase().includes(search.toLowerCase()) ||
    order.customer.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-slate-900">Órdenes</h1>
        <p className="text-slate-600 mt-2">Gestiona todas tus órdenes en un solo lugar</p>
      </div>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search size={18} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por ID, producto o cliente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg font-medium text-slate-900 transition-colors">
          <Filter size={18} />
          Filtrar
        </button>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
          <Download size={18} />
          Exportar
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">ID</th>
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">Fecha</th>
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">Producto</th>
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">Cliente</th>
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">Plataforma</th>
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">Monto</th>
                <th className="text-left py-3 px-4 text-slate-600 font-semibold">Estado</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4 font-mono text-slate-900 font-medium">{order.id}</td>
                  <td className="py-3 px-4 text-slate-600">{order.date}</td>
                  <td className="py-3 px-4 text-slate-900 font-medium">{order.product}</td>
                  <td className="py-3 px-4 text-slate-600">{order.customer}</td>
                  <td className="py-3 px-4 text-slate-600">{order.platform}</td>
                  <td className="py-3 px-4 text-slate-900 font-semibold">{order.amount}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      order.status === 'Entregado' ? 'bg-green-100 text-green-700' :
                      order.status === 'En tránsito' ? 'bg-blue-100 text-blue-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {order.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">Mostrando {filteredOrders.length} de {orders.length} órdenes</p>
        <div className="flex gap-2">
          <button className="px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50">Anterior</button>
          <button className="px-3 py-2 bg-blue-600 text-white rounded-lg">1</button>
          <button className="px-3 py-2 border border-slate-200 rounded-lg hover:bg-slate-50">Siguiente</button>
        </div>
      </div>
    </div>
  )
}
