'use client'

/**
 * /sellia-brain
 *
 * SellIA Brain Command Center: Real-time AI sales agent dashboard.
 * Autonomous B2B sales escuadrones, pipeline management, revenue operations.
 */

import { useState } from 'react'
import type { UUID } from 'crypto'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import { ExternalLink } from 'lucide-react'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'

import { SettingsProvider } from '@/lib/settings'
import { ServerSoftwareApplicationSchema, ServerFAQPageSchema } from '@/components/seo/ServerJsonLd'
import { ControlCenter } from '@/components/sellia-brain/ControlCenter'

const EnterpriseCommandCenter = dynamic(
  () => import('@/components/sellia-brain/EnterpriseCommandCenter'),
  {
    ssr: true,
    loading: () => <BootSplash />,
  },
)

const ToggleAnalytics = dynamic(
  () => import('@/components/sellia-brain/ToggleAnalytics'),
  {
    ssr: false,
    loading: () => <LoadingSpinner />,
  },
)

export default function SelliaBrainPage(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<'overview' | 'control' | 'analytics'>('overview')
  const { snapshot, loading, unavailable } = useBusinessSnapshot()
  const businessId = snapshot?.business.id

  if (loading) {
    return (
      <SettingsProvider>
        <main className="w-full p-4 flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </main>
      </SettingsProvider>
    )
  }

  // Visión General (EnterpriseCommandCenter) needs no businessId prop -- it
  // resolves its own account state internally and already shows its own
  // "Completá tu negocio" banner when there's none. This page used to hard
  // block the WHOLE page (including that tab) on `!businessId`, which meant
  // a real fetch failure ("unavailable") and "you just haven't created a
  // business yet" both looked like the same permanent dead end -- neither
  // needed to block anything. Only Control Center/Analytics actually need a
  // real businessId prop, so only those two are gated below.
  return (
    <SettingsProvider>
      <ServerSoftwareApplicationSchema />
      <ServerFAQPageSchema />
      <main role="main" className="w-full">
        <h1 className="sr-only">SellIA Brain - Command Center de Ventas Autónoma IA</h1>

        {/* Tabs */}
        <div className="border-b border-slate-200 dark:border-slate-700 sticky top-0 bg-white dark:bg-slate-900 z-40">
          <div className="max-w-7xl mx-auto px-4 flex gap-1">
            <TabButton
              label="📊 Visión General"
              active={activeTab === 'overview'}
              onClick={() => setActiveTab('overview')}
            />
            <TabButton
              label="🎛️ Control Center"
              active={activeTab === 'control'}
              onClick={() => setActiveTab('control')}
            />
            <TabButton
              label="📈 Analytics"
              active={activeTab === 'analytics'}
              onClick={() => setActiveTab('analytics')}
            />
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && <EnterpriseCommandCenter />}
        {(activeTab === 'control' || activeTab === 'analytics') && (
          <div className="max-w-7xl mx-auto px-4 py-8">
            {unavailable && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 mb-6">
                <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
                <p className="text-sm text-slate-600 mt-1">Recargá la página. No se muestran cifras de ejemplo.</p>
              </div>
            )}
            {!businessId ? (
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 flex items-center justify-between flex-wrap gap-4">
                <div>
                  <p className="font-semibold text-slate-900">Todavía no configuraste tu negocio</p>
                  <p className="text-sm text-slate-600 mt-1">
                    Control Center y Analytics necesitan un negocio real para mostrar datos.
                  </p>
                </div>
                <Link
                  href="/sellia-onboarding"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
                >
                  Configurar <ExternalLink className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <>
                {/* ControlCenter/ToggleAnalytics type businessId as Node's
                    crypto.UUID (a branded template-literal type) -- the
                    account snapshot only ever gives a plain validated UUID
                    string, never runtime-branded, so this cast is safe and
                    matches the pre-existing prop type in those components
                    (out of scope to change here). */}
                {activeTab === 'control' && <ControlCenter businessId={businessId as UUID} />}
                {activeTab === 'analytics' && <ToggleAnalytics businessId={businessId as UUID} />}
              </>
            )}
          </div>
        )}
      </main>
    </SettingsProvider>
  )
}

interface TabButtonProps {
  label: string
  active: boolean
  onClick: () => void
}

const TabButton = ({ label, active, onClick }: TabButtonProps) => (
  <button
    onClick={onClick}
    className={`
      py-4 px-4 font-medium text-sm border-b-2 transition-colors
      ${
        active
          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
          : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
      }
    `}
  >
    {label}
  </button>
)

const BootSplash = (): React.JSX.Element => (
  <div className="min-h-screen bg-[#0A0F1A] flex items-center justify-center">
    <div className="text-center">
      <div className="relative w-14 h-14 mx-auto mb-4">
        <span className="absolute inset-0 rounded-lg border border-blue-500/40 animate-ping" />
        <span className="absolute inset-2 rounded-lg bg-gradient-to-br from-blue-600 to-blue-400 animate-pulse" />
      </div>
      <p className="text-[10px] font-mono tracking-[0.3em] text-slate-500 uppercase">
        Inicializando command center…
      </p>
    </div>
  </div>
)

const LoadingSpinner = (): React.JSX.Element => (
  <div className="flex items-center justify-center min-h-96">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
  </div>
)

