'use client'

/**
 * Constructor de autoridad.
 *
 * Three things sit side by side on purpose: the chart (is authority growing?),
 * the analyst reading it (why did it move?), and the work queue (what do I do
 * about it?). A chart without the reading makes the user guess; a reading
 * without the queue leaves them with a diagnosis and no treatment.
 *
 * The advice comes from agents grounded in documented persuasion psychology,
 * applied to this account's real measurements — see
 * backend/app/domains/authority/psychology.py. Nothing here is generic
 * motivation: every recommendation cites the number that produced it.
 */

import React, { useCallback, useEffect, useState } from 'react'
import {
  Activity, AlertTriangle, BrainCircuit, Check, ChevronDown, Copy, Loader2, Minus, PlayCircle,
  RefreshCw, Sparkles, TrendingDown, TrendingUp, Users, X,
} from 'lucide-react'
import {
  authorityApi, MODE_LABEL, pillarColor, scoreTone,
  type ActionPreview, type AuthorityAction, type AuthorityDashboard, type TrendPoint,
} from '@/lib/authorityBuilder'

const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: 'WhatsApp',
  instagram: 'Instagram',
  web: 'Tu web',
  email: 'Email',
}

/** Real trend, drawn from stored snapshots. One point stays one point: it is
 *  never interpolated into a slope that did not happen. */
const TrendChart = ({ points }: { points: TrendPoint[] }): React.JSX.Element => {
  if (points.length === 0) {
    return <p className="text-sm text-slate-500">Sin mediciones todavía.</p>
  }

  const W = 640
  const H = 180
  const PAD = 28
  const maxScore = 100
  const xFor = (i: number): number =>
    points.length === 1 ? W / 2 : PAD + (i * (W - PAD * 2)) / (points.length - 1)
  const yFor = (v: number): number => H - PAD - (v / maxScore) * (H - PAD * 2)

  const line = points.map((p, i) => `${xFor(i)},${yFor(p.total_score)}`).join(' ')
  const area = `${PAD},${H - PAD} ${line} ${xFor(points.length - 1)},${H - PAD}`

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Evolución de autoridad">
      {[0, 25, 50, 75, 100].map(tick => (
        <g key={tick}>
          <line x1={PAD} x2={W - PAD} y1={yFor(tick)} y2={yFor(tick)} stroke="#e2e8f0" strokeWidth="1" />
          <text x={4} y={yFor(tick) + 4} fontSize="10" fill="#94a3b8">{tick}</text>
        </g>
      ))}
      {points.length > 1 && (
        <>
          <polygon points={area} fill="rgba(59,130,246,0.12)" />
          <polyline points={line} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinejoin="round" />
        </>
      )}
      {points.map((p, i) => (
        <g key={p.captured_at}>
          <circle cx={xFor(i)} cy={yFor(p.total_score)} r="4" fill="#3b82f6" />
          <title>{`${p.date}: ${p.total_score}/100`}</title>
        </g>
      ))}
      <text x={PAD} y={H - 6} fontSize="10" fill="#94a3b8">{points[0].date}</text>
      {points.length > 1 && (
        <text x={W - PAD} y={H - 6} fontSize="10" fill="#94a3b8" textAnchor="end">
          {points[points.length - 1].date}
        </text>
      )}
    </svg>
  )
}

export default function AuthorityBuilder(): React.JSX.Element {
  const [data, setData] = useState<AuthorityDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [measuring, setMeasuring] = useState(false)
  const [busyAction, setBusyAction] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [scriptSource, setScriptSource] = useState<Record<string, 'ia' | 'plantilla'>>({})
  const [openScript, setOpenScript] = useState<string | null>(null)
  const [showAgents, setShowAgents] = useState(false)
  const [preview, setPreview] = useState<{ action: AuthorityAction; data: ActionPreview } | null>(null)
  const [running, setRunning] = useState(false)
  const [runResult, setRunResult] = useState<Record<string, string>>({})

  const load = useCallback(async (): Promise<void> => {
    try {
      setData(await authorityApi.dashboard())
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const remeasure = async (): Promise<void> => {
    setMeasuring(true)
    try {
      await authorityApi.measure()
      await load()
    } finally {
      setMeasuring(false)
    }
  }

  const mark = async (action: AuthorityAction, status: 'done' | 'dismissed'): Promise<void> => {
    setBusyAction(action.id)
    try {
      await authorityApi.setStatus(action.id, status)
      await load()
    } finally {
      setBusyAction(null)
    }
  }

  const personalize = async (action: AuthorityAction): Promise<void> => {
    setBusyAction(action.id)
    try {
      const res = await authorityApi.personalize(action.id)
      setScriptSource(prev => ({ ...prev, [action.id]: res.source }))
      setData(prev => prev && {
        ...prev,
        actions: prev.actions.map(a => (a.id === action.id ? { ...a, script: res.script } : a)),
      })
    } finally {
      setBusyAction(null)
    }
  }

  /** Anything that reaches the user's customers goes through a preview first:
   *  they see the real recipient list and the exact text before confirming. */
  const startRun = async (action: AuthorityAction): Promise<void> => {
    setBusyAction(action.id)
    try {
      const data = await authorityApi.preview(action.id)
      if (data.executable && data.needs_confirmation) {
        setPreview({ action, data })
      } else if (data.executable) {
        const res = await authorityApi.run(action.id)
        setRunResult(prev => ({ ...prev, [action.id]: res.detail }))
        await load()
      }
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setRunResult(prev => ({ ...prev, [action.id]: detail || 'No se pudo ejecutar.' }))
    } finally {
      setBusyAction(null)
    }
  }

  const confirmRun = async (): Promise<void> => {
    if (!preview) return
    setRunning(true)
    try {
      const res = await authorityApi.run(preview.action.id, {
        confirm: true,
        conversation_ids: preview.data.recipients?.map(r => r.conversation_id),
      })
      setRunResult(prev => ({ ...prev, [preview.action.id]: res.detail }))
      setPreview(null)
      await load()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setRunResult(prev => ({ ...prev, [preview.action.id]: detail || 'No se pudo enviar.' }))
    } finally {
      setRunning(false)
    }
  }

  const copyScript = async (action: AuthorityAction): Promise<void> => {
    if (!action.script) return
    await navigator.clipboard.writeText(action.script)
    setCopied(action.id)
    setTimeout(() => setCopied(null), 2000)
  }

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 flex items-center justify-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" /> Midiendo tu autoridad…
      </div>
    )
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
        <p className="font-semibold text-slate-900">No se pudo calcular tu autoridad.</p>
        <p className="text-sm text-slate-600 mt-1">
          No se muestra un score estimado mientras tanto: sin datos reales, no hay número.
        </p>
      </div>
    )
  }

  const pending = data.actions.filter(a => a.status === 'suggested' || a.status === 'in_progress')
  const done = data.actions.filter(a => a.status === 'done')
  const TrendIcon = data.analysis.direction === 'up' ? TrendingUp
    : data.analysis.direction === 'down' ? TrendingDown : Minus

  return (
    <div className="space-y-5">
      {/* ── Gráfico + analista, uno al lado del otro ── */}
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-start justify-between flex-wrap gap-3 mb-2">
            <div>
              <p className="text-sm font-medium text-slate-600">Autoridad de tu marca</p>
              <p className={`text-5xl font-bold ${scoreTone(data.total_score)}`}>
                {data.total_score}
                <span className="text-xl text-slate-400 font-semibold">/100</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Medido el {new Date(data.captured_at).toLocaleString('es-AR')}
              </p>
            </div>
            <button
              type="button"
              onClick={remeasure}
              disabled={measuring}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {measuring ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Volver a medir
            </button>
          </div>
          <TrendChart points={data.trend} />
        </div>

        {/* Analista de gráficos */}
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 flex flex-col">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700 flex items-center gap-2">
            <Activity className="w-4 h-4" /> Analista de datos
          </p>
          <p className="text-slate-900 font-medium mt-2 leading-relaxed flex items-start gap-2">
            <TrendIcon className={`w-5 h-5 shrink-0 mt-0.5 ${
              data.analysis.direction === 'up' ? 'text-emerald-600'
                : data.analysis.direction === 'down' ? 'text-red-600' : 'text-slate-500'
            }`} />
            {data.analysis.headline}
          </p>
          {data.analysis.detail && (
            <p className="text-sm text-slate-700 mt-3">{data.analysis.detail}</p>
          )}
          {data.analysis.movements.length > 0 && (
            <ul className="mt-3 space-y-1">
              {data.analysis.movements.map(m => (
                <li key={m.pillar} className="text-sm flex items-center justify-between gap-2">
                  <span className="text-slate-700">{m.label}</span>
                  <span className={m.change > 0 ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'}>
                    {m.change > 0 ? '+' : ''}{m.change}
                  </span>
                </li>
              ))}
            </ul>
          )}
          {data.analysis.next_focus && (
            <p className="text-sm text-slate-900 mt-auto pt-3 border-t border-blue-200/60">
              {data.analysis.next_focus}
            </p>
          )}
        </div>
      </div>

      {/* ── Los seis pilares, con lo que falta en cada uno ── */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <p className="font-semibold text-slate-900 mb-4">De qué está hecha tu autoridad</p>
        <div className="grid sm:grid-cols-2 gap-x-8 gap-y-4">
          {data.pillars.map(p => (
            <div key={p.key}>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-sm font-medium text-slate-900">{p.label}</span>
                <span className="text-sm text-slate-600">
                  {p.score}
                  <span className="text-xs text-slate-400"> · pesa {Math.round(p.weight * 100)}%</span>
                </span>
              </div>
              <div className="h-2 rounded-full bg-slate-100 overflow-hidden mt-1.5">
                <div className={`h-full ${pillarColor(p.score)}`} style={{ width: `${p.score}%` }} />
              </div>
              {p.missing.length > 0 && (
                <p className="text-xs text-slate-500 mt-1.5">{p.missing[0]}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Consejos: qué hacer y cómo comunicarlo ── */}
      <div className="rounded-xl border border-slate-200 bg-white">
        <div className="p-5 border-b border-slate-100 flex items-start justify-between flex-wrap gap-3">
          <div>
            <p className="font-semibold text-slate-900 flex items-center gap-2">
              <BrainCircuit className="w-4 h-4 text-blue-600" /> Qué hacer para crecer
            </p>
            <p className="text-sm text-slate-600 mt-0.5">
              Recomendaciones de agentes especializados en psicología de la persuasión, aplicadas a
              tus números reales. Cada una dice de qué medición salió.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowAgents(v => !v)}
            className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1"
          >
            Ver los {data.agents.length} agentes
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAgents ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {showAgents && (
          <div className="p-5 grid sm:grid-cols-2 gap-3 bg-slate-50 border-b border-slate-100">
            {data.agents.map(agent => (
              <div key={agent.key} className="rounded-lg border border-slate-200 bg-white p-3">
                <p className="text-sm font-medium text-slate-900">{agent.name}</p>
                <p className="text-xs text-slate-600 mt-0.5">{agent.focus}</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Principio: {agent.principle} · {agent.source}
                </p>
              </div>
            ))}
          </div>
        )}

        {pending.length === 0 && (
          <div className="p-8 text-center">
            <p className="font-medium text-slate-900">No hay acciones pendientes.</p>
            <p className="text-sm text-slate-600 mt-1">
              Cargá tus links y conectá un canal para que los agentes tengan qué analizar.
            </p>
          </div>
        )}

        <ul className="divide-y divide-slate-100">
          {pending.map(action => {
            const mode = MODE_LABEL[action.mode]
            return (
              <li key={action.id} className="p-5">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="flex-1 min-w-[240px]">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-slate-900">{action.title}</p>
                      <span className={`text-[11px] px-2 py-0.5 rounded-full border ${mode.className}`}>
                        {mode.label}
                      </span>
                      {action.principle && (
                        <span className="text-[11px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                          {action.principle}
                        </span>
                      )}
                      {action.impact_score ? (
                        <span
                          className="text-[11px] text-slate-500"
                          title="Proyección calculada con la misma fórmula del pilar: cerrar esta brecha mueve el score exactamente esto."
                        >
                          +{action.impact_score.toFixed(1)} pts de score
                        </span>
                      ) : null}
                    </div>
                    {action.rationale && (
                      <p className="text-sm text-slate-600 mt-1.5 leading-relaxed">{action.rationale}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {action.executable && (
                      <button
                        type="button"
                        onClick={() => startRun(action)}
                        disabled={busyAction === action.id}
                        className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-1.5"
                      >
                        {busyAction === action.id
                          ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          : <PlayCircle className="w-3.5 h-3.5" />}
                        {action.needs_confirmation ? 'Preparar envío' : 'Ejecutar'}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => mark(action, 'done')}
                      disabled={busyAction === action.id}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50 inline-flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" /> Hecho
                    </button>
                    <button
                      type="button"
                      onClick={() => mark(action, 'dismissed')}
                      disabled={busyAction === action.id}
                      title="No me interesa"
                      className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 disabled:opacity-50"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {runResult[action.id] && (
                  <p className="text-sm text-slate-700 mt-2 flex gap-2">
                    <Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                    {runResult[action.id]}
                  </p>
                )}

                {action.script && (
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => setOpenScript(openScript === action.id ? null : action.id)}
                      className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1"
                    >
                      {openScript === action.id ? 'Ocultar' : 'Ver'} qué decir
                      {action.channel && ` en ${CHANNEL_LABEL[action.channel] ?? action.channel}`}
                      <ChevronDown className={`w-3.5 h-3.5 transition-transform ${openScript === action.id ? 'rotate-180' : ''}`} />
                    </button>

                    {openScript === action.id && (
                      <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-4">
                        <pre className="text-sm text-slate-800 whitespace-pre-wrap font-sans">
                          {action.script}
                        </pre>
                        <div className="flex items-center gap-2 mt-3 flex-wrap">
                          <button
                            type="button"
                            onClick={() => copyScript(action)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-medium hover:bg-slate-800"
                          >
                            {copied === action.id ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                            {copied === action.id ? 'Copiado' : 'Copiar'}
                          </button>
                          <button
                            type="button"
                            onClick={() => personalize(action)}
                            disabled={busyAction === action.id}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 hover:bg-white disabled:opacity-50"
                          >
                            {busyAction === action.id
                              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              : <Sparkles className="w-3.5 h-3.5" />}
                            Adaptarlo a mi negocio con IA
                          </button>
                          {scriptSource[action.id] && (
                            <span className="text-[11px] text-slate-500">
                              {scriptSource[action.id] === 'ia'
                                ? 'Reescrito por la IA con los datos de tu negocio.'
                                : 'Sigue siendo la plantilla base: la IA no está disponible ahora.'}
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-2">
                          Reemplazá lo que está entre llaves. Ningún dato, precio ni plazo se completa
                          solo: eso lo ponés vos porque sólo vos sabés si es cierto.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </li>
            )
          })}
        </ul>

        {done.length > 0 && (
          <div className="p-5 border-t border-slate-100">
            <p className="text-sm font-medium text-slate-900 mb-2">
              Ya resuelto ({done.length})
            </p>
            <ul className="space-y-1">
              {done.slice(0, 6).map(action => (
                <li key={action.id} className="text-sm text-slate-500 flex items-center gap-2">
                  <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                  <span className="line-through">{action.title}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Confirmación de envío: los destinatarios son conversaciones reales y el
          mensaje sale con el nombre del usuario, así que no se manda nada sin
          que los vea primero. */}
      {preview && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-5 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900">{preview.action.title}</h3>
              {preview.data.warning && (
                <p className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3 mt-3 flex gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  {preview.data.warning}
                </p>
              )}
            </div>

            <div className="p-5 space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-900 mb-1">Mensaje que se envía</p>
                <pre className="text-sm text-slate-800 whitespace-pre-wrap font-sans rounded-lg border border-slate-200 bg-slate-50 p-3">
                  {preview.data.script}
                </pre>
                <p className="text-[11px] text-slate-500 mt-1">
                  El marcador de nombre se reemplaza por el nombre real de cada cliente.
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-slate-900 mb-2 flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-400" />
                  {preview.data.recipients?.length ?? 0} cliente(s) reales
                </p>
                {(preview.data.recipients?.length ?? 0) === 0 ? (
                  <p className="text-sm text-slate-600">
                    Todavía no hay clientes que califiquen: hace falta alguien que te haya escrito
                    y a quien hayas respondido en los últimos 90 días.
                  </p>
                ) : (
                  <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 max-h-64 overflow-y-auto">
                    {preview.data.recipients?.map(r => (
                      <li key={r.conversation_id} className="px-3 py-2">
                        <p className="text-sm font-medium text-slate-900 truncate">{r.name}</p>
                        <p className="text-xs text-slate-500 truncate">
                          {r.platform}
                          {r.last_message_at && ` · último mensaje ${new Date(r.last_message_at).toLocaleDateString('es-AR')}`}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="p-5 border-t border-slate-100 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPreview(null)}
                className="px-4 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmRun}
                disabled={running || (preview.data.recipients?.length ?? 0) === 0}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {running && <Loader2 className="w-4 h-4 animate-spin" />}
                Enviar a {preview.data.recipients?.length ?? 0}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
