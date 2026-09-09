'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import {
  Menu, X, Settings, Home, ShoppingCart, Package, BarChart3, LogOut, Plug,
  TrendingUp, Award, Store, MessageSquare,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { businessApi, type Business } from '@/lib/business'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const pathname = usePathname()
  const { user, loading, logout } = useAuth()

  // Real business of the signed-in account -- the header used to hardcode
  // "Juan Pérez / Tienda de Electrónica" for everyone, so every screenshot of
  // this dashboard showed a person and a shop that do not exist.
  const [business, setBusiness] = useState<Business | null>(null)
  useEffect(() => {
    if (!user) { setBusiness(null); return }
    let alive = true
    businessApi.list()
      .then(list => { if (alive) setBusiness(list[0] ?? null) })
      .catch(() => { /* sin negocio todavía -> se muestra el estado honesto */ })
    return () => { alive = false }
  }, [user])

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/dashboard/orders', label: 'Órdenes', icon: ShoppingCart },
    { href: '/dashboard/listings', label: 'Listings', icon: Package },
    { href: '/dashboard/platforms', label: 'Plataformas', icon: Plug },
    { href: '/dashboard/phase12', label: 'SEO', icon: TrendingUp },
    { href: '/dashboard/phase3', label: 'Construya Autoridad', icon: Award },
    { href: '/dashboard/phase33', label: 'Vendedor Multiplataforma', icon: Store },
    { href: '/dashboard/conversaciones', label: 'Conversaciones', icon: MessageSquare },
    { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
    { href: '/dashboard/settings', label: 'Configuración', icon: Settings },
  ]

  const accountName = user?.full_name || user?.email || (loading ? '' : 'Sin sesión')
  const accountSubtitle = business?.name
    ?? (user ? 'Sin negocio configurado' : 'Iniciá sesión para ver tus datos')

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
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                title={item.label}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-slate-800 text-cyan-300' : 'hover:bg-slate-800'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon size={20} className="shrink-0" />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-slate-700">
          {/* Used to only pop a "Sesión cerrada" toast while leaving the
              session fully active -- it actually logs out now. */}
          <button
            onClick={() => { void logout() }}
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
            aria-label={sidebarOpen ? 'Contraer menú' : 'Expandir menú'}
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-semibold text-slate-900">{accountName || '—'}</p>
              <p className="text-xs text-slate-500">{accountSubtitle}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-400 to-pink-400 grid place-items-center text-white font-bold">
              {(user?.full_name || user?.email || '?').trim().charAt(0).toUpperCase()}
            </div>
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
