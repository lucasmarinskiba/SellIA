'use client'

import { Suspense, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react'
import { auth } from '@/lib/auth'

function ResetPasswordContent(): React.JSX.Element {
  const params = useSearchParams()
  const router = useRouter()
  const token = params?.get('token')

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    setError(null)
    if (!token) { setError('Falta el token de este link. Pedí uno nuevo desde "¿Olvidaste tu contraseña?".'); return }
    if (password.length < 8) { setError('La contraseña debe tener al menos 8 caracteres.'); return }
    if (password !== confirm) { setError('Las contraseñas no coinciden.'); return }
    setSubmitting(true)
    try {
      await auth.resetPassword(token, password)
      setDone(true)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'No se pudo restablecer la contraseña. El link puede haber expirado.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-xl font-bold text-slate-900 mb-1">Restablecer contraseña</h1>
        {done ? (
          <>
            <div className="flex items-center gap-2 text-emerald-600 text-sm mt-4 mb-6">
              <CheckCircle2 className="w-5 h-5 shrink-0" /> Contraseña actualizada. Ya podés iniciar sesión.
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="w-full px-5 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-black"
            >
              Ir a iniciar sesión
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-slate-600 mb-6">Elegí tu nueva contraseña.</p>
            <form onSubmit={e => { void handleSubmit(e) }} className="space-y-4">
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Nueva contraseña"
                  required
                  className="w-full px-3 py-2.5 pr-10 text-sm rounded-lg border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                placeholder="Confirmar contraseña"
                required
                className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
              />
              {error && (
                <p className="flex items-start gap-2 text-xs text-red-600">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
                </p>
              )}
              <button
                type="submit"
                disabled={submitting}
                className="w-full px-5 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-black disabled:opacity-50"
              >
                {submitting ? 'Guardando…' : 'Guardar nueva contraseña'}
              </button>
            </form>
          </>
        )}
        <p className="text-xs text-slate-400 mt-4 text-center">
          <Link href="/dashboard" className="text-cyan-600 hover:underline">Volver</Link>
        </p>
      </div>
    </div>
  )
}

export default function ResetPasswordPage(): React.JSX.Element {
  return (
    <Suspense fallback={null}>
      <ResetPasswordContent />
    </Suspense>
  )
}
