'use client'

/**
 * SellIA signup · creates tenant + owner user.
 */
import { useState, type FormEvent } from 'react'

import { QueryProvider, useSignup, extractErrorMessage } from '@/lib/sellia-api'

// Mirrors backend/app/api/v1/signup.py's real validator (8+ chars, upper,
// lower, digit, one of @+-!#$%) -- client-side just so the error surfaces
// before a round-trip, not instead of the real check.
const PASSWORD_HINT = 'Mínimo 8 caracteres, con mayúscula, minúscula, número y un símbolo (@+-!#$%)'
const isStrongPassword = (p: string): boolean =>
  p.length >= 8 && /[A-Z]/.test(p) && /[a-z]/.test(p) && /\d/.test(p) && /[@+\-!#$%]/.test(p)

function SignupInner() {
  // tenant_name used to be collected here but never sent anywhere real (the
  // backend's /auth/signup only takes email/password/full_name) -- the
  // business name is asked for real at /sellia-onboarding step 1 instead
  // (OnboardingCompleteRequest.business_name), so it's not duplicated here.
  const [form, setForm] = useState({ email: '', password: '', name: '' })
  const [error, setError] = useState<string | null>(null)
  const signup = useSignup()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!isStrongPassword(form.password)) {
      setError(PASSWORD_HINT)
      return
    }
    try {
      await signup.mutateAsync(form)
      window.location.href = '/sellia-onboarding'
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Error creando cuenta'))
    }
  }

  return (
    <div className="min-h-screen bg-[#060812] flex items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-[#081218]/90 to-[#0a0e1a]/95 p-6 backdrop-blur">
        <h1 className="text-xl font-black mb-1">
          <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">SellIA</span>
        </h1>
        <p className="text-[11px] text-white/50 mb-5">Crear cuenta · trial 14 días</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          {([
            { k: 'name',         label: 'Tu nombre',           type: 'text',     ac: 'name' },
            { k: 'email',        label: 'Email',               type: 'email',    ac: 'email' },
            { k: 'password',     label: 'Contraseña',          type: 'password', ac: 'new-password' },
          ] as const).map((f) => (
            <div key={f.k}>
              <label className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-1 block">{f.label}</label>
              <input
                type={f.type}
                autoComplete={f.ac}
                required
                minLength={f.type === 'password' ? 8 : 2}
                value={form[f.k]}
                onChange={(e) => setForm((s) => ({ ...s, [f.k]: e.target.value }))}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-400/50"
              />
              {f.k === 'password' && (
                <p className="text-[10px] text-white/30 mt-1">{PASSWORD_HINT}</p>
              )}
            </div>
          ))}

          {error && (
            <div className="text-[11px] text-red-300 px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/25">{error}</div>
          )}

          <button
            type="submit"
            disabled={signup.isPending}
            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-pink-500 text-white font-bold text-sm disabled:opacity-50"
          >
            {signup.isPending ? 'Creando…' : 'Crear cuenta'}
          </button>
        </form>

        <p className="text-[11px] text-white/40 text-center mt-4">
          ¿Ya tenés cuenta?{' '}
          <a href="/sellia-login" className="text-cyan-400 hover:underline">
            Entrar
          </a>
        </p>
      </div>
    </div>
  )
}

export default function SellIASignupPage() {
  return (
    <QueryProvider>
      <SignupInner />
    </QueryProvider>
  )
}

