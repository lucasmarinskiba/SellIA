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
  Bot,
  Mail,
  Lock,
  Shield,
} from 'lucide-react'

/* ============================================================
   LOGIN — Premium Glassmorphism + Seguridad Anti-Hackeo
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
  { icon: Zap, label: 'Respuesta', value: '< 2 min', color: 'text-brand-orange', bg: 'bg-brand-orange/20' },
  { icon: MessageCircle, label: 'Conversaciones', value: '24/7', color: 'text-brand-teal', bg: 'bg-brand-teal/20' },
  { icon: TrendingUp, label: 'Conversión', value: '+300%', color: 'text-brand-violet', bg: 'bg-brand-violet/20' },
  { icon: Bot, label: 'Automatización', value: '100%', color: 'text-brand-orange', bg: 'bg-brand-orange/20' },
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

  // Rate limiting visual (client-side)
  const [failedAttempts, setFailedAttempts] = useState(0)
  const [isLocked, setIsLocked] = useState(false)
  const [lockCountdown, setLockCountdown] = useState(0)

  // Honeypot anti-bot
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

  // Cargar script de Cloudflare Turnstile
  useEffect(() => {
    if (document.getElementById('turnstile-script')) return
    const script = document.createElement('script')
    script.id = 'turnstile-script'
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
    script.async = true
    script.defer = true
    document.body.appendChild(script)

    // Callback global requerido por Turnstile
    ;(window as any).turnstileCallback = (token: string) => {
      setTurnstileToken(token)
    }
  }, [])

  // Contador regresivo de bloqueo
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

      // Si el honeypot tiene contenido, es un bot — simular éxito para no dar pistas
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
        // Auth token se almacena en cookie httpOnly automáticamente
        // No se guarda en localStorage por seguridad
        setFailedAttempts(0)
        setRequires2FA(false)
        router.push('/dashboard')
      } catch (err: any) {
        const detail = err.response?.data?.detail || ''
        
        // Si el servidor pide 2FA
        if (detail === '2FA_REQUIRED') {
          setRequires2FA(true)
          setLoading(false)
          return
        }

        // Si el email no está verificado
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
    <div className="min-h-screen bg-[#060812] text-white relative flex items-center justify-center overflow-hidden">
      {/* Ambient orbs */}
      <div className="absolute inset-0 bg-mesh opacity-60" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-brand-orange/[0.04] blur-[150px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] rounded-full bg-brand-violet/[0.03] blur-[120px] pointer-events-none" />
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full bg-brand-teal/[0.03] blur-[100px] pointer-events-none" />

      {/* SVG noise */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '128px',
        }}
      />

      {/* Back to home */}
      <div
        className={`absolute top-6 left-1/2 -translate-x-1/2 z-20 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
        }`}
      >
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card text-sm text-white/40 hover:text-white/70 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Volver al inicio
        </Link>
      </div>

      {/* Floating stat cards — left side */}
      <div className="absolute top-1/2 -translate-y-1/2 left-6 hidden xl:flex flex-col gap-3 z-10">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className={`glass-card p-3.5 flex items-center gap-3 min-w-[180px] transition-all duration-700 ${
              mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'
            }`}
            style={{ transitionDelay: `${150 + i * 120}ms` }}
          >
            <div className={`w-9 h-9 rounded-xl ${stat.bg} flex items-center justify-center`}>
              <stat.icon className={`w-4.5 h-4.5 ${stat.color}`} />
            </div>
            <div>
              <p className="text-[10px] text-white/30 uppercase tracking-wider">{stat.label}</p>
              <p className="text-sm font-bold text-white/80">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Main glass card */}
      <div
        className={`relative z-10 w-full max-w-[460px] mx-6 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-8 scale-[0.97]'
        }`}
        style={{ transitionDelay: '100ms' }}
      >
        <div className="rounded-[32px] bg-white/[0.03] backdrop-blur-xl border border-white/[0.08] p-10 sm:p-12 shadow-2xl shadow-black/50 relative overflow-hidden">
          {/* Inner glows */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-brand-orange/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-brand-violet/10 rounded-full blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="flex flex-col items-center mb-10 relative">
            <div
              className={`mb-6 p-3.5 rounded-2xl bg-white/5 border border-white/10 transition-all duration-700 ${
                mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
              }`}
              style={{ transitionDelay: '200ms' }}
            >
              <Logo size={48} showText={false} />
            </div>
            <h1 className="text-[26px] font-bold text-white tracking-tight">¡Hola de nuevo! 👋</h1>
            <p className="text-sm text-white/40 mt-2">Iniciá sesión para seguir vendiendo</p>
          </div>

          {/* Security badge */}
          <div className="flex items-center justify-center gap-2 mb-6 text-xs text-emerald-400/70 bg-emerald-500/5 border border-emerald-500/10 rounded-full px-4 py-1.5">
            <Shield className="w-3.5 h-3.5" />
            <span>Conexión protegida por ciberseguridad moderna</span>
          </div>

          {/* Social login */}
          <div
            className={`flex gap-3 mb-6 transition-all duration-700 ${
              mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: '250ms' }}
          >
            <button
              type="button"
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] hover:border-white/[0.14] transition-all active:scale-[0.98]"
            >
              <GoogleIcon className="w-5 h-5" />
              <span className="text-sm text-white/70 font-medium">Google</span>
            </button>
            <button
              type="button"
              className="flex-1 flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] hover:border-white/[0.14] transition-all active:scale-[0.98]"
            >
              <AppleIcon className="w-5 h-5 text-white/80" />
              <span className="text-sm text-white/70 font-medium">Apple</span>
            </button>
          </div>

          {/* Divider */}
          <div
            className={`flex items-center gap-4 mb-6 transition-all duration-700 ${
              mounted ? 'opacity-100' : 'opacity-0'
            }`}
            style={{ transitionDelay: '300ms' }}
          >
            <div className="flex-1 h-px bg-white/[0.06]" />
            <span className="text-xs text-white/25 font-medium">o con tu email</span>
            <div className="flex-1 h-px bg-white/[0.06]" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5 relative">
            {/* Honeypot anti-bot: campo oculto */}
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
              <div className="flex items-start gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/15 text-red-400 text-sm animate-shake">
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
                className="w-full py-2.5 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-sm font-medium hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
              >
                {loading ? 'Enviando...' : 'Reenviar email de verificación'}
              </button>
            )}

            {isLocked && (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/10 border border-amber-500/15 text-amber-400 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  Demasiados intentos fallidos. Esperá {lockCountdown}s para volver a intentar.
                </span>
              </div>
            )}

            <div>
              <label className="label flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-white/30" />
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                placeholder="tu@email.com"
                className="input-field focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange/40 transition-all"
              />
            </div>

            <div>
              <label className="label flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-white/30" />
                Contraseña
              </label>
              <div className="relative group">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="input-field pr-12 focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange/40 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg text-white/20 hover:text-white/60 hover:bg-white/5 transition-all"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Campo 2FA cuando es requerido */}
            {requires2FA && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="label flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-white/30" />
                    {isBackupCode ? 'Código de backup' : 'Código de verificación (2FA)'}
                  </label>
                  <button
                    type="button"
                    onClick={() => {
                      setIsBackupCode(!isBackupCode)
                      setTfaCode('')
                    }}
                    className="text-[11px] text-brand-orange hover:underline"
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
                  className="input-field text-center tracking-[0.3em] font-mono focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange/40 transition-all"
                />
                <p className="text-[11px] text-white/30">
                  {isBackupCode
                    ? 'Ingresá uno de tus códigos de backup de un solo uso'
                    : 'Ingresá el código de tu app de autenticación'}
                </p>
              </div>
            )}

            {/* Cloudflare Turnstile */}
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

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <div className="relative">
                  <input type="checkbox" className="peer sr-only" />
                  <div className="w-4.5 h-4.5 rounded border border-white/20 bg-white/5 peer-checked:bg-brand-orange peer-checked:border-brand-orange transition-all" />
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
                <span className="text-sm text-white/35 group-hover:text-white/55 transition-colors">
                  Recordarme
                </span>
              </label>
              <Link
                href="#"
                className="text-sm text-brand-orange hover:text-brand-orange-light transition-colors font-medium"
              >
                ¿Olvidaste? 🤔
              </Link>
            </div>

            <button
              type="submit"
              disabled={loading || isLocked}
              className="w-full flex items-center justify-center gap-2.5 px-6 py-3.5 bg-brand-orange text-white text-sm font-semibold rounded-xl hover:bg-brand-orange-dark transition-all active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 shadow-lg shadow-brand-orange/20"
            >
              {loading ? (
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 border-[2.5px] border-white/25 border-t-white rounded-full animate-spin" />
                  <span className="text-white/80">Ingresando...</span>
                </div>
              ) : (
                <>
                  Iniciar sesión
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-white/[0.06] text-center">
            <p className="text-sm text-white/25">
              ¿No tenés cuenta?{' '}
              <Link
                href="/register"
                className="text-brand-orange hover:text-brand-orange-light font-semibold transition-colors"
              >
                Creá una gratis ✨
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
