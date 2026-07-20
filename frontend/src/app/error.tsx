'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('App route error:', error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#060812] text-white p-6">
      <div className="max-w-md text-center">
        <div className="w-16 h-16 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center justify-center mx-auto mb-5">
          <AlertTriangle className="w-7 h-7 text-red-400" />
        </div>
        <h2 className="text-xl font-bold mb-2">Algo salió mal</h2>
        <p className="text-sm text-white/50 mb-1">No pudimos cargar esta página.</p>
        {error.digest && (
          <p className="text-[10px] text-white/30 mb-5 font-mono">ref: {error.digest}</p>
        )}
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-orange/20 border border-brand-orange/30 text-brand-orange font-medium hover:bg-brand-orange/30 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Reintentar
        </button>
      </div>
    </div>
  )
}
