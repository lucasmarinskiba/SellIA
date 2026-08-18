'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import Logo from '@/components/Logo'
import { Eye, EyeOff, Mail, Lock, AlertCircle, Sparkles } from 'lucide-react'

const translations = {
  es: {
    welcome: '¡Bienvenido a SellIA!',
    subtitle: 'Tu asistente IA para vendedores',
    description: 'Automatiza tareas repetitivas y vende mientras duermes. Obtén resultados extraordinarios con IA generativa.',
    loginTitle: '¡Bienvenido de nuevo!',
    email: 'Email',
    password: 'Contraseña',
    loginButton: 'Iniciar sesión',
    googleLogin: 'Iniciar con Google',
    forgot: '¿Olvidaste tu contraseña?',
    noAccount: '¿No tenés cuenta?',
    createAccount: 'Creá una gratis',
    loading: 'Ingresando...',
    copyright: '© 2026 SellIA. Todos los derechos reservados.',
  },
  en: {
    welcome: 'Welcome to SellIA!',
    subtitle: 'Your AI Assistant for Sales',
    description: 'Automate repetitive tasks and sell while you sleep. Achieve extraordinary results with generative AI.',
    loginTitle: 'Welcome Back!',
    email: 'Email',
    password: 'Password',
    loginButton: 'Login Now',
    googleLogin: 'Login with Google',
    forgot: 'Forgot password?',
    noAccount: "Don't have an account?",
    createAccount: 'Create one for free',
    loading: 'Logging in...',
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

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [lang, setLang] = useState<'es' | 'en'>('es')

  useEffect(() => {
    setMounted(true)
    // Detect language from browser
    const browserLang = navigator.language?.startsWith('es') ? 'es' : 'en'
    setLang(browserLang)
  }, [])

  const t = translations[lang]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await auth.login(email, password)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen flex overflow-hidden bg-white">
      {/* Left side - Blue gradient with marketing */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 to-blue-800 text-white flex-col justify-between p-12 relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -mr-48 -mt-48" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-blue-400/10 rounded-full blur-3xl -ml-36 -mb-36" />

        {/* Content */}
        <div className="relative z-10">
          <div className="mb-16">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-white/15 backdrop-blur-sm rounded-2xl">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
          </div>

          <div>
            <h1 className="text-6xl font-black mb-6 leading-tight">
              {t.welcome}
            </h1>
            <p className="text-xl text-white/95 leading-relaxed max-w-lg">
              {t.description}
            </p>
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-white/50 text-sm">{t.copyright}</p>
        </div>
      </div>

      {/* Right side - Login form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center px-6 py-16 sm:px-12 lg:px-20 bg-white">
        <div className="w-full max-w-md">
          {/* Logo */}
          <div className="mb-12">
            <h2 className="text-3xl font-black text-gray-900">SellIA</h2>
          </div>

          {/* Welcome message */}
          <div className="mb-10">
            <h3 className="text-4xl font-black text-gray-900 mb-3">{t.loginTitle}</h3>
            <p className="text-gray-600 text-sm">{lang === 'es' ? 'No tenés cuenta?' : "Don't have an account?"} <Link href="/register" className="text-blue-600 font-bold hover:text-blue-700 underline">{t.createAccount}</Link></p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
              <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-3">
                {t.email}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                placeholder="usuario@email.com"
                className="w-full px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:bg-white focus:border-blue-500 focus:ring-0 focus:outline-none transition-all shadow-sm hover:border-gray-300"
              />
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-semibold text-gray-900">
                  {t.password}
                </label>
                <Link href="#" className="text-xs text-blue-600 hover:text-blue-700 font-semibold">
                  {t.forgot}
                </Link>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full px-4 py-3.5 bg-gray-50 border-2 border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:bg-white focus:border-blue-500 focus:ring-0 focus:outline-none transition-all shadow-sm hover:border-gray-300"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Login button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-10 px-6 py-3.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:opacity-60 disabled:cursor-not-allowed transition-all active:scale-[0.98] shadow-md hover:shadow-lg"
            >
              {loading ? t.loading : t.loginButton}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-500 font-medium">O continúa con</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          {/* Google login */}
          <button
            type="button"
            className="w-full px-6 py-3.5 border-2 border-gray-200 bg-white text-gray-700 font-semibold rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all flex items-center justify-center gap-3 shadow-sm"
          >
            <GoogleIcon className="w-5 h-5" />
            {t.googleLogin}
          </button>
        </div>
      </div>

      {/* Mobile welcome message */}
      <div className="lg:hidden absolute top-6 left-6 z-20">
        <h2 className="text-xl font-bold text-gray-900">SellIA</h2>
      </div>
    </div>
  )
}
