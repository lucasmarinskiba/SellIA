'use client'

/**
 * /sellia-brain
 *
 * SellIA Brain Command Center: Real-time AI sales agent dashboard.
 * Autonomous B2B sales escuadrones, pipeline management, revenue operations.
 */

import dynamic from 'next/dynamic'

import { SettingsProvider } from '@/lib/settings'
import { ServerSoftwareApplicationSchema, ServerFAQPageSchema } from '@/components/seo/ServerJsonLd'


const EnterpriseCommandCenter = dynamic(
  () => import('@/components/sellia-brain/EnterpriseCommandCenter'),
  {
    ssr: true,
    loading: () => <BootSplash />,
  },
)


export default function SelliaBrainPage(): React.JSX.Element {
  return (
    <SettingsProvider>
      <ServerSoftwareApplicationSchema />
      <ServerFAQPageSchema />
      <main role="main" className="w-full">
        <h1 className="sr-only">SellIA Brain - Command Center de Ventas Autónoma IA</h1>
        <EnterpriseCommandCenter />
      </main>
    </SettingsProvider>
  )
}


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

