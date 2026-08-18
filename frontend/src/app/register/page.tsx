'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import { Eye, EyeOff, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react'

const translations = {
  es: {
    welcome: '¡Hola',
    welcomeEnd: '!',
    emoji: '👋',
    description: 'Automatiza tareas repetitivas de ventas. Obtén resultados extraordinarios con IA y ahorra tiempo.',
    registerTitle: '¡Creá tu cuenta!',
    subtext: '¿Ya tenés cuenta? Inicia sesión aquí. Toma menos de un minuto crear una.',
    fullName: 'Nombre completo',
    fullNamePlaceholder: 'Juan Pérez',
    email: 'Email',
    emailPlaceholder: 'usuario@gmail.com',
    password: 'Contraseña',
    passwordPlaceholder: '••••••••',
    confirmPassword: 'Confirmar contraseña',
    nextButton: 'Siguiente',
    registerButton: 'Crear cuenta',
    haveAccount: '¿Ya tenés cuenta?',
    loginHere: 'Inicia sesión aquí',
    loading: 'Creando cuenta...',
    copyright: '© 2026 SellIA. Todos los derechos reservados.',
  },
  en: {
    welcome: 'Hello',
    welcomeEnd: '!',
    emoji: '👋',
    description: 'Skip repetitive sales tasks. Get highly productive through automation and save tons of time!',
    registerTitle: 'Create Your Account!',
    subtext: "Already have an account? Sign in here. It takes less than a minute to create one.",
    fullName: 'Full Name',
    fullNamePlaceholder: 'John Doe',
    email: 'Email',
    emailPlaceholder: 'usuario@gmail.com',
    password: 'Password',
    passwordPlaceholder: '••••••••',
    confirmPassword: 'Confirm Password',
    nextButton: 'Next',
    registerButton: 'Create Account',
    haveAccount: 'Already have an account?',
    loginHere: 'Sign in here',
    loading: 'Creating account...',
    copyright: '© 2026 SellIA. All rights reserved.',
  },
}

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

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '', honeypot: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [step, setStep] = useState(1)
  const [lang, setLang] = useState<'es' | 'en'>('es')

  useEffect(() => {
    setMounted(true)
    const browserLang = navigator.language?.startsWith('es') ? 'es' : 'en'
    setLang(browserLang)
  }, [])

  const t = translations[lang]
  const update = (field: string, value: string) => setForm(f => ({ ...f, [field]: value }))

  const validateStep1 = () => {
    if (!form.full_name.trim()) return lang === 'es' ? 'Ingresá tu nombre completo' : 'Enter your full name'
    if (!form.email.trim()) return lang === 'es' ? 'Ingresá tu email' : 'Enter your email'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return lang === 'es' ? 'Email inválido' : 'Invalid email'
    return ''
  }

  const validateStep2 = () => {
    if (form.password.length < 10) return lang === 'es' ? 'Mínimo 10 caracteres' : 'Minimum 10 characters'
    if (!/[A-Z]/.test(form.password)) return lang === 'es' ? 'Necesita mayúscula' : 'Needs uppercase'
    if (!/[a-z]/.test(form.password)) return lang === 'es' ? 'Necesita minúscula' : 'Needs lowercase'
    if (!/[0-9]/.test(form.password)) return lang === 'es' ? 'Necesita número' : 'Needs number'
    if (form.password !== form.confirm_password) return lang === 'es' ? 'Las contraseñas no coinciden' : 'Passwords do not match'
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
      setError(err.response?.data?.detail || (lang === 'es' ? 'Error al crear la cuenta' : 'Account creation failed'))
    } finally {
      setLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen flex overflow-hidden bg-white">
      {/* Left side - Blue gradient with diagonal pattern */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-blue-700 to-blue-900 text-white flex-col justify-between p-16 relative overflow-hidden">
        {/* SVG Diagonal Lines Pattern - More Visible */}
        <svg className="absolute inset-0 w-full h-full opacity-30" preserveAspectRatio="none" viewBox="0 0 1000 1000">
          <defs>
            <pattern id="diagonals" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="100" y2="100" stroke="white" strokeWidth="2" />
              <line x1="100" y1="0" x2="0" y2="100" stroke="white" strokeWidth="2" />
            </pattern>
          </defs>
          <rect width="1000" height="1000" fill="url(#diagonals)" />
        </svg>

        {/* Gradient Orbs */}
        <div className="absolute top-20 right-20 w-80 h-80 bg-blue-400/20 rounded-full blur-3xl" />
        <div className="absolute bottom-20 left-10 w-60 h-60 bg-blue-300/20 rounded-full blur-3xl" />

        {/* Content */}
        <div className="relative z-10">
          <div className="mb-20">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 backdrop-blur-xl rounded-3xl border border-white/30">
              <span className="text-4xl">✨</span>
            </div>
          </div>

          <div>
            <h1 className="text-7xl font-black mb-4 leading-tight">
              {t.welcome}
              <br />
              SellIA{t.welcomeEnd}
              <span className="text-6xl ml-3">{t.emoji}</span>
            </h1>
            <p className="text-xl text-white/90 leading-relaxed max-w-xl mt-8">
              {t.description}
            </p>
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-white/40 text-sm">{t.copyright}</p>
        </div>
      </div>

      {/* Right side - Register form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center px-8 py-16 sm:px-12 lg:px-24 bg-white">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="mb-16">
            <h2 className="text-4xl font-black text-gray-900">SellIA</h2>
          </div>

          {/* Welcome message */}
          <div className="mb-12">
            <h3 className="text-4xl font-black text-gray-900 mb-4">{t.registerTitle}</h3>
            <p className="text-gray-600 text-base leading-relaxed">
              {t.haveAccount}{' '}
              <Link href="/login" className="text-blue-600 font-bold hover:text-blue-700">
                {t.loginHere}
              </Link>
            </p>
          </div>

          {/* Step indicator */}
          <div className="mb-10 flex gap-4">
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step === 1 ? 'bg-black' : 'bg-gray-300'}`} />
            <div className={`flex-1 h-1.5 rounded-full transition-colors ${step === 2 ? 'bg-black' : 'bg-gray-300'}`} />
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-8 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Step 1: Basic Info */}
          {step === 1 && (
            <form onSubmit={(e) => { e.preventDefault(); handleNext(); }} className="space-y-10">
              <div>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={(e) => update('full_name', e.target.value)}
                  placeholder={t.fullNamePlaceholder}
                  className="w-full px-0 py-3 bg-transparent border-b-2 border-gray-300 text-gray-900 placeholder-gray-400 text-base focus:border-gray-600 focus:outline-none transition-colors"
                />
              </div>

              <div>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => update('email', e.target.value)}
                  placeholder={t.emailPlaceholder}
                  className="w-full px-0 py-3 bg-transparent border-b-2 border-gray-300 text-gray-900 placeholder-gray-400 text-base focus:border-gray-600 focus:outline-none transition-colors"
                />
              </div>

              <button
                type="submit"
                className="w-full mt-12 px-6 py-3.5 bg-black text-white font-bold text-lg rounded-lg hover:bg-gray-900 disabled:opacity-60 disabled:cursor-not-allowed transition-all active:scale-[0.98] flex items-center justify-center gap-2"
              >
                {t.nextButton}
                <ArrowRight className="w-5 h-5" />
              </button>

              <button
                type="button"
                className="w-full px-6 py-3.5 border-2 border-gray-300 bg-white text-gray-700 font-semibold text-base rounded-lg hover:bg-gray-50 transition-all flex items-center justify-center gap-3"
              >
                <GoogleIcon className="w-5 h-5" />
                {lang === 'es' ? 'Registrarse con Google' : 'Sign up with Google'}
              </button>
            </form>
          )}

          {/* Step 2: Password */}
          {step === 2 && (
            <form onSubmit={handleSubmit} className="space-y-10">
              <div>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => update('password', e.target.value)}
                    placeholder={t.passwordPlaceholder}
                    className="w-full px-0 py-3 bg-transparent border-b-2 border-gray-300 text-gray-900 placeholder-gray-400 text-base focus:border-gray-600 focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div>
                <div className="relative">
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    value={form.confirm_password}
                    onChange={(e) => update('confirm_password', e.target.value)}
                    placeholder={t.passwordPlaceholder}
                    className="w-full px-0 py-3 bg-transparent border-b-2 border-gray-300 text-gray-900 placeholder-gray-400 text-base focus:border-gray-600 focus:outline-none transition-colors"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {showConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 px-6 py-3.5 border-2 border-gray-300 text-gray-700 font-semibold text-base rounded-lg hover:bg-gray-50 transition-all"
                >
                  {lang === 'es' ? 'Atrás' : 'Back'}
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-6 py-3.5 bg-black text-white font-bold text-lg rounded-lg hover:bg-gray-900 disabled:opacity-60 disabled:cursor-not-allowed transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  {loading ? t.loading : t.registerButton}
                  {!loading && <CheckCircle2 className="w-5 h-5" />}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Mobile logo */}
      <div className="lg:hidden absolute top-8 left-8 z-20">
        <h2 className="text-2xl font-black text-gray-900">SellIA</h2>
      </div>
    </div>
  )
}
