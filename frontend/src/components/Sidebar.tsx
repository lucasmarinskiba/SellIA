'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import Logo from './Logo'
import {
  LayoutDashboard, Store, Package, MessageSquare, Settings,
  Plug, Crown, ChevronRight, Bot, Zap, BarChart3, X, KanbanSquare, CircleDollarSign,
  ShoppingCart, Wallet, Shield, FileSearch, Bell, Lightbulb, Mail, Headphones, Truck, Calendar,
  MessageCircle, Target, Heart, Brain, MonitorPlay, TrendingUp, Home,
  ShoppingBag, Camera as Instagram, Award, Activity, Users, Radar,
  Gift, Ticket, Swords, Moon, Eye, Crosshair
} from 'lucide-react'
import { CompanionWidget } from './gamification/CompanionWidget'
import { GardenWidget } from './gamification/GardenWidget'
import { TrustBuilder } from './gamification/TrustBuilder'

const baseNavItems = [
  { href: '/dashboard/home', label: 'Inicio', icon: Home },
  { href: '/dashboard/mientras-dormias', label: 'Mientras Dormías', icon: Moon },
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/radar', label: 'Radar', icon: Radar },
  { href: '/dashboard/negocios', label: 'Mis Negocios', icon: Store },
  { href: '/dashboard/catalogo', label: 'Catálogo', icon: Package },
  { href: '/dashboard/equipo', label: 'Mi Equipo', icon: Users },
  { href: '/dashboard/crm', label: 'CRM Pipeline', icon: KanbanSquare },
  { href: '/dashboard/ordenes', label: 'Órdenes', icon: ShoppingCart },
  { href: '/dashboard/envios', label: 'Envíos', icon: Truck },
  { href: '/dashboard/agenda', label: 'Agenda', icon: Calendar },
  { href: '/dashboard/finanzas', label: 'Finanzas', icon: Wallet },
  { href: '/dashboard/pipeline', label: 'Pipeline IA', icon: Target },
  { href: '/dashboard/agentes', label: 'Agentes IA', icon: Bot },
  { href: '/dashboard/agente-vivo', label: 'Agente en Vivo', icon: MonitorPlay },
  { href: '/dashboard/caja-de-cristal', label: 'Caja de Cristal', icon: MonitorPlay },
  { href: '/dashboard/autonomo', label: 'Sistema Autónomo', icon: Activity },
  { href: '/dashboard/autopilot', label: 'Autopilot 24/7', icon: Brain },
  { href: '/dashboard/automatizaciones', label: 'Automatizaciones', icon: Zap },
  { href: '/dashboard/sequences', label: 'Secuencias', icon: Mail },
  { href: '/dashboard/conversaciones', label: 'Conversaciones', icon: MessageSquare },
  { href: '/dashboard/canales', label: 'Canales', icon: Plug },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/misiones', label: 'Misiones', icon: Crosshair },
  { href: '/dashboard/objetivos', label: 'Objetivos & KPIs', icon: Target },
  { href: '/dashboard/retencion', label: 'Retención', icon: Heart },
  { href: '/dashboard/clientes-fieles', label: 'Clientes Fieles', icon: Heart },
  { href: '/dashboard/inteligencia', label: 'Inteligencia', icon: Brain },
  { href: '/dashboard/growth', label: 'Growth Engine', icon: TrendingUp },
  { href: '/dashboard/marketplace', label: 'Marketplace', icon: ShoppingBag },
  { href: '/dashboard/social-growth', label: 'Social Growth', icon: Instagram },
  { href: '/dashboard/ambassador', label: 'Ambassador', icon: Award },
  { href: '/dashboard/planes', label: 'Planes', icon: Crown },
  { href: '/dashboard/alertas', label: 'Alertas', icon: Bell },
  { href: '/dashboard/recomendaciones', label: 'Recomendaciones', icon: Lightbulb },
  { href: '/dashboard/seguridad', label: 'Seguridad', icon: Shield },
  { href: '/dashboard/sessions', label: 'Sesiones', icon: Lock },
  { href: '/dashboard/configuracion', label: 'Configuración', icon: Settings },
  { href: '/soporte', label: 'Soporte', icon: Headphones },
  { href: '/feedback', label: 'Feedback', icon: MessageCircle },
  { href: '/dashboard/referrals', label: 'Referidos', icon: Gift },
  { href: '/dashboard/coupons', label: 'Cupones', icon: Ticket },
  { href: '/dashboard/battlecards', label: 'Battlecards', icon: Swords },
  { href: '/dashboard/competencia', label: 'Competencia', icon: Eye },
]

import { Lock } from 'lucide-react'

interface SidebarProps {
  onClose?: () => void
}

export default function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname()
  const { user } = useAuth()

  const navItems = [...baseNavItems]
  if (user?.is_superuser) {
    navItems.push({ href: '/dashboard/admin/metrics', label: 'Métricas', icon: BarChart3 })
    navItems.push({ href: '/dashboard/admin/audit', label: 'Audit', icon: FileSearch })
    navItems.push({ href: '/dashboard/admin/soporte', label: 'Soporte Admin', icon: Headphones })
    navItems.push({ href: '/dashboard/admin/feedback', label: 'Feedback Admin', icon: MessageCircle })
  }

  return (
    <aside className="w-72 bg-card border-r border-border min-h-screen flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-border flex items-center justify-between">
        <Logo size={36} />
        <button 
          onClick={onClose}
          className="lg:hidden p-2 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Cerrar sidebar"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto no-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                isActive
                  ? 'bg-primary/10 text-primary border border-primary/20'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground border border-transparent'
              }`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-primary' : 'text-muted-foreground/60'}`} />
              <span className="flex-1">{item.label}</span>
              {isActive && <ChevronRight className="w-4 h-4 opacity-50" aria-hidden="true" />}
            </Link>
          )
        })}
      </nav>

      {/* Gamification Widgets */}
      <div className="px-4 pb-2 space-y-3">
        <CompanionWidget />
        <GardenWidget />
        <TrustBuilder />
      </div>

      {/* Plan card */}
      <div className="p-4 border-t border-border">
        <div className="rounded-2xl p-5 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-brand-violet/10 border border-border rounded-2xl" />
          <div className="absolute -top-10 -right-10 w-24 h-24 bg-primary/20 blur-2xl rounded-full pointer-events-none" />
          <div className="relative">
            <p className="text-xs font-medium text-muted-foreground mb-1">Plan actual</p>
            <p className="text-sm font-bold text-foreground mb-1">Free</p>
            <p className="text-[10px] text-muted-foreground/60 mb-3">1 agente · 1 canal · 50 conversaciones</p>
            <Link
              href="/dashboard/planes"
              className="inline-flex items-center text-xs font-semibold text-primary hover:opacity-90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-lg"
            >
              Ver planes <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    </aside>
  )
}
