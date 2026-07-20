'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import { Eye, EyeOff, ArrowRight, AlertCircle, CheckCircle2, User, Mail, Lock, Briefcase, Store, ChevronLeft, Globe, Zap, Clock, Bot, Users, MessageSquare, Shield } from 'lucide-react'

/* ============================================================
   REGISTER — Premium Dark Glassmorphism
   ============================================================ */

function LogoDark({ size = 40 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" className="shrink-0">
      <path d="M50 5L93.3 30V80L50 105L6.7 80V30L50 5Z" fill="url(#rg1)" transform="scale(0.95) translate(2.5,0)" />
      <path d="M50 15L83.3 34V72L50 91L16.7 72V34L50 15Z" fill="url(#rg2)" />
      <path d="M35 38C35 38 42 32 50 32C58 32 65 38 65 46C65 54 58 60 50 60C47 60 44 59 42 57L35 64L37 54C36 52 35 49 35 46C35 44 35 41 35 38Z" fill="white" fillOpacity="0.95" />
      <path d="M52 36L48 44H54L48 52" stroke="#FF6B35" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx="70" cy="28" r="4" fill="#00D4AA" />
      <circle cx="78" cy="38" r="3" fill="#7C3AED" />
      <circle cx="74" cy="50" r="2.5" fill="#FF6B35" />
      <defs>
        <linearGradient id="rg1" x1="50" y1="5" x2="50" y2="105"><stop stopColor="#1a3a5c" /><stop offset="1" stopColor="#0A2540" /></linearGradient>
        <linearGradient id="rg2" x1="50" y1="15" x2="50" y2="91"><stop stopColor="#0F2D4A" /><stop offset="1" stopColor="#0A2540" /></linearGradient>
      </defs>
    </svg>
  )
}

function SocialButton({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <button
      type="button"
      className="flex items-center justify-center gap-2.5 w-full px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/[0.12] transition-all duration-300 active:scale-[0.98] group"
    >
      <span className="text-white/60 group-hover:text-white/80 transition-colors">{icon}</span>
      <span className="text-sm font-medium text-white/50 group-hover:text-white/70 transition-colors">{label}</span>
    </button>
  )
}

function FloatingCard({ icon, label, value, delay, position }: { icon: React.ReactNode; label: string; value: string; delay: number; position: string }) {
  const [isVisible, setIsVisible] = useState(false)
  
  useEffect(() => {
    const t = setTimeout(() => setIsVisible(true), delay)
    return () => clearTimeout(t)
  }, [delay])

  return (
    <div
      className={`absolute hidden lg:flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/[0.03] backdrop-blur-md border border-white/[0.08] shadow-2xl shadow-black/40 transition-all duration-1000 ${position} ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
      style={{ animation: `float 6s ease-in-out infinite ${delay * 0.1}s` }}
    >
      <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-brand-orange">
        {icon}
      </div>
      <div>
        <p className="text-sm font-bold text-white/90 leading-tight">{value}</p>
        <p className="text-[11px] text-white/30 leading-tight">{label}</p>
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

  useEffect(() => { setMounted(true) }, [])

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
  const strengthColor = pwdScore >= 5 ? 'text-brand-teal' : pwdScore >= 3 ? 'text-amber-400' : 'text-red-400'
  const strengthPercent = pwdScore >= 5 ? 100 : pwdScore >= 3 ? 60 : form.password.length > 0 ? 25 : 0
  const strengthBarColor = pwdScore >= 5 ? 'bg-brand-teal' : pwdScore >= 3 ? 'bg-amber-400' : form.password.length > 0 ? 'bg-red-400' : 'bg-white/5'

  const progress = step === 1 ? 50 : 100

  return (
    <div className="min-h-screen bg-[#060812] text-white relative flex items-center justify-center overflow-hidden">
      {/* Rich ambient background */}
      <div className="absolute inset-0 bg-mesh opacity-60" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-brand-orange/[0.035] blur-[160px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] rounded-full bg-brand-violet/[0.03] blur-[140px] pointer-events-none" />
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] rounded-full bg-brand-teal/[0.025] blur-[120px] pointer-events-none" />

      <div className="absolute inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat', backgroundSize: '128px',
        }}
      />

      {/* Back to home */}
      <div className={`absolute top-6 left-6 z-20 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
        <Link href="/" className="flex items-center gap-2 text-sm text-white/30 hover:text-white/60 transition-colors group">
          <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center group-hover:bg-white/10 group-hover:border-white/15 transition-all">
            <ChevronLeft className="w-4 h-4" />
          </div>
          <span className="hidden sm:inline font-medium">Volver al inicio</span>
        </Link>
      </div>

      {/* Floating benefit cards */}
      <FloatingCard
        icon={<Users className="w-4 h-4" />}
        value="30 Agentes"
        label="IA Especializados"
        delay={200}
        position="left-12 xl:left-24 top-[22%]"
      />
      <FloatingCard
        icon={<MessageSquare className="w-4 h-4" />}
        value="7 Canales"
        label="WhatsApp, IG, Web..."
        delay={400}
        position="left-8 xl:left-16 top-[42%]"
      />
      <FloatingCard
        icon={<Clock className="w-4 h-4" />}
        value="24/7 Activo"
        label="Nunca duerme"
        delay={600}
        position="left-14 xl:left-32 top-[62%]"
      />
      <FloatingCard
        icon={<Shield className="w-4 h-4" />}
        value="99.9% Uptime"
        label="Infraestructura Cloud"
        delay={800}
        position="right-12 xl:right-24 top-[28%]"
      />
      <FloatingCard
        icon={<Zap className="w-4 h-4" />}
        value="2 Min"
        label="Setup inicial"
        delay={1000}
        position="right-8 xl:right-16 top-[52%]"
      />

      {/* Main card */}
      <div className={`relative z-10 w-full max-w-[480px] mx-6 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
        <div className="rounded-[32px] bg-white/[0.025] backdrop-blur-2xl border border-white/[0.08] p-8 sm:p-10 shadow-2xl shadow-black/50 relative overflow-hidden">
          {/* Subtle inner glow */}
          <div className="absolute -top-32 -right-32 w-64 h-64 bg-brand-violet/8 rounded-full blur-[80px] pointer-events-none" />
          <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-brand-orange/6 rounded-full blur-[80px] pointer-events-none" />

          {/* Progress bar */}
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-white/5">
            <div
              className="h-full bg-gradient-to-r from-brand-orange to-brand-violet transition-all duration-700 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="flex flex-col items-center mb-8 relative">
            <div className="mb-5 p-3.5 rounded-2xl bg-white/[0.04] border border-white/[0.08] shadow-lg shadow-black/20">
              <LogoDark size={44} />
            </div>
            <h1 className="text-[26px] font-bold text-white tracking-tight">¡Creá tu cuenta! 🚀</h1>
            <p className="text-sm text-white/35 mt-2">Empezá a vender con IA en minutos</p>

            {/* Step indicator */}
            <div className="flex items-center gap-0 mt-7 w-full max-w-[240px]">
              <div className="flex flex-col items-center gap-2 flex-1">
                <div className={`flex items-center justify-center w-9 h-9 rounded-full text-xs font-bold transition-all duration-500 border-2 ${
                  step >= 1
                    ? step > 1
                      ? 'bg-brand-orange border-brand-orange text-white'
                      : 'bg-brand-orange/10 border-brand-orange text-brand-orange shadow-[0_0_16px_rgba(255,107,53,0.25)]'
                    : 'bg-white/[0.03] border-white/10 text-white/25'
                }`}>
                  {step > 1 ? <CheckCircle2 className="w-4 h-4" /> : '1'}
                </div>
                <span className={`text-[10px] font-semibold uppercase tracking-wider transition-colors duration-300 ${step >= 1 ? 'text-white/50' : 'text-white/20'}`}>
                  Datos personales
                </span>
              </div>

              {/* Connector */}
              <div className="flex-1 h-[2px] mx-2 relative">
                <div className="absolute inset-0 bg-white/[0.06] rounded-full" />
                <div
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-brand-orange to-brand-violet rounded-full transition-all duration-700"
                  style={{ width: step >= 2 ? '100%' : '0%' }}
                />
              </div>

              <div className="flex flex-col items-center gap-2 flex-1">
                <div className={`flex items-center justify-center w-9 h-9 rounded-full text-xs font-bold transition-all duration-500 border-2 ${
                  step >= 2
                    ? 'bg-brand-orange/10 border-brand-orange text-brand-orange shadow-[0_0_16px_rgba(255,107,53,0.25)]'
                    : 'bg-white/[0.03] border-white/10 text-white/25'
                }`}>
                  2
                </div>
                <span className={`text-[10px] font-semibold uppercase tracking-wider transition-colors duration-300 ${step >= 2 ? 'text-white/50' : 'text-white/20'}`}>
                  Tu negocio
                </span>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 relative">
            {/* Honeypot anti-bot: campo oculto */}
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
            {/* Social signup */}
            <div className="grid grid-cols-2 gap-3">
              <SocialButton
                label="Google"
                icon={
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                }
              />
              <SocialButton
                label="Apple"
                icon={
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
                  </svg>
                }
              />
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-white/[0.06]" />
              <span className="text-[11px] text-white/20 font-medium uppercase tracking-wider">o con email</span>
              <div className="flex-1 h-px bg-white/[0.06]" />
            </div>

            {error && (
              <div className="flex items-start gap-3 p-4 rounded-2xl bg-red-500/[0.06] border border-red-500/10 text-red-400 text-sm animate-fade-in">
                <div className="w-7 h-7 rounded-lg bg-red-500/10 flex items-center justify-center shrink-0">
                  <AlertCircle className="w-3.5 h-3.5" />
                </div>
                <span className="mt-0.5">{error}</span>
              </div>
            )}

            <div className={`transition-all duration-500 ${step === 1 ? 'opacity-100 translate-x-0 relative' : 'opacity-0 translate-x-[-20px] absolute pointer-events-none'}`}>
              {step === 1 && (
                <div className="space-y-5">
                  <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-white/40 uppercase tracking-wider mb-2.5 ml-1">
                      <User className="w-3.5 h-3.5" /> Nombre completo
                    </label>
                    <input
                      type="text"
                      value={form.full_name}
                      onChange={e => update('full_name', e.target.value)}
                      required
                      autoFocus
                      placeholder="Juan Pérez"
                      className="w-full px-4 py-3.5 bg-white/[0.03] border border-white/[0.08] rounded-xl text-sm text-white placeholder:text-white/20 outline-none transition-all duration-300 focus:bg-white/[0.05] focus:border-brand-orange/30 focus:shadow-[0_0_0_3px_rgba(255,107,53,0.08)] hover:border-white/[0.12]"
                    />
                  </div>
                  <div className="group">
                    <label className="flex items-center gap-2 text-xs font-semibold text-white/40 uppercase tracking-wider mb-2.5 ml-1">
                      <Mail className="w-3.5 h-3.5" /> Email
                    </label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => update('email', e.target.value)}
                      required
                      placeholder="juan@tunegocio.com"
                      className="w-full px-4 py-3.5 bg-white/[0.03] border border-white/[0.08] rounded-xl text-sm text-white placeholder:text-white/20 outline-none transition-all duration-300 focus:bg-white/[0.05] focus:border-brand-orange/30 focus:shadow-[0_0_0_3px_rgba(255,107,53,0.08)] hover:border-white/[0.12]"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleNext}
                    className="w-full flex items-center justify-center gap-2.5 px-6 py-3.5 bg-white/[0.04] text-white text-sm font-semibold rounded-xl border border-white/[0.08] hover:bg-white/[0.08] hover:border-white/[0.12] transition-all duration-300 active:scale-[0.98] mt-2"
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
                    <label className="flex items-center gap-2 text-xs font-semibold text-white/40 uppercase tracking-wider mb-2.5 ml-1">
                      <Lock className="w-3.5 h-3.5" /> Contraseña
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={form.password}
                        onChange={e => update('password', e.target.value)}
                        required
                        placeholder="Mínimo 10 caracteres, mayúscula, número y símbolo"
                        className="w-full px-4 py-3.5 bg-white/[0.03] border border-white/[0.08] rounded-xl text-sm text-white placeholder:text-white/20 outline-none transition-all duration-300 focus:bg-white/[0.05] focus:border-brand-orange/30 focus:shadow-[0_0_0_3px_rgba(255,107,53,0.08)] hover:border-white/[0.12] pr-12"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/50 transition-colors p-1.5 rounded-lg hover:bg-white/5"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {form.password.length > 0 && (
                      <div className="mt-2.5 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <p className={`text-xs font-medium transition-colors duration-300 ${strengthColor}`}>{strength}</p>
                          <p className="text-[10px] text-white/20">{form.password.length}/10+</p>
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
                    <label className="flex items-center gap-2 text-xs font-semibold text-white/40 uppercase tracking-wider mb-2.5 ml-1">
                      <Lock className="w-3.5 h-3.5" /> Confirmar contraseña
                    </label>
                    <div className="relative">
                      <input
                        type={showConfirm ? 'text' : 'password'}
                        value={form.confirm_password}
                        onChange={e => update('confirm_password', e.target.value)}
                        required
                        placeholder="Repetí tu contraseña"
                        className="w-full px-4 py-3.5 bg-white/[0.03] border border-white/[0.08] rounded-xl text-sm text-white placeholder:text-white/20 outline-none transition-all duration-300 focus:bg-white/[0.05] focus:border-brand-orange/30 focus:shadow-[0_0_0_3px_rgba(255,107,53,0.08)] hover:border-white/[0.12] pr-12"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirm(!showConfirm)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/50 transition-colors p-1.5 rounded-lg hover:bg-white/5"
                      >
                        {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {form.confirm_password && form.password === form.confirm_password && (
                      <p className="text-xs text-brand-teal mt-2 flex items-center gap-1.5 font-medium animate-fade-in">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Coinciden ✅
                      </p>
                    )}
                  </div>

                  <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-brand-teal/[0.04] border border-brand-teal/[0.08]">
                    <div className="w-9 h-9 rounded-xl bg-brand-teal/10 flex items-center justify-center shrink-0 mt-0.5">
                      <Store className="w-4 h-4 text-brand-teal" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white/80">¿Tenés un negocio?</p>
                      <p className="text-xs text-white/30 mt-1 leading-relaxed">Después de registrarte podés configurar tu negocio, catálogo y canales desde el dashboard.</p>
                    </div>
                  </div>

                  <div className="flex gap-3 pt-1">
                    <button
                      type="button"
                      onClick={() => { setStep(1); setError('') }}
                      className="flex-1 px-5 py-3.5 bg-white/[0.03] text-white text-sm font-semibold rounded-xl border border-white/[0.08] hover:bg-white/[0.06] hover:border-white/[0.12] transition-all duration-300 active:scale-[0.98]"
                    >
                      Atrás
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="flex-[2] relative flex items-center justify-center gap-2.5 px-6 py-3.5 bg-brand-orange text-white text-sm font-bold rounded-xl hover:bg-brand-orange-dark transition-all duration-300 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden group"
                    >
                      {/* Glow effect */}
                      <div className="absolute inset-0 bg-gradient-to-r from-brand-orange via-orange-400 to-brand-orange opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                      <div className="absolute inset-0 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]" />
                      <div className="absolute -inset-1 bg-brand-orange/30 blur-lg opacity-0 group-hover:opacity-60 transition-opacity duration-500" />
                      <span className="relative flex items-center gap-2.5">
                        {loading ? (
                          <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                          <>Crear cuenta gratis ✨ <ArrowRight className="w-4 h-4" /></>
                        )}
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </form>

          <div className="mt-8 pt-6 border-t border-white/[0.05] text-center">
            <p className="text-sm text-white/25">
              ¿Ya tenés cuenta?{' '}
              <Link href="/login" className="text-brand-orange hover:text-brand-orange-light font-semibold transition-colors duration-300">
                Iniciar sesión →
              </Link>
            </p>
          </div>
        </div>

        {/* Micro social proof */}
        <div className={`mt-7 flex items-center justify-center gap-3 transition-all duration-1000 delay-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex -space-x-2.5">
            {[1,2,3,4].map(i => (
              <div
                key={i}
                className="w-7 h-7 rounded-full border-2 border-[#060812] bg-gradient-to-br from-brand-orange to-brand-violet"
                style={{ opacity: 1 - i * 0.15 }}
              />
            ))}
          </div>
          <p className="text-xs text-white/20">
            +2,500 emprendedores ya venden con SellIA 🧡
          </p>
        </div>
      </div>
    </div>
  )
}
