'use client'

import { TrendingUp, DollarSign, ShoppingCart, Package } from 'lucide-react'

export default function DashboardHome() {
  const stats = [
    { label: 'Ingresos (30d)', value: '$47,300', change: '+12%', icon: DollarSign },
    { label: 'Órdenes', value: '234', change: '+8%', icon: ShoppingCart },
    { label: 'Listings activos', value: '89', change: '+3%', icon: Package },
    { label: 'Tasa de conversión', value: '4.2%', change: '+0.5%', icon: TrendingUp },
  ]

  const recentOrders = [
    { id: 'ORD-001', product: 'iPhone 15 Pro', platform: 'Mercado Libre', amount: '$999', status: 'Entregado' },
    { id: 'ORD-002', product: 'AirPods Pro', platform: 'Amazon', amount: '$249', status: 'En tránsito' },
    { id: 'ORD-003', product: 'MacBook Air M3', platform: 'Hotmart', amount: '$1,299', status: 'Pendiente' },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-2">Bienvenido de vuelta, Juan</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="bg-white rounded-lg border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <Icon className="text-slate-400" size={24} />
                <span className="text-sm text-green-600 font-medium">{stat.change}</span>
              </div>
              <p className="text-slate-600 text-sm mb-1">{stat.label}</p>
              <p className="text-2xl font-black text-slate-900">{stat.value}</p>
            </div>
          )
        })}
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4">Órdenes recientes</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-2 px-2 text-slate-600 font-medium">ID</th>
                <th className="text-left py-2 px-2 text-slate-600 font-medium">Producto</th>
                <th className="text-left py-2 px-2 text-slate-600 font-medium">Plataforma</th>
                <th className="text-left py-2 px-2 text-slate-600 font-medium">Monto</th>
                <th className="text-left py-2 px-2 text-slate-600 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((order) => (
                <tr key={order.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-2 font-mono text-slate-900">{order.id}</td>
                  <td className="py-3 px-2 text-slate-900">{order.product}</td>
                  <td className="py-3 px-2 text-slate-600">{order.platform}</td>
                  <td className="py-3 px-2 font-semibold text-slate-900">{order.amount}</td>
                  <td className="py-3 px-2">
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
    </div>
  )
}
