'use client'

import { useEffect, useState } from 'react'
import NotificationCenter from '@/components/NotificationCenter'
import ActivityFeed from '@/components/ActivityFeed'
import AgentDashboard from '@/components/AgentDashboard'
import { Bell, Zap, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function DemoAgentsPage() {
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4" />
          <p className="text-white">Cargando demo...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-4 md:p-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-slate-600 hover:text-brand-orange transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al inicio
        </Link>

        <div className="max-w-4xl">
          <h1 className="text-4xl font-bold text-brand-night mb-2 flex items-center gap-3">
            <Zap className="w-8 h-8 text-orange-500" />
            Demo: Sistema de Notificaciones en Tiempo Real
          </h1>
          <p className="text-slate-600">
            Explora cómo tu equipo de agentes IA te mantiene actualizado 24/7 con alertas, celebraciones y estrategias
          </p>
        </div>
      </div>

      {/* Demo Layout */}
      <div className="space-y-8">
        {/* Navbar Preview */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-brand-night mb-4">1. Centro de Notificaciones en Navbar</h2>
          <p className="text-slate-600 mb-4">
            Haz clic en el ícono de campana para ver todas tus notificaciones. Se actualiza automáticamente cada 30 segundos.
          </p>
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 rounded-lg flex items-center justify-between">
            <span className="text-white font-semibold">Panel de Navegación</span>
            <div className="flex items-center gap-4">
              <div className="p-2 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors cursor-pointer">
                <Bell className="w-5 h-5 text-slate-300" />
              </div>
              <span className="text-slate-400 text-sm">← Prueba aquí</span>
            </div>
          </div>
        </div>

        {/* Notification Center Preview */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-brand-night mb-4">2. Notificaciones Interactivas</h2>
          <p className="text-slate-600 mb-4">
            Panel con 6 tipos de notificaciones: alertas de agentes, celebraciones de ventas, estrategias recomendadas, aprobaciones pendientes, hitos y soporte de emergencia.
          </p>
          <div className="bg-slate-50 p-6 rounded-lg border border-slate-200">
            <div className="max-w-md">
              <NotificationCenter />
            </div>
          </div>
        </div>

        {/* Activity Feed Preview */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-brand-night mb-4">3. Feed de Actividad en Tiempo Real</h2>
          <p className="text-slate-600 mb-4">
            Visualiza lo que están haciendo tus 4 agentes principales: Lead Scout, Closer Bot, Coach Agent y Analytics Engine.
          </p>
          <div className="bg-slate-50 p-6 rounded-lg border border-slate-200">
            <ActivityFeed />
          </div>
        </div>

        {/* Full Dashboard Preview */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-brand-night mb-4">4. Centro de Control Completo</h2>
          <p className="text-slate-600 mb-4">
            Dashboard con tabs para: Resumen (actividad), Coaching diario, Estrategias + celebraciones, y Aprobaciones pendientes.
          </p>
          <div className="bg-white p-6 rounded-lg border border-slate-200 overflow-auto max-h-96">
            <AgentDashboard />
          </div>
        </div>

        {/* Features Grid */}
        <div className="card p-6">
          <h2 className="text-lg font-bold text-brand-night mb-4">¿Qué puedes ver?</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                icon: '🎯',
                title: 'Coaching Diario',
                desc: 'Mensajes personalizados según tu etapa empresarial (Day 1 → Scaling)',
              },
              {
                icon: '🎉',
                title: 'Celebraciones',
                desc: 'Notificación inmediata cuando cierres una venta en cualquier plataforma',
              },
              {
                icon: '💡',
                title: 'Estrategias IA',
                desc: 'Recomendaciones automáticas del equipo de agentes',
              },
              {
                icon: '⚠️',
                title: 'Aprobaciones',
                desc: 'Autorizar acciones que requieren tu decisión (campañas, automatizaciones)',
              },
              {
                icon: '🤖',
                title: 'Actividad de Agentes',
                desc: '4 agentes trabajando 24/7: Lead Scout, Closer Bot, Coach, Analytics',
              },
              {
                icon: '📊',
                title: 'Métricas en Vivo',
                desc: 'Alertas, celebraciones, estrategias y aprobaciones en un dashboard',
              },
            ].map((feature, i) => (
              <div key={i} className="p-4 bg-gradient-to-br from-blue-50 to-violet-50 rounded-lg border border-blue-200">
                <p className="text-2xl mb-2">{feature.icon}</p>
                <p className="font-semibold text-brand-night">{feature.title}</p>
                <p className="text-sm text-slate-600 mt-1">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Technical Details */}
        <div className="card p-6 bg-gradient-to-r from-brand-orange/5 to-orange-500/5 border-l-4 border-l-brand-orange">
          <h2 className="text-lg font-bold text-brand-night mb-4">Detalles Técnicos</h2>
          <div className="space-y-3 text-sm text-slate-700">
            <p>
              <strong>Hook useNotifications:</strong> Polling cada 30s a endpoints del backend:
              <code className="bg-white px-2 py-1 rounded ml-2">/api/v1/coach/daily-coaching</code>
              y
              <code className="bg-white px-2 py-1 rounded ml-2">/api/v1/adaptive/personalization</code>
            </p>
            <p>
              <strong>Integración Backend:</strong> Conecta con Phases 23-24 (Entrepreneurship Coach + Adaptive Architecture)
            </p>
            <p>
              <strong>Componentes:</strong> NotificationCenter, ActivityFeed, AgentDashboard con tabs y estado en tiempo real
            </p>
            <p>
              <strong>Actualización:</strong> Auto-refresh sin necesidad de refrescar la página. Stack: React + Next.js + TypeScript
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="bg-gradient-to-r from-brand-orange to-orange-600 text-white p-8 rounded-xl text-center">
          <h3 className="text-2xl font-bold mb-2">¿Listo para tu equipo de agentes IA?</h3>
          <p className="mb-4 opacity-90">
            El sistema completo (backend + frontend + notificaciones) está listo para producción.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/"
              className="px-6 py-2 bg-white text-brand-orange font-semibold rounded-lg hover:bg-slate-100 transition-colors"
            >
              Comenzar gratis
            </Link>
            <a
              href="https://github.com/lucasmarinskiba/SellIA"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition-colors"
            >
              Ver código
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

