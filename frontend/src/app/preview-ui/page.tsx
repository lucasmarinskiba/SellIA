'use client'

/**
 * /preview-ui
 *
 * Repointed to the new selling-brain shell so every preview surface stays in sync.
 */

import dynamic from 'next/dynamic'

import { QueryProvider } from '@/lib/sellia-api'


const SellIABrainShell = dynamic(
  () => import('@/components/sellia-brain/SellIABrainShell'),
  { ssr: false, loading: () => <BootSplash /> },
)


export default function PreviewUIPage(): React.JSX.Element {
  return (
    <QueryProvider>
      <SellIABrainShell />
    </QueryProvider>
  )
}


const BootSplash = (): React.JSX.Element => (
  <div className="min-h-screen bg-[#03050e] flex items-center justify-center">
    <div className="text-center">
      <div className="relative w-16 h-16 mx-auto mb-4">
        <span className="absolute inset-0 rounded-full border border-cyan-400/40 animate-ping" />
        <span className="absolute inset-2 rounded-full border border-pink-400/40 animate-ping [animation-delay:200ms]" />
        <span className="absolute inset-4 rounded-full bg-gradient-to-br from-cyan-400 via-pink-400 to-emerald-400 animate-pulse" />
      </div>
      <p className="text-[10px] font-mono tracking-[0.3em] text-white/40 uppercase">
        Activando sinapsis…
      </p>
    </div>
  </div>
)
