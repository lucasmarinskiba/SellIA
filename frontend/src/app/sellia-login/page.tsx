'use client'

/**
 * SellIA login · uses new sellia-api auth flow.
 * Standalone from legacy /login. Renders at /sellia-login.
 */
import { useState, type FormEvent } from 'react'

import { useLogin, QueryProvider } from '@/lib/sellia-api'

function LoginInner() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const login = useLogin()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    try {
      await login.mutateAsync({ email, password })
      window.location.href = '/dashboard'
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Error iniciando sesión')
    }
  }

  return (
    <div className="min-h-screen bg-[#060812] flex items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-2xl border border-purple-500/20 bg-gradient-to-br from-[#0c0a1a]/90 to-[#0a0e1a]/95 p-6 backdrop-blur">
        <h1 className="text-xl font-black mb-1">
          <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">SellIA</span>
        </h1>
        <p className="text-[11px] text-white/50 mb-5">Iniciá sesión en tu Brain Hub</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-1 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-400/50"
            />
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-1 block">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="current-password"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-400/50"
            />
          </div>

          {error && (
            <div className="text-[11px] text-red-300 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/25">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={login.isPending}
            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-pink-500 text-white font-bold text-sm disabled:opacity-50"
          >
            {login.isPending ? 'Entrando…' : 'Entrar'}
          </button>
        </form>

        <p className="text-[11px] text-white/40 text-center mt-4">
          ¿No tenés cuenta?{' '}
          <a href="/sellia-signup" className="text-cyan-400 hover:underline">
            Crear ahora
          </a>
        </p>
      </div>
    </div>
  )
}

export default function SellIALoginPage() {
  return (
    <QueryProvider>
      <LoginInner />
    </QueryProvider>
  )
}
