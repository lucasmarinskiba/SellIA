'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Zap,
  Globe,
  Palette,
  ShoppingBag,
  Settings,
  Sparkles,
} from 'lucide-react'
import { websites } from '@/lib/api/websites'

/* ============================================================
   ONBOARDING — SellIA 2026 · 5-Step Setup Flow
   ============================================================ */

interface OnboardingData {
  business_name: string
  business_description: string
  website_template: 'MINIMAL' | 'CLASSIC' | 'MODERN' | 'ECOMMERCE' | 'PORTFOLIO'
  subdomain: string
}

const TEMPLATES = [
  {
    id: 'MODERN',
    name: 'Moderno',
    description: 'Diseño limpio y contemporáneo. Ideal para servicios y negocios profesionales.',
    icon: Sparkles,
    color: 'from-cyan-400 to-indigo-400',
  },
  {
    id: 'ECOMMERCE',
    name: 'Ecommerce',
    description: 'Optimizado para venta de productos. Carrito, galería y checkout incluido.',
    icon: ShoppingBag,
    color: 'from-emerald-400 to-cyan-400',
  },
  {
    id: 'CLASSIC',
    name: 'Clásico',
    description: 'Elegante y tradicional. Perfecto para establecimientos establecidos.',
    icon: Globe,
    color: 'from-indigo-400 to-purple-400',
  },
  {
    id: 'PORTFOLIO',
    name: 'Portfolio',
    description: 'Showcase de trabajos y proyectos. Para creadores y freelancers.',
    icon: Palette,
    color: 'from-pink-400 to-rose-400',
  },
]

const STEPS = [
  { num: 1, title: 'Nombre', icon: Zap },
  { num: 2, title: 'Descripción', icon: Sparkles },
  { num: 3, title: 'Template', icon: Palette },
  { num: 4, title: 'Dominio', icon: Globe },
  { num: 5, title: 'Resumen', icon: CheckCircle2 },
]

export default function OnboardingPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  const [data, setData] = useState<OnboardingData>({
    business_name: '',
    business_description: '',
    website_template: 'MODERN',
    subdomain: '',
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  const updateData = (field: keyof OnboardingData, value: string) => {
    setData(prev => ({ ...prev, [field]: value }))
    setError('')
  }

  const validateStep = (): boolean => {
    switch (step) {
      case 1:
        if (!data.business_name.trim()) {
          setError('Ingresá el nombre de tu negocio')
          return false
        }
        return true
      case 2:
        if (!data.business_description.trim()) {
          setError('Ingresá una descripción de tu negocio')
          return false
        }
        if (data.business_description.length < 20) {
          setError('La descripción debe tener al menos 20 caracteres')
          return false
        }
        return true
      case 3:
        return true
      case 4:
        if (!data.subdomain.trim()) {
          setError('Ingresá un subdominio')
          return false
        }
        if (!/^[a-z0-9-]{3,63}$/.test(data.subdomain.toLowerCase())) {
          setError('Subdominio inválido. Solo letras, números y guiones. 3-63 caracteres.')
          return false
        }
        return true
      case 5:
        return true
      default:
        return true
    }
  }

  const handleNext = () => {
    if (validateStep()) {
      if (step < 5) {
        setStep(step + 1)
      } else {
        handleSubmit()
      }
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    try {
      const website = await websites.completeOnboarding({
        business_name: data.business_name,
        business_description: data.business_description,
        website_template: data.website_template,
        subdomain: data.subdomain,
      })
      router.push(`/dashboard/websites`)
    } catch (err: any) {
      setError(err.message || 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white relative flex items-center justify-center overflow-hidden p-4">
      {/* Ambient orbs */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full bg-cyan-500/[0.08] blur-[180px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[700px] h-[700px] rounded-full bg-indigo-500/[0.06] blur-[150px] pointer-events-none" />

      {/* Main card */}
      <div
        className={`relative z-10 w-full max-w-[600px] transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}
      >
        <div className="rounded-2xl bg-slate-900/50 backdrop-blur-2xl border border-cyan-500/[0.2] p-8 sm:p-10 shadow-2xl shadow-cyan-950/50 hover:shadow-cyan-500/[0.15] transition-shadow duration-500">
          {/* Progress indicator */}
          <div className="mb-10">
            <div className="flex justify-between mb-4">
              {STEPS.map((s) => (
                <div key={s.num} className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-all duration-300 ${
                      step > s.num
                        ? 'bg-emerald-500 text-white'
                        : step === s.num
                        ? 'bg-cyan-500/20 border-2 border-cyan-500 text-cyan-400'
                        : 'bg-white/5 border border-white/10 text-white/30'
                    }`}
                  >
                    {step > s.num ? <CheckCircle2 className="w-5 h-5" /> : s.num}
                  </div>
                  <span className="text-xs text-center text-white/50 hidden sm:inline">{s.title}</span>
                </div>
              ))}
            </div>

            {/* Progress bar */}
            <div className="h-1.5 bg-white/[0.1] rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-500 shadow-lg shadow-cyan-500/30"
                style={{ width: `${(step / 5) * 100}%` }}
              />
            </div>
          </div>

          {/* Content */}
          <div className="min-h-[400px]">
            {/* Step 1: Business Name */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">¿Cuál es el nombre de tu negocio?</h2>
                  <p className="text-white/50">Este será visible en tu website</p>
                </div>

                <input
                  type="text"
                  value={data.business_name}
                  onChange={(e) => updateData('business_name', e.target.value)}
                  placeholder="Ej: Mi Negocio Digital"
                  autoFocus
                  className="w-full px-4 py-3 rounded-lg bg-white/[0.08] border border-white/[0.15] text-white placeholder-white/50 hover:bg-white/[0.1] hover:border-white/[0.2] focus:bg-white/[0.12] focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/30 focus:outline-none transition-all duration-200"
                />
              </div>
            )}

            {/* Step 2: Description */}
            {step === 2 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Describe tu negocio</h2>
                  <p className="text-white/50">¿Qué ofreces? ¿A quién le sirve?</p>
                </div>

                <textarea
                  value={data.business_description}
                  onChange={(e) => updateData('business_description', e.target.value)}
                  placeholder="Ej: Vendemos ropa de moda sostenible para jóvenes que buscan estilo y conciencia ambiental..."
                  autoFocus
                  className="w-full px-4 py-3 rounded-lg bg-white/[0.05] border border-white/[0.1] text-white placeholder-white/40 focus:bg-white/[0.08] focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 transition-all resize-none h-[180px]"
                />
                <p className="text-xs text-white/40">
                  {data.business_description.length} / 500 caracteres
                </p>
              </div>
            )}

            {/* Step 3: Template */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Elige un template</h2>
                  <p className="text-white/50">Puedes cambiar después</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {TEMPLATES.map((t) => {
                    const Icon = t.icon
                    const isSelected = data.website_template === t.id
                    return (
                      <button
                        key={t.id}
                        onClick={() => updateData('website_template', t.id)}
                        className={`p-4 rounded-lg border-2 transition-all text-left ${
                          isSelected
                            ? 'border-cyan-500 bg-cyan-500/15 shadow-lg shadow-cyan-500/20'
                            : 'border-white/[0.15] bg-white/[0.06] hover:border-cyan-500/40 hover:bg-white/[0.08] hover:shadow-lg hover:shadow-white/[0.05]'
                        }`}
                      >
                        <Icon className="w-6 h-6 mb-2 text-cyan-400" />
                        <p className="font-semibold text-sm">{t.name}</p>
                        <p className="text-xs text-white/50 mt-1">{t.description.substring(0, 50)}...</p>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Step 4: Subdomain */}
            {step === 4 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Tu dominio</h2>
                  <p className="text-white/50">Elige tu subdominio único</p>
                </div>

                <div>
                  <label className="block text-sm text-white/70 mb-3">
                    Subdominio (tunegocio.sellia.app)
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={data.subdomain}
                      onChange={(e) => updateData('subdomain', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                      placeholder="tunegocio"
                      autoFocus
                      className="flex-1 px-4 py-3 rounded-lg bg-white/[0.05] border border-white/[0.1] text-white placeholder-white/40 focus:bg-white/[0.08] focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                    />
                    <span className="text-white/40">.sellia.app</span>
                  </div>
                  <p className="text-xs text-white/40 mt-2">3-63 caracteres, solo letras, números y guiones</p>
                </div>
              </div>
            )}

            {/* Step 5: Summary */}
            {step === 5 && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Resumen de tu setup</h2>
                  <p className="text-white/50">Verifica los datos antes de crear</p>
                </div>

                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-white/[0.06] border border-cyan-500/[0.2] hover:bg-white/[0.08] transition-all duration-200">
                    <p className="text-xs text-white/50 uppercase mb-1">Nombre del negocio</p>
                    <p className="text-lg font-semibold text-white">{data.business_name}</p>
                  </div>

                  <div className="p-4 rounded-lg bg-white/[0.06] border border-cyan-500/[0.2] hover:bg-white/[0.08] transition-all duration-200">
                    <p className="text-xs text-white/50 uppercase mb-1">Descripción</p>
                    <p className="text-sm text-white/80">{data.business_description}</p>
                  </div>

                  <div className="p-4 rounded-lg bg-white/[0.06] border border-cyan-500/[0.2] hover:bg-white/[0.08] transition-all duration-200">
                    <p className="text-xs text-white/50 uppercase mb-1">Template</p>
                    <p className="text-lg font-semibold text-white">
                      {TEMPLATES.find((t) => t.id === data.website_template)?.name}
                    </p>
                  </div>

                  <div className="p-4 rounded-lg bg-white/[0.06] border border-cyan-500/[0.2] hover:bg-white/[0.08] transition-all duration-200">
                    <p className="text-xs text-white/50 uppercase mb-1">Tu dominio</p>
                    <p className="text-lg font-semibold text-cyan-400">{data.subdomain}.sellia.app</p>
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mt-6 flex items-start gap-3 p-4 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-sm font-medium animate-in fade-in slide-in-from-top-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <p>{error}</p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-8">
            <button
              onClick={() => setStep(Math.max(1, step - 1))}
              disabled={step === 1}
              className="flex-1 px-4 py-3 rounded-lg bg-white/[0.06] border border-white/[0.15] text-white hover:bg-white/[0.12] hover:border-white/[0.25] hover:shadow-lg hover:shadow-white/[0.05] focus:outline-none focus:ring-2 focus:ring-white/30 active:scale-[0.96] disabled:opacity-50 transition-all duration-200 font-semibold group"
            >
              <ArrowLeft className="w-4 h-4 inline mr-2 group-hover:-translate-x-0.5 transition-transform" />
              Atrás
            </button>

            <button
              onClick={handleNext}
              disabled={loading}
              className="flex-1 px-4 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-cyan-600 text-white hover:from-cyan-400 hover:to-cyan-500 hover:shadow-xl hover:shadow-cyan-500/40 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 active:scale-[0.96] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 font-bold group"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/25 border-t-white rounded-full animate-spin inline-block" />
              ) : step === 5 ? (
                <>
                  Crear Website <ArrowRight className="w-4 h-4 inline ml-2 group-hover:translate-x-0.5 transition-transform" />
                </>
              ) : (
                <>
                  Siguiente <ArrowRight className="w-4 h-4 inline ml-2 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
