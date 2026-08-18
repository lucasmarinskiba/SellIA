'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { auth } from '@/lib/auth'
import { Eye, EyeOff, AlertCircle } from 'lucide-react'

const translations = {
  es: {
    welcome: '¡Hola',
    welcomeEnd: '!',
    emoji: '👋',
    description: 'Automatiza tareas repetitivas de ventas. Obtén resultados extraordinarios con IA y ahorra tiempo.',
    loginTitle: '¡Bienvenido de nuevo!',
    subtext: '¿No tenés cuenta? Crea una nueva. ¡Es GRATIS! Toma menos de un minuto.',
    email: 'Email',
    emailPlaceholder: 'usuario@gmail.com',
    password: 'Contraseña',
    passwordPlaceholder: '••••••••',
    loginButton: 'Iniciar sesión',
    googleLogin: 'Iniciar con Google',
    forgot: '¿Olvidaste tu contraseña? Haz clic aquí',
    loading: 'Ingresando...',
    copyright: '© 2026 SellIA. Todos los derechos reservados.',
  },
  en: {
    welcome: 'Hello',
    welcomeEnd: '!',
    emoji: '👋',
    description: 'Skip repetitive sales tasks. Get highly productive through automation and save tons of time!',
    loginTitle: 'Welcome Back!',
    subtext: "Don't have an account? Create a new account now. It's FREE! Takes less than a minute.",
    email: 'Email',
    emailPlaceholder: 'usuario@gmail.com',
    password: 'Password',
    passwordPlaceholder: '••••••••',
    loginButton: 'Login Now',
    googleLogin: 'Login with Google',
    forgot: 'Forgot password? Click here',
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

      {/* Right side - Login form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center px-8 py-16 sm:px-12 lg:px-24 bg-white">
        <div className="w-full max-w-sm">
          {/* Logo */}
          <div className="mb-16">
            <h2 className="text-4xl font-black text-gray-900">SellIA</h2>
          </div>

          {/* Welcome message */}
          <div className="mb-12">
            <h3 className="text-4xl font-black text-gray-900 mb-4">{t.loginTitle}</h3>
            <p className="text-gray-600 text-base leading-relaxed">{t.subtext}</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-8 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-10">
            {/* Email */}
            <div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                placeholder={t.emailPlaceholder}
                className="w-full px-0 py-3 bg-transparent border-b-2 border-gray-300 text-gray-900 placeholder-gray-400 text-base focus:border-gray-600 focus:outline-none transition-colors"
              />
            </div>

            {/* Password */}
            <div>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
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

            {/* Login button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-12 px-6 py-3.5 bg-black text-white font-bold text-lg rounded-lg hover:bg-gray-900 disabled:opacity-60 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {loading ? t.loading : t.loginButton}
            </button>
          </form>

          {/* Google login */}
          <button
            type="button"
            className="w-full mt-6 px-6 py-3.5 border-2 border-gray-300 bg-white text-gray-700 font-semibold text-base rounded-lg hover:bg-gray-50 transition-all flex items-center justify-center gap-3"
          >
            <GoogleIcon className="w-5 h-5" />
            {t.googleLogin}
          </button>

          {/* Forgot password link */}
          <div className="mt-10 text-center">
            <Link href="#" className="text-sm text-gray-600 hover:text-gray-900 font-medium">
              {t.forgot}
            </Link>
          </div>
        </div>
      </div>

      {/* Mobile logo */}
      <div className="lg:hidden absolute top-8 left-8 z-20">
        <h2 className="text-2xl font-black text-gray-900">SellIA</h2>
      </div>
    </div>
  )
}
