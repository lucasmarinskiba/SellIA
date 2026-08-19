'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'

const translations = {
  es: {
    welcome: '¡Hola SellIA!',
    description: 'Automatiza tareas repetitivas de ventas. Obtén resultados extraordinarios con IA y ahorra tiempo.',
    registerTitle: 'Creá tu cuenta',
    subtext: '¿Ya tenés cuenta? Inicia sesión aquí.',
    fullName: 'Nombre completo',
    fullNamePlaceholder: 'Juan Pérez',
    email: 'Email',
    emailPlaceholder: 'usuario@gmail.com',
    password: 'Contraseña',
    passwordPlaceholder: '••••••••',
    confirmPassword: 'Confirmar contraseña',
    registerButton: 'Crear cuenta',
    loading: 'Creando...',
    googleSignup: 'Registrarse con Google',
    copyright: '© 2026 SellIA. Todos los derechos reservados.',
  },
  en: {
    welcome: 'Hello SellIA!',
    description: 'Skip repetitive sales tasks. Get highly productive through automation and save tons of time!',
    registerTitle: 'Create Your Account',
    subtext: "Already have an account? Sign in here.",
    fullName: 'Full Name',
    fullNamePlaceholder: 'John Doe',
    email: 'Email',
    emailPlaceholder: 'usuario@gmail.com',
    password: 'Password',
    passwordPlaceholder: '••••••••',
    confirmPassword: 'Confirm Password',
    registerButton: 'Create Account',
    loading: 'Creating...',
    googleSignup: 'Sign up with Google',
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
  const [lang, setLang] = useState<'es' | 'en'>('es')

  useEffect(() => {
    setMounted(true)
    const browserLang = navigator.language?.startsWith('es') ? 'es' : 'en'
    setLang(browserLang)
  }, [])

  const t = translations[lang]
  const update = (field: string, value: string) => setForm(f => ({ ...f, [field]: value }))

  const validateForm = () => {
    if (!form.full_name.trim()) return lang === 'es' ? 'Nombre requerido' : 'Name required'
    if (!form.email.trim()) return lang === 'es' ? 'Email requerido' : 'Email required'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) return lang === 'es' ? 'Email inválido' : 'Invalid email'
    if (form.password.length < 10) return lang === 'es' ? 'Mínimo 10 caracteres' : 'Min 10 characters'
    if (!/[A-Z]/.test(form.password)) return lang === 'es' ? 'Mayúscula requerida' : 'Uppercase required'
    if (!/[a-z]/.test(form.password)) return lang === 'es' ? 'Minúscula requerida' : 'Lowercase required'
    if (!/[0-9]/.test(form.password)) return lang === 'es' ? 'Número requerido' : 'Number required'
    if (form.password !== form.confirm_password) return lang === 'es' ? 'Contraseñas no coinciden' : 'Passwords do not match'
    return ''
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err = validateForm()
    if (err) { setError(err); return }
    setError('')
    setLoading(true)
    try {
      await auth.register({ email: form.email, password: form.password, full_name: form.full_name, honeypot: form.honeypot })
      await auth.login({ email: form.email, password: form.password })
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || (lang === 'es' ? 'Error al crear cuenta' : 'Creation failed'))
    } finally {
      setLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen flex overflow-hidden bg-white">
      {/* Left - Yellow form panel */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center px-6 py-12 sm:px-8 lg:px-16 bg-amber-50">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="mb-8">
            <h2 className="text-3xl font-black text-gray-900">SellIA</h2>
          </div>

          {/* Welcome */}
          <div className="mb-8">
            <h3 className="text-2xl font-black text-gray-900 mb-2">{t.registerTitle}</h3>
            <p className="text-sm text-gray-700">
              {t.subtext}{' '}
              <Link href="/login" className="text-amber-700 font-semibold hover:text-amber-800">
                {lang === 'es' ? 'Ingresá aquí' : 'Sign in'}
              </Link>
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
              <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name */}
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => update('full_name', e.target.value)}
              placeholder={t.fullNamePlaceholder}
              className="w-full px-0 py-2 bg-transparent border-b border-amber-800/30 text-sm text-gray-900 placeholder-gray-500 focus:border-gray-900 focus:outline-none transition-colors"
            />

            {/* Email */}
            <input
              type="email"
              value={form.email}
              onChange={(e) => update('email', e.target.value)}
              placeholder={t.emailPlaceholder}
              className="w-full px-0 py-2 bg-transparent border-b border-amber-800/30 text-sm text-gray-900 placeholder-gray-500 focus:border-gray-900 focus:outline-none transition-colors"
            />

            {/* Password */}
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                placeholder={t.passwordPlaceholder}
                className="w-full px-0 py-2 bg-transparent border-b border-amber-800/30 text-sm text-gray-900 placeholder-gray-500 focus:border-gray-900 focus:outline-none transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-900"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Confirm Password */}
            <div className="relative">
              <input
                type={showConfirm ? 'text' : 'password'}
                value={form.confirm_password}
                onChange={(e) => update('confirm_password', e.target.value)}
                placeholder={t.passwordPlaceholder}
                className="w-full px-0 py-2 bg-transparent border-b border-amber-800/30 text-sm text-gray-900 placeholder-gray-500 focus:border-gray-900 focus:outline-none transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-0 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-900"
              >
                {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-6 px-6 py-2.5 bg-gray-900 text-white font-semibold text-sm rounded-lg hover:bg-black disabled:opacity-60 transition-all active:scale-[0.98]"
            >
              {loading ? t.loading : t.registerButton}
            </button>
          </form>

          {/* Google */}
          <button
            type="button"
            className="w-full mt-3 px-6 py-2.5 border border-amber-800/30 bg-white text-gray-700 font-semibold text-sm rounded-lg hover:bg-amber-100/50 transition-all flex items-center justify-center gap-2"
          >
            <GoogleIcon className="w-4 h-4" />
            {t.googleSignup}
          </button>
        </div>
      </div>

      {/* Right - Dark blue welcome panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-900 to-slate-900 text-white flex-col justify-between p-12 relative">
        <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-blue-700/10 rounded-full blur-3xl -ml-48" />

        <div className="relative z-10">
          <div className="mb-16">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
              <span className="text-3xl">✨</span>
            </div>
          </div>

          <div>
            <h1 className="text-6xl font-black mb-8 leading-tight">
              {t.welcome}
            </h1>
            <p className="text-lg text-white/90 leading-relaxed max-w-xl">
              {t.description}
            </p>
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-white/40 text-sm">{t.copyright}</p>
        </div>
      </div>

      {/* Mobile logo */}
      <div className="lg:hidden absolute top-8 left-8 z-20">
        <h2 className="text-2xl font-black text-gray-900">SellIA</h2>
      </div>
    </div>
  )
}
