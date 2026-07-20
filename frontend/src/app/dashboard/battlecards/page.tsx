'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '@/lib/api'
import {
  Swords,
  Loader2,
  AlertCircle,
  X,
  Plus,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
  Check,
  X as XIcon,
  Zap,
} from 'lucide-react'
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/Dialog'

interface Competitor {
  id: string
  name: string
  url: string
  market_share: number
  price_comparison: 'higher' | 'lower' | 'similar'
  price_amount: number
  strengths: string[]
  weaknesses: string[]
  dimensions: {
    Precio: number
    Features: number
    UX: number
    Soporte: number
    Velocidad: number
  }
  features: Record<string, boolean>
}

const MY_PRODUCT_DIMENSIONS = {
  Precio: 85,
  Features: 90,
  UX: 88,
  Soporte: 92,
  Velocidad: 87,
}

const MY_PRODUCT_FEATURES: Record<string, boolean> = {
  'IA Conversacional': true,
  'Multi-canal': true,
  'Analytics Avanzado': true,
  'API REST': true,
  'Webhooks': true,
  'Whatsapp Business': true,
  'Instagram DM': true,
  'CRM Integrado': true,
  'Facturación': true,
  'White-label': true,
}

const MOCK_COMPETITORS: Competitor[] = [
  {
    id: 'comp-1',
    name: 'ChatCorp Pro',
    url: 'https://chatcorp.example.com',
    market_share: 28,
    price_comparison: 'higher',
    price_amount: 299,
    strengths: ['Enterprise SSO', 'SLA garantizado'],
    weaknesses: ['Precio elevado', 'Curva de aprendizaje'],
    dimensions: { Precio: 60, Features: 85, UX: 75, Soporte: 90, Velocidad: 80 },
    features: {
      'IA Conversacional': true,
      'Multi-canal': true,
      'Analytics Avanzado': true,
      'API REST': true,
      'Webhooks': true,
      'Whatsapp Business': true,
      'Instagram DM': false,
      'CRM Integrado': true,
      'Facturación': false,
      'White-label': true,
    },
  },
  {
    id: 'comp-2',
    name: 'BotFlow',
    url: 'https://botflow.example.com',
    market_share: 18,
    price_comparison: 'lower',
    price_amount: 79,
    strengths: ['Precio accesible', 'Fácil de usar'],
    weaknesses: ['Features limitados', 'Soporte básico'],
    dimensions: { Precio: 95, Features: 55, UX: 92, Soporte: 60, Velocidad: 85 },
    features: {
      'IA Conversacional': true,
      'Multi-canal': false,
      'Analytics Avanzado': false,
      'API REST': false,
      'Webhooks': true,
      'Whatsapp Business': true,
      'Instagram DM': true,
      'CRM Integrado': false,
      'Facturación': false,
      'White-label': false,
    },
  },
  {
    id: 'comp-3',
    name: 'SalesAI',
    url: 'https://salesai.example.com',
    market_share: 15,
    price_comparison: 'similar',
    price_amount: 149,
    strengths: ['Automatización avanzada', 'Integraciones'],
    weaknesses: ['Soporte lento', 'Documentación'],
    dimensions: { Precio: 80, Features: 78, UX: 70, Soporte: 65, Velocidad: 75 },
    features: {
      'IA Conversacional': true,
      'Multi-canal': true,
      'Analytics Avanzado': true,
      'API REST': true,
      'Webhooks': false,
      'Whatsapp Business': true,
      'Instagram DM': true,
      'CRM Integrado': true,
      'Facturación': true,
      'White-label': false,
    },
  },
]

const COMPETITOR_COLORS = ['#FF6B35', '#7C3AED', '#00D4AA']

export default function BattlecardsPage() {
  const [competitors, setCompetitors] = useState<Competitor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCompetitors, setSelectedCompetitors] = useState<string[]>([])
  const [addModalOpen, setAddModalOpen] = useState(false)
  const [newCompetitor, setNewCompetitor] = useState({ name: '', url: '' })

  useEffect(() => {
    fetchBattlecards()
  }, [])

  const fetchBattlecards = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/battlecards')
      const data = res.data.competitors || res.data || []
      setCompetitors(data.length > 0 ? data : MOCK_COMPETITORS)
    } catch {
      setCompetitors(MOCK_COMPETITORS)
    } finally {
      setLoading(false)
    }
  }

  const toggleCompetitor = (id: string) => {
    setSelectedCompetitors((prev) => {
      if (prev.includes(id)) {
        return prev.filter((c) => c !== id)
      }
      if (prev.length >= 3) {
        return [...prev.slice(1), id]
      }
      return [...prev, id]
    })
  }

  const selected = competitors.filter((c) => selectedCompetitors.includes(c.id))

  const radarData = [
    { dimension: 'Precio', 'Mi producto': MY_PRODUCT_DIMENSIONS.Precio },
    { dimension: 'Features', 'Mi producto': MY_PRODUCT_DIMENSIONS.Features },
    { dimension: 'UX', 'Mi producto': MY_PRODUCT_DIMENSIONS.UX },
    { dimension: 'Soporte', 'Mi producto': MY_PRODUCT_DIMENSIONS.Soporte },
    { dimension: 'Velocidad', 'Mi producto': MY_PRODUCT_DIMENSIONS.Velocidad },
  ]

  selected.forEach((comp, idx) => {
    radarData.forEach((d) => {
      ;(d as any)[comp.name] = comp.dimensions[d.dimension as keyof typeof comp.dimensions]
    })
  })

  const allFeatureKeys = Array.from(
    new Set([
      ...Object.keys(MY_PRODUCT_FEATURES),
      ...selected.flatMap((c) => Object.keys(c.features)),
    ])
  )

  const handleAddCompetitor = () => {
    if (!newCompetitor.name.trim() || !newCompetitor.url.trim()) return
    const comp: Competitor = {
      id: `comp-${Date.now()}`,
      name: newCompetitor.name,
      url: newCompetitor.url,
      market_share: 0,
      price_comparison: 'similar',
      price_amount: 0,
      strengths: [],
      weaknesses: [],
      dimensions: { Precio: 70, Features: 70, UX: 70, Soporte: 70, Velocidad: 70 },
      features: Object.fromEntries(allFeatureKeys.map((k) => [k, false])),
    }
    setCompetitors((prev) => [...prev, comp])
    setNewCompetitor({ name: '', url: '' })
    setAddModalOpen(false)
  }

  const priceIcon = (comparison: string) => {
    if (comparison === 'higher') return <TrendingUp className="w-3.5 h-3.5 text-red-400" />
    if (comparison === 'lower') return <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
    return <Minus className="w-3.5 h-3.5 text-white/40" />
  }

  const priceLabel = (comparison: string) => {
    if (comparison === 'higher') return 'Más caro'
    if (comparison === 'lower') return 'Más barato'
    return 'Similar'
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-brand-orange/10">
            <Swords className="w-6 h-6 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Battlecards</h1>
            <p className="text-sm text-white/50">Análisis competitivo</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-6">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Mis Competidores */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Mis Competidores</h2>
            <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={() => setAddModalOpen(true)}>
              Agregar competidor
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {competitors.map((comp, idx) => {
                const isSelected = selectedCompetitors.includes(comp.id)
                return (
                  <motion.div
                    key={comp.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`p-5 rounded-2xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-white/[0.06] border-brand-orange/30 shadow-lg shadow-brand-orange/5'
                        : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.05]'
                    }`}
                    onClick={() => toggleCompetitor(comp.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-semibold text-white">{comp.name}</h3>
                        <a
                          href={comp.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-white/40 hover:text-brand-orange flex items-center gap-1 mt-0.5"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {comp.url.replace(/^https?:\/\//, '')}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      {isSelected && (
                        <div className="w-5 h-5 rounded-full bg-brand-orange/20 flex items-center justify-center">
                          <Check className="w-3 h-3 text-brand-orange" />
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div className="p-2.5 rounded-xl bg-white/[0.03]">
                        <p className="text-[10px] uppercase tracking-wider text-white/40 mb-1">Market share</p>
                        <p className="text-sm font-bold text-white">{comp.market_share}%</p>
                      </div>
                      <div className="p-2.5 rounded-xl bg-white/[0.03]">
                        <p className="text-[10px] uppercase tracking-wider text-white/40 mb-1">Precio</p>
                        <div className="flex items-center gap-1.5">
                          {priceIcon(comp.price_comparison)}
                          <span className="text-sm font-bold text-white">${comp.price_amount}</span>
                        </div>
                        <p className="text-[10px] text-white/30">{priceLabel(comp.price_comparison)}</p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex flex-wrap gap-1.5">
                        {comp.strengths.map((s) => (
                          <Badge key={s} variant="success" className="text-[10px]">
                            {s}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {comp.weaknesses.map((w) => (
                          <Badge key={w} variant="destructive" className="text-[10px]">
                            {w}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        toggleCompetitor(comp.id)
                      }}
                      className="mt-3 w-full py-2 rounded-xl text-xs font-medium transition-colors border border-white/[0.08] text-white/60 hover:bg-white/[0.05] hover:text-white"
                    >
                      {isSelected ? 'Quitar comparativa' : 'Ver comparativa'}
                    </button>
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        </div>

        {/* Comparativa */}
        <AnimatePresence>
          {selected.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]"
            >
              <div className="flex items-center gap-3 mb-6">
                <Zap className="w-5 h-5 text-brand-orange" />
                <h2 className="text-lg font-semibold text-white">Comparativa</h2>
                <span className="text-xs text-white/30 ml-auto">{selected.length}/3 seleccionados</span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Radar Chart */}
                <div className="p-4 rounded-xl bg-white/[0.02]">
                  <ResponsiveContainer width="100%" height={320}>
                    <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis
                        dataKey="dimension"
                        tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                      />
                      <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={{ fill: 'rgba(255,255,255,0.2)', fontSize: 9 }}
                        tickCount={6}
                        stroke="rgba(255,255,255,0.06)"
                      />
                      <Radar
                        name="Mi producto"
                        dataKey="Mi producto"
                        stroke="#FF6B35"
                        fill="#FF6B35"
                        fillOpacity={0.15}
                        strokeWidth={2}
                      />
                      {selected.map((comp, idx) => (
                        <Radar
                          key={comp.id}
                          name={comp.name}
                          dataKey={comp.name}
                          stroke={COMPETITOR_COLORS[idx % COMPETITOR_COLORS.length]}
                          fill={COMPETITOR_COLORS[idx % COMPETITOR_COLORS.length]}
                          fillOpacity={0.1}
                          strokeWidth={2}
                        />
                      ))}
                      <Legend
                        wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.6)' }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#0A0E1A',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '12px',
                          color: '#fff',
                          fontSize: '12px',
                        }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

                {/* Feature Comparison Table */}
                <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/[0.06]">
                        <th className="text-left px-4 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Feature</th>
                        <th className="text-center px-4 py-3 text-xs font-medium text-brand-orange uppercase tracking-wider">Mi producto</th>
                        {selected.map((comp) => (
                          <th key={comp.id} className="text-center px-4 py-3 text-xs font-medium text-white/60 uppercase tracking-wider">
                            {comp.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {allFeatureKeys.map((feature, i) => (
                        <tr
                          key={feature}
                          className={i % 2 === 0 ? 'bg-white/[0.01]' : 'bg-transparent'}
                        >
                          <td className="px-4 py-2.5 text-white/70">{feature}</td>
                          <td className="text-center px-4 py-2.5">
                            {MY_PRODUCT_FEATURES[feature] ? (
                              <Check className="w-4 h-4 text-emerald-400 mx-auto" />
                            ) : (
                              <XIcon className="w-4 h-4 text-white/20 mx-auto" />
                            )}
                          </td>
                          {selected.map((comp) => (
                            <td key={comp.id} className="text-center px-4 py-2.5">
                              {comp.features[feature] ? (
                                <Check className="w-4 h-4 text-emerald-400 mx-auto" />
                              ) : (
                                <XIcon className="w-4 h-4 text-white/20 mx-auto" />
                              )}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Add Competitor Modal */}
      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Agregar competidor</DialogTitle>
            <DialogDescription>Completá los datos del nuevo competidor para analizarlo.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <label className="text-xs font-medium text-white/50 mb-1.5 block">Nombre</label>
              <Input
                placeholder="Ej: Competidor X"
                value={newCompetitor.name}
                onChange={(e) => setNewCompetitor((prev) => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-white/50 mb-1.5 block">URL</label>
              <Input
                placeholder="https://..."
                value={newCompetitor.url}
                onChange={(e) => setNewCompetitor((prev) => ({ ...prev, url: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddModalOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleAddCompetitor} disabled={!newCompetitor.name.trim() || !newCompetitor.url.trim()}>
              Guardar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
