'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
} from 'recharts'
import {
  Sparkles, Target, Flame, AlertTriangle, CheckCircle2, XCircle, Loader2,
  ChevronDown, ChevronRight, Rocket, ShieldAlert, Gauge, Zap,
} from 'lucide-react'
import { businessApi } from '@/lib/business'
import Button from '@/components/ui/Button'
import { StageArtifact } from './StageArtifact'
import {
  brandTransformation as bt,
  type Diagnosis, type Program, type StageInfo, type DomainHealth,
  type BusinessProfileIn, type FomoCampaignPlan, type AutoBridges,
} from '@/lib/api/brandTransformation'

const card = 'rounded-xl border border-white/10 bg-white/[0.04] p-5'
const chip = 'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium'

const COMMOD_COLOR: Record<string, string> = {
  low: 'bg-emerald-500/15 text-emerald-300',
  medium: 'bg-amber-500/15 text-amber-300',
  high: 'bg-orange-500/15 text-orange-300',
  severe: 'bg-red-500/15 text-red-300',
  unknown: 'bg-white/10 text-white/50',
}

function scoreColor(n: number) {
  if (n >= 70) return 'text-emerald-400'
  if (n >= 45) return 'text-amber-400'
  return 'text-red-400'
}

function List({ items, tone = 'default' }: { items?: string[] | null; tone?: 'default' | 'good' | 'bad' }) {
  if (!items?.length) return <p className="text-sm text-white/40">—</p>
  const Icon = tone === 'good' ? CheckCircle2 : tone === 'bad' ? XCircle : ChevronRight
  const c = tone === 'good' ? 'text-emerald-400' : tone === 'bad' ? 'text-red-400' : 'text-white/30'
  return (
    <ul className="space-y-1.5">
      {items.map((it, i) => (
        <li key={i} className="flex gap-2 text-sm text-white/80">
          <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${c}`} />
          <span>{typeof it === 'string' ? it : JSON.stringify(it)}</span>
        </li>
      ))}
    </ul>
  )
}

function Json({ data }: { data: any }) {
  if (data == null) return <p className="text-sm text-white/40">—</p>
  if (Array.isArray(data)) return <List items={data.map((x) => (typeof x === 'string' ? x : JSON.stringify(x)))} />
  if (typeof data === 'object') {
    return (
      <div className="space-y-2">
        {Object.entries(data).map(([k, v]) => (
          <div key={k}>
            <p className="text-xs font-semibold uppercase tracking-wide text-white/40">{k.replace(/_/g, ' ')}</p>
            <div className="text-sm text-white/80">
              {typeof v === 'object' ? <Json data={v} /> : String(v)}
            </div>
          </div>
        ))}
      </div>
    )
  }
  return <p className="text-sm text-white/80">{String(data)}</p>
}

function Accordion({ title, subtitle, children, defaultOpen = false }: {
  title: string; subtitle?: string; children: React.ReactNode; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className={card}>
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center justify-between text-left">
        <div>
          <p className="font-semibold text-white">{title}</p>
          {subtitle && <p className="text-sm text-white/50">{subtitle}</p>}
        </div>
        <ChevronDown className={`h-5 w-5 text-white/40 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="mt-4 border-t border-white/10 pt-4">{children}</div>}
    </div>
  )
}

const DEFAULT_PROFILE: BusinessProfileIn = {
  industry: '',
  what_they_sell: '',
  current_positioning: '',
  known_competitors: [],
  revenue_model: '',
  target_customer: '',
  price_point: '',
  notes: '',
}

export function TransformacionContent() {
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [health, setHealth] = useState<DomainHealth | null>(null)
  const [stages, setStages] = useState<StageInfo[]>([])
  const [diag, setDiag] = useState<Diagnosis | null>(null)
  const [programs, setPrograms] = useState<Program[]>([])
  const [activeProgram, setActiveProgram] = useState<Program | null>(null)
  const [fomoPlan, setFomoPlan] = useState<FomoCampaignPlan | null>(null)
  const [alerts, setAlerts] = useState<Array<{ type: string; severity: string; headline: string | null; recommended_action: string | null }>>([])

  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [profile, setProfile] = useState<BusinessProfileIn>(DEFAULT_PROFILE)
  const [showForm, setShowForm] = useState(false)
  const [autoBridges, setAutoBridges] = useState<AutoBridges>({ competitive: false, assets: false, fomo: { enabled: false } })

  useEffect(() => {
    ;(async () => {
      try {
        const list = await businessApi.list()
        if (list.length) setBusinessId(list[0].id)
        else setError('No hay negocios. Creá uno primero.')
      } catch {
        setError('No se pudo cargar el negocio')
      }
    })()
  }, [])

  const refresh = useCallback(async (bid: string) => {
    setLoading(true)
    try {
      const [h, st, d, pr, al] = await Promise.allSettled([
        bt.health(bid), bt.stages(bid), bt.latestDiagnosis(bid), bt.listPrograms(bid), bt.automationAlerts(bid),
      ])
      if (h.status === 'fulfilled') setHealth(h.value)
      if (st.status === 'fulfilled') setStages(st.value)
      if (d.status === 'fulfilled') setDiag(d.value)
      if (pr.status === 'fulfilled') {
        setPrograms(pr.value)
        if (pr.value.length) setActiveProgram(pr.value[0])
      }
      if (al.status === 'fulfilled') setAlerts(al.value)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (businessId) refresh(businessId)
  }, [businessId, refresh])

  const run = async (key: string, fn: () => Promise<void>) => {
    setBusy(key); setError('')
    try { await fn() } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Error')
    } finally { setBusy(null) }
  }

  const doDiagnosis = () =>
    run('diag', async () => {
      if (!businessId) return
      const d = await bt.runDiagnosis(businessId, profile)
      setDiag(d); setShowForm(false)
    })

  const doCreateProgram = () =>
    run('program', async () => {
      if (!businessId) return
      const p = await bt.createProgram(businessId, 'Brand Transformation', profile, autoBridges)
      setPrograms((ps) => [p, ...ps]); setActiveProgram(p)
    })

  const doRunAll = () =>
    run('runall', async () => {
      if (!businessId || !activeProgram) return
      await bt.runAll(businessId, activeProgram.id)
      const p = await bt.getProgram(businessId, activeProgram.id)
      setActiveProgram(p)
      setPrograms((ps) => ps.map((x) => (x.id === p.id ? p : x)))
    })

  const doRunStage = (key: string) =>
    run(`stage:${key}`, async () => {
      if (!businessId || !activeProgram) return
      await bt.runStage(businessId, activeProgram.id, key, { profile })
      const p = await bt.getProgram(businessId, activeProgram.id)
      setActiveProgram(p)
    })

  const doCoherence = () =>
    run('coherence', async () => {
      if (!businessId || !activeProgram) return
      await bt.coherenceAudit(businessId, activeProgram.id)
      const p = await bt.getProgram(businessId, activeProgram.id)
      setActiveProgram(p)
    })

  const doFomoPreview = () =>
    run('fomo-preview', async () => {
      if (!businessId) return
      setFomoPlan(await bt.fomoCampaignPreview(businessId))
    })

  const doFomoDeploy = (activate: boolean) =>
    run('fomo-deploy', async () => {
      if (!businessId) return
      setFomoPlan(await bt.deployFomoCampaigns(businessId, { activate }))
    })

  const [bridgeMsg, setBridgeMsg] = useState('')
  const doDeployAssets = () =>
    run('assets', async () => {
      if (!businessId) return
      const r = await bt.deployAssets(businessId)
      setBridgeMsg(`Identidad → contenido: ${r.created_count ?? 0} assets + plantilla de voz.`)
    })
  const doDeployCompetitive = () =>
    run('competitive', async () => {
      if (!businessId) return
      const comps = (profile.known_competitors ?? []).map((n) => ({ name: n }))
      const r = await bt.deployCompetitive(businessId, { competitors: comps })
      setBridgeMsg(`Posicionamiento → competitive: ${r.created_count ?? 0} (monitores necesitan URL; ${r.skipped?.length ?? 0} sin URL).`)
    })

  const radarData = useMemo(() => {
    const sc = diag?.scorecard
    if (!sc) return []
    return Object.entries(sc)
      .filter(([, v]) => typeof v === 'number')
      .map(([k, v]) => ({ axis: k.replace(/_/g, ' '), value: v as number }))
  }, [diag])

  const completed = new Set(activeProgram?.completed_stages ?? [])
  const coherence = activeProgram?.coherence_audit
  const roadmap = activeProgram?.roadmap

  if (loading && !diag && !programs.length) {
    return (
      <div className="flex h-64 items-center justify-center text-white/50">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 text-white">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/15 text-primary">
          <Sparkles className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Transformación de Marca</h1>
          <p className="text-sm text-white/50">
            Diagnóstico → posicionamiento → identidad → modelo → FOMO → go-to-market → reestructuración
          </p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          <AlertTriangle className="h-4 w-4" /> {error}
        </div>
      )}

      {alerts.length > 0 && (
        <div className="space-y-1.5">
          {alerts.map((a, i) => (
            <div
              key={i}
              className={`flex items-start gap-2 rounded-lg border p-3 text-sm ${
                a.severity === 'critical'
                  ? 'border-red-500/30 bg-red-500/10 text-red-200'
                  : 'border-amber-500/30 bg-amber-500/10 text-amber-200'
              }`}
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <span className="font-semibold">[{a.type}]</span> {a.headline}
                {a.recommended_action && <span className="block text-xs opacity-80">→ {a.recommended_action}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {health && !health.llm_available && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
          <ShieldAlert className="h-4 w-4 shrink-0" />
          Modo <b>fallback</b>: sin <code>ANTHROPIC_API_KEY</code> los agentes devuelven plantillas, no IA. {health.note}
        </div>
      )}

      {/* Profile form */}
      {(showForm || (!diag && !programs.length)) && (
        <div className={card}>
          <p className="mb-3 font-semibold">Perfil del negocio</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {([
              ['industry', 'Industria *'],
              ['what_they_sell', 'Qué vende *'],
              ['current_positioning', 'Posicionamiento actual'],
              ['revenue_model', 'Modelo de ingresos'],
              ['target_customer', 'Cliente objetivo'],
              ['price_point', 'Rango de precio'],
            ] as [keyof BusinessProfileIn, string][]).map(([k, label]) => (
              <label key={k} className="text-sm">
                <span className="mb-1 block text-white/50">{label}</span>
                <input
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary/50"
                  value={(profile[k] as string) ?? ''}
                  onChange={(e) => setProfile((p) => ({ ...p, [k]: e.target.value }))}
                />
              </label>
            ))}
            <label className="text-sm sm:col-span-2">
              <span className="mb-1 block text-white/50">Competidores (coma)</span>
              <input
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary/50"
                value={(profile.known_competitors ?? []).join(', ')}
                onChange={(e) =>
                  setProfile((p) => ({ ...p, known_competitors: e.target.value.split(',').map((s) => s.trim()).filter(Boolean) }))
                }
              />
            </label>
            <label className="text-sm sm:col-span-2">
              <span className="mb-1 block text-white/50">Notas</span>
              <textarea
                rows={2}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-primary/50"
                value={profile.notes ?? ''}
                onChange={(e) => setProfile((p) => ({ ...p, notes: e.target.value }))}
              />
            </label>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-white/60">
            <span className="text-white/40">Auto-integraciones al completar etapa:</span>
            {([['competitive', 'Competencia'], ['assets', 'Contenido']] as [keyof AutoBridges, string][]).map(([k, label]) => (
              <label key={k} className="flex items-center gap-1.5">
                <input
                  type="checkbox"
                  checked={!!autoBridges[k]}
                  onChange={(e) => setAutoBridges((a) => ({ ...a, [k]: e.target.checked }))}
                />
                {label}
              </label>
            ))}
            <label className="flex items-center gap-1.5">
              <input
                type="checkbox"
                checked={!!autoBridges.fomo?.enabled}
                onChange={(e) => setAutoBridges((a) => ({ ...a, fomo: { ...a.fomo, enabled: e.target.checked } }))}
              />
              FOMO
            </label>
          </div>
          <div className="mt-4 flex gap-2">
            <Button onClick={doDiagnosis} disabled={busy === 'diag' || !profile.industry || !profile.what_they_sell}>
              {busy === 'diag' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Gauge className="h-4 w-4" />}
              Diagnosticar
            </Button>
            <Button variant="secondary" onClick={doCreateProgram} disabled={busy === 'program' || !profile.industry}>
              {busy === 'program' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
              Crear programa completo
            </Button>
            {diag && (
              <Button variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Button>
            )}
          </div>
        </div>
      )}

      {/* Diagnosis */}
      {diag && (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className={`${card} lg:col-span-1`}>
            <p className="text-sm text-white/50">Referent Potential Score</p>
            <p className={`mt-1 text-5xl font-black ${scoreColor(diag.referent_potential_score)}`}>
              {diag.referent_potential_score}
              <span className="text-lg text-white/30">/100</span>
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <span className={`${chip} ${COMMOD_COLOR[diag.commoditization_level] ?? COMMOD_COLOR.unknown}`}>
                commoditización: {diag.commoditization_level}
              </span>
              <span className={`${chip} bg-white/10 text-white/60`}>evidencia: {diag.evidence_quality ?? '—'}</span>
              <span className={`${chip} ${diag.generated_by === 'llm' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-white/10 text-white/50'}`}>
                {diag.generated_by === 'llm' ? 'IA' : diag.generated_by} · conf {diag.confidence}
              </span>
              {diag.score_delta != null && (
                <span className={`${chip} ${diag.score_delta >= 0 ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300'}`}>
                  Δ {diag.score_delta > 0 ? '+' : ''}{diag.score_delta}
                </span>
              )}
            </div>
            {diag.summary && <p className="mt-4 text-sm text-white/70">{diag.summary}</p>}
            <Button variant="secondary" className="mt-4 w-full" onClick={() => setShowForm(true)}>
              Re-diagnosticar
            </Button>
          </div>

          <div className={`${card} lg:col-span-2`}>
            <p className="mb-2 text-sm text-white/50">Scorecard (0-5 por eje)</p>
            {radarData.length ? (
              <ResponsiveContainer width="100%" height={240}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.12)" />
                  <PolarAngleAxis dataKey="axis" tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 5]} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} />
                  <Radar dataKey="value" stroke="#f97316" fill="#f97316" fillOpacity={0.35} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-white/40">Sin scorecard</p>
            )}
          </div>

          <div className={card}>
            <p className="mb-2 font-semibold text-white/80">Síntomas</p>
            <List items={diag.symptoms} tone="bad" />
          </div>
          <div className={card}>
            <p className="mb-2 font-semibold text-white/80">Causas raíz</p>
            <List items={diag.root_causes} />
          </div>
          <div className={card}>
            <p className="mb-2 font-semibold text-white/80">Palancas de mayor apalancamiento</p>
            <List items={diag.highest_leverage_moves} tone="good" />
          </div>
          <div className={card}>
            <p className="mb-2 font-semibold text-white/80">Quick wins (≤30 días)</p>
            <List items={diag.quick_wins} tone="good" />
          </div>
          <div className={card}>
            <p className="mb-2 font-semibold text-white/80">Movimientos estructurales</p>
            <List items={diag.structural_moves} />
          </div>
          <div className={card}>
            <p className="mb-2 font-semibold text-white/80">Kill criteria (cuándo NO perseguir)</p>
            <List items={diag.kill_criteria} tone="bad" />
          </div>
          {diag.closest_precedent && (
            <Accordion title="Precedente más cercano" subtitle={diag.closest_precedent.brand}>
              <Json data={diag.closest_precedent} />
            </Accordion>
          )}
          {diag.moat_assessment && (
            <Accordion title="Evaluación de moat">
              <Json data={diag.moat_assessment} />
            </Accordion>
          )}
        </div>
      )}

      {/* Program */}
      {activeProgram ? (
        <div className={card}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold">{activeProgram.name}</p>
              <p className="text-sm text-white/50">
                {completed.size}/{stages.length} etapas · estado {activeProgram.status}
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={doRunAll} disabled={busy === 'runall'}>
                {busy === 'runall' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Rocket className="h-4 w-4" />}
                Correr todas las etapas
              </Button>
              <Button variant="secondary" onClick={doCoherence} disabled={busy === 'coherence'}>
                {busy === 'coherence' ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldAlert className="h-4 w-4" />}
                Auditar coherencia
              </Button>
            </div>
          </div>

          {/* stage rail */}
          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {stages.map((s) => {
              const done = completed.has(s.key)
              const running = busy === `stage:${s.key}`
              return (
                <button
                  key={s.key}
                  onClick={() => doRunStage(s.key)}
                  disabled={!!busy}
                  className={`rounded-lg border p-2.5 text-left text-xs transition-colors ${
                    done ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-white/10 bg-white/5 hover:bg-white/10'
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> :
                      done ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> :
                      <div className="h-3.5 w-3.5 rounded-full border border-white/30" />}
                    <span className="font-semibold text-white/80">{s.name.split('—')[0].trim()}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-white/40">{s.name.split('—')[1]?.trim()}</p>
                </button>
              )
            })}
          </div>

          {/* coherence */}
          {coherence && (
            <div className="mt-4 rounded-lg border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2">
                <span className={`text-2xl font-black ${scoreColor(coherence.score ?? 0)}`}>{coherence.score ?? '—'}</span>
                <span className="text-sm text-white/50">/100 coherencia entre etapas</span>
              </div>
              {coherence.summary && <p className="mt-1 text-sm text-white/70">{coherence.summary}</p>}
              {!!coherence.must_fix_before_launch?.length && (
                <div className="mt-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-red-300">Arreglar antes de lanzar</p>
                  <List items={coherence.must_fix_before_launch} tone="bad" />
                </div>
              )}
            </div>
          )}

          {/* roadmap */}
          {roadmap?.north_star && (
            <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary">North star</p>
              <p className="text-sm text-white/85">{roadmap.north_star}</p>
              {roadmap.roadmap && (
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  {['90', '180', '365'].map((h) => (
                    <div key={h} className="rounded-md bg-white/5 p-2 text-xs">
                      <p className="font-semibold text-white/70">{h} días — {roadmap.roadmap[h]?.theme}</p>
                      <p className="mt-1 text-white/40">{roadmap.roadmap[h]?.exit_gate?.question}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* stage artifacts — deep view */}
          {activeProgram.metrics_board && (
            <div className="mt-4 space-y-3">
              {stages.filter((s) => s.key !== 'roadmap' && activeProgram.metrics_board?.[s.key]).map((s) => {
                const bridge = activeProgram.metrics_board?.[`${s.key}_bridge`]
                return (
                  <Accordion key={s.key} title={s.name} subtitle={s.deliverable}>
                    <StageArtifact stageKey={s.key} artifact={activeProgram.metrics_board![s.key]} />
                    {bridge && (
                      <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-sm">
                        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-300">
                          Bridge automático{bridge.created_count != null ? ` · ${bridge.created_count} creados` : ''}
                        </p>
                        <Json data={bridge.deployed ?? bridge} />
                      </div>
                    )}
                  </Accordion>
                )
              })}
            </div>
          )}
        </div>
      ) : (
        <div className={card}>
          <p className="text-sm text-white/60">
            No hay programa activo.{' '}
            <button className="text-primary underline" onClick={() => setShowForm(true)}>Crear uno</button>
          </p>
        </div>
      )}

      {/* Other bridges */}
      <div className={card}>
        <p className="mb-3 font-semibold">Integraciones</p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={doDeployAssets} disabled={busy === 'assets'}>
            {busy === 'assets' ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Identidad → biblioteca de contenido
          </Button>
          <Button size="sm" variant="secondary" onClick={doDeployCompetitive} disabled={busy === 'competitive'}>
            {busy === 'competitive' ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Posicionamiento → monitores + battlecards
          </Button>
        </div>
        {bridgeMsg && <p className="mt-2 text-sm text-emerald-400">{bridgeMsg}</p>}
      </div>

      {/* FOMO bridge */}
      <div className={card}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-400" />
            <p className="font-semibold">Campañas FOMO reales</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={doFomoPreview} disabled={busy === 'fomo-preview'}>
              {busy === 'fomo-preview' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
              Previsualizar
            </Button>
            <Button size="sm" variant="secondary" onClick={() => doFomoDeploy(false)} disabled={busy === 'fomo-deploy'}>
              Crear borradores
            </Button>
            <Button size="sm" onClick={() => doFomoDeploy(true)} disabled={busy === 'fomo-deploy'}>
              Crear y activar
            </Button>
          </div>
        </div>
        {fomoPlan && (
          <div className="mt-3 space-y-2 text-sm">
            <p className="text-white/50">Cadencia: {fomoPlan.cadence ?? '—'}</p>
            {fomoPlan.campaign_specs.map((c, i) => (
              <div key={i} className="rounded-md border border-white/10 bg-white/5 p-2">
                <span className={`${chip} bg-orange-500/15 text-orange-300`}>{c.campaign_type}</span>
                <span className="ml-2 text-white/80">{c.headline}</span>
              </div>
            ))}
            {!!fomoPlan.skipped_levers?.length && (
              <p className="text-xs text-white/40">
                Omitidos: {fomoPlan.skipped_levers.map((s) => s.lever).join(', ')}
              </p>
            )}
            {fomoPlan.created_count != null && (
              <p className="text-emerald-400">{fomoPlan.created_count} campañas creadas.</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
