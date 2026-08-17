'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import Logo from '@/components/Logo'
import {
  Eye,
  EyeOff,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Zap,
  MessageCircle,
  TrendingUp,
  Sparkles,
  Mail,
  Lock,
  Shield,
} from 'lucide-react'

/* ============================================================
   LOGIN — SellIA 2026 · Glassmorphism Minimalism
   Design System: Dark-First, Cian Accents, Glass Effects
   ============================================================ */

function GoogleIcon({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  )
}

function AppleIcon({ className = '' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.22 7.13-.57 1.5-1.31 2.99-2.27 4.08zm-5.85-15.1c.07-2.04 1.76-3.79 3.78-3.94.29 2.32-1.93 4.48-3.78 3.94z" />
    </svg>
  )
}

const stats = [
  { icon: Zap, label: 'Respuesta', value: '< 2 min', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  { icon: MessageCircle, label: 'Conversaciones', value: '24/7', color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
  { icon: TrendingUp, label: 'Conversión', value: '+300%', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  { icon: Sparkles, label: 'IA Avanzada', value: '100%', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
]

const MAX_LOGIN_ATTEMPTS = 3
const LOCKOUT_SECONDS = 60

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  const [failedAttempts, setFailedAttempts] = useState(0)
  const [isLocked, setIsLocked] = useState(false)
  const [lockCountdown, setLockCountdown] = useState(0)

  const [honeypot, setHoneypot] = useState('')
  const [turnstileToken, setTurnstileToken] = useState('')
  const [requires2FA, setRequires2FA] = useState(false)
  const [requiresVerification, setRequiresVerification] = useState(false)
  const [tfaCode, setTfaCode] = useState('')
  const [isBackupCode, setIsBackupCode] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50)
    return () => clearTimeout(t)
  }, [])

  useEffect(() => {
    if (document.getElementById('turnstile-script')) return
    const script = document.createElement('script')
    script.id = 'turnstile-script'
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
    script.async = true
    script.defer = true
    document.body.appendChild(script)

    ;(window as any).turnstileCallback = (token: string) => {
      setTurnstileToken(token)
    }
  }, [])

  useEffect(() => {
    if (lockCountdown > 0) {
      const timer = setInterval(() => {
        setLockCountdown((prev) => {
          if (prev <= 1) {
            setIsLocked(false)
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [lockCountdown])

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      if (isLocked) return

      setError('')
      setLoading(true)

      if (honeypot.trim() !== '') {
        setLoading(false)
        return
      }

      try {
        await auth.login({
          email,
          password,
          turnstileToken: turnstileToken || undefined,
          tfaCode: tfaCode || undefined,
        })
        setFailedAttempts(0)
        setRequires2FA(false)
        router.push('/dashboard')
      } catch (err: any) {
        const detail = err.response?.data?.detail || ''

        if (detail === '2FA_REQUIRED') {
          setRequires2FA(true)
          setLoading(false)
          return
        }

        if (detail === 'EMAIL_NOT_VERIFIED') {
          setError('Tu cuenta no está verificada. Revisá tu email o solicitá uno nuevo.')
          setRequiresVerification(true)
          setLoading(false)
          return
        }
        setRequiresVerification(false)

        const msg = detail || 'Email o contraseña incorrectos'
        setError(msg)
        const nextAttempts = failedAttempts + 1
        setFailedAttempts(nextAttempts)
        if (nextAttempts >= MAX_LOGIN_ATTEMPTS) {
          setIsLocked(true)
          setLockCountdown(LOCKOUT_SECONDS)
        }
      } finally {
        setLoading(false)
      }
    },
    [email, password, honeypot, isLocked, failedAttempts, router, turnstileToken, tfaCode]
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white relative flex items-center justify-center overflow-hidden">
      {/* Ambient gradient orbs — SellIA 2026 */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full bg-cyan-500/[0.08] blur-[180px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[700px] h-[700px] rounded-full bg-indigo-500/[0.06] blur-[150px] pointer-events-none" />
      <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-cyan-400/[0.04] blur-[120px] pointer-events-none" />

      {/* SVG noise texture */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '128px',
        }}
      />

      {/* Back button */}
      <div
        className={`absolute top-6 left-1/2 -translate-x-1/2 z-20 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
        }`}
      >
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.08] border border-white/[0.15] text-sm text-white/70 hover:text-white hover:bg-white/[0.12] hover:border-white/[0.25] focus:outline-none focus:ring-2 focus:ring-white/30 transition-all duration-300"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Volver al inicio</span>
          <span className="sm:hidden">Atrás</span>
        </Link>
      </div>

      {/* Floating stat cards — left side */}
      <div className="absolute top-1/2 -translate-y-1/2 left-6 hidden xl:flex flex-col gap-3 z-10">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className={`bg-white/[0.05] border border-white/[0.1] rounded-lg p-4 flex items-center gap-3 min-w-[200px] transition-all duration-700 ${
              mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'
            }`}
            style={{ transitionDelay: `${150 + i * 120}ms` }}
          >
            <div className={`w-10 h-10 rounded-lg ${stat.bg} flex items-center justify-center`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div>
              <p className="text-[11px] text-white/40 uppercase tracking-wider font-medium">{stat.label}</p>
              <p className="text-sm font-semibold text-white">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main glass card */}
      <div
        className={`relative z-10 w-full max-w-[480px] mx-6 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-8 scale-[0.97]'
        }`}
        style={{ transitionDelay: '100ms' }}
      >
        <div className="rounded-2xl bg-slate-900/50 backdrop-blur-2xl border border-cyan-500/[0.2] p-8 sm:p-12 shadow-2xl shadow-cyan-950/50 relative overflow-hidden group hover:shadow-cyan-500/[0.15] transition-shadow duration-500">
          {/* Glow edges */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

          {/* Inner glows */}
          <div className="absolute -top-32 -right-32 w-64 h-64 bg-cyan-500/[0.08] rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-56 h-56 bg-indigo-500/[0.06] rounded-full blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="flex flex-col items-center mb-8 relative z-10">
            <div
              className={`mb-4 p-3.5 rounded-2xl bg-gradient-to-br from-cyan-500/8 to-indigo-500/4 border border-cyan-500/15 transition-all duration-700 ${
                mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
              }`}
              style={{ transitionDelay: '200ms' }}
            >
              <Logo size={44} showText={false} />
            </div>
            <h1 className="text-3xl font-black text-white tracking-tight">¡Hola de nuevo!</h1>
            <p className="text-xs text-white/45 mt-2.5 font-medium">Iniciá sesión para seguir vendiendo</p>
          </div>

          {/* Security badge */}
          <div className="flex items-center justify-center gap-1.5 mb-5 text-[10px] text-emerald-300/90 bg-emerald-500/6 border border-emerald-500/15 rounded-full px-3.5 py-1.5 font-medium">
            <Shield className="w-3 h-3" />
            <span>Protegido 2026</span>
          </div>

          {/* Social login */}
          <div
            className={`flex gap-2.5 mb-5 transition-all duration-700 ${
              mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: '250ms' }}
          >
            <button
              type="button"
              className="flex-1 flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg bg-white/[0.05] border border-white/[0.1] hover:bg-white/[0.1] hover:border-white/[0.2] hover:shadow-md hover:shadow-cyan-500/10 focus:ring-1.5 focus:ring-cyan-400/40 transition-all duration-150 active:scale-[0.96] group"
            >
              <GoogleIcon className="w-4.5 h-4.5 group-hover:scale-105 transition-transform duration-200" />
              <span className="text-xs text-white/70 font-semibold group-hover:text-white/90 transition-colors">Google</span>
            </button>
            <button
              type="button"
              className="flex-1 flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg bg-white/[0.05] border border-white/[0.1] hover:bg-white/[0.1] hover:border-white/[0.2] hover:shadow-md hover:shadow-cyan-500/10 focus:ring-1.5 focus:ring-cyan-400/40 transition-all duration-150 active:scale-[0.96] group"
            >
              <AppleIcon className="w-4.5 h-4.5 text-white/75 group-hover:text-white/95 transition-colors duration-200" />
              <span className="text-xs text-white/70 font-semibold group-hover:text-white/90 transition-colors">Apple</span>
            </button>
          </div>

          {/* Divider */}
          <div
            className={`flex items-center gap-3 mb-4 transition-all duration-700 ${
              mounted ? 'opacity-100' : 'opacity-0'
            }`}
            style={{ transitionDelay: '300ms' }}
          >
            <div className="flex-1 h-px bg-white/[0.05]" />
            <span className="text-[10px] text-white/25 font-semibold uppercase tracking-wider">o con email</span>
            <div className="flex-1 h-px bg-white/[0.05]" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5 relative">
            {/* Honeypot */}
            <div className="absolute opacity-0 top-0 left-0 h-0 w-0 overflow-hidden">
              <label htmlFor="website">Website</label>
              <input
                id="website"
                name="website"
                type="text"
                tabIndex={-1}
                autoComplete="off"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
              />
            </div>

            {error && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-sm font-medium animate-in fade-in slide-in-from-top-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {requiresVerification && (
              <button
                type="button"
                onClick={async () => {
                  setLoading(true)
                  try {
                    await auth.resendVerification()
                    setError('Email de verificación reenviado. Revisá tu bandeja de entrada.')
                  } catch (e: any) {
                    setError(e.response?.data?.detail || 'Error al reenviar email')
                  } finally {
                    setLoading(false)
                  }
                }}
                disabled={loading}
                className="w-full py-2.5 rounded-lg bg-orange-500/15 border border-orange-500/30 text-orange-300 text-sm font-medium hover:bg-orange-500/25 hover:border-orange-500/40 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Enviando...' : 'Reenviar email de verificación'}
              </button>
            )}

            {isLocked && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300 text-sm font-medium">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  Demasiados intentos fallidos. Esperá {lockCountdown}s para volver a intentar.
                </span>
              </div>
            )}

            <div>
              <label className="text-xs font-bold uppercase text-white/60 flex items-center gap-1.5 mb-2 tracking-wider">
                <Mail className="w-3.5 h-3.5 text-cyan-400" />
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                placeholder="tu@email.com"
                className="w-full px-4 py-2.5 rounded-lg bg-white/[0.06] border border-white/[0.12] text-white placeholder-white/40 hover:bg-white/[0.09] hover:border-white/[0.18] focus:bg-white/[0.11] focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/40 focus:outline-none transition-all duration-150"
              />
            </div>

            <div>
              <label className="text-xs font-bold uppercase text-white/60 flex items-center gap-1.5 mb-2 tracking-wider">
                <Lock className="w-3.5 h-3.5 text-cyan-400" />
                Contraseña
              </label>
              <div className="relative group">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 rounded-lg bg-white/[0.06] border border-white/[0.12] text-white placeholder-white/40 pr-12 hover:bg-white/[0.09] hover:border-white/[0.18] focus:bg-white/[0.11] focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/40 focus:outline-none transition-all duration-150"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-md text-white/35 hover:text-white/65 hover:bg-white/8 transition-all duration-150 focus:outline-none focus:ring-1 focus:ring-cyan-400/30"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            {/* 2FA */}
            {requires2FA && (
              <div className="space-y-3 p-4 rounded-lg bg-emerald-500/8 border border-emerald-500/20">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-semibold text-white/85 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" />
                    {isBackupCode ? 'Código de backup' : 'Código 2FA'}
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setIsBackupCode(!isBackupCode)
                      setTfaCode('')
                    }}
                    className="text-[11px] text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                  >
                    {isBackupCode ? 'Usar código TOTP' : 'Usar código de backup'}
                  </button>
                </div>
                <input
                  type="text"
                  value={tfaCode}
                  onChange={(e) => {
                    const v = e.target.value.toUpperCase()
                    if (isBackupCode) {
                      setTfaCode(v.replace(/[^A-F0-9]/g, '').slice(0, 8))
                    } else {
                      setTfaCode(v.replace(/\D/g, '').slice(0, 6))
                    }
                  }}
                  required={requires2FA}
                  placeholder={isBackupCode ? 'ABCDEF12' : '123456'}
                  maxLength={isBackupCode ? 8 : 6}
                  autoFocus
                  className="w-full px-4 py-3 rounded-lg bg-white/[0.08] border border-emerald-500/30 text-white placeholder-white/50 text-center tracking-[0.3em] font-mono hover:bg-white/[0.1] focus:bg-white/[0.12] focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/30 focus:outline-none transition-all duration-200"
                />
                <p className="text-[11px] text-white/50">
                  {isBackupCode
                    ? '✓ Ingresá uno de tus códigos de backup de un solo uso'
                    : '✓ Ingresá el código de tu app de autenticación'}
                </p>
              </div>
            )}

            {/* Turnstile */}
            {!requires2FA && (
              <div className="flex justify-center">
                <div
                  className="cf-turnstile"
                  data-sitekey={process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || '1x00000000000000000000AA'}
                  data-callback="turnstileCallback"
                  data-theme="dark"
                />
              </div>
            )}

            <div className="flex items-center justify-between pt-2">
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" className="peer sr-only" />
                  <div className="w-5 h-5 rounded-md border border-white/25 bg-white/5 peer-checked:bg-cyan-500 peer-checked:border-cyan-500 group-hover:border-white/35 transition-all duration-200" />
                  <svg
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-white opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={3}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <span className="text-sm text-white/60 group-hover:text-white/80 transition-colors font-medium">
                  Recordarme
                </span>
              </label>
              <Link
                href="#"
                className="text-sm text-cyan-400 hover:text-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 rounded px-1 transition-all font-medium"
              >
                ¿Olvidaste?
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading || isLocked}
              className="w-full flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white text-xs font-black rounded-lg hover:from-cyan-400 hover:to-cyan-500 hover:shadow-lg hover:shadow-cyan-500/30 focus:outline-none focus:ring-1.5 focus:ring-cyan-300/50 active:scale-[0.96] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 uppercase tracking-wider"
            >
              {loading ? (
                <div className="flex items-center gap-1.5">
                  <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Ingresando...</span>
                </div>
              ) : (
                <>
                  Iniciar sesión
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-white/[0.06] text-center">
            <p className="text-xs text-white/50 font-medium">
              ¿No tenés cuenta?{' '}
              <Link
                href="/register"
                className="text-cyan-400 hover:text-cyan-300 font-bold focus:outline-none focus:underline transition-all"
              >
                Registrate
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
