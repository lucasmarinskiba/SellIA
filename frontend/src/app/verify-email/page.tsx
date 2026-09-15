'use client'

/**
 * The verification email's link (backend/app/api/v1/auth.py's
 * _send_verification_email) points at {FRONTEND_URL}/verify-email?token=...
 * -- this page never existed, so every "click here to verify" link 404'd on
 * Vercel and no one could ever actually verify an account through it.
 */

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

function VerifyEmailContent(): React.JSX.Element {
  const params = useSearchParams()
  const token = params?.get('token')
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) { setStatus('error'); setMessage('Falta el token de verificación en el link.'); return }
    api.get('/auth/verify-email', { params: { token } })
      .then(res => { setStatus('ok'); setMessage(res.data?.message || 'Email verificado.') })
      .catch(err => {
        setStatus('error')
        setMessage(err?.response?.data?.detail || 'El link es inválido o expiró.')
      })
  }, [token])

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-sm text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="w-10 h-10 text-cyan-500 animate-spin mx-auto mb-4" />
            <p className="text-slate-600 text-sm">Verificando tu email…</p>
          </>
        )}
        {status === 'ok' && (
          <>
            <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-4" />
            <h1 className="text-lg font-bold text-slate-900 mb-1">¡Listo!</h1>
            <p className="text-slate-600 text-sm mb-6">{message}</p>
            <Link href="/dashboard" className="inline-block px-5 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-black">
              Ir al dashboard
            </Link>
          </>
        )}
        {status === 'error' && (
          <>
            <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
            <h1 className="text-lg font-bold text-slate-900 mb-1">No se pudo verificar</h1>
            <p className="text-slate-600 text-sm mb-6">{message}</p>
            <Link href="/dashboard" className="inline-block px-5 py-2.5 rounded-lg bg-gray-900 text-white text-sm font-semibold hover:bg-black">
              Volver al dashboard
            </Link>
          </>
        )}
      </div>
    </div>
  )
}

export default function VerifyEmailPage(): React.JSX.Element {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  )
}
