'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import { consumoApi, type CostAttributionSummary, type QualityGateConfig, type PlanRecommendation, type OnboardingProgress, type OnboardingHelpResponse } from '@/lib/consumo'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, LineChart, Line
} from 'recharts'
import {
  Settings,
  Key,
  DollarSign,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Minus,
  Compass,
  Loader2,
  RefreshCw,
  Copy,
  Check,
  AlertTriangle,
  Zap,
  BarChart3,
  Gauge,
  Lightbulb,
  ChevronRight,
  HelpCircle,
  MessageSquare,
  Bot,
  ShoppingBag,
  Workflow,
  Users,
  Wifi,
  CheckCircle2,
  Circle,
} from 'lucide-react'

// ============ API KEYS SECTION ============

function ApiKeysSection() {
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [message, setMessage] = useState('')

  const fetchApiKey = async () => {
    setLoading(true)
    try {
      const res = await api.get('/users/me')
      // The API key is hashed; we can't show it. We'll show a masked version.
      setApiKey('•••••••••••••••••••••••••••••••••')
    } catch {
      setMessage('Error al cargar datos del usuario')
    } finally {
      setLoading(false)
    }
  }

  const regenerate = async () => {
    setRegenerating(true)
    try {
      const res = await api.post('/selfservice/regenerate-api-key')
      setApiKey(res.data.api_key)
      setMessage('API key regenerada exitosamente')
      setTimeout(() => setMessage(''), 3000)
    } catch {
      setMessage('Error al regenerar API key')
    } finally {
      setRegenerating(false)
    }
  }

  const copyToClipboard = () => {
    if (apiKey && !apiKey.startsWith('•')) {
      navigator.clipboard.writeText(apiKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  useEffect(() => {
    fetchApiKey()
  }, [])

  return (
    <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-brand-orange/10">
          <Key className="w-5 h-5 text-brand-orange" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">API Keys</h3>
          <p className="text-sm text-white/50">Gestiona tus credenciales de acceso</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-white/50">
          <Loader2 className="w-4 h-4 animate-spin" />
          Cargando...
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex-1 px-4 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] font-mono text-sm text-white/80 flex items-center justify-between">
              <span>{apiKey || '•••••••••••••••••••••••••••••••••'}</span>
              {apiKey && !apiKey.startsWith('•') && (
                <button onClick={copyToClipboard} className="p-1 hover:bg-white/10 rounded transition-colors">
                  {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-white/50" />}
                </button>
              )}
            </div>
            <button
              onClick={regenerate}
              disabled={regenerating}
              className="px-4 py-3 rounded-xl bg-brand-orange/20 text-brand-orange hover:bg-brand-orange/30 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50"
            >
              {regenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Regenerar
            </button>
          </div>
          {message && (
            <p className={`text-sm ${message.includes('Error') ? 'text-red-400' : 'text-green-400'}`}>{message}</p>
          )}
        </div>
      )}
    </div>
  )
}

// ============ COST ATTRIBUTION SECTION ============

const CHART_COLORS = ['#F97316', '#10B981', '#3B82F6', '#A855F7', '#EF4444', '#F59E0B']

function CostAttributionSection() {
  const [data, setData] = useState<CostAttributionSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    loadData()
  }, [days])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await consumoApi.getCostAttribution(days)
      setData(res)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  // FOMO indicators
  const fomoMessages = (d: CostAttributionSummary) => {
    const msgs = []
    if (d.cache_hit_rate > 50) msgs.push({ icon: '🔥', text: `Tu cache hit rate del ${d.cache_hit_rate}% está en el top 10%` })
    if (d.total_cost_usd > 5) msgs.push({ icon: '⚡', text: 'Proyectado: $' + (d.total_cost_usd * 3).toFixed(2) + ' este trimestre si mantenés este ritmo' })
    if (d.total_calls > 100) msgs.push({ icon: '🚀', text: `${d.total_calls} llamadas AI — ${Math.round(d.total_calls / 30)} por día promedio` })
    return msgs
  }

  return (
    <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Cost Attribution Dashboard</h3>
            <p className="text-sm text-white/50">Análisis de costos de IA por proveedor y modelo</p>
          </div>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-3 py-2 rounded-lg bg-white/[0.05] border border-white/[0.08] text-sm text-white/80"
        >
          <option value={7}>Últimos 7 días</option>
          <option value={30}>Últimos 30 días</option>
          <option value={90}>Últimos 90 días</option>
        </select>
      </div>

      {loading || !data ? (
        <div className="flex items-center gap-2 text-white/50 py-8">
          <Loader2 className="w-4 h-4 animate-spin" />
          Cargando métricas...
        </div>
      ) : (
        <div className="space-y-6">
          {/* FOMO Indicators */}
          {fomoMessages(data).length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {fomoMessages(data).map((m, i) => (
                <div key={i} className="p-3 rounded-xl bg-gradient-to-r from-brand-orange/10 to-purple-500/10 border border-brand-orange/20">
                  <p className="text-sm text-white/80">{m.icon} {m.text}</p>
                </div>
              ))}
            </div>
          )}

          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Llamadas AI" value={data.total_calls.toLocaleString()} icon={<Zap className="w-4 h-4" />} color="text-amber-400" />
            <MetricCard label="Costo Total" value={`$${data.total_cost_usd.toFixed(4)}`} icon={<DollarSign className="w-4 h-4" />} color="text-emerald-400" />
            <MetricCard label="Tokens Input" value={data.total_tokens_input.toLocaleString()} icon={<MessageSquare className="w-4 h-4" />} color="text-blue-400" />
            <MetricCard label="Cache Hit Rate" value={`${data.cache_hit_rate}%`} icon={<Gauge className="w-4 h-4" />} color="text-purple-400" />
          </div>

          {/* Charts */}
          {data.by_provider.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Chart - Provider Costs */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <h4 className="text-sm font-medium text-white/70 mb-4">Costo por Proveedor</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.by_provider}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                    <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                      formatter={(value: any) => [`$${Number(value).toFixed(4)}`, 'Costo']}
                    />
                    <Bar dataKey="cost_usd" fill="#F97316" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Pie Chart - Task Type */}
              {data.by_task_type.length > 0 && (
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <h4 className="text-sm font-medium text-white/70 mb-4">Distribución por Tarea</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={data.by_task_type}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        paddingAngle={4}
                        dataKey="cost_usd"
                        nameKey="name"
                      >
                        {data.by_task_type.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                        formatter={(value: any) => [`$${Number(value).toFixed(4)}`, 'Costo']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}

          {/* Projection */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
            <h4 className="text-sm font-medium text-white/70 mb-4">Proyección de Costos (30 días)</h4>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={[
                { day: 'Hoy', actual: data.total_cost_usd, projected: data.total_cost_usd },
                { day: '+7d', actual: 0, projected: data.total_cost_usd * 1.2 },
                { day: '+14d', actual: 0, projected: data.total_cost_usd * 1.5 },
                { day: '+21d', actual: 0, projected: data.total_cost_usd * 1.9 },
                { day: '+30d', actual: 0, projected: data.total_cost_usd * 2.4 },
              ]}>
                <defs>
                  <linearGradient id="projGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 12 }} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                  formatter={(value: any) => [`$${Number(value).toFixed(4)}`, '']}
                />
                <Area type="monotone" dataKey="projected" stroke="#F97316" fillOpacity={1} fill="url(#projGradient)" strokeDasharray="5 5" />
                <Area type="monotone" dataKey="actual" stroke="#10B981" fill="none" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {data.total_calls === 0 && (
            <div className="text-center py-8 text-white/40 text-sm">
              No hay llamadas AI registradas en este período.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, icon, color }: { label: string; value: string; icon: React.ReactNode; color: string }) {
  return (
    <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.05]">
      <div className={`flex items-center gap-2 mb-2 ${color}`}>
        {icon}
        <span className="text-xs font-medium text-white/50">{label}</span>
      </div>
      <div className="text-xl font-bold text-white">{value}</div>
    </div>
  )
}

// ============ QUALITY GATE SECTION ============

function QualityGateSection() {
  const [config, setConfig] = useState<QualityGateConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const res = await consumoApi.getQualityGate()
      setConfig(res)
    } catch {
      setMessage('Error al cargar configuración')
    } finally {
      setLoading(false)
    }
  }

  const save = async () => {
    if (!config) return
    setSaving(true)
    try {
      const res = await consumoApi.updateQualityGate(config)
      setConfig(res)
      setMessage('Configuración guardada')
      setTimeout(() => setMessage(''), 3000)
    } catch {
      setMessage('Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-2 text-white/50">
          <Loader2 className="w-4 h-4 animate-spin" />
          Cargando...
        </div>
      </div>
    )
  }

  return (
    <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-blue-500/10">
          <ShieldCheck className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Quality Gate para Soporte AI</h3>
          <p className="text-sm text-white/50">Controla cuándo la IA puede responder tickets automáticamente</p>
        </div>
      </div>

      {config && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">Activar Quality Gate</p>
              <p className="text-xs text-white/40">Si está desactivado, la IA responde todos los tickets</p>
            </div>
            <button
              onClick={() => setConfig({ ...config, enabled: !config.enabled })}
              className={`relative w-12 h-6 rounded-full transition-colors ${config.enabled ? 'bg-brand-orange' : 'bg-white/10'}`}
            >
              <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${config.enabled ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-white">Umbral mínimo de confianza</p>
              <span className="text-sm text-brand-orange font-medium">{(config.min_confidence_threshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.3"
              max="0.95"
              step="0.05"
              value={config.min_confidence_threshold}
              onChange={(e) => setConfig({ ...config, min_confidence_threshold: parseFloat(e.target.value) })}
              className="w-full accent-brand-orange"
            />
            <p className="text-xs text-white/40 mt-1">
              Si la confianza de la IA es menor a este valor, el ticket se escalará a un humano.
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">Auto-escalar en confianza baja</p>
              <p className="text-xs text-white/40">Crea automáticamente un ticket escalado</p>
            </div>
            <button
              onClick={() => setConfig({ ...config, auto_escalate_on_low_confidence: !config.auto_escalate_on_low_confidence })}
              className={`relative w-12 h-6 rounded-full transition-colors ${config.auto_escalate_on_low_confidence ? 'bg-brand-orange' : 'bg-white/10'}`}
            >
              <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform ${config.auto_escalate_on_low_confidence ? 'translate-x-6' : 'translate-x-0.5'}`} />
            </button>
          </div>

          <div>
            <p className="text-sm font-medium text-white mb-2">Máx. mensajes AI antes de humano</p>
            <input
              type="number"
              min={1}
              max={10}
              value={config.max_ai_messages_before_human}
              onChange={(e) => setConfig({ ...config, max_ai_messages_before_human: parseInt(e.target.value) || 2 })}
              className="w-24 px-3 py-2 rounded-lg bg-white/[0.05] border border-white/[0.08] text-sm text-white"
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={save}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Guardar cambios'}
            </button>
            {message && (
              <span className={`text-sm ${message.includes('Error') ? 'text-red-400' : 'text-green-400'}`}>{message}</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ============ PLAN RECOMMENDATION SECTION ============

function PlanRecommendationSection() {
  const [rec, setRec] = useState<PlanRecommendation | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRec()
  }, [])

  const loadRec = async () => {
    try {
      const res = await consumoApi.getPlanRecommendation()
      setRec(res)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  const getIcon = () => {
    if (!rec) return <Minus className="w-6 h-6" />
    if (rec.recommendation === 'upgrade') return <TrendingUp className="w-6 h-6 text-amber-400" />
    if (rec.recommendation === 'downgrade') return <TrendingDown className="w-6 h-6 text-emerald-400" />
    return <CheckCircle2 className="w-6 h-6 text-blue-400" />
  }

  const getBg = () => {
    if (!rec) return 'bg-white/[0.03]'
    if (rec.recommendation === 'upgrade') return 'bg-amber-500/[0.05] border-amber-500/20'
    if (rec.recommendation === 'downgrade') return 'bg-emerald-500/[0.05] border-emerald-500/20'
    return 'bg-blue-500/[0.05] border-blue-500/20'
  }

  return (
    <div className={`mb-8 p-6 rounded-2xl border ${getBg()}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-white/[0.05]">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Recomendación de Plan</h3>
          <p className="text-sm text-white/50">Optimización inteligente basada en tu uso real</p>
        </div>
      </div>

      {loading || !rec ? (
        <div className="flex items-center gap-2 text-white/50 py-4">
          <Loader2 className="w-4 h-4 animate-spin" />
          Analizando uso...
        </div>
      ) : (rec as any).recommendation === 'no_active_subscription' ? (
        <p className="text-sm text-white/60">No hay suscripción activa para analizar.</p>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            {getIcon()}
            <div>
              <p className="text-white font-medium">
                {rec.recommendation === 'upgrade' && 'Considerá subir de plan'}
                {rec.recommendation === 'downgrade' && 'Podés ahorrar bajando de plan'}
                {rec.recommendation === 'keep' && 'Tu plan está bien dimensionado'}
              </p>
              <p className="text-sm text-white/50">{rec.reason}</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 rounded-lg bg-white/[0.03]">
              <p className="text-xs text-white/40">Plan actual</p>
              <p className="text-white font-medium capitalize">{rec.current_plan}</p>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.03]">
              <p className="text-xs text-white/40">Uso</p>
              <p className="text-white font-medium">{rec.usage_percent}%</p>
            </div>
            <div className="p-3 rounded-lg bg-white/[0.03]">
              <p className="text-xs text-white/40">Precio</p>
              <p className="text-white font-medium">${rec.current_plan_price}</p>
            </div>
          </div>

          {rec.recommendation !== 'keep' && (
            <div className="flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span className="text-white/60">
                {rec.recommendation === 'upgrade'
                  ? 'Estás cerca de tu límite. Subir de plan evita cortes de servicio.'
                  : 'Usás menos del 30% de tu plan. Bajando ahorrás sin perder funcionalidad.'}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============ ONBOARDING GUIDE SECTION ============

function OnboardingGuideSection() {
  const [progress, setProgress] = useState<OnboardingProgress | null>(null)
  const [loading, setLoading] = useState(true)
  const [helpLoading, setHelpLoading] = useState(false)
  const [helpResponse, setHelpResponse] = useState<OnboardingHelpResponse | null>(null)

  useEffect(() => {
    loadProgress()
  }, [])

  const loadProgress = async () => {
    try {
      const res = await consumoApi.getOnboarding()
      setProgress(res)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  const requestHelp = async () => {
    if (!progress) return
    setHelpLoading(true)
    try {
      const res = await consumoApi.requestOnboardingHelp(progress.current_step)
      setHelpResponse(res)
    } catch {
      // silent
    } finally {
      setHelpLoading(false)
    }
  }

  const steps = [
    { key: 'account_created', label: 'Crear cuenta', icon: <Users className="w-4 h-4" /> },
    { key: 'business_created', label: 'Crear negocio', icon: <ShoppingBag className="w-4 h-4" /> },
    { key: 'channel_connected', label: 'Conectar canal', icon: <Wifi className="w-4 h-4" /> },
    { key: 'agent_configured', label: 'Configurar agente', icon: <Bot className="w-4 h-4" /> },
    { key: 'first_conversation', label: 'Primera conversación', icon: <MessageSquare className="w-4 h-4" /> },
    { key: 'catalog_added', label: 'Agregar catálogo', icon: <ShoppingBag className="w-4 h-4" /> },
    { key: 'automation_created', label: 'Crear automatización', icon: <Workflow className="w-4 h-4" /> },
  ]

  return (
    <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Compass className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Guía de Onboarding Inteligente</h3>
            <p className="text-sm text-white/50">Progreso de configuración inicial</p>
          </div>
        </div>
        {progress && progress.progress_percent < 100 && (
          <button
            onClick={requestHelp}
            disabled={helpLoading}
            className="px-3 py-2 rounded-lg bg-purple-500/20 text-purple-300 text-sm hover:bg-purple-500/30 transition-colors flex items-center gap-2"
          >
            {helpLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <HelpCircle className="w-4 h-4" />}
            Necesito ayuda
          </button>
        )}
      </div>

      {loading || !progress ? (
        <div className="flex items-center gap-2 text-white/50 py-4">
          <Loader2 className="w-4 h-4 animate-spin" />
          Cargando progreso...
        </div>
      ) : (
        <div className="space-y-5">
          {/* Progress bar */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/60">Progreso general</span>
              <span className="text-sm font-medium text-white">{progress.progress_percent}%</span>
            </div>
            <div className="h-2 rounded-full bg-white/[0.05] overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-brand-orange to-purple-500 transition-all"
                style={{ width: `${progress.progress_percent}%` }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {steps.map((step) => {
              const completed = (progress as any)[step.key]
              return (
                <div
                  key={step.key}
                  className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${
                    completed
                      ? 'bg-white/[0.03] border-white/[0.06]'
                      : 'bg-white/[0.02] border-white/[0.04] opacity-60'
                  }`}
                >
                  {completed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  ) : (
                    <Circle className="w-5 h-5 text-white/20 shrink-0" />
                  )}
                  <span className={`text-sm ${completed ? 'text-white/80' : 'text-white/40'}`}>{step.label}</span>
                </div>
              )
            })}
          </div>

          {/* AI Help Response */}
          {helpResponse && (
            <div className="p-4 rounded-xl bg-purple-500/[0.05] border border-purple-500/20">
              <p className="text-sm text-white/80 mb-2">{helpResponse.message}</p>
              <p className="text-sm text-purple-300 mb-2">{helpResponse.suggested_action}</p>
              <div className="flex flex-wrap gap-2">
                {helpResponse.resources.map((r) => (
                  <a
                    key={r}
                    href={r}
                    className="text-xs text-white/50 hover:text-white/80 underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {r}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============ MAIN PAGE ============

export default function ConfiguracionPage() {
  const { user, loading: authLoading } = useAuth()
  const [activeTab, setActiveTab] = useState<'general' | 'consumo'>('general')

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-4xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-brand-orange/10">
            <Settings className="w-6 h-6 text-brand-orange" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Configuración</h1>
            <p className="text-sm text-white/50">Gestiona tu cuenta, API keys y consumo</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-8">
          <button
            onClick={() => setActiveTab('general')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'general'
                ? 'bg-white/[0.08] text-white'
                : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'
            }`}
          >
            General
          </button>
          <button
            onClick={() => setActiveTab('consumo')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'consumo'
                ? 'bg-white/[0.08] text-white'
                : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'
            }`}
          >
            Consumo
          </button>
        </div>

        {activeTab === 'general' && (
          <div>
            <ApiKeysSection />
            {/* Aquí se pueden agregar más secciones de configuración general */}
          </div>
        )}

        {activeTab === 'consumo' && (
          <div>
            <CostAttributionSection />
            <QualityGateSection />
            <PlanRecommendationSection />
            <OnboardingGuideSection />
          </div>
        )}
      </div>
    </div>
  )
}
