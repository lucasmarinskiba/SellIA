'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/sellia-api'
import {
  Sparkles, Search, Loader2, AlertCircle, X, RefreshCw, Users,
  TrendingUp, Award, Crown, Target, Mail, CheckCircle2, Zap,
} from 'lucide-react'

interface FunnelHealth {
  total_prospects: number
  stage_breakdown: Record<string, number>
  conversion_rates: Record<string, number>
  fomo_contribution: number
  personality_match_lift: number
  average_deal_cycle: number
  average_deal_value: number
}

interface LoyaltyStatus {
  user_id: string
  tier: string
  points_balance: number
  points_to_next_tier: number
  progress_to_next_tier: number
  exclusive_perks_unlocked: string[]
  dedicated_account_manager: string | null
  referral_bonus_available: boolean
  churn_risk_score: number
}

interface ClosingEffectiveness {
  user_id: string
  sequence_id: string
  deal_stage: string
  probability_to_close: number
  estimated_deal_value: number
  touches_sent: number
  touch_1_opened: boolean
  objections_raised: string[]
  demo_scheduled: boolean
  demo_date: string | null
  last_closing_angle: string | null
  closed_value: number
}

const TIER_COLOR: Record<string, string> = {
  bronze: 'text-orange-400 bg-orange-400/10 border-orange-400/20',
  silver: 'text-slate-300 bg-slate-300/10 border-slate-300/20',
  gold: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  platinum: 'text-cyan-300 bg-cyan-300/10 border-cyan-300/20',
}

const PERSONALITIES = ['pragmatist', 'skeptic', 'impulse_buyer', 'early_adopter', 'analyst', 'social_proof_seeker', 'status_conscious', 'value_maximizer']

function pct(n: number): string {
  return `${Math.round(n * 100)}%`
}

export default function AcquisitionEnginePage() {
  const [funnel, setFunnel] = useState<FunnelHealth | null>(null)
  const [funnelError, setFunnelError] = useState<string | null>(null)
  const [loadingFunnel, setLoadingFunnel] = useState(true)

  const [searchId, setSearchId] = useState('')
  const [searchEmail, setSearchEmail] = useState('')
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [loyalty, setLoyalty] = useState<LoyaltyStatus | null>(null)
  const [loyaltyNotFound, setLoyaltyNotFound] = useState(false)
  const [closing, setClosing] = useState<ClosingEffectiveness | null>(null)
  const [closingNotFound, setClosingNotFound] = useState(false)

  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [personality, setPersonality] = useState('pragmatist')

  const loadFunnel = useCallback(async () => {
    setLoadingFunnel(true)
    setFunnelError(null)
    try {
      const r = await api.get<FunnelHealth>('/api/v1/acquisition-orchestrator/funnel-health')
      setFunnel(r.data)
    } catch (e: unknown) {
      setFunnelError(e instanceof Error ? e.message : 'Error cargando funnel health')
    } finally {
      setLoadingFunnel(false)
    }
  }, [])

  useEffect(() => { void loadFunnel() }, [loadFunnel])

  const runSearch = useCallback(async () => {
    if (!searchId.trim()) return
    setSearching(true)
    setSearchError(null)
    setLoyalty(null)
    setClosing(null)
    setLoyaltyNotFound(false)
    setClosingNotFound(false)

    const [loyaltyRes, closingRes] = await Promise.allSettled([
      api.get<LoyaltyStatus>(`/api/v1/loyalty-engine/loyalty-status/${encodeURIComponent(searchId)}`),
      api.get<ClosingEffectiveness>(`/api/v1/conversion-engine/closing-effectiveness/${encodeURIComponent(searchId)}`),
    ])

    if (loyaltyRes.status === 'fulfilled') setLoyalty(loyaltyRes.value.data)
    else setLoyaltyNotFound(true)

    if (closingRes.status === 'fulfilled') setClosing(closingRes.value.data)
    else setClosingNotFound(true)

    setSearching(false)
  }, [searchId])

  const enrollLoyalty = async () => {
    if (!searchId.trim() || !searchEmail.trim()) { setSearchError('Necesito user_id + email para inscribir'); return }
    setActionLoading('enroll')
    try {
      const r = await api.post<LoyaltyStatus>(`/api/v1/loyalty-engine/enroll-loyalty/${encodeURIComponent(searchId)}`, searchEmail)
      setLoyalty(r.data as unknown as LoyaltyStatus)
      setLoyaltyNotFound(false)
    } catch (e: unknown) {
      setSearchError(e instanceof Error ? e.message : 'Error al inscribir')
    } finally {
      setActionLoading(null)
    }
  }

  const unlockVip = async () => {
    setActionLoading('vip')
    try {
      await api.post(`/api/v1/loyalty-engine/unlock-vip/${encodeURIComponent(searchId)}`)
      await runSearch()
    } catch (e: unknown) {
      setSearchError(e instanceof Error ? e.message : 'Error al desbloquear VIP')
    } finally {
      setActionLoading(null)
    }
  }

  const startClosing = async () => {
    if (!searchEmail.trim()) { setSearchError('Necesito el email para arrancar la secuencia'); return }
    setActionLoading('closing')
    try {
      await api.post(`/api/v1/conversion-engine/start-closing-sequence/${encodeURIComponent(searchId)}`, {
        email: searchEmail,
        personality_type: personality,
      })
      await runSearch()
    } catch (e: unknown) {
      setSearchError(e instanceof Error ? e.message : 'Error al iniciar secuencia')
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="space-y-8 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-brand-orange" />
            Motor de Adquisición
          </h1>
          <p className="text-sm text-white/40">Perfil de personalidad → FOMO → cierre → loyalty, en un solo lugar</p>
        </div>
        <button
          onClick={loadFunnel}
          disabled={loadingFunnel}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-brand-orange/10 border border-brand-orange/20 text-sm text-brand-orange hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loadingFunnel ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Funnel health */}
      {funnelError && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" /> {funnelError}
        </div>
      )}
      {funnel && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-brand-orange" /> Funnel general
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
              <p className="text-2xl font-bold text-white">{funnel.total_prospects}</p>
              <p className="text-xs text-white/30 mt-1">Prospectos totales</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
              <p className="text-2xl font-bold text-white">{pct(funnel.conversion_rates.overall ?? 0)}</p>
              <p className="text-xs text-white/30 mt-1">Conversión total</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
              <p className="text-2xl font-bold text-white">{pct(funnel.fomo_contribution)}</p>
              <p className="text-xs text-white/30 mt-1">Atribuido a FOMO</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 text-center">
              <p className="text-2xl font-bold text-white">{funnel.average_deal_cycle}d</p>
              <p className="text-xs text-white/30 mt-1">Ciclo promedio</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {Object.entries(funnel.stage_breakdown).map(([stage, count]) => (
              <div key={stage} className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-3 text-center">
                <p className="text-lg font-bold text-brand-orange">{count}</p>
                <p className="text-[10px] text-white/30 capitalize mt-0.5">{stage.replace(/_/g, ' ')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Per-user lookup */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
          <Users className="w-5 h-5 text-brand-orange" /> Buscar un lead o cliente
        </h2>
        <div className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-4 flex flex-col sm:flex-row gap-3">
          <input
            value={searchId}
            onChange={e => setSearchId(e.target.value)}
            placeholder="user_id"
            className="flex-1 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          />
          <input
            value={searchEmail}
            onChange={e => setSearchEmail(e.target.value)}
            placeholder="email (para inscribir/iniciar secuencia)"
            className="flex-1 px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          />
          <button
            onClick={runSearch}
            disabled={searching || !searchId.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors disabled:opacity-50"
          >
            {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Buscar
          </button>
        </div>

        {searchError && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4" /> {searchError}
            <button onClick={() => setSearchError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
          </div>
        )}

        {(loyalty || loyaltyNotFound || closing || closingNotFound) && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Loyalty card */}
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Award className="w-4 h-4 text-brand-orange" /> Loyalty
                </h3>
                {loyalty && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border uppercase font-semibold ${TIER_COLOR[loyalty.tier] || 'text-white/50 bg-white/5 border-white/10'}`}>
                    {loyalty.tier}
                  </span>
                )}
              </div>

              {loyalty ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-white/5">
                      <p className="text-white/20">Puntos</p>
                      <p className="text-white font-medium">{loyalty.points_balance}</p>
                    </div>
                    <div className="p-2 rounded-lg bg-white/5">
                      <p className="text-white/20">Riesgo de churn</p>
                      <p className="text-white font-medium">{pct(loyalty.churn_risk_score)}</p>
                    </div>
                  </div>
                  {loyalty.exclusive_perks_unlocked.length > 0 && (
                    <div className="space-y-1">
                      {loyalty.exclusive_perks_unlocked.slice(0, 3).map((perk, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-[11px] text-white/50">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" /> {perk}
                        </div>
                      ))}
                    </div>
                  )}
                  {loyalty.tier !== 'platinum' && (
                    <button
                      onClick={unlockVip}
                      disabled={actionLoading === 'vip'}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-medium hover:bg-cyan-500/20 transition-colors disabled:opacity-50"
                    >
                      {actionLoading === 'vip' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Crown className="w-3 h-3" />}
                      Desbloquear VIP
                    </button>
                  )}
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-xs text-white/30 mb-3">No inscripto en loyalty todavía</p>
                  <button
                    onClick={enrollLoyalty}
                    disabled={actionLoading === 'enroll'}
                    className="flex items-center gap-2 mx-auto px-3 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-xs font-medium hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
                  >
                    {actionLoading === 'enroll' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Award className="w-3 h-3" />}
                    Inscribir
                  </button>
                </div>
              )}
            </motion.div>

            {/* Closing sequence card */}
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Target className="w-4 h-4 text-brand-orange" /> Secuencia de cierre
                </h3>
                {closing && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border uppercase font-semibold text-white/60 bg-white/5 border-white/10">
                    {closing.deal_stage}
                  </span>
                )}
              </div>

              {closing ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-white/5">
                      <p className="text-white/20">Touches enviados</p>
                      <p className="text-white font-medium">{closing.touches_sent}/4</p>
                    </div>
                    <div className="p-2 rounded-lg bg-white/5">
                      <p className="text-white/20">Valor cerrado</p>
                      <p className="text-white font-medium">${closing.closed_value || 0}</p>
                    </div>
                  </div>
                  {closing.last_closing_angle && (
                    <p className="text-[11px] text-white/40">Ángulo: <span className="text-white/70">{closing.last_closing_angle}</span></p>
                  )}
                </div>
              ) : (
                <div className="text-center py-4 space-y-3">
                  <p className="text-xs text-white/30">Sin secuencia activa</p>
                  <select
                    value={personality}
                    onChange={e => setPersonality(e.target.value)}
                    className="w-full px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white"
                  >
                    {PERSONALITIES.map(p => <option key={p} value={p} className="bg-[#0A0E1A]">{p}</option>)}
                  </select>
                  <button
                    onClick={startClosing}
                    disabled={actionLoading === 'closing'}
                    className="flex items-center gap-2 mx-auto px-3 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-xs font-medium hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
                  >
                    {actionLoading === 'closing' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                    Iniciar secuencia
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </div>
    </div>
  )
}
