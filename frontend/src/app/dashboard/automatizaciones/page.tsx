'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { businessApi } from '@/lib/business'
import { automationsApi, Workflow, EmailTemplate, EmailSequence, ChatbotRule } from '@/lib/automations'
import Button from '@/components/ui/Button'
import {
  Zap, Mail, MessageSquare, GitBranch, Plus, Trash2, Edit3, Power,
  Loader2, AlertCircle, X, Check, Clock, Send, Bot, Wand2, FlaskConical
} from 'lucide-react'
import ABTestModal from '@/components/automations/ABTestModal'

type Tab = 'workflows' | 'templates' | 'sequences' | 'rules'

const TRIGGER_LABELS: Record<string, string> = {
  new_lead: 'Nuevo Lead',
  message_received: 'Mensaje Recibido',
  conversation_idle: 'Conversación Inactiva',
  abandoned_cart: 'Carrito Abandonado',
  follow_up_due: 'Seguimiento Pendiente',
  manual: 'Manual',
}

const INTENT_LABELS: Record<string, string> = {
  greeting: 'Saludo',
  price: 'Precio',
  availability: 'Disponibilidad',
  objection: 'Objeción',
  complaint: 'Reclamo',
  support: 'Soporte',
  goodbye: 'Despedida',
  default: 'Default',
}

export default function AutomatizacionesPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<Tab>('workflows')
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Data states
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [sequences, setSequences] = useState<EmailSequence[]>([])
  const [rules, setRules] = useState<ChatbotRule[]>([])

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState<Tab | null>(null)
  const [editingItem, setEditingItem] = useState<any>(null)
  const [saving, setSaving] = useState(false)
  const [seeding, setSeeding] = useState(false)
  const [seedSuccess, setSeedSuccess] = useState(false)
  const [abTestWorkflow, setAbTestWorkflow] = useState<Workflow | null>(null)

  // Load businesses
  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => setError('No se pudieron cargar los negocios'))
  }, [])

  // Load data when business or tab changes
  useEffect(() => {
    if (!selectedBusinessId) return
    loadData(activeTab)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId, activeTab])

  const loadData = async (tab: Tab) => {
    setLoading(true)
    setError(null)
    try {
      switch (tab) {
        case 'workflows':
          setWorkflows(await automationsApi.getWorkflows(selectedBusinessId))
          break
        case 'templates':
          setTemplates(await automationsApi.getEmailTemplates(selectedBusinessId))
          break
        case 'sequences':
          setSequences(await automationsApi.getEmailSequences(selectedBusinessId))
          break
        case 'rules':
          setRules(await automationsApi.getChatbotRules(selectedBusinessId))
          break
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  const toggleActive = async (tab: Tab, item: any) => {
    try {
      const newState = !item.is_active
      switch (tab) {
        case 'workflows':
          await automationsApi.updateWorkflow(item.id, { is_active: newState })
          setWorkflows(prev => prev.map(w => w.id === item.id ? { ...w, is_active: newState } : w))
          break
        case 'templates':
          await automationsApi.updateEmailTemplate(item.id, { is_active: newState })
          setTemplates(prev => prev.map(t => t.id === item.id ? { ...t, is_active: newState } : t))
          break
        case 'sequences':
          await automationsApi.updateEmailSequence(item.id, { is_active: newState })
          setSequences(prev => prev.map(s => s.id === item.id ? { ...s, is_active: newState } : s))
          break
        case 'rules':
          await automationsApi.updateChatbotRule(item.id, { is_active: newState })
          setRules(prev => prev.map(r => r.id === item.id ? { ...r, is_active: newState } : r))
          break
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al actualizar')
    }
  }

  const deleteItem = async (tab: Tab, id: string) => {
    if (!confirm('¿Estás seguro de eliminar este elemento?')) return
    try {
      switch (tab) {
        case 'workflows':
          await automationsApi.deleteWorkflow(id)
          setWorkflows(prev => prev.filter(w => w.id !== id))
          break
        case 'templates':
          await automationsApi.deleteEmailTemplate(id)
          setTemplates(prev => prev.filter(t => t.id !== id))
          break
        case 'sequences':
          await automationsApi.deleteEmailSequence(id)
          setSequences(prev => prev.filter(s => s.id !== id))
          break
        case 'rules':
          await automationsApi.deleteChatbotRule(id)
          setRules(prev => prev.filter(r => r.id !== id))
          break
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al eliminar')
    }
  }

  const openModal = (tab: Tab, item?: any) => {
    setModalType(tab)
    setEditingItem(item || null)
    setShowModal(true)
  }

  const saveModal = async (data: any) => {
    if (!selectedBusinessId) return
    setSaving(true)
    try {
      const payload = { ...data, business_id: selectedBusinessId }
      switch (modalType) {
        case 'workflows':
          if (editingItem) {
            await automationsApi.updateWorkflow(editingItem.id, payload)
          } else {
            await automationsApi.createWorkflow(payload)
          }
          setWorkflows(await automationsApi.getWorkflows(selectedBusinessId))
          break
        case 'templates':
          if (editingItem) {
            await automationsApi.updateEmailTemplate(editingItem.id, payload)
          } else {
            await automationsApi.createEmailTemplate(payload)
          }
          setTemplates(await automationsApi.getEmailTemplates(selectedBusinessId))
          break
        case 'sequences':
          if (editingItem) {
            await automationsApi.updateEmailSequence(editingItem.id, payload)
          } else {
            await automationsApi.createEmailSequence(payload)
          }
          setSequences(await automationsApi.getEmailSequences(selectedBusinessId))
          break
        case 'rules':
          if (editingItem) {
            await automationsApi.updateChatbotRule(editingItem.id, payload)
          } else {
            await automationsApi.createChatbotRule(payload)
          }
          setRules(await automationsApi.getChatbotRules(selectedBusinessId))
          break
      }
      setShowModal(false)
      setEditingItem(null)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const tabs: { id: Tab; label: string; icon: any; count: number }[] = [
    { id: 'workflows', label: 'Workflows', icon: GitBranch, count: workflows.length },
    { id: 'templates', label: 'Plantillas Email', icon: Mail, count: templates.length },
    { id: 'sequences', label: 'Secuencias', icon: Send, count: sequences.length },
    { id: 'rules', label: 'Reglas Chatbot', icon: Bot, count: rules.length },
  ]

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-brand-night">⚡ Automatizaciones</h1>
          <p className="text-slate-500 mt-1">
            Crea workflows, secuencias de email y reglas de chatbot para automatizar tu ventas.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/dashboard/automatizaciones/builder">
            <Button leftIcon={<Plus className="w-4 h-4" />}>
              Nuevo Workflow
            </Button>
          </Link>
        </div>
      </div>

      {/* Business selector */}
      {businesses.length > 0 && (
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">Negocio:</span>
          <select
            value={selectedBusinessId}
            onChange={e => setSelectedBusinessId(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          >
            {businesses.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        {tabs.map(tab => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                isActive
                  ? 'border-brand-orange text-brand-orange'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              <span className={`px-1.5 py-0.5 rounded-md text-xs ${isActive ? 'bg-brand-orange/10' : 'bg-slate-100'}`}>
                {tab.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-brand-night">
            {tabs.find(t => t.id === activeTab)?.label}
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              onClick={async () => {
                if (!selectedBusinessId) return
                setSeeding(true)
                setSeedSuccess(false)
                try {
                  await automationsApi.seedAutomations(selectedBusinessId)
                  setSeedSuccess(true)
                  loadData(activeTab)
                  setTimeout(() => setSeedSuccess(false), 3000)
                } catch (e: any) {
                  setError(e.response?.data?.detail || 'Error al crear automatizaciones sugeridas')
                } finally {
                  setSeeding(false)
                }
              }}
              disabled={seeding}
              leftIcon={seeding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
            >
              {seeding ? 'Creando...' : 'Sugeridas'}
            </Button>
            <Button onClick={() => openModal(activeTab)} leftIcon={<Plus className="w-4 h-4" />}>
              Nuevo
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
          </div>
        ) : (
          <>
            {activeTab === 'workflows' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {workflows.map(wf => (
                  <div key={wf.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-brand-orange/10 flex items-center justify-center">
                          <GitBranch className="w-5 h-5 text-brand-orange" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-brand-night">{wf.name}</h3>
                          <p className="text-xs text-slate-500">{TRIGGER_LABELS[wf.trigger_type] || wf.trigger_type}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => toggleActive('workflows', wf)}
                          className={`p-2 rounded-lg transition-colors ${wf.is_active ? 'bg-green-50 text-green-600' : 'bg-slate-50 text-slate-400'}`}
                          title={wf.is_active ? 'Activo' : 'Inactivo'}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setAbTestWorkflow(wf)}
                          className="p-2 rounded-lg hover:bg-violet-50 text-slate-400 hover:text-violet-600"
                          title="A/B Testing"
                        >
                          <FlaskConical className="w-4 h-4" />
                        </button>
                        <button onClick={() => openModal('workflows', wf)} className="p-2 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button onClick={() => deleteItem('workflows', wf.id)} className="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {wf.description && <p className="text-sm text-slate-500 mb-3">{wf.description}</p>}
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1"><Zap className="w-3 h-3" /> {wf.execution_count} ejecuciones</span>
                      <span className="flex items-center gap-1"><Check className="w-3 h-3" /> {wf.conversion_count} conversiones</span>
                      <span className={`px-2 py-0.5 rounded-full ${wf.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-slate-50 text-slate-500'}`}>{wf.status}</span>
                    </div>
                  </div>
                ))}
                {workflows.length === 0 && (
                  <div className="col-span-2 text-center py-16 text-slate-400">
                    <GitBranch className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay workflows creados aún.</p>
                    <button onClick={() => openModal('workflows')} className="text-brand-orange text-sm font-medium mt-2 hover:underline">Crear workflow</button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'templates' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map(tpl => (
                  <div key={tpl.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-brand-violet/10 flex items-center justify-center">
                          <Mail className="w-5 h-5 text-brand-violet" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-brand-night">{tpl.name}</h3>
                          <p className="text-xs text-slate-500">{tpl.category || 'Sin categoría'}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => toggleActive('templates', tpl)}
                          className={`p-2 rounded-lg transition-colors ${tpl.is_active ? 'bg-green-50 text-green-600' : 'bg-slate-50 text-slate-400'}`}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button onClick={() => openModal('templates', tpl)} className="p-2 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button onClick={() => deleteItem('templates', tpl.id)} className="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <p className="text-sm font-medium text-slate-700 mb-1">{tpl.subject}</p>
                    <p className="text-sm text-slate-500 line-clamp-2 mb-3">{tpl.body_text}</p>
                    {tpl.variables.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {tpl.variables.map((v: string) => (
                          <span key={v} className="px-2 py-0.5 bg-slate-100 rounded text-xs text-slate-500">{'{{'+v+'}}'}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {templates.length === 0 && (
                  <div className="col-span-2 text-center py-16 text-slate-400">
                    <Mail className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay plantillas de email creadas aún.</p>
                    <button onClick={() => openModal('templates')} className="text-brand-orange text-sm font-medium mt-2 hover:underline">Crear plantilla</button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'sequences' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sequences.map(seq => (
                  <div key={seq.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-brand-teal/10 flex items-center justify-center">
                          <Send className="w-5 h-5 text-brand-teal" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-brand-night">{seq.name}</h3>
                          <p className="text-xs text-slate-500">{seq.category || 'Sin categoría'}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => toggleActive('sequences', seq)}
                          className={`p-2 rounded-lg transition-colors ${seq.is_active ? 'bg-green-50 text-green-600' : 'bg-slate-50 text-slate-400'}`}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button onClick={() => openModal('sequences', seq)} className="p-2 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button onClick={() => deleteItem('sequences', seq.id)} className="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {seq.description && <p className="text-sm text-slate-500 mb-3">{seq.description}</p>}
                    <div className="space-y-2">
                      {seq.steps?.map((step, i) => (
                        <div key={step.id} className="flex items-center gap-3 text-sm">
                          <span className="w-6 h-6 rounded-full bg-brand-teal/10 text-brand-teal flex items-center justify-center text-xs font-medium">{i + 1}</span>
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span className="text-slate-500">{step.delay_hours}h {step.delay_minutes}m</span>
                          <span className="text-slate-400">·</span>
                          <span className="text-slate-600 truncate">{step.subject_override || 'Sin asunto'}</span>
                        </div>
                      ))}
                      {(!seq.steps || seq.steps.length === 0) && (
                        <p className="text-sm text-slate-400 italic">Sin pasos configurados</p>
                      )}
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${seq.status === 'active' ? 'bg-green-50 text-green-600' : 'bg-slate-50 text-slate-500'}`}>{seq.status}</span>
                      {seq.trigger_type && (
                        <span className="px-2 py-0.5 rounded-full text-xs bg-slate-50 text-slate-500">{TRIGGER_LABELS[seq.trigger_type] || seq.trigger_type}</span>
                      )}
                    </div>
                  </div>
                ))}
                {sequences.length === 0 && (
                  <div className="col-span-2 text-center py-16 text-slate-400">
                    <Send className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay secuencias de email creadas aún.</p>
                    <button onClick={() => openModal('sequences')} className="text-brand-orange text-sm font-medium mt-2 hover:underline">Crear secuencia</button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'rules' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {rules.map(rule => (
                  <div key={rule.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-brand-night/10 flex items-center justify-center">
                          <Bot className="w-5 h-5 text-brand-night" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-brand-night">{rule.name}</h3>
                          <p className="text-xs text-slate-500">{INTENT_LABELS[rule.intent] || rule.intent}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => toggleActive('rules', rule)}
                          className={`p-2 rounded-lg transition-colors ${rule.is_active ? 'bg-green-50 text-green-600' : 'bg-slate-50 text-slate-400'}`}
                        >
                          <Power className="w-4 h-4" />
                        </button>
                        <button onClick={() => openModal('rules', rule)} className="p-2 rounded-lg hover:bg-slate-50 text-slate-400 hover:text-slate-600">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button onClick={() => deleteItem('rules', rule.id)} className="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div className="space-y-2 mb-3">
                      <div className="flex flex-wrap gap-1">
                        {rule.keywords.map((k: string) => (
                          <span key={k} className="px-2 py-0.5 bg-brand-orange/10 text-brand-orange rounded text-xs">{k}</span>
                        ))}
                      </div>
                      <p className="text-sm text-slate-600 bg-slate-50 rounded-lg p-3">{rule.response_template}</p>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>Prioridad: {rule.priority}</span>
                      <span>{rule.usage_count} usos</span>
                      {rule.requires_human && <span className="px-2 py-0.5 bg-amber-50 text-amber-600 rounded-full">Requiere humano</span>}
                      {rule.channel_filter.length > 0 && (
                        <span className="px-2 py-0.5 bg-slate-100 rounded-full">{rule.channel_filter.join(', ')}</span>
                      )}
                    </div>
                  </div>
                ))}
                {rules.length === 0 && (
                  <div className="col-span-2 text-center py-16 text-slate-400">
                    <Bot className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay reglas de chatbot creadas aún.</p>
                    <button onClick={() => openModal('rules')} className="text-brand-orange text-sm font-medium mt-2 hover:underline">Crear regla</button>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal */}
      {showModal && modalType && (
        <AutomationModal
          type={modalType}
          item={editingItem}
          onClose={() => { setShowModal(false); setEditingItem(null) }}
          onSave={saveModal}
          saving={saving}
        />
      )}

      {/* A/B Test Modal */}
      {abTestWorkflow && (
        <ABTestModal
          workflow={abTestWorkflow}
          onClose={() => setAbTestWorkflow(null)}
        />
      )}
    </div>
  )
}

/* ============================================================
   MODAL COMPONENT
   ============================================================ */

function AutomationModal({ type, item, onClose, onSave, saving }: {
  type: Tab
  item: any
  onClose: () => void
  onSave: (data: any) => void
  saving: boolean
}) {
  const [form, setForm] = useState<any>(() => {
    if (item) return { ...item }
    switch (type) {
      case 'workflows':
        return { name: '', description: '', trigger_type: 'new_lead', trigger_config: {}, actions: [], status: 'draft', is_active: true }
      case 'templates':
        return { name: '', subject: '', body_text: '', body_html: '', variables: [], category: '', is_active: true }
      case 'sequences':
        return { name: '', description: '', category: '', status: 'draft', trigger_type: '', steps: [], is_active: true }
      case 'rules':
        return { name: '', intent: 'greeting', keywords: [], response_template: '', response_type: 'text', priority: 0, channel_filter: [], requires_human: false, is_active: true }
    }
  })

  const update = (field: string, value: any) => setForm((prev: any) => ({ ...prev, [field]: value }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(form)
  }

  const label = type === 'workflows' ? 'Workflow' : type === 'templates' ? 'Plantilla' : type === 'sequences' ? 'Secuencia' : 'Regla'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h3 className="text-lg font-semibold text-brand-night">{item ? 'Editar' : 'Nuevo'} {label}</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Common fields */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
            <input
              type="text"
              value={form.name || ''}
              onChange={e => update('name', e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              required
            />
          </div>

          {type === 'workflows' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
                <textarea
                  value={form.description || ''}
                  onChange={e => update('description', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  rows={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Trigger</label>
                <select
                  value={form.trigger_type}
                  onChange={e => update('trigger_type', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                >
                  {Object.entries(TRIGGER_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Acciones (JSON)</label>
                <textarea
                  value={typeof form.actions === 'string' ? form.actions : JSON.stringify(form.actions || [], null, 2)}
                  onChange={e => {
                    try { update('actions', JSON.parse(e.target.value)) } catch {}
                  }}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  rows={4}
                  placeholder='[{"type": "send_message", "config": {}}]'
                />
              </div>
            </>
          )}

          {type === 'templates' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Asunto</label>
                <input
                  type="text"
                  value={form.subject || ''}
                  onChange={e => update('subject', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Cuerpo (texto)</label>
                <textarea
                  value={form.body_text || ''}
                  onChange={e => update('body_text', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  rows={4}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Variables (separadas por coma)</label>
                <input
                  type="text"
                  value={Array.isArray(form.variables) ? form.variables.join(', ') : form.variables || ''}
                  onChange={e => update('variables', e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  placeholder="nombre, empresa, precio"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Categoría</label>
                <input
                  type="text"
                  value={form.category || ''}
                  onChange={e => update('category', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                />
              </div>
            </>
          )}

          {type === 'sequences' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
                <textarea
                  value={form.description || ''}
                  onChange={e => update('description', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  rows={2}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Trigger</label>
                <select
                  value={form.trigger_type || ''}
                  onChange={e => update('trigger_type', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                >
                  <option value="">Sin trigger</option>
                  {Object.entries(TRIGGER_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
            </>
          )}

          {type === 'rules' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Intención</label>
                <select
                  value={form.intent}
                  onChange={e => update('intent', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                >
                  {Object.entries(INTENT_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Keywords (separadas por coma)</label>
                <input
                  type="text"
                  value={Array.isArray(form.keywords) ? form.keywords.join(', ') : form.keywords || ''}
                  onChange={e => update('keywords', e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  placeholder="hola, precio, cuanto cuesta"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Respuesta</label>
                <textarea
                  value={form.response_template || ''}
                  onChange={e => update('response_template', e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  rows={3}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Prioridad</label>
                  <input
                    type="number"
                    value={form.priority}
                    onChange={e => update('priority', parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Canales (separados por coma)</label>
                  <input
                    type="text"
                    value={Array.isArray(form.channel_filter) ? form.channel_filter.join(', ') : form.channel_filter || ''}
                    onChange={e => update('channel_filter', e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                    placeholder="whatsapp, instagram, email"
                  />
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={form.requires_human}
                  onChange={e => update('requires_human', e.target.checked)}
                  className="rounded border-slate-300"
                />
                Requiere intervención humana
              </label>
            </>
          )}

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800">
              Cancelar
            </button>
            <Button type="submit" disabled={saving} leftIcon={saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}>
              {saving ? 'Guardando...' : 'Guardar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
