'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { businessApi } from '@/lib/business'
import { sequencesApi, EmailSequence, SequenceAnalytics } from '@/lib/sequences'
import {
  Mail, Plus, Loader2, AlertCircle, X, BarChart3,
  Clock, Send, Eye, MousePointerClick, TrendingUp, Trash2
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

export default function SequencesPage() {
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('')
  const [sequences, setSequences] = useState<EmailSequence[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [selectedSequence, setSelectedSequence] = useState<EmailSequence | null>(null)
  const [analytics, setAnalytics] = useState<SequenceAnalytics | null>(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => setError('No se pudieron cargar los negocios'))
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadSequences()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId])

  const loadSequences = async () => {
    setLoading(true)
    setError(null)
    try {
      setSequences(await sequencesApi.list(selectedBusinessId))
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar secuencias')
    } finally {
      setLoading(false)
    }
  }

  const loadAnalytics = async (seq: EmailSequence) => {
    setAnalyticsLoading(true)
    try {
      setAnalytics(await sequencesApi.analytics(seq.id))
    } catch {
      setAnalytics(null)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('¿Eliminar esta secuencia?')) return
    try {
      await sequencesApi.delete(id)
      if (selectedSequence?.id === id) setSelectedSequence(null)
      loadSequences()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al eliminar')
    }
  }

  return (
    <div className="space-y-8 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">📧 Secuencias de Email</h1>
          <p className="text-sm text-white/40">Crea, edita y mide secuencias de email automatizadas.</p>
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
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nueva Secuencia
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sequences List */}
          <div className="lg:col-span-1 space-y-4">
            <h2 className="text-sm font-semibold text-white/60 uppercase tracking-wider">Secuencias</h2>
            {sequences.length === 0 && (
              <div className="glass-card p-6 text-center text-white/20">
                <Mail className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">Sin secuencias aún</p>
              </div>
            )}
            {sequences.map(seq => (
              <motion.div
                key={seq.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`glass-card p-4 cursor-pointer transition-all ${selectedSequence?.id === seq.id ? 'ring-1 ring-brand-orange' : ''}`}
                onClick={() => { setSelectedSequence(seq); loadAnalytics(seq); }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-sm font-semibold text-white">{seq.name}</h3>
                    <p className="text-xs text-white/40">{seq.category || 'Sin categoría'}</p>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${seq.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-white/40'}`}>
                    {seq.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-white/30 mt-3">
                  <span className="flex items-center gap-1"><Send className="w-3 h-3" /> {seq.sent_count}</span>
                  <span className="flex items-center gap-1"><Eye className="w-3 h-3" /> {seq.opens_count}</span>
                  <span className="flex items-center gap-1"><MousePointerClick className="w-3 h-3" /> {seq.clicks_count}</span>
                </div>
                <div className="flex items-center gap-2 mt-3 pt-3 border-t border-white/5">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(seq.id); }}
                    className="p-1.5 rounded-lg hover:bg-red-500/10 text-white/20 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Detail / Analytics */}
          <div className="lg:col-span-2 space-y-5">
            {selectedSequence ? (
              <>
                <div className="glass-card p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-white">{selectedSequence.name}</h2>
                    <span className="text-xs text-white/40">{selectedSequence.steps.length} pasos</span>
                  </div>
                  <div className="space-y-3">
                    {selectedSequence.steps.map((step, i) => (
                      <div key={step.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                        <div className="w-8 h-8 rounded-full bg-brand-orange/20 flex items-center justify-center text-xs font-bold text-brand-orange">
                          {i + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white/80">
                            {step.subject_override || step.body_override?.slice(0, 40) || 'Sin contenido'}
                          </p>
                          <p className="text-xs text-white/30">
                            <Clock className="w-3 h-3 inline mr-1" />
                            +{step.delay_hours}h {step.delay_minutes}m
                            {step.condition && ` • Condición: ${step.condition}`}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {analyticsLoading ? (
                  <div className="flex items-center justify-center py-10">
                    <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
                  </div>
                ) : analytics ? (
                  <>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <KpiCard icon={Send} label="Enviados" value={analytics.total_sent.toLocaleString()} />
                      <KpiCard icon={Eye} label="Aperturas" value={analytics.total_opens.toLocaleString()} />
                      <KpiCard icon={MousePointerClick} label="Clicks" value={analytics.total_clicks.toLocaleString()} />
                      <KpiCard icon={TrendingUp} label="Tasa Apertura" value={`${analytics.open_rate}%`} />
                    </div>

                    <div className="glass-card p-5">
                      <h3 className="text-sm font-semibold text-white/70 mb-4">Envíos por día</h3>
                      <ResponsiveContainer width="100%" height={220}>
                        <BarChart data={analytics.sent_trend}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="date" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                          <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} stroke="rgba(255,255,255,0.1)" />
                          <Tooltip contentStyle={{ background: '#0A0E1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }} />
                          <Bar dataKey="count" fill="#FF6B35" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </>
                ) : (
                  <div className="glass-card p-6 text-center text-white/20">
                    <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p className="text-sm">Sin datos de analytics aún</p>
                  </div>
                )}
              </>
            ) : (
              <div className="glass-card p-10 text-center text-white/20">
                <Mail className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Seleccioná una secuencia para ver detalles y métricas</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Modal */}
      <AnimatePresence>
        {showCreate && (
          <CreateSequenceModal
            businessId={selectedBusinessId}
            onClose={() => setShowCreate(false)}
            onCreated={() => { setShowCreate(false); loadSequences(); }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

function KpiCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-brand-orange" />
        <span className="text-xs text-white/40">{label}</span>
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
    </motion.div>
  )
}

function CreateSequenceModal({ businessId, onClose, onCreated }: {
  businessId: string; onClose: () => void; onCreated: () => void
}) {
  const [name, setName] = useState('')
  const [category, setCategory] = useState('welcome')
  const [steps, setSteps] = useState([
    { step_order: 0, delay_hours: 0, delay_minutes: 0, subject_override: '', body_override: '', condition: '' }
  ])
  const [saving, setSaving] = useState(false)

  const addStep = () => {
    setSteps([...steps, { step_order: steps.length, delay_hours: 24, delay_minutes: 0, subject_override: '', body_override: '', condition: '' }])
  }

  const removeStep = (idx: number) => {
    setSteps(steps.filter((_, i) => i !== idx).map((s, i) => ({ ...s, step_order: i })))
  }

  const updateStep = (idx: number, field: string, value: string | number) => {
    const next = [...steps]
    next[idx] = { ...next[idx], [field]: value }
    setSteps(next)
  }

  const handleSave = async () => {
    if (!name.trim()) return
    setSaving(true)
    try {
      await sequencesApi.create({
        business_id: businessId,
        name,
        category,
        steps: steps.map(s => ({
          ...s,
          delay_hours: Number(s.delay_hours) || 0,
          delay_minutes: Number(s.delay_minutes) || 0,
        })),
      })
      onCreated()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al crear')
    } finally {
      setSaving(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
        className="bg-[#0F1629] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Nueva Secuencia</h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5"><X className="w-5 h-5 text-white/40" /></button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-white/40 mb-1 block">Nombre</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              placeholder="Ej: Bienvenida nuevos leads"
            />
          </div>
          <div>
            <label className="text-xs text-white/40 mb-1 block">Categoría</label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
            >
              <option value="welcome" className="bg-[#0A0E1A]">Bienvenida</option>
              <option value="nurture" className="bg-[#0A0E1A]">Nutrición</option>
              <option value="sales" className="bg-[#0A0E1A]">Ventas</option>
              <option value="cart_recovery" className="bg-[#0A0E1A]">Recuperación carrito</option>
              <option value="re_engagement" className="bg-[#0A0E1A]">Re-engagement</option>
            </select>
          </div>

          <div className="pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white/70">Pasos</h3>
              <button onClick={addStep} className="text-xs text-brand-orange hover:underline">+ Agregar paso</button>
            </div>
            <div className="space-y-3">
              {steps.map((step, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-white/5 border border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-white/40">Paso {idx + 1}</span>
                    {steps.length > 1 && (
                      <button onClick={() => removeStep(idx)} className="text-xs text-red-400 hover:text-red-300">Eliminar</button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] text-white/30 mb-1 block">Delay horas</label>
                      <input
                        type="number"
                        value={step.delay_hours}
                        onChange={e => updateStep(idx, 'delay_hours', e.target.value)}
                        className="w-full px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-white/30 mb-1 block">Delay minutos</label>
                      <input
                        type="number"
                        value={step.delay_minutes}
                        onChange={e => updateStep(idx, 'delay_minutes', e.target.value)}
                        className="w-full px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm"
                      />
                    </div>
                  </div>
                  <input
                    value={step.subject_override}
                    onChange={e => updateStep(idx, 'subject_override', e.target.value)}
                    className="w-full px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm"
                    placeholder="Asunto (opcional)"
                  />
                  <textarea
                    value={step.body_override}
                    onChange={e => updateStep(idx, 'body_override', e.target.value)}
                    rows={3}
                    className="w-full px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm resize-none"
                    placeholder="Cuerpo del email..."
                  />
                  <input
                    value={step.condition}
                    onChange={e => updateStep(idx, 'condition', e.target.value)}
                    className="w-full px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-sm"
                    placeholder="Condición: opened_previous:yes / clicked_previous:no"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-white/5">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-white/60 hover:text-white transition-colors">Cancelar</button>
          <button
            onClick={handleSave}
            disabled={saving || !name.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 disabled:opacity-50 transition-colors"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            Guardar Secuencia
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}
