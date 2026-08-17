'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import { Eye, EyeOff, ArrowRight, AlertCircle, CheckCircle2, User, Mail, Lock, Store, ChevronLeft, Sparkles, Users, MessageSquare, Shield, Clock, Zap } from 'lucide-react'

/* ============================================================
   REGISTER — SellIA 2026 · Glassmorphism Minimalism
   Design System: Dark-First, Cyan Accents, Glass Effects
   ============================================================ */

function FloatingCard({ icon, label, value, delay, position }: { icon: React.ReactNode; label: string; value: string; delay: number; position: string }) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setIsVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  return (
    <div
      className={`absolute hidden lg:flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900/40 backdrop-blur-md border border-cyan-500/[0.15] shadow-lg shadow-cyan-950/30 transition-all duration-1000 ${position} ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
      style={{ animation: `float 6s ease-in-out infinite ${delay * 0.1}s` }}
    >
      <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
        {icon}
      </div>
      <div>
        <p className="text-sm font-bold text-white/90 leading-tight">{value}</p>
        <p className="text-[11px] text-white/40 leading-tight">{label}</p>
      </div>
    </div>
  )
}

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '', business_name: '', honeypot: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [step, setStep] = useState(1)

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50)
    return () => clearTimeout(t)
  }, [])

  const update = (field: string, value: string) => setForm(f => ({ ...f, [field]: value }))

  const validateStep1 = () => {
    if (!form.full_name.trim()) return 'Ingresá tu nombre completo'
    if (!form.email.trim()) return 'Ingresá tu email'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return 'Ingresá un email válido'
    return ''
  }

  const validateStep2 = () => {
    if (form.password.length < 10) return 'La contraseña debe tener al menos 10 caracteres'
    if (!/[A-Z]/.test(form.password)) return 'La contraseña debe contener al menos una mayúscula'
    if (!/[a-z]/.test(form.password)) return 'La contraseña debe contener al menos una minúscula'
    if (!/[0-9]/.test(form.password)) return 'La contraseña debe contener al menos un número'
    if (!/[!@#$%^&*(),.?":{}|<>\-_=+\[\]/~`]/.test(form.password)) return 'La contraseña debe contener al menos un símbolo'
    if (form.password !== form.confirm_password) return 'Las contraseñas no coinciden'
    return ''
  }

  const handleNext = () => {
    const err = validateStep1()
    if (err) { setError(err); return }
    setError('')
    setStep(2)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err = validateStep2()
    if (err) { setError(err); return }
    setError('')
    setLoading(true)
    try {
      await auth.register({ email: form.email, password: form.password, full_name: form.full_name, honeypot: form.honeypot })
      await auth.login({ email: form.email, password: form.password })
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear la cuenta')
    } finally {
      setLoading(false)
    }
  }

  const pwdScore = (() => {
    let score = 0
    if (form.password.length >= 10) score += 1
    if (/[A-Z]/.test(form.password)) score += 1
    if (/[a-z]/.test(form.password)) score += 1
    if (/[0-9]/.test(form.password)) score += 1
    if (/[!@#$%^&*(),.?":{}|<>\-_=+\[\]/~`]/.test(form.password)) score += 1
    return score
  })()
  const strength = pwdScore >= 5 ? 'Fuerte 💪' : pwdScore >= 3 ? 'Media ⚡' : form.password.length > 0 ? 'Débil 😅' : ''
  const strengthColor = pwdScore >= 5 ? 'text-emerald-400' : pwdScore >= 3 ? 'text-amber-400' : 'text-red-400'
  const strengthPercent = pwdScore >= 5 ? 100 : pwdScore >= 3 ? 60 : form.password.length > 0 ? 25 : 0
  const strengthBarColor = pwdScore >= 5 ? 'bg-emerald-500' : pwdScore >= 3 ? 'bg-amber-500' : form.password.length > 0 ? 'bg-red-500' : 'bg-white/5'

  const progress = step === 1 ? 50 : 100

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
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/[0.05] border border-white/[0.1] text-sm text-white/50 hover:text-white/80 hover:bg-white/[0.08] transition-all duration-300"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
          Volver al inicio
        </Link>
      </div>

      {/* Floating benefit cards — left side */}
      <div className="absolute top-1/3 -translate-y-1/2 left-6 hidden xl:flex flex-col gap-3 z-10">
        <FloatingCard
          icon={<Users className="w-4 h-4" />}
          value="30 Agentes"
          label="IA Especializados"
          delay={200}
          position=""
        />
        <FloatingCard
          icon={<MessageSquare className="w-4 h-4" />}
          value="7 Canales"
          label="WhatsApp, IG, Web"
          delay={400}
          position=""
        />
        <FloatingCard
          icon={<Clock className="w-4 h-4" />}
          value="24/7 Activo"
          label="Nunca duerme"
          delay={600}
          position=""
        />
      </div>

      {/* Main glass card */}
      <div
        className={`relative z-10 w-full max-w-[480px] mx-6 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-8 scale-[0.97]'
        }`}
        style={{ transitionDelay: '100ms' }}
      >
        <div className="rounded-2xl bg-slate-900/40 backdrop-blur-xl border border-cyan-500/[0.15] p-10 sm:p-12 shadow-2xl shadow-cyan-950/50 relative overflow-hidden group">
          {/* Glow edges */}
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

          {/* Inner glows */}
          <div className="absolute -top-32 -right-32 w-64 h-64 bg-cyan-500/[0.08] rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-56 h-56 bg-indigo-500/[0.06] rounded-full blur-3xl pointer-events-none" />

          {/* Progress bar */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-white/5">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-700 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Header */}
          <div className="flex flex-col items-center mb-10 relative z-10">
            <div
              className={`mb-6 p-3 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-indigo-500/5 border border-cyan-500/20 transition-all duration-700 ${
                mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
              }`}
              style={{ transitionDelay: '200ms' }}
            >
              <Sparkles className="w-8 h-8 text-cyan-400" />
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">¡Creá tu cuenta! 🚀</h1>
            <p className="text-sm text-white/50 mt-3">Trial 14 días · sin tarjeta de crédito</p>

            {/* Step indicator */}
            <div className="flex items-center gap-0 mt-8 w-full max-w-[240px]">
              <div className="flex flex-col items-center gap-2 flex-1">
                <div className={`flex items-center justify-center w-9 h-9 rounded-full text-xs font-bold transition-all duration-500 border-2 ${
                  step >= 1
                    ? step > 1
                      ? 'bg-cyan-500 border-cyan-500 text-white'
                      : 'bg-cyan-500/10 border-cyan-500 text-cyan-400 shadow-[0_0_16px_rgba(6,200,255,0.25)]'
                    : 'bg-white/[0.03] border-white/10 text-white/25'
                }`}>
                  {step > 1 ? <CheckCircle2 className="w-4 h-4" /> : '1'}
                </div>
                <span className={`text-[10px] font-semibold uppercase tracking-wider transition-colors duration-300 ${step >= 1 ? 'text-white/50' : 'text-white/20'}`}>
                  Datos
                </span>
              </div>

              {/* Connector */}
              <div className="flex-1 h-[2px] mx-2 relative">
                <div className="absolute inset-0 bg-white/[0.06] rounded-full" />
                <div
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full transition-all duration-700"
                  style={{ width: step >= 2 ? '100%' : '0%' }}
                />
              </div>

              <div className="flex flex-col items-center gap-2 flex-1">
                <div className={`flex items-center justify-center w-9 h-9 rounded-full text-xs font-bold transition-all duration-500 border-2 ${
                  step >= 2
                    ? 'bg-cyan-500/10 border-cyan-500 text-cyan-400 shadow-[0_0_16px_rgba(6,200,255,0.25)]'
                    : 'bg-white/[0.03] border-white/10 text-white/25'
                }`}>
                  2
                </div>
                <span className={`text-[10px] font-semibold uppercase tracking-wider transition-colors duration-300 ${step >= 2 ? 'text-white/50' : 'text-white/20'}`}>
                  Contraseña
                </span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 relative">
            {/* Honeypot */}
            <div className="absolute opacity-0 top-0 left-0 h-0 w-0 overflow-hidden">
              <label htmlFor="company">Company</label>
              <input
                id="company"
                name="company"
                type="text"
                tabIndex={-1}
                autoComplete="off"
                value={form.honeypot}
                onChange={e => update('honeypot', e.target.value)}
              />
            </div>

            {error && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div className={`transition-all duration-500 ${step === 1 ? 'opacity-100 translate-x-0 relative' : 'opacity-0 translate-x-[-20px] absolute pointer-events-none'}`}>
              {step === 1 && (
                <div className="space-y-5">
                  <div>
                    <label className="text-sm font-medium text-white/70 flex items-center gap-1.5 mb-2">
                      <User className="w-3.5 h-3.5" />
                      Nombre completo
                    </label>
                    <input
                      type="text"
                      value={form.full_name}
                      onChange={e => update('full_name', e.target.value)}
                      required
                      autoFocus
                      placeholder="Juan Pérez"
                      className="w-full px-4 py-3 rounded-lg bg-white/[0.05] border border-white/[0.1] text-white placeholder-white/40 focus:bg-white/[0.08] focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-white/70 flex items-center gap-1.5 mb-2">
                      <Mail className="w-3.5 h-3.5" />
                      Email
                    </label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => update('email', e.target.value)}
                      required
                      placeholder="tu@email.com"
                      className="w-full px-4 py-3 rounded-lg bg-white/[0.05] border border-white/[0.1] text-white placeholder-white/40 focus:bg-white/[0.08] focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleNext}
                    className="w-full flex items-center justify-center gap-2.5 px-6 py-3 bg-white/[0.05] border border-white/[0.1] text-white text-sm font-semibold rounded-lg hover:bg-white/[0.08] hover:border-white/[0.15] transition-all duration-300 active:scale-[0.98] mt-3"
                  >
                    Continuar <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            <div className={`transition-all duration-500 ${step === 2 ? 'opacity-100 translate-x-0 relative' : 'opacity-0 translate-x-[20px] absolute pointer-events-none'}`}>
              {step === 2 && (
                <div className="space-y-5">
                  <div>
                    <label className="text-sm font-medium text-white/70 flex items-center gap-1.5 mb-2">
                      <Lock className="w-3.5 h-3.5" />
                      Contraseña
                    </label>
                    <div className="relative group">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={form.password}
                        onChange={e => update('password', e.target.value)}
                        required
                        placeholder="Mínimo 10 caracteres"
                        className="w-full px-4 py-3 rounded-lg bg-white/[0.05] border border-white/[0.1] text-white placeholder-white/40 pr-12 focus:bg-white/[0.08] focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg text-white/30 hover:text-white/60 hover:bg-white/5 transition-all"
                        tabIndex={-1}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {form.password.length > 0 && (
                      <div className="mt-3 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <p className={`text-xs font-medium transition-colors duration-300 ${strengthColor}`}>{strength}</p>
                          <p className="text-[10px] text-white/30">{form.password.length}/10+</p>
                        </div>
                        <div className="h-1 w-full bg-white/[0.06] rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ease-out ${strengthBarColor}`}
                            style={{ width: `${strengthPercent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-white/70 flex items-center gap-1.5 mb-2">
                      <Lock className="w-3.5 h-3.5" />
                      Confirmar contraseña
                    </label>
                    <div className="relative group">
                      <input
                        type={showConfirm ? 'text' : 'password'}
                        value={form.confirm_password}
                        onChange={e => update('confirm_password', e.target.value)}
                        required
                        placeholder="Repetí tu contraseña"
                        className="w-full px-4 py-3 rounded-lg bg-white/[0.05] border border-white/[0.1] text-white placeholder-white/40 pr-12 focus:bg-white/[0.08] focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-300"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirm(!showConfirm)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-lg text-white/30 hover:text-white/60 hover:bg-white/5 transition-all"
                        tabIndex={-1}
                      >
                        {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {form.confirm_password && form.password === form.confirm_password && (
                      <p className="text-xs text-emerald-400 mt-2 flex items-center gap-1.5 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Coinciden ✅
                      </p>
                    )}
                  </div>

                  <div className="flex items-start gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                    <Store className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold text-white/80">¿Tenés un negocio?</p>
                      <p className="text-xs text-white/40 mt-1">Después podés configurar tu catálogo y canales desde el dashboard.</p>
                    </div>
                  </div>

                  <div className="flex gap-3 pt-1">
                    <button
                      type="button"
                      onClick={() => { setStep(1); setError('') }}
                      className="flex-1 px-5 py-3 bg-white/[0.05] border border-white/[0.1] text-white text-sm font-semibold rounded-lg hover:bg-white/[0.08] transition-all duration-300 active:scale-[0.98]"
                    >
                      Atrás
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-[2] flex items-center justify-center gap-2.5 px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white text-sm font-semibold rounded-lg hover:from-cyan-400 hover:to-cyan-500 transition-all duration-300 active:scale-[0.98] disabled:opacity-50 shadow-lg shadow-cyan-500/25"
                    >
                      {loading ? (
                        <span className="w-4 h-4 border-2 border-white/25 border-t-white rounded-full animate-spin" />
                      ) : (
                        <>Crear cuenta gratis ✨ <ArrowRight className="w-4 h-4" /></>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </form>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-white/[0.06] text-center">
            <p className="text-sm text-white/40">
              ¿Ya tenés cuenta?{' '}
              <Link
                href="/login"
                className="text-cyan-400 hover:text-cyan-300 font-semibold transition-colors"
              >
                Iniciar sesión →
              </Link>
            </p>
          </div>

          {/* Social proof */}
          <div className={`mt-7 flex items-center justify-center gap-3 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
            <div className="flex -space-x-2.5">
              {[1,2,3,4].map(i => (
                <div
                  key={i}
                  className="w-7 h-7 rounded-full border-2 border-slate-900 bg-gradient-to-br from-cyan-400 to-indigo-500"
                  style={{ opacity: 1 - i * 0.15 }}
                />
              ))}
            </div>
            <p className="text-xs text-white/30">
              +2,500 emprendedores ya venden 🧡
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
