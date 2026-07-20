'use client'

import { useState, useEffect } from 'react'
import { automationsApi, WorkflowVariant, ABTestResult, Workflow } from '@/lib/automations'
import Button from '@/components/ui/Button'
import {
  X, Loader2, Plus, Trash2, Edit3, Check, BarChart3, TrendingUp, Users, Target, FlaskConical,
} from 'lucide-react'

interface ABTestModalProps {
  workflow: Workflow
  onClose: () => void
}

export default function ABTestModal({ workflow, onClose }: ABTestModalProps) {
  const [variants, setVariants] = useState<WorkflowVariant[]>([])
  const [results, setResults] = useState<ABTestResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingVariant, setEditingVariant] = useState<WorkflowVariant | null>(null)
  const [form, setForm] = useState({
    variant_name: '',
    traffic_split: 50,
    actions: [] as Record<string, any>[],
    is_control: false,
    is_active: true,
  })

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [v, r] = await Promise.all([
        automationsApi.getVariants(workflow.id),
        automationsApi.getABTestResults(workflow.id),
      ])
      setVariants(v)
      setResults(r)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflow.id])

  const resetForm = () => {
    setForm({ variant_name: '', traffic_split: 50, actions: [], is_control: false, is_active: true })
    setEditingVariant(null)
    setShowForm(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (editingVariant) {
        await automationsApi.updateVariant(workflow.id, editingVariant.id, form)
      } else {
        await automationsApi.createVariant(workflow.id, form)
      }
      resetForm()
      loadData()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al guardar variante')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (variantId: string) => {
    if (!confirm('¿Eliminar esta variante?')) return
    try {
      await automationsApi.deleteVariant(workflow.id, variantId)
      loadData()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al eliminar')
    }
  }

  const startEdit = (v: WorkflowVariant) => {
    setEditingVariant(v)
    setForm({
      variant_name: v.variant_name,
      traffic_split: v.traffic_split,
      actions: v.actions || [],
      is_control: v.is_control,
      is_active: v.is_active,
    })
    setShowForm(true)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <div>
            <h2 className="text-xl font-bold text-brand-night flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-brand-orange" />
              A/B Testing: {workflow.name}
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Crea variantes para probar diferentes acciones y optimiza la conversión.
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-600 text-sm">
              <TrendingUp className="w-4 h-4" />
              {error}
            </div>
          )}

          {/* Results Summary */}
          {results && results.variants.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Resultados
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-brand-night">{results.total_executions}</p>
                  <p className="text-xs text-slate-500">Ejecuciones totales</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-brand-orange">{results.variants.length}</p>
                  <p className="text-xs text-slate-500">Variantes activas</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {results.winner || '-'}
                  </p>
                  <p className="text-xs text-slate-500">Ganador</p>
                </div>
              </div>
              {results.recommendation && (
                <div className="p-3 rounded-lg bg-brand-orange/5 text-sm text-brand-night">
                  <span className="font-medium">💡 Recomendación:</span> {results.recommendation}
                </div>
              )}
            </div>
          )}

          {/* Variants List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-700">Variantes</h3>
              <Button size="sm" onClick={() => setShowForm(!showForm)} leftIcon={<Plus className="w-3 h-3" />}>
                Nueva variante
              </Button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-10">
                <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
              </div>
            ) : (
              <div className="space-y-2">
                {variants.map(v => (
                  <div
                    key={v.id}
                    className={`flex items-center justify-between p-4 rounded-xl border ${
                      v.is_control ? 'border-brand-orange bg-brand-orange/5' : 'border-slate-200 bg-white'
                    }`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-brand-night">{v.variant_name}</span>
                        {v.is_control && (
                          <span className="px-2 py-0.5 rounded-full bg-brand-orange text-white text-xs font-medium">
                            Control
                          </span>
                        )}
                        {!v.is_active && (
                          <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-600 text-xs">
                            Inactiva
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                        <span className="flex items-center gap-1"><Target className="w-3 h-3" /> {v.traffic_split}% tráfico</span>
                        <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {v.execution_count} ejec.</span>
                        <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3" /> {v.conversion_count} conv.</span>
                        <span className="flex items-center gap-1">
                          <BarChart3 className="w-3 h-3" />
                          {v.execution_count > 0 ? ((v.conversion_count / v.execution_count) * 100).toFixed(1) : 0}% tasa
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button onClick={() => startEdit(v)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600">
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(v.id)} className="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
                {variants.length === 0 && (
                  <div className="text-center py-8 text-slate-400 text-sm">
                    <FlaskConical className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    No hay variantes. Crea la primera para empezar a testear.
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Create/Edit Form */}
          {showForm && (
            <form onSubmit={handleSubmit} className="space-y-4 p-4 rounded-xl border border-slate-200 bg-slate-50">
              <h4 className="text-sm font-semibold text-slate-700">
                {editingVariant ? 'Editar variante' : 'Nueva variante'}
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
                  <input
                    type="text"
                    value={form.variant_name}
                    onChange={e => setForm(f => ({ ...f, variant_name: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                    placeholder="Ej: Variante B - Descuento 20%"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Tráfico (%)</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={form.traffic_split}
                    onChange={e => setForm(f => ({ ...f, traffic_split: parseInt(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                    required
                  />
                </div>
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={form.is_control}
                    onChange={e => setForm(f => ({ ...f, is_control: e.target.checked }))}
                    className="rounded border-slate-300"
                  />
                  Variante control (original)
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))}
                    className="rounded border-slate-300"
                  />
                  Activa
                </label>
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button type="button" onClick={resetForm} className="px-3 py-2 text-sm text-slate-600 hover:text-slate-800">
                  Cancelar
                </button>
                <Button type="submit" size="sm" disabled={saving} leftIcon={saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}>
                  {saving ? 'Guardando...' : 'Guardar'}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
