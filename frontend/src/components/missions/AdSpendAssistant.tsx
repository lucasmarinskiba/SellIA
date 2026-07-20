'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { missionsApi } from '@/lib/missions'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import { Megaphone, X, TrendingUp, Target, Loader2, Zap, BarChart3 } from 'lucide-react'

interface AdSpendAssistantProps {
  onClose: () => void
}

const PLATFORMS = ['meta', 'google', 'tiktok']
const OBJECTIVES = ['awareness', 'conversions', 'lead_generation', 'retention']
const BUSINESS_TYPES = ['ecommerce', 'saas', 'local_service', 'fashion', 'b2b', 'education']

export default function AdSpendAssistant({ onClose }: AdSpendAssistantProps) {
  const [tab, setTab] = useState<'platforms' | 'budget' | 'creatives'>('platforms')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [monthlyBudget, setMonthlyBudget] = useState('500')
  const [businessType, setBusinessType] = useState('ecommerce')
  const [goal, setGoal] = useState('sales')
  const [platform, setPlatform] = useState('meta')

  const fetchPlatforms = async () => {
    setLoading(true)
    try {
      const data = await missionsApi.getAdsPlatformRecommendations(
        { business_type: businessType, country: 'AR' },
        parseInt(monthlyBudget) || 500
      )
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchBudget = async () => {
    setLoading(true)
    try {
      const data = await missionsApi.getAdsBudgetAllocation(
        parseInt(monthlyBudget) || 500,
        businessType,
        goal
      )
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchCreatives = async () => {
    setLoading(true)
    try {
      const data = await missionsApi.getAdsCreativeRecommendations(platform, businessType)
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-[#0c0e1a] border border-white/10 rounded-3xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 bg-[#0c0e1a]/95 backdrop-blur-md border-b border-white/5 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-violet/10 flex items-center justify-center text-brand-violet">
                <Megaphone className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">📢 Asistente de Publicidad</h2>
                <p className="text-xs text-white/40">Meta, Google y TikTok Ads</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="flex gap-2 mt-4">
            {[
              { key: 'platforms', label: 'Plataformas', icon: <Target className="w-3 h-3" /> },
              { key: 'budget', label: 'Presupuesto', icon: <BarChart3 className="w-3 h-3" /> },
              { key: 'creatives', label: 'Creativos', icon: <Zap className="w-3 h-3" /> },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => { setTab(t.key as any); setResult(null); }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  tab === t.key
                    ? 'bg-brand-violet/20 text-brand-violet border border-brand-violet/20'
                    : 'bg-white/5 text-white/40 border border-white/5 hover:bg-white/10'
                }`}
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 mb-1 block">Tipo de negocio</label>
              <select value={businessType} onChange={e => setBusinessType(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm">
                {BUSINESS_TYPES.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1 block">Presupuesto mensual (USD)</label>
              <input type="number" value={monthlyBudget} onChange={e => setMonthlyBudget(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm" />
            </div>
          </div>

          {tab === 'platforms' && (
            <div className="space-y-4">
              <Button onClick={fetchPlatforms} disabled={loading} className="w-full">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Target className="w-4 h-4 mr-2" />}
                Analizar plataformas
              </Button>
              {result && result.ranking && (
                <div className="space-y-3">
                  {result.ranking.map((p: any, i: number) => (
                    <Card key={i} className="border-l-4" style={{ borderLeftColor: i === 0 ? '#00D4AA' : i === 1 ? '#F59E0B' : '#3B82F6' }}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-white capitalize">{p.platform}</p>
                            <p className="text-xs text-white/40">Score: {p.score}/100 · Dificultad: {p.difficulty}</p>
                          </div>
                          <Badge variant={i === 0 ? 'success' : 'secondary'} className="text-[10px]">
                            #{i + 1}
                          </Badge>
                        </div>
                        <p className="text-xs text-white/30 mt-2">{p.reasoning}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {tab === 'budget' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-white/40 mb-1 block">Objetivo</label>
                  <select value={goal} onChange={e => setGoal(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm">
                    <option value="sales">Ventas</option>
                    <option value="leads">Leads</option>
                    <option value="traffic">Tráfico</option>
                    <option value="awareness">Awareness</option>
                  </select>
                </div>
              </div>
              <Button onClick={fetchBudget} disabled={loading} className="w-full">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <BarChart3 className="w-4 h-4 mr-2" />}
                Distribuir presupuesto
              </Button>
              {result && result.allocation && (
                <div className="space-y-3">
                  {Object.entries(result.allocation).map(([plat, alloc]: [string, any]) => (
                    <div key={plat} className="p-3 rounded-lg bg-white/5">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-white/80 capitalize">{plat}</span>
                        <span className="text-sm font-medium text-brand-violet">${alloc.amount_usd}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full bg-brand-violet" style={{ width: `${alloc.percentage}%` }} />
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className="text-[10px] text-white/20">Top: ${alloc.funnel_breakdown.top}</span>
                        <span className="text-[10px] text-white/20">Mid: ${alloc.funnel_breakdown.mid}</span>
                        <span className="text-[10px] text-white/20">Bot: ${alloc.funnel_breakdown.bottom}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {tab === 'creatives' && (
            <div className="space-y-4">
              <div>
                <label className="text-xs text-white/40 mb-1 block">Plataforma</label>
                <select value={platform} onChange={e => setPlatform(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm">
                  {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <Button onClick={fetchCreatives} disabled={loading} className="w-full">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Zap className="w-4 h-4 mr-2" />}
                Ver recomendaciones de creativos
              </Button>
              {result && result.recommendations && (
                <div className="space-y-2">
                  {result.recommendations.map((rec: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-white/5">
                      <TrendingUp className="w-4 h-4 text-brand-orange mt-0.5 shrink-0" />
                      <span className="text-sm text-white/60">{rec}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
