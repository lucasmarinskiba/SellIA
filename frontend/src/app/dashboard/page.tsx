'use client'

import { useAuth } from '@/hooks/useAuth'
import StatCard from '@/components/ui/StatCard'
import Button from '@/components/ui/Button'
import {
  TrendingUp, Users, ShoppingCart, DollarSign,
  Store, Package, Plug, MessageSquare, ArrowRight, Sparkles
} from 'lucide-react'
import Link from 'next/link'

const stats = [
  { label: 'Ventas del mes', value: '$0', icon: DollarSign, color: 'orange' as const, trend: { value: '0%', isPositive: true } },
  { label: 'Leads generados', value: '0', icon: Users, color: 'teal' as const, trend: { value: '0%', isPositive: true } },
  { label: 'Conversaciones activas', value: '0', icon: ShoppingCart, color: 'violet' as const, trend: { value: '0 nuevas', isPositive: true } },
  { label: 'Tasa de conversión', value: '0%', icon: TrendingUp, color: 'blue' as const, trend: { value: '0%', isPositive: true } },
]

const quickActions = [
  { icon: Store, label: 'Nuevo negocio', href: '/dashboard/negocios/nuevo', color: 'bg-brand-orange/10 text-brand-orange' },
  { icon: Package, label: 'Agregar producto', href: '/dashboard/catalogo/nuevo', color: 'bg-brand-teal/10 text-brand-teal' },
  { icon: Plug, label: 'Conectar canal', href: '/dashboard/canales', color: 'bg-brand-violet/10 text-brand-violet' },
  { icon: MessageSquare, label: 'Ver conversaciones', href: '/dashboard/conversaciones', color: 'bg-blue-50 text-blue-600' },
]

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Welcome */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-brand-night">
            ¡Hola, {user?.full_name?.split(' ')[0] || 'Bienvenido'}! 👋
          </h1>
          <p className="text-slate-500 mt-1">
            Este es tu panel de control de <span className="font-semibold text-brand-orange">SellIA</span>.
          </p>
        </div>
        <Link href="/dashboard/planes">
          <Button variant="secondary" leftIcon={<Sparkles className="w-4 h-4 text-brand-orange" />}>
            Ver planes
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat) => (
          <StatCard
            key={stat.label}
            label={stat.label}
            value={stat.value}
            icon={<stat.icon className="w-6 h-6" />}
            color={stat.color}
            trend={stat.trend}
          />
        ))}
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-lg font-bold text-brand-night mb-4">Acciones rápidas</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon
            return (
              <Link
                key={action.label}
                href={action.href}
                className="card p-5 hover:shadow-card-hover transition-all duration-300 group"
              >
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-3 ${action.color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-brand-night">{action.label}</span>
                  <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-brand-orange group-hover:translate-x-1 transition-all" />
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Onboarding */}
      <div className="card p-8">
        <h2 className="text-lg font-bold text-brand-night mb-6">Próximos pasos para empezar a vender</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              step: '1',
              title: 'Configura tu negocio',
              desc: 'Define si vendes servicios, bienes o digitales y configura las opciones de entrega.',
              href: '/dashboard/negocios/nuevo',
            },
            {
              step: '2',
              title: 'Carga tu catálogo',
              desc: 'Agrega los productos, servicios o archivos digitales que quieres vender.',
              href: '/dashboard/catalogo',
            },
            {
              step: '3',
              title: 'Conecta tus canales',
              desc: 'Vincula WhatsApp, MercadoLibre, Instagram y otros canales de venta.',
              href: '/dashboard/canales',
            },
          ].map((item) => (
            <Link key={item.step} href={item.href} className="group">
              <div className="flex items-start gap-4 p-4 rounded-xl bg-slate-50 hover:bg-brand-orange/5 transition-colors duration-200">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-brand-orange font-bold text-sm shadow-sm shrink-0">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold text-brand-night group-hover:text-brand-orange transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-sm text-slate-500 mt-1">{item.desc}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
