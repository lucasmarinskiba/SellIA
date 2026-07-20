'use client'

/**
 * Onboarding wizard · post-signup · claim subdomain + Stripe Connect.
 */
import { useState, type FormEvent } from 'react'

import { api, QueryProvider, useSellIAAuth, SellIAAuthProvider } from '@/lib/sellia-api'
import { businessContextApi } from '@/lib/businessContext'

function Step({ active, num, label }: { active: boolean; num: number; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold ${
        active ? 'bg-cyan-500 text-black' : 'bg-white/5 text-white/40 border border-white/10'
      }`}>{num}</div>
      <span className={`text-[11px] uppercase tracking-widest ${active ? 'text-white' : 'text-white/30'}`}>{label}</span>
    </div>
  )
}

function OnboardingInner() {
  const { isAuthenticated, isLoading } = useSellIAAuth()
  const [step, setStep] = useState(1)
  const [subdomain, setSubdomain] = useState('')
  const [available, setAvailable] = useState<boolean | null>(null)
  const [checking, setChecking] = useState(false)
  const [claimError, setClaimError] = useState<string | null>(null)
  const [connectUrl, setConnectUrl] = useState<string | null>(null)

  const [contextForm, setContextForm] = useState({
    business_type: 'other',
    industry: '',
    target_audience: '',
    sales_model: 'b2c',
  })
  const [savingContext, setSavingContext] = useState(false)

  if (isLoading) return <div className="min-h-screen bg-[#060812] flex items-center justify-center text-white/50">Cargando…</div>
  if (!isAuthenticated && typeof window !== 'undefined') {
    window.location.href = '/sellia-login'
    return null
  }

  const checkSubdomain = async (value: string) => {
    setSubdomain(value)
    setAvailable(null)
    setClaimError(null)
    if (value.length < 3) return
    setChecking(true)
    try {
      const r = await api.get(`/onboarding/subdomain/check`, { params: { subdomain: value } })
      setAvailable(r.data.available)
      if (!r.data.available && r.data.reason) setClaimError(r.data.reason)
    } catch (e: any) {
      setClaimError(e?.response?.data?.detail || 'Error verificando')
    } finally {
      setChecking(false)
    }
  }

  const claim = async (e: FormEvent) => {
    e.preventDefault()
    setClaimError(null)
    try {
      await api.post('/onboarding/subdomain', { subdomain })
      setStep(2)
    } catch (e: any) {
      setClaimError(e?.response?.data?.detail || 'Error claiming')
    }
  }

  const saveContext = async () => {
    setSavingContext(true)
    try {
      await businessContextApi.updateContext({
        business_type: contextForm.business_type,
        industry: contextForm.industry,
        target_audience: contextForm.target_audience,
        sales_model: contextForm.sales_model,
      })
      setStep(3)
    } catch (e: any) {
      setClaimError(e?.response?.data?.detail || 'Error guardando perfil')
    } finally {
      setSavingContext(false)
    }
  }

  const startConnect = async () => {
    try {
      const r = await api.post('/connect/onboard', {
        return_url: `${window.location.origin}/sellia-onboarding?step=3`,
        refresh_url: `${window.location.origin}/sellia-onboarding?step=2`,
      })
      setConnectUrl(r.data.onboarding_url)
      window.location.href = r.data.onboarding_url
    } catch (e: any) {
      setClaimError(e?.response?.data?.detail || 'Stripe Connect failed')
    }
  }

  return (
    <div className="min-h-screen bg-[#060812] py-12 px-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-black mb-1">
          <span className="bg-gradient-to-r from-cyan-400 to-pink-400 bg-clip-text text-transparent uppercase tracking-widest">Onboarding SellIA</span>
        </h1>
        <p className="text-[12px] text-white/50 mb-8">Configurá tu tenant en 3 pasos · ~3 minutos</p>

        <div className="flex items-center gap-4 mb-8">
          <Step active={step >= 1} num={1} label="Subdomain" />
          <div className="h-px flex-1 bg-white/10" />
          <Step active={step >= 2} num={2} label="Perfil" />
          <div className="h-px flex-1 bg-white/10" />
          <Step active={step >= 3} num={3} label="Stripe" />
          <div className="h-px flex-1 bg-white/10" />
          <Step active={step >= 4} num={4} label="Listo" />
        </div>

        {step === 1 && (
          <div className="rounded-2xl border border-cyan-500/20 bg-[#0a0e1a]/80 p-6">
            <h2 className="text-base font-bold mb-2">1 · Elegí tu subdominio</h2>
            <p className="text-[11px] text-white/40 mb-4">Tu negocio vivirá en <code className="text-cyan-300">{subdomain || 'tunegocio'}.sellia.app</code></p>
            <form onSubmit={claim} className="space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  required
                  minLength={3}
                  maxLength={63}
                  pattern="[a-z][a-z0-9-]{1,61}[a-z0-9]"
                  value={subdomain}
                  onChange={(e) => checkSubdomain(e.target.value.toLowerCase())}
                  placeholder="tunegocio"
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-cyan-400/50 font-mono"
                />
                <span className="text-sm text-white/40 font-mono">.sellia.app</span>
              </div>

              {checking && <p className="text-[11px] text-white/40">Verificando…</p>}
              {available === true && <p className="text-[11px] text-emerald-400">✓ Disponible</p>}
              {claimError && <p className="text-[11px] text-red-400">{claimError}</p>}

              <button type="submit" disabled={!available || checking}
                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-pink-500 text-white font-bold text-sm disabled:opacity-40">
                Reservar y continuar
              </button>
            </form>
          </div>
        )}

        {step === 2 && (
          <div className="rounded-2xl border border-brand-orange/20 bg-[#0a0e1a]/80 p-6">
            <h2 className="text-base font-bold mb-2">2 · Perfil de negocio</h2>
            <p className="text-[11px] text-white/40 mb-4">Contanos qué hacés para personalizar la IA.</p>
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] text-white/40 mb-1">Tipo de negocio</label>
                <select
                  value={contextForm.business_type}
                  onChange={(e) => setContextForm({ ...contextForm, business_type: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-orange/40"
                >
                  <option value="physical_products">Productos físicos</option>
                  <option value="digital_products">Productos digitales</option>
                  <option value="services">Servicios</option>
                  <option value="consulting">Consultoría / Coaching</option>
                  <option value="software">Software / SaaS</option>
                  <option value="food_beverage">Food & Beverage</option>
                  <option value="fashion_beauty">Moda & Belleza</option>
                  <option value="health_wellness">Salud & Bienestar</option>
                  <option value="home_decor">Hogar & Decoración</option>
                  <option value="handcraft">Artesanías</option>
                  <option value="other">Otro</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] text-white/40 mb-1">Industria / Rubro</label>
                <input
                  type="text"
                  value={contextForm.industry}
                  onChange={(e) => setContextForm({ ...contextForm, industry: e.target.value })}
                  placeholder="Ej: Indumentaria femenina"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-brand-orange/40"
                />
              </div>
              <div>
                <label className="block text-[11px] text-white/40 mb-1">Público objetivo</label>
                <input
                  type="text"
                  value={contextForm.target_audience}
                  onChange={(e) => setContextForm({ ...contextForm, target_audience: e.target.value })}
                  placeholder="Ej: Mujeres 25-40"
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-brand-orange/40"
                />
              </div>
              <div>
                <label className="block text-[11px] text-white/40 mb-1">Modelo de venta</label>
                <select
                  value={contextForm.sales_model}
                  onChange={(e) => setContextForm({ ...contextForm, sales_model: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-orange/40"
                >
                  <option value="b2c">B2C</option>
                  <option value="b2b">B2B</option>
                  <option value="b2b2c">B2B2C</option>
                  <option value="d2c">D2C</option>
                  <option value="marketplace">Marketplace</option>
                </select>
              </div>
              {claimError && <p className="text-[11px] text-red-400">{claimError}</p>}
              <button
                onClick={saveContext}
                disabled={savingContext}
                className="w-full py-2.5 rounded-lg bg-gradient-to-r from-brand-orange to-brand-violet text-white font-bold text-sm disabled:opacity-40"
              >
                {savingContext ? 'Guardando…' : 'Guardar y continuar →'}
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="rounded-2xl border border-purple-500/20 bg-[#0a0e1a]/80 p-6">
            <h2 className="text-base font-bold mb-2">3 · Conectá Stripe</h2>
            <p className="text-[11px] text-white/40 mb-4">Cobrá a tus clientes vía Stripe Connect. Comisión SellIA: <span className="text-emerald-400 font-bold">5%</span> por transacción.</p>
            <button onClick={startConnect}
              className="w-full py-2.5 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold text-sm">
              Conectar Stripe Express →
            </button>
            <button onClick={() => setStep(4)}
              className="w-full mt-2 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 text-xs">
              Saltar por ahora
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="rounded-2xl border border-emerald-500/20 bg-[#0a0e1a]/80 p-6 text-center">
            <div className="text-4xl mb-3">🎉</div>
            <h2 className="text-base font-bold mb-2">¡Listo!</h2>
            <p className="text-[12px] text-white/60 mb-5">Tu Brain Hub está activo en <code className="text-cyan-300">{subdomain}.sellia.app</code></p>
            <a href="/dashboard" className="inline-block py-2.5 px-6 rounded-lg bg-gradient-to-r from-emerald-500 to-cyan-500 text-white font-bold text-sm">
              Ir al Dashboard →
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default function OnboardingPage() {
  return (
    <QueryProvider>
      <SellIAAuthProvider>
        <OnboardingInner />
      </SellIAAuthProvider>
    </QueryProvider>
  )
}
