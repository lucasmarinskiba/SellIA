'use client'

/**
 * /sellia-brain
 *
 * SellIA Brain Command Center: Real-time AI sales agent dashboard.
 * Autonomous B2B sales escuadrones, pipeline management, revenue operations.
 */

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { useSession } from '@/lib/auth/hooks'

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
  const { session } = useSession()
  const businessId = session?.businesses?.[0]?.id

  if (!businessId) {
    return (
      <SettingsProvider>
        <main className="w-full p-4">
          <p className="text-slate-600">No business found</p>
        </main>
      </SettingsProvider>
    )
  }

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
        <div className="max-w-7xl mx-auto px-4 py-8">
          {activeTab === 'overview' && <EnterpriseCommandCenter />}
          {activeTab === 'control' && <ControlCenter businessId={businessId} />}
          {activeTab === 'analytics' && <ToggleAnalytics businessId={businessId} />}
        </div>
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

