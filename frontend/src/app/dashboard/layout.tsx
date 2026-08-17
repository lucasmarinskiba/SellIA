'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Menu, X, Settings, Home, ShoppingCart, Package, BarChart3, LogOut, Plug } from 'lucide-react'
import { useNotification } from '@/app/providers'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { notify } = useNotification()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/dashboard/orders', label: 'Órdenes', icon: ShoppingCart },
    { href: '/dashboard/listings', label: 'Listings', icon: Package },
    { href: '/dashboard/platforms', label: 'Plataformas', icon: Plug },
    { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
    { href: '/dashboard/settings', label: 'Configuración', icon: Settings },
  ]

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-slate-900 text-white transition-all duration-300 flex flex-col`}>
        {/* Logo */}
        <div className="p-4 border-b border-slate-700">
          <Link href="/dashboard" className="font-black text-xl bg-gradient-to-r from-cyan-400 to-pink-400 bg-clip-text text-transparent">
            {sidebarOpen ? 'SellIA' : 'S'}
          </Link>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <Icon size={20} />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-slate-700">
          <button
            onClick={() => notify('Sesión cerrada', 'info')}
            className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors w-full text-left"
          >
            <LogOut size={20} />
            {sidebarOpen && <span className="text-sm font-medium">Salir</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-slate-100 rounded-lg"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-semibold text-slate-900">Juan Pérez</p>
              <p className="text-xs text-slate-500">Tienda de Electrónica</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-400 to-pink-400" />
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          <div className="p-6">{children}</div>
        </div>
      </div>
    </div>
  )
}
