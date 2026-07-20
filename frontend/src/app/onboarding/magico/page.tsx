'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'
import {
  Sparkles, Search, Loader2, Store, Package, Bot, Workflow,
  Palette, Users, CheckCircle2, ArrowRight, Wand2, Edit3,
  Camera as Instagram, Globe, Zap, ChevronLeft, RefreshCw
} from 'lucide-react'

/* ============================================================
   ONBOARDING MÁGICO — "Cloná tu negocio con IA"
   ============================================================ */

type Discovery = {
  name: string
  description: string | null
  type: string
  tone_of_voice: string | null
  brand_colors: string[]
  target_audience: string | null
  products: Array<{
    name: string
    description: string | null
    price: number | null
    currency: string
    category: string | null
  }>
  suggested_agents: Array<Record<string, any>>
  suggested_workflows: Array<Record<string, any>>
}

type Stage = 'input' | 'scanning' | 'review' | 'context' | 'creating' | 'success'

type ContextForm = {
  business_type: string
  industry: string
  target_audience: string
  sales_model: string
  geographic_reach: string
  presence_type: string
  primary_goal: string
}

export default function OnboardingMagicoPage() {
  const router = useRouter()
  const [source, setSource] = useState('')
  const [stage, setStage] = useState<Stage>('input')
  const [discovery, setDiscovery] = useState<Discovery | null>(null)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0)
  const [createdIds, setCreatedIds] = useState({ business_id: '', catalog: 0, agents: 0, workflows: 0 })
  const [contextForm, setContextForm] = useState<ContextForm>({
    business_type: 'other',
    industry: '',
    target_audience: '',
    sales_model: 'b2c',
    geographic_reach: 'local',
    presence_type: 'online_only',
    primary_goal: 'more_sales',
  })

  // Animación de progreso durante scanning
  useEffect(() => {
    if (stage !== 'scanning') return
    let p = 0
    const interval = setInterval(() => {
      p += Math.random() * 8 + 2
      if (p > 95) p = 95
      setProgress(p)
    }, 300)
    return () => clearInterval(interval)
  }, [stage])

  const handleAnalyze = async () => {
    if (!source.trim()) return
    setError('')
    setStage('scanning')
    setProgress(0)
    try {
      const { data } = await api.post('/onboarding/analyze', { source: source.trim() })
      setDiscovery(data.discovery)
      // Pre-fill context form from AI discovery
      const typeMap: Record<string, string> = {
        services: 'services',
        goods: 'physical_products',
        digital: 'digital_products',
        mixed: 'other',
      }
      setContextForm({
        business_type: typeMap[data.discovery?.type] || 'other',
        industry: data.discovery?.name || '',
        target_audience: data.discovery?.target_audience || '',
        sales_model: 'b2c',
        geographic_reach: 'local',
        presence_type: 'online_only',
        primary_goal: 'more_sales',
      })
      setProgress(100)
      setTimeout(() => setStage('review'), 600)
    } catch (err: any) {
      setStage('input')
      setError(err.response?.data?.detail || 'No se pudo analizar la fuente. Probá con otra URL.')
    }
  }

  const handleCreate = async () => {
    if (!discovery) return
    setStage('creating')
    try {
      const { data } = await api.post('/onboarding/create', {
        discovery,
        source: source.trim(),
      })
      // Update BusinessContext with enriched fields
      if (data.business_id) {
        try {
          const { businessContextApi } = await import('@/lib/businessContext')
          await businessContextApi.updateContext({
            business_type: contextForm.business_type,
            industry: contextForm.industry,
            target_audience: contextForm.target_audience,
            sales_model: contextForm.sales_model,
            geographic_reach: contextForm.geographic_reach,
            presence_type: contextForm.presence_type,
            primary_goal: contextForm.primary_goal,
            value_proposition: discovery.description || '',
            ai_brand_voice: discovery.tone_of_voice || '',
          }, data.business_id)
        } catch (ctxErr: any) {
          console.warn('Failed to update business context:', ctxErr)
        }
      }
      setCreatedIds({
        business_id: data.business_id,
        catalog: data.catalog_items_count,
        agents: data.agents_count,
        workflows: data.workflows_count,
      })
      setStage('success')
    } catch (err: any) {
      setStage('context')
      setError(err.response?.data?.detail || 'Error al crear el negocio.')
    }
  }

  const businessTypeLabel = (t: string) => {
    const map: Record<string, string> = {
      services: 'Servicios',
      goods: 'Productos físicos',
      digital: 'Productos digitales',
      mixed: 'Mixto',
    }
    return map[t] || t
  }

  return (
    <div className="min-h-screen bg-[#060812] text-white relative overflow-hidden flex flex-col items-center justify-center px-4">
      {/* Background effects */}
      <div className="absolute inset-0 bg-mesh opacity-40" />
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[700px] h-[700px] rounded-full bg-brand-orange/[0.04] blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-brand-violet/[0.03] blur-[120px] pointer-events-none" />

      {/* Floating particles */}
      {stage === 'scanning' && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {Array.from({ length: 20 }).map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-brand-orange/40 rounded-full"
              initial={{
                x: Math.random() * (typeof window !== 'undefined' ? window.innerWidth : 1000),
                y: Math.random() * (typeof window !== 'undefined' ? window.innerHeight : 800),
                opacity: 0,
              }}
              animate={{
                y: [null, -100],
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: 2 + Math.random() * 3,
                repeat: Infinity,
                delay: Math.random() * 2,
              }}
            />
          ))}
        </div>
      )}

      <div className="relative z-10 w-full max-w-[520px]">
        {/* Header */}
        <motion.div
          className="text-center mb-10"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-xs font-semibold tracking-wide uppercase mb-5">
            <Sparkles className="w-3.5 h-3.5" />
            Onboarding Mágico
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">
            Cloná tu negocio <span className="text-brand-orange">con IA</span>
          </h1>
          <p className="text-white/40 text-sm max-w-[360px] mx-auto">
            Poné tu Instagram o web y la IA configura todo automáticamente en segundos.
          </p>
        </motion.div>

        <AnimatePresence mode="wait">
          {/* === STAGE: INPUT === */}
          {stage === 'input' && (
            <motion.div
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="space-y-5"
            >
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20">
                  {source.includes('instagram') || source.startsWith('@') ? (
                    <Instagram className="w-5 h-5" />
                  ) : (
                    <Globe className="w-5 h-5" />
                  )}
                </div>
                <input
                  type="text"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  placeholder="@tu_negocio o https://tunegocio.com"
                  className="w-full pl-12 pr-4 py-4 rounded-2xl bg-white/[0.03] border border-white/[0.08] text-white placeholder:text-white/20 focus:outline-none focus:border-brand-orange/40 focus:ring-1 focus:ring-brand-orange/20 transition-all text-base"
                  onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                />
              </div>

              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="flex items-center gap-2 text-red-400 text-sm px-1"
                >
                  <RefreshCw className="w-4 h-4" />
                  {error}
                </motion.div>
              )}

              <button
                onClick={handleAnalyze}
                disabled={!source.trim()}
                className="group w-full flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-gradient-to-r from-brand-orange to-brand-violet text-white font-semibold shadow-lg shadow-brand-orange/20 hover:shadow-brand-orange/30 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                <Wand2 className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                Analizar con IA
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <div className="flex items-center justify-center gap-6 text-white/20 text-xs pt-2">
                <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" /> 60 segundos</span>
                <span className="flex items-center gap-1.5"><Bot className="w-3.5 h-3.5" /> GPT-4o</span>
                <span className="flex items-center gap-1.5"><Store className="w-3.5 h-3.5" /> 100% automático</span>
              </div>
            </motion.div>
          )}

          {/* === STAGE: SCANNING === */}
          {stage === 'scanning' && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              className="text-center py-10"
            >
              <div className="relative w-24 h-24 mx-auto mb-8">
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-brand-orange/30"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  style={{ borderTopColor: 'transparent' }}
                />
                <motion.div
                  className="absolute inset-2 rounded-full border-2 border-brand-violet/30"
                  animate={{ rotate: -360 }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                  style={{ borderBottomColor: 'transparent' }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Search className="w-8 h-8 text-brand-orange" />
                </div>
              </div>

              <h2 className="text-xl font-bold mb-2">Escaneando tu negocio...</h2>
              <p className="text-white/40 text-sm mb-8">La IA está analizando productos, precios y tono de voz</p>

              <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-brand-orange to-brand-violet"
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="text-white/20 text-xs mt-3 text-right">{Math.round(progress)}%</p>
            </motion.div>
          )}

          {/* === STAGE: REVIEW === */}
          {stage === 'review' && discovery && (
            <motion.div
              key="review"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-5"
            >
              {/* Business card */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-2xl bg-white/[0.03] border border-white/[0.08] p-5"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center text-brand-orange">
                      <Store className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg leading-tight">{discovery.name}</h3>
                      <span className="text-xs text-white/40">{businessTypeLabel(discovery.type)}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setStage('input')}
                    className="text-white/20 hover:text-white/50 transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                </div>
                {discovery.description && (
                  <p className="text-sm text-white/50 leading-relaxed">{discovery.description}</p>
                )}
                <div className="flex flex-wrap gap-2 mt-3">
                  {discovery.brand_colors.map((c) => (
                    <span key={c} className="flex items-center gap-1.5 text-xs text-white/40 bg-white/5 px-2 py-1 rounded-lg">
                      <span className="w-3 h-3 rounded-full border border-white/10" style={{ backgroundColor: c }} />
                      {c}
                    </span>
                  ))}
                  {discovery.tone_of_voice && (
                    <span className="flex items-center gap-1.5 text-xs text-white/40 bg-white/5 px-2 py-1 rounded-lg">
                      <Palette className="w-3 h-3" />
                      {discovery.tone_of_voice}
                    </span>
                  )}
                </div>
              </motion.div>

              {/* Products */}
              {discovery.products.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="rounded-2xl bg-white/[0.03] border border-white/[0.08] p-5"
                >
                  <div className="flex items-center gap-2 mb-3 text-brand-teal">
                    <Package className="w-4 h-4" />
                    <span className="text-sm font-semibold">{discovery.products.length} productos detectados</span>
                  </div>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1 custom-scrollbar">
                    {discovery.products.map((p, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                        <div>
                          <p className="text-sm font-medium">{p.name}</p>
                          {p.description && <p className="text-xs text-white/30">{p.description}</p>}
                        </div>
                        {p.price ? (
                          <span className="text-sm font-bold text-brand-teal">${p.price}</span>
                        ) : (
                          <span className="text-xs text-white/20">Consultar</span>
                        )}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Agents & Workflows summary */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="grid grid-cols-2 gap-3"
              >
                <div className="rounded-2xl bg-white/[0.03] border border-white/[0.08] p-4 text-center">
                  <Bot className="w-5 h-5 text-brand-violet mx-auto mb-2" />
                  <p className="text-xl font-bold">{discovery.suggested_agents.length}</p>
                  <p className="text-xs text-white/30">Agentes IA</p>
                </div>
                <div className="rounded-2xl bg-white/[0.03] border border-white/[0.08] p-4 text-center">
                  <Workflow className="w-5 h-5 text-brand-orange mx-auto mb-2" />
                  <p className="text-xl font-bold">{discovery.suggested_workflows.length}</p>
                  <p className="text-xs text-white/30">Automatizaciones</p>
                </div>
              </motion.div>

              {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-400 text-sm text-center">
                  {error}
                </motion.div>
              )}

              <button
                onClick={() => setStage('context')}
                className="group w-full flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-gradient-to-r from-brand-orange to-brand-violet text-white font-semibold shadow-lg shadow-brand-orange/20 hover:shadow-brand-orange/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                <Sparkles className="w-5 h-5" />
                Confirmar y continuar
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </motion.div>
          )}

          {/* === STAGE: CONTEXT === */}
          {stage === 'context' && (
            <motion.div
              key="context"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-5"
            >
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-2xl bg-white/[0.03] border border-white/[0.08] p-5"
              >
                <h3 className="font-bold text-lg mb-1">Contanos más de tu negocio</h3>
                <p className="text-sm text-white/40 mb-4">
                  Esto nos ayuda a personalizar los agentes IA y las estrategias para vos.
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-white/40 mb-1.5">Tipo de negocio</label>
                    <select
                      value={contextForm.business_type}
                      onChange={(e) => setContextForm({ ...contextForm, business_type: e.target.value })}
                      className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-orange/40"
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
                    <label className="block text-xs text-white/40 mb-1.5">Industria / Rubro</label>
                    <input
                      type="text"
                      value={contextForm.industry}
                      onChange={(e) => setContextForm({ ...contextForm, industry: e.target.value })}
                      placeholder="Ej: Indumentaria femenina"
                      className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-brand-orange/40"
                    />
                  </div>

                  <div>
                    <label className="block text-xs text-white/40 mb-1.5">Público objetivo</label>
                    <input
                      type="text"
                      value={contextForm.target_audience}
                      onChange={(e) => setContextForm({ ...contextForm, target_audience: e.target.value })}
                      placeholder="Ej: Mujeres 25-40, clase media-alta"
                      className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-brand-orange/40"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-white/40 mb-1.5">Modelo de venta</label>
                      <select
                        value={contextForm.sales_model}
                        onChange={(e) => setContextForm({ ...contextForm, sales_model: e.target.value })}
                        className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-orange/40"
                      >
                        <option value="b2c">B2C</option>
                        <option value="b2b">B2B</option>
                        <option value="b2b2c">B2B2C</option>
                        <option value="d2c">D2C</option>
                        <option value="marketplace">Marketplace</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-white/40 mb-1.5">Alcance</label>
                      <select
                        value={contextForm.geographic_reach}
                        onChange={(e) => setContextForm({ ...contextForm, geographic_reach: e.target.value })}
                        className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-orange/40"
                      >
                        <option value="local">Local</option>
                        <option value="regional">Regional</option>
                        <option value="national">Nacional</option>
                        <option value="cross_border">Cross-border</option>
                        <option value="global">Global</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs text-white/40 mb-1.5">Objetivo principal</label>
                    <select
                      value={contextForm.primary_goal}
                      onChange={(e) => setContextForm({ ...contextForm, primary_goal: e.target.value })}
                      className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-orange/40"
                    >
                      <option value="more_sales">Más ventas</option>
                      <option value="more_leads">Más leads</option>
                      <option value="more_traffic">Más tráfico</option>
                      <option value="brand_awareness">Awareness de marca</option>
                      <option value="expansion">Expansión</option>
                    </select>
                  </div>
                </div>
              </motion.div>

              {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-400 text-sm text-center">
                  {error}
                </motion.div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => setStage('review')}
                  className="flex-1 py-4 rounded-2xl bg-white/5 border border-white/10 text-white/60 font-semibold text-sm hover:bg-white/10 transition-all"
                >
                  Volver
                </button>
                <button
                  onClick={handleCreate}
                  className="flex-[2] group flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-gradient-to-r from-brand-orange to-brand-violet text-white font-semibold shadow-lg shadow-brand-orange/20 hover:shadow-brand-orange/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                  <Sparkles className="w-5 h-5" />
                  Crear todo con IA
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </motion.div>
          )}

          {/* === STAGE: CREATING === */}
          {stage === 'creating' && (
            <motion.div
              key="creating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-12"
            >
              <Loader2 className="w-10 h-10 text-brand-orange animate-spin mx-auto mb-5" />
              <h2 className="text-xl font-bold mb-2">Configurando tu negocio...</h2>
              <p className="text-white/40 text-sm">Creando catálogo, agentes y automatizaciones</p>
            </motion.div>
          )}

          {/* === STAGE: SUCCESS === */}
          {stage === 'success' && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center py-6"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                className="w-20 h-20 rounded-full bg-brand-teal/10 border border-brand-teal/30 flex items-center justify-center mx-auto mb-6"
              >
                <CheckCircle2 className="w-10 h-10 text-brand-teal" />
              </motion.div>

              <h2 className="text-2xl font-bold mb-2">¡Listo! 🎉</h2>
              <p className="text-white/50 text-sm mb-8">
                Tu negocio fue creado con {createdIds.catalog} productos, {createdIds.agents} agentes y {createdIds.workflows} automatizaciones.
              </p>

              <div className="grid grid-cols-3 gap-3 mb-8">
                <div className="rounded-xl bg-white/[0.03] border border-white/[0.08] p-3">
                  <p className="text-lg font-bold text-brand-teal">{createdIds.catalog}</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-wide">Productos</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] border border-white/[0.08] p-3">
                  <p className="text-lg font-bold text-brand-violet">{createdIds.agents}</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-wide">Agentes</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] border border-white/[0.08] p-3">
                  <p className="text-lg font-bold text-brand-orange">{createdIds.workflows}</p>
                  <p className="text-[10px] text-white/30 uppercase tracking-wide">Workflows</p>
                </div>
              </div>

              <button
                onClick={() => router.push('/dashboard')}
                className="group w-full flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-white text-[#060812] font-bold hover:bg-white/90 active:scale-[0.98] transition-all"
              >
                Ir al Dashboard
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
