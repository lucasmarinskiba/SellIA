'use client'

export const dynamic = 'force-dynamic'

import { logger } from '@/lib/logger';
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Lightbulb, Check, X, Loader2, Sparkles, MessageSquare, MoveRight, Bot, ShoppingCart, Clock } from 'lucide-react'
import { alertsApi, Recommendation } from '@/lib/alerts'
import { businessApi } from '@/lib/business'
import { Button } from '@/components/ui/Button'

export default function RecomendacionesPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState('')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    businessApi.list().then(res => {
      setBusinesses(res)
      if (res.length > 0) setSelectedBusinessId(res[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadData()
  }, [selectedBusinessId])

  async function loadData() {
    setLoading(true)
    try {
      const data = await alertsApi.getRecommendations(selectedBusinessId, 'pending')
      setRecommendations(data)
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
    }
  }

  async function apply(id: string) {
    await alertsApi.applyRecommendation(id)
    loadData()
  }

  async function dismiss(id: string) {
    await alertsApi.dismissRecommendation(id)
    loadData()
  }

  const typeIcon = (type: string) => {
    switch (type) {
      case 'score_increase': return <Sparkles className="w-5 h-5 text-amber-400" />
      case 'deal_move': return <MoveRight className="w-5 h-5 text-blue-400" />
      case 'follow_up': return <MessageSquare className="w-5 h-5 text-green-400" />
      case 'assign_agent': return <Bot className="w-5 h-5 text-purple-400" />
      case 'create_order': return <ShoppingCart className="w-5 h-5 text-brand-orange" />
      default: return <Lightbulb className="w-5 h-5 text-white/40" />
    }
  }

  const priorityColor = (priority: number) => {
    if (priority >= 5) return 'border-red-500/30 bg-red-500/5'
    if (priority >= 4) return 'border-amber-500/30 bg-amber-500/5'
    if (priority >= 3) return 'border-brand-orange/30 bg-brand-orange/5'
    return 'border-white/[0.06] bg-white/[0.02]'
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Lightbulb className="w-7 h-7 text-brand-orange" />
            Recomendaciones
          </h1>
          <p className="text-sm text-white/40 mt-1">Acciones sugeridas por IA para optimizar tus ventas</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedBusinessId}
            onChange={e => setSelectedBusinessId(e.target.value)}
            className="bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-orange/50"
          >
            {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
      </div>

      {/* Recommendations grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
        </div>
      ) : recommendations.length === 0 ? (
        <div className="text-center py-20">
          <Lightbulb className="w-12 h-12 text-white/10 mx-auto mb-4" />
          <p className="text-white/30">No hay recomendaciones pendientes</p>
          <p className="text-white/20 text-sm mt-1">Las recomendaciones aparecen cuando el sistema detecta oportunidades</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          <AnimatePresence>
            {recommendations.map((rec) => (
              <motion.div
                key={rec.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`rounded-2xl p-5 border ${priorityColor(rec.priority)} hover:bg-white/[0.04] transition-colors`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {typeIcon(rec.type)}
                    <div>
                      <h3 className="text-sm font-semibold text-white">{rec.title}</h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-white/30">Prioridad {rec.priority}/5</span>
                        <span className="text-xs text-white/20">{new Date(rec.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {rec.description && (
                  <p className="text-sm text-white/50 mb-3">{rec.description}</p>
                )}

                {rec.context_data && Object.keys(rec.context_data).length > 0 && (
                  <div className="bg-white/[0.03] rounded-xl p-3 mb-4">
                    <p className="text-xs text-white/30 mb-1">Contexto</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(rec.context_data).map(([k, v]) => (
                        <span key={k} className="text-xs text-white/50 bg-white/[0.04] px-2 py-1 rounded-lg">
                          {k}: {String(v)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    onClick={() => apply(rec.id)}
                    className="flex-1"
                  >
                    <Check className="w-4 h-4 mr-1" />
                    Aplicar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => dismiss(rec.id)}
                  >
                    <X className="w-4 h-4 mr-1" />
                    Descartar
                  </Button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
