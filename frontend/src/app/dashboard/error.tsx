'use client'

/**
 * Error boundary of the dashboard segment.
 *
 * Without it, any render error on a dashboard page bubbled up to the root `error.tsx`, which replaces the whole
 * screen (menu included) with "Algo salió mal". Here the failure stays inside the content area: the menu keeps
 * working, the person can retry or go somewhere else, and the technical detail is only shown in development.
 */

import Link from 'next/link'
import { useEffect } from 'react'
import { AlertTriangle, Home, RefreshCw } from 'lucide-react'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('Dashboard route error:', error)
  }, [error])

  return (
    <div role="alert" className="mx-auto flex max-w-xl flex-col items-center rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600" aria-hidden="true">
        <AlertTriangle className="h-7 w-7" />
      </div>
      <h2 className="text-xl font-bold text-slate-900">Esta sección no pudo mostrarse</h2>
      <p className="mt-2 text-sm text-slate-600">
        Algo falló al cargar esta pantalla. El resto del panel sigue funcionando: podés reintentar o seguir en otra sección.
      </p>
      {error.digest && <p className="mt-2 font-mono text-[11px] text-slate-400">ref: {error.digest}</p>}
      {process.env.NODE_ENV !== 'production' && (
        <p className="mt-3 max-w-full break-words rounded-lg bg-slate-50 px-3 py-2 text-left font-mono text-xs text-slate-600">
          {error.message}
        </p>
      )}
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" /> Reintentar
        </button>
        <Link
          href="/dashboard"
          className="inline-flex h-11 items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
        >
          <Home className="h-4 w-4" aria-hidden="true" /> Ir al inicio
        </Link>
      </div>
    </div>
  )
}
