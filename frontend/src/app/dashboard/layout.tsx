'use client'

import Link from 'next/link'
import dynamic from 'next/dynamic'
import { usePathname } from 'next/navigation'
import { useEffect, useRef, useState } from 'react'
import {
  Menu, X, Settings, Home, ShoppingCart, Package, BarChart3, LogOut, Plug,
  TrendingUp, Award, Store, MessageSquare, Brain, ChevronDown, UserPlus,
  MapPin, CreditCard, Briefcase, Check, Loader2,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { businessApi, type Business } from '@/lib/business'
import { api } from '@/lib/api'

// Same chat widget as /sellia-brain (dock prop = same docked-right design,
// same conversation history) -- lazy-loaded client-side only, it touches
// browser voice/localStorage APIs.
const SellIAAssistant = dynamic(() => import('@/components/SellIAAssistant'), { ssr: false })

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const pathname = usePathname()
  const { user, loading, logout } = useAuth()

  // ── Account dropdown (Google-style: switch/add account, address, plan) ──
  const [accountMenuOpen, setAccountMenuOpen] = useState(false)
  const accountMenuRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!accountMenuOpen) return
    const onDown = (e: MouseEvent): void => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(e.target as Node)) setAccountMenuOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [accountMenuOpen])

  // "+ Añadir otra cuenta": the real /dashboard session cookie is httpOnly
  // (JS can't read/restore it), so true instant multi-account switching
  // would need a saved-sessions store + switch endpoint on the backend --
  // real feature, not built yet. This does what Google itself falls back
  // to when it doesn't have the other account cached: log out, go to login.
  const handleAddAccount = (): void => { void logout() }

  // Compact inline form -- POST /business-context already supports a
  // partial update (city/address/country) without touching the full
  // BusinessContextWizard multi-step flow.
  const [addressOpen, setAddressOpen] = useState(false)
  const [addressCity, setAddressCity] = useState('')
  const [addressStreet, setAddressStreet] = useState('')
  const [addressSaving, setAddressSaving] = useState(false)
  const [addressSaved, setAddressSaved] = useState(false)
  const handleSaveAddress = async (): Promise<void> => {
    if (!business?.id || (!addressCity.trim() && !addressStreet.trim())) return
    setAddressSaving(true)
    setAddressSaved(false)
    try {
      await api.post(`/business-context?business_id=${business.id}`, {
        city: addressCity.trim() || undefined,
        address: addressStreet.trim() || undefined,
        country: 'Argentina',
      })
      setAddressSaved(true)
    } catch {
      // se muestra "Guardar" de nuevo -- el usuario puede reintentar
    } finally {
      setAddressSaving(false)
    }
  }

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

  // GET /users/me masks the caller's own name and email ("O*** T***",
  // "o***4@selliatest.dev") -- fine for listing other people, wrong for the
  // header showing you your own account. /auth/me returns the real values for
  // the token's own user, so the header shows who you actually are.
  const [ownName, setOwnName] = useState<string | null>(null)
  useEffect(() => {
    if (!user) { setOwnName(null); return }
    let alive = true
    api.get<{ full_name?: string; email?: string }>('/auth/me')
      .then(res => { if (alive) setOwnName(res.data.full_name || res.data.email || null) })
      .catch(() => { /* se cae al valor enmascarado de useAuth */ })
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

  const accountName = ownName || user?.full_name || user?.email || (loading ? '' : 'Sin sesión')
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

        {/* SellIA Brain -- distinct from the regular nav list, this is the
            other half of the app (agentes/automatizaciones/mapa neuronal,
            not a dashboard sub-page), so users can jump between the two
            easily instead of hunting for a URL. */}
        <div className="p-4 border-b border-slate-700">
          <Link
            href="/sellia-brain"
            title="SellIA Brain"
            className="flex items-center gap-3 px-4 py-3 rounded-lg bg-gradient-to-r from-cyan-500/20 to-pink-500/20 border border-cyan-400/30 hover:from-cyan-500/30 hover:to-pink-500/30 transition-colors"
          >
            <Brain size={20} className="shrink-0 text-cyan-300" />
            {sidebarOpen && <span className="text-sm font-semibold text-cyan-100">SellIA Brain</span>}
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
          <div className="relative" ref={accountMenuRef}>
            <button
              onClick={() => setAccountMenuOpen(v => !v)}
              className="flex items-center gap-4 p-1.5 pr-2 rounded-full hover:bg-slate-100 transition-colors"
              aria-expanded={accountMenuOpen}
            >
              <div className="text-right">
                <p className="font-semibold text-slate-900">{accountName || '—'}</p>
                {!loading && !user ? (
                  <Link
                    href="/login"
                    onClick={e => e.stopPropagation()}
                    className="text-xs text-cyan-600 font-medium hover:underline"
                  >
                    {accountSubtitle}
                  </Link>
                ) : (
                  <p className="text-xs text-slate-500">{accountSubtitle}</p>
                )}
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-400 to-pink-400 grid place-items-center text-white font-bold shrink-0">
                {(ownName || user?.full_name || user?.email || '?').trim().charAt(0).toUpperCase()}
              </div>
              <ChevronDown size={16} className={`text-slate-400 shrink-0 transition-transform ${accountMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {accountMenuOpen && (
              <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-50">
                {/* Header: same account info Google shows at the top */}
                <div className="p-5 flex flex-col items-center text-center border-b border-slate-100">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-cyan-400 to-pink-400 grid place-items-center text-white text-2xl font-bold mb-2">
                    {(ownName || user?.full_name || user?.email || '?').trim().charAt(0).toUpperCase()}
                  </div>
                  <p className="font-semibold text-slate-900">{accountName || '—'}</p>
                  {user?.email && <p className="text-xs text-slate-500">{user.email}</p>}
                  {business?.name && <p className="text-xs text-slate-400 mt-0.5">{business.name}</p>}
                  {!loading && !user && (
                    <Link
                      href="/login"
                      onClick={() => setAccountMenuOpen(false)}
                      className="mt-3 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors"
                    >
                      Iniciar sesión
                    </Link>
                  )}
                </div>

                <div className="p-2 border-b border-slate-100">
                  <Link
                    href="/dashboard/planes"
                    onClick={() => setAccountMenuOpen(false)}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-pink-500 text-white font-semibold text-sm hover:opacity-90 transition-opacity"
                  >
                    <CreditCard size={18} className="shrink-0" />
                    Obtén un plan SellIA
                  </Link>
                </div>

                {/* Dirección del local -- mejora resultados para público local */}
                <div className="p-2 border-b border-slate-100">
                  <button
                    onClick={() => setAddressOpen(v => !v)}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-700"
                  >
                    <MapPin size={18} className="shrink-0 text-slate-400" />
                    Establecer dirección de tu local
                  </button>
                  {addressOpen && (
                    <div className="px-3 pb-2 pt-1 space-y-2">
                      <input
                        value={addressCity}
                        onChange={e => { setAddressCity(e.target.value); setAddressSaved(false) }}
                        placeholder="Ciudad"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                      />
                      <input
                        value={addressStreet}
                        onChange={e => { setAddressStreet(e.target.value); setAddressSaved(false) }}
                        placeholder="Dirección"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                      />
                      <button
                        onClick={() => { void handleSaveAddress() }}
                        disabled={addressSaving || !business?.id}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-lg bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
                      >
                        {addressSaving ? <Loader2 size={14} className="animate-spin" /> : addressSaved ? <Check size={14} /> : null}
                        {addressSaving ? 'Guardando…' : addressSaved ? 'Guardado' : 'Guardar dirección'}
                      </button>
                      {!business?.id && <p className="text-[11px] text-slate-400">Configurá tu negocio primero para guardar la dirección.</p>}
                    </div>
                  )}
                </div>

                <div className="p-2 border-b border-slate-100">
                  <Link href="/dashboard/negocios" onClick={() => setAccountMenuOpen(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-700">
                    <Briefcase size={18} className="shrink-0 text-slate-400" />
                    Mi negocio
                  </Link>
                  <Link href="/dashboard/configuracion" onClick={() => setAccountMenuOpen(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-700">
                    <Settings size={18} className="shrink-0 text-slate-400" />
                    Configuración
                  </Link>
                </div>

                <div className="p-2">
                  <button
                    onClick={() => { setAccountMenuOpen(false); handleAddAccount() }}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-700"
                  >
                    <UserPlus size={18} className="shrink-0 text-slate-400" />
                    + Añadir otra cuenta
                  </button>
                  <button
                    onClick={() => { setAccountMenuOpen(false); void logout() }}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg hover:bg-slate-50 transition-colors text-sm text-slate-700"
                  >
                    <LogOut size={18} className="shrink-0 text-slate-400" />
                    Cerrar sesión
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          <div className="p-6">{children}</div>
        </div>
      </div>

      <SellIAAssistant businessId={business?.id} dock />
    </div>
  )
}
