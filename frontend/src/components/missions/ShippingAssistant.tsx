'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { missionsApi } from '@/lib/missions'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { Card, CardContent } from '@/components/ui/Card'
import { Truck, X, Package, Globe, ChevronRight, Loader2, DollarSign } from 'lucide-react'

interface ShippingAssistantProps {
  onClose: () => void
}

const COUNTRIES = ['Brasil', 'Chile', 'Uruguay', 'México', 'Colombia', 'Estados Unidos', 'España']

export default function ShippingAssistant({ onClose }: ShippingAssistantProps) {
  const [tab, setTab] = useState<'recommend' | 'estimate' | 'crossborder'>('recommend')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [carrier, setCarrier] = useState('')
  const [country, setCountry] = useState('Brasil')
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [weight, setWeight] = useState('1')

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const data = await missionsApi.getShippingRecommendations({
        country: 'AR',
        reach: 'national',
        product_type: 'physical_products',
      })
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchEstimate = async () => {
    setLoading(true)
    try {
      const data = await missionsApi.estimateShippingCosts({
        origin,
        destination,
        weight: parseFloat(weight),
        dimensions: { length: 20, width: 15, height: 10 },
      })
      setResult(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const fetchCrossBorder = async () => {
    setLoading(true)
    try {
      const data = await missionsApi.getCrossBorderRequirements(country.toLowerCase())
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
              <div className="w-10 h-10 rounded-xl bg-brand-teal/10 flex items-center justify-center text-brand-teal">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">🚚 Asistente de Envíos</h2>
                <p className="text-xs text-white/40">Carriers, costos y cross-border</p>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="flex gap-2 mt-4">
            {[
              { key: 'recommend', label: 'Recomendaciones', icon: <Package className="w-3 h-3" /> },
              { key: 'estimate', label: 'Cotizar', icon: <DollarSign className="w-3 h-3" /> },
              { key: 'crossborder', label: 'Cross-Border', icon: <Globe className="w-3 h-3" /> },
            ].map(t => (
              <button
                key={t.key}
                onClick={() => { setTab(t.key as any); setResult(null); }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  tab === t.key
                    ? 'bg-brand-teal/20 text-brand-teal border border-brand-teal/20'
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
          {tab === 'recommend' && (
            <div className="space-y-4">
              <Button onClick={fetchRecommendations} disabled={loading} className="w-full">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Package className="w-4 h-4 mr-2" />}
                Ver recomendaciones de carriers
              </Button>
              {result && Array.isArray(result) && (
                <div className="space-y-3">
                  {result.map((r: any, i: number) => (
                    <Card key={i} className="border-l-4" style={{ borderLeftColor: r.score > 80 ? '#00D4AA' : r.score > 50 ? '#F59E0B' : '#EF4444' }}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium text-white">{r.carrier}</p>
                            <p className="text-xs text-white/40">{r.coverage} · {r.integration_difficulty}</p>
                          </div>
                          <Badge variant={r.tier === 'premium' ? 'orange' : 'secondary'} className="text-[10px]">
                            {r.tier}
                          </Badge>
                        </div>
                        {r.recommended && (
                          <p className="text-xs text-brand-teal mt-2">✅ Recomendado para tu negocio</p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {tab === 'estimate' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <input placeholder="Origen (ciudad)" value={origin} onChange={e => setOrigin(e.target.value)} className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm" />
                <input placeholder="Destino (ciudad)" value={destination} onChange={e => setDestination(e.target.value)} className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm" />
              </div>
              <input type="number" placeholder="Peso (kg)" value={weight} onChange={e => setWeight(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm" />
              <Button onClick={fetchEstimate} disabled={loading || !origin || !destination} className="w-full">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <DollarSign className="w-4 h-4 mr-2" />}
                Cotizar envío
              </Button>
              {result && result.estimates && (
                <div className="space-y-2">
                  {result.estimates.map((e: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                      <span className="text-sm text-white/80">{e.carrier}</span>
                      <span className="text-sm font-medium text-brand-teal">{e.cost_ars} ARS</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {tab === 'crossborder' && (
            <div className="space-y-4">
              <select value={country} onChange={e => setCountry(e.target.value)} className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm">
                {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <Button onClick={fetchCrossBorder} disabled={loading} className="w-full">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Globe className="w-4 h-4 mr-2" />}
                Ver requisitos
              </Button>
              {result && (
                <div className="space-y-3">
                  {result.requirements?.map((req: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-white/60">
                      <ChevronRight className="w-4 h-4 text-brand-orange mt-0.5 shrink-0" />
                      {req}
                    </div>
                  ))}
                  {result.recommended_carriers && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {result.recommended_carriers.map((c: string) => (
                        <Badge key={c} variant="secondary" className="text-[10px]">{c}</Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
