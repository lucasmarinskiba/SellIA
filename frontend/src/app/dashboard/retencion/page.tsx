'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { retentionApi, ReferralProgram, NpsCampaign, NpsScore, CustomerSegment } from '@/lib/retention'
import {
  Heart, Users, Star, Loader2, AlertCircle, X,
  Gift, TrendingUp, TrendingDown, Minus, RefreshCw
} from 'lucide-react'

const SEGMENT_COLORS: Record<string, string> = {
  champions: '#00D4AA',
  loyal: '#3B82F6',
  potential: '#F59E0B',
  new: '#8B5CF6',
  at_risk: '#EF4444',
  lost: '#6B7280',
}

const SEGMENT_LABELS: Record<string, string> = {
  champions: 'Campeones',
  loyal: 'Leales',
  potential: 'Potenciales',
  new: 'Nuevos',
  at_risk: 'En Riesgo',
  lost: 'Perdidos',
}

export default function RetencionPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [referralPrograms, setReferralPrograms] = useState<ReferralProgram[]>([])
  const [npsCampaigns, setNpsCampaigns] = useState<NpsCampaign[]>([])
  const [npsScore, setNpsScore] = useState<NpsScore | null>(null)
  const [segments, setSegments] = useState<CustomerSegment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rfmLoading, setRfmLoading] = useState(false)

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => setError('No se pudieron cargar los negocios'))
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [programs, campaigns, score, segs] = await Promise.all([
        retentionApi.getReferralPrograms(selectedBusinessId),
        retentionApi.getNpsCampaigns(selectedBusinessId),
        retentionApi.getNpsScore(selectedBusinessId).catch(() => null),
        retentionApi.getCustomerSegments(selectedBusinessId),
      ])
      setReferralPrograms(programs)
      setNpsCampaigns(campaigns)
      setNpsScore(score)
      setSegments(segs)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar retención')
    } finally {
      setLoading(false)
    }
  }

  const runRFM = async () => {
    setRfmLoading(true)
    try {
      await retentionApi.calculateRFM(selectedBusinessId)
      await loadAll()
    } catch (e: any) {
      setError('Error al calcular RFM')
    } finally {
      setRfmLoading(false)
    }
  }

  const segmentCounts = segments.reduce((acc, s) => {
    acc[s.segment] = (acc[s.segment] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-8 max-w-7xl">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">❤️ Retención & Lealtad</h1>
          <p className="text-sm text-white/40">Programas de referidos, NPS y segmentación RFM.</p>
        </div>
        <div className="flex items-center gap-3">
          {businesses.length > 0 && (
            <select
              value={selectedBusinessId}
              onChange={e => setSelectedBusinessId(e.target.value)}
              className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
            >
              {businesses.map(b => (
                <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
              ))}
            </select>
          )}
          <button
            onClick={runRFM}
            disabled={rfmLoading}
            className="flex items-center gap-2 px-3 py-2 rounded-xl bg-brand-orange/10 border border-brand-orange/20 text-sm text-brand-orange hover:bg-brand-orange/20 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${rfmLoading ? 'animate-spin' : ''}`} />
            Calcular RFM
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : (
        <>
          {/* NPS Score */}
          {npsScore && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-2 mb-4">
                <Star className="w-5 h-5 text-yellow-400" />
                <h2 className="text-lg font-semibold text-white/80">NPS Score</h2>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 rounded-xl bg-white/5">
                  <p className="text-3xl font-bold text-white">{npsScore.nps}</p>
                  <p className="text-xs text-white/30 mt-1">NPS Total</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-green-500/10">
                  <p className="text-2xl font-bold text-green-400">{npsScore.promoters}</p>
                  <p className="text-xs text-white/30 mt-1">Promotores</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-yellow-500/10">
                  <p className="text-2xl font-bold text-yellow-400">{npsScore.passives}</p>
                  <p className="text-xs text-white/30 mt-1">Pasivos</p>
                </div>
                <div className="text-center p-4 rounded-xl bg-red-500/10">
                  <p className="text-2xl font-bold text-red-400">{npsScore.detractors}</p>
                  <p className="text-xs text-white/30 mt-1">Detractores</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* RFM Segments */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Users className="w-5 h-5 text-brand-teal" />
              Segmentación RFM
              <span className="text-xs text-white/30 font-normal ml-2">({segments.length} clientes)</span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(SEGMENT_LABELS).map(([key, label]) => {
                const count = segmentCounts[key] || 0
                const color = SEGMENT_COLORS[key]
                return (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="glass-card p-4 text-center"
                  >
                    <div className="w-3 h-3 rounded-full mx-auto mb-2" style={{ backgroundColor: color }} />
                    <p className="text-xl font-bold text-white">{count}</p>
                    <p className="text-xs text-white/30">{label}</p>
                  </motion.div>
                )
              })}
            </div>
          </div>

          {/* Referral Programs */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Gift className="w-5 h-5 text-brand-violet" />
              Programas de Referidos
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {referralPrograms.map(prog => (
                <motion.div
                  key={prog.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-card p-5"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-semibold text-white">{prog.name}</h3>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${prog.is_active ? 'bg-green-500/20 text-green-400' : 'bg-white/5 text-white/30'}`}>
                      {prog.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                  <p className="text-xs text-white/30 mb-3">{prog.description || 'Sin descripción'}</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-white/5">
                      <p className="text-white/30">Recompensa</p>
                      <p className="text-white font-medium">{prog.reward_value} {prog.reward_type}</p>
                    </div>
                    <div className="p-2 rounded-lg bg-white/5">
                      <p className="text-white/30">Max referidos</p>
                      <p className="text-white font-medium">{prog.max_referrals_per_user}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
              {referralPrograms.length === 0 && (
                <div className="glass-card p-5 text-center text-white/20 text-sm col-span-full">
                  No hay programas de referidos.
                </div>
              )}
            </div>
          </div>

          {/* NPS Campaigns */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white/80 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-400" />
              Campañas NPS
            </h2>
            <div className="space-y-3">
              {npsCampaigns.map(camp => (
                <motion.div
                  key={camp.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-card p-4 flex items-center justify-between"
                >
                  <div>
                    <h3 className="text-sm font-semibold text-white">{camp.name}</h3>
                    <p className="text-xs text-white/30">{camp.trigger_type} · {camp.trigger_days} días</p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${camp.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-white/5 text-white/30'}`}>
                    {camp.status}
                  </span>
                </motion.div>
              ))}
              {npsCampaigns.length === 0 && (
                <div className="glass-card p-5 text-center text-white/20 text-sm">
                  No hay campañas NPS.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
