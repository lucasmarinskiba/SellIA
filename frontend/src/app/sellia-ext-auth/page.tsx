'use client'

/**
 * Extension OAuth · user enters user_code shown in extension popup · approves binding.
 */
import { useEffect, useState, type FormEvent } from 'react'

import { api, QueryProvider, SellIAAuthProvider, useSellIAAuth } from '@/lib/sellia-api'

function ApproveInner() {
  const { isAuthenticated, isLoading } = useSellIAAuth()
  const [code, setCode] = useState('')
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  // Prefill code from ?code= query param (when opened from extension popup)
  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    const q = params.get('code')
    if (q) setCode(q.trim().toUpperCase())
  }, [])

  if (isLoading) return <div className="min-h-screen bg-[#060812] flex items-center justify-center text-white/50">Cargando…</div>
  if (!isAuthenticated && typeof window !== 'undefined') {
    const here = window.location.pathname + window.location.search
    window.location.href = `/sellia-login?next=${encodeURIComponent(here)}`
    return null
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setStatus('submitting')
    setError(null)
    try {
      await api.post('/ext/device/approve', { user_code: code.trim().toUpperCase() })
      setStatus('success')
    } catch (err: any) {
      setStatus('error')
      setError(err?.response?.data?.detail || 'Código inválido o expirado')
    }
  }

  return (
    <div className="min-h-screen bg-[#060812] flex items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-[#081218]/90 to-[#0a0e1a]/95 p-6 backdrop-blur">
        <h1 className="text-lg font-black mb-1">
          <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">
            Conectar extensión
          </span>
        </h1>
        <p className="text-[11px] text-white/50 mb-5">Pegá el código que aparece en tu extensión SellIA</p>

        {status !== 'success' && (
          <form onSubmit={submit} className="space-y-3">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              maxLength={8}
              required
              placeholder="ABC123"
              autoComplete="one-time-code"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-3 text-center text-2xl tracking-[0.5em] font-mono text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-400/50 uppercase"
            />
            {error && (
              <div className="text-[11px] text-red-300 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/25">{error}</div>
            )}
            <button
              type="submit"
              disabled={status === 'submitting' || code.length < 4}
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-pink-500 text-white font-bold text-sm disabled:opacity-50"
            >
              {status === 'submitting' ? 'Aprobando…' : 'Aprobar extensión'}
            </button>
          </form>
        )}

        {status === 'success' && (
          <div className="text-center py-4">
            <div className="text-4xl mb-3">✓</div>
            <p className="text-emerald-400 font-bold text-sm mb-2">Extensión aprobada</p>
            <p className="text-[11px] text-white/50">Ya podés volver a la extensión · debería conectarse automáticamente</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default function ExtAuthPage() {
  return (
    <QueryProvider>
      <SellIAAuthProvider>
        <ApproveInner />
      </SellIAAuthProvider>
    </QueryProvider>
  )
}
