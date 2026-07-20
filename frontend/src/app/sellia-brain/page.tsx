'use client'

/**
 * /sellia-brain
 *
 * Canonical entry point for the SellIA selling brain UX.
 * Wraps the funnel-organized shell with QueryProvider so any embedded
 * TanStack Query hooks have access to the shared client.
 */

import dynamic from 'next/dynamic'

import { QueryProvider } from '@/lib/sellia-api'
import { SettingsProvider } from '@/lib/settings'


const EnterpriseCommandCenter = dynamic(
  () => import('@/components/sellia-brain/EnterpriseCommandCenter'),
  { ssr: false, loading: () => <BootSplash /> },
)


export default function SelliaBrainPage(): React.JSX.Element {
  return (
    <SettingsProvider>
      <QueryProvider>
        <EnterpriseCommandCenter />
      </QueryProvider>
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
