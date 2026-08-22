'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/sellia-api'
import {
  Flame, Loader2, AlertCircle, RefreshCw, ShieldCheck, Users2,
  Clock, Sparkles, TrendingUp, Search,
} from 'lucide-react'

interface StrategyDef {
  id: string
  name: string
  description: string
  requires_fields: string[]
}

interface StrategyBreakdownRow {
  strategy_type: string
  personality_type: string
  sample_size: number
  conversion_rate: number
  trust_score: number | null
  confidence_level: string
  recommendation: string
}

interface IntelligenceReport {
  generated_at: string
  total_applications: number
  total_outcomes_measured: number
  strategy_breakdown: StrategyBreakdownRow[]
}

interface TransparencyDashboard {
  verified_metrics: {
    fomo_strategies_registered: number
    total_conversions_tracked: number
    total_impressions_tracked: number
    total_revenue_attributed: number
    overall_conversion_rate: number
  }
  data_integrity_note: string
}

interface RecommendResult {
  personality_type: string
  recommended_strategy: string
  confidence: string
  conversion_rate?: number
  trust_score?: number | null
  reason: string
  alternatives?: { strategy: string; conversion_rate: number }[]
}

const STRATEGY_COLOR: Record<string, string> = {
  escasez_real: 'text-orange-400 bg-orange-400/10 border-orange-400/20',
  prueba_social: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  exclusividad: 'text-violet-400 bg-violet-400/10 border-violet-400/20',
  transparencia: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
}

const CONFIDENCE_LABEL: Record<string, string> = {
  low: 'Baja confianza',
  medium: 'Confianza media',
  high: 'Alta confianza',
  prior: 'Sin datos aún (heurística)',
}

const PERSONALITIES = ['pragmatist', 'skeptic', 'impulse_buyer', 'early_adopter', 'analyst', 'social_proof_seeker', 'status_conscious', 'value_maximizer']

function pct(n: number): string {
  return `${Math.round(n * 100)}%`
}

export default function FomoIntelligencePage() {
  const [strategies, setStrategies] = useState<StrategyDef[]>([])
  const [report, setReport] = useState<IntelligenceReport | null>(null)
  const [transparency, setTransparency] = useState<TransparencyDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [personality, setPersonality] = useState('pragmatist')
  const [recommendation, setRecommendation] = useState<RecommendResult | null>(null)
  const [recommending, setRecommending] = useState(false)

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, r, t] = await Promise.all([
        api.get<{ strategies: StrategyDef[] }>('/api/v1/fomo-intelligence/strategies'),
        api.get<IntelligenceReport>('/api/v1/fomo-intelligence/intelligence-report'),
        api.get<TransparencyDashboard>('/api/v1/fomo-intelligence/transparency-dashboard'),
      ])
      setStrategies(s.data.strategies)
      setReport(r.data)
      setTransparency(t.data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error cargando FOMO Intelligence')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void loadAll() }, [loadAll])

  const runRecommend = useCallback(async () => {
    setRecommending(true)
    try {
      const r = await api.get<RecommendResult>(`/api/v1/fomo-intelligence/recommend-strategy/${encodeURIComponent(personality)}`)
      setRecommendation(r.data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error obteniendo recomendación')
    } finally {
      setRecommending(false)
    }
  }, [personality])

  return (
    <div className="space-y-8 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
            <Flame className="w-8 h-8 text-orange-400" />
            FOMO Intelligence
          </h1>
          <p className="text-sm text-white/40">Escasez real · Prueba social · Exclusividad · Transparencia — qué convierte, medido de verdad</p>
        </div>
        <button
          onClick={loadAll}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-brand-orange/10 border border-brand-orange/20 text-sm text-brand-orange hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : (
        <>
          {/* Transparency: verified real metrics */}
          {transparency && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" /> Métricas verificadas
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
                  <p className="text-2xl font-bold text-white">{transparency.verified_metrics.fomo_strategies_registered}</p>
                  <p className="text-xs text-white/30 mt-1">Estrategias registradas</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
                  <p className="text-2xl font-bold text-white">{transparency.verified_metrics.total_conversions_tracked}</p>
                  <p className="text-xs text-white/30 mt-1">Conversiones</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
                  <p className="text-2xl font-bold text-white">{transparency.verified_metrics.total_impressions_tracked}</p>
                  <p className="text-xs text-white/30 mt-1">Impresiones</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
                  <p className="text-2xl font-bold text-white">${transparency.verified_metrics.total_revenue_attributed}</p>
                  <p className="text-xs text-white/30 mt-1">Revenue atribuido</p>
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
                  <p className="text-2xl font-bold text-white">{pct(transparency.verified_metrics.overall_conversion_rate)}</p>
                  <p className="text-xs text-white/30 mt-1">Conversión general</p>
                </div>
              </div>
              <p className="text-[11px] text-white/25 italic">{transparency.data_integrity_note}</p>
            </div>
          )}

          {/* The 4 strategies */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-brand-orange" /> Las 4 estrategias
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {strategies.map((s, idx) => (
                <motion.div
                  key={s.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className={`bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 border ${STRATEGY_COLOR[s.id]?.split(' ').slice(1).join(' ') || 'border-white/10'}`}
                >
                  <h3 className={`text-sm font-semibold mb-1 ${STRATEGY_COLOR[s.id]?.split(' ')[0] || 'text-white'}`}>{s.name}</h3>
                  <p className="text-xs text-white/40 leading-relaxed">{s.description}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Recommend for personality */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Users2 className="w-5 h-5 text-brand-orange" /> ¿Qué estrategia usar por personalidad?
            </h2>
            <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 flex flex-col sm:flex-row gap-3 items-center">
              <select
                value={personality}
                onChange={e => setPersonality(e.target.value)}
                className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white flex-1"
              >
                {PERSONALITIES.map(p => <option key={p} value={p} className="bg-[#0A0E1A]">{p}</option>)}
              </select>
              <button
                onClick={runRecommend}
                disabled={recommending}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors disabled:opacity-50"
              >
                {recommending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Recomendar
              </button>
            </div>

            {recommendation && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-5">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`text-xs px-3 py-1 rounded-full border font-semibold uppercase ${STRATEGY_COLOR[recommendation.recommended_strategy] || 'text-white bg-white/5 border-white/10'}`}>
                    {recommendation.recommended_strategy.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] text-white/30">{CONFIDENCE_LABEL[recommendation.confidence] || recommendation.confidence}</span>
                </div>
                <p className="text-sm text-white/60">{recommendation.reason}</p>
                {recommendation.conversion_rate !== undefined && (
                  <p className="text-xs text-white/30 mt-2">Conversión medida: {pct(recommendation.conversion_rate)}</p>
                )}
              </motion.div>
            )}
          </div>

          {/* Strategy breakdown table */}
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-brand-orange" /> Rendimiento medido
              {report && <span className="text-xs text-white/30 font-normal ml-2">({report.total_applications} aplicaciones · {report.total_outcomes_measured} resultados)</span>}
            </h2>

            {report && report.strategy_breakdown.length === 0 ? (
              <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-10 text-center">
                <Clock className="w-10 h-10 text-white/10 mx-auto mb-3" />
                <p className="text-white/30 text-sm">Todavía no hay estrategias registradas con resultados medidos.</p>
              </div>
            ) : (
              <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/10 text-left text-white/30 text-xs uppercase">
                        <th className="px-4 py-3">Estrategia</th>
                        <th className="px-4 py-3">Personalidad</th>
                        <th className="px-4 py-3">Muestra</th>
                        <th className="px-4 py-3">Conversión</th>
                        <th className="px-4 py-3">Confianza</th>
                        <th className="px-4 py-3">Recomendación</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report?.strategy_breakdown.map((row, i) => (
                        <tr key={i} className="border-b border-white/5 last:border-0">
                          <td className="px-4 py-3">
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${STRATEGY_COLOR[row.strategy_type] || 'text-white/50 bg-white/5 border-white/10'}`}>
                              {row.strategy_type.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-white/60">{row.personality_type}</td>
                          <td className="px-4 py-3 text-white/60">{row.sample_size}</td>
                          <td className="px-4 py-3 text-white font-medium">{pct(row.conversion_rate)}</td>
                          <td className="px-4 py-3 text-white/40 text-xs">{CONFIDENCE_LABEL[row.confidence_level] || row.confidence_level}</td>
                          <td className="px-4 py-3 text-white/40 text-xs">{row.recommendation}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
