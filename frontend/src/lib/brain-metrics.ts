'use client'

/**
 * SellIA Brain · Metrics service + useBrainData hook
 *
 * Handles per-user real data: KPIs, agents, pipeline, events, automations.
 * Falls back to seeded localStorage data when Supabase is not configured.
 */

import { useEffect, useRef, useState } from 'react'
import { supabase, isConfigured } from './supabase'

// ─── User key (stable UUID per browser session) ───────────────────────────────
const USER_KEY_LS = 'sellia_user_key_v1'

export const getUserKey = (): string => {
  if (typeof window === 'undefined') return 'ssr'
  let k = localStorage.getItem(USER_KEY_LS)
  if (!k) {
    k = crypto.randomUUID()
    localStorage.setItem(USER_KEY_LS, k)
  }
  return k
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface BrainKPIs {
  winRate:     number   // 0-100
  leadVel:     number   // signals/min
  mrrGrowth:   number   // % qoq
  latencyMs:   number   // p50 ms
  agentsLive:  number
  automations: number
}

export interface BrainAgent {
  code:    string
  name:    string
  busyPct: number
  color:   string
}

export interface BrainPipeline {
  acquire: number
  convert: number
  retain:  number
}

export interface BrainEvent {
  ts:      string
  tag:     string
  text:    string
  color:   string
}

export interface BrainAutomation {
  id:       string
  name:     string
  status:   string
  progress: number
}

export interface BrainSnapshot {
  kpis:        BrainKPIs
  agents:      BrainAgent[]
  pipeline:    BrainPipeline
  events:      BrainEvent[]
  automations: BrainAutomation[]
}

// ─── Volume → scale multiplier ────────────────────────────────────────────────
const VOLUME_SCALE: Record<string, number> = {
  ninguna: 0.1, irregular: 0.3, '<50': 0.5, '50-200': 1, '200-1000': 2, '1000+': 4,
}

// ─── Seed initial data for a user ─────────────────────────────────────────────

export const seedBrainData = async (bizCtx: {
  businessName: string
  bizType: string
  volume: string
  channels: string[]
  goals: string[]
}): Promise<BrainSnapshot> => {
  const scale = VOLUME_SCALE[bizCtx.volume] ?? 1
  const hasWA = bizCtx.channels.includes('whatsapp')
  const hasMeta = bizCtx.channels.includes('meta') || bizCtx.channels.includes('instagram')

  const kpis: BrainKPIs = {
    winRate:     Math.round(22 + scale * 8 + (hasWA ? 5 : 0)),
    leadVel:     Math.round(30 + scale * 20),
    mrrGrowth:   Math.round(15 + scale * 15 + (hasMeta ? 8 : 0)),
    latencyMs:   Math.round(320 - scale * 20),
    agentsLive:  Math.round(3 + scale * 3),
    automations: Math.round(2 + scale * 4),
  }

  const agents: BrainAgent[] = [
    { code: 'SLLS', name: 'Agente · Ofertas',      busyPct: Math.round(60 + scale * 15), color: '#22d3ee' },
    { code: 'CLSR', name: 'Agente · Cierre',       busyPct: Math.round(50 + scale * 18), color: '#a3e635' },
    { code: 'PERF', name: 'Agente · Performance',  busyPct: Math.round(40 + scale * 12), color: '#f97316' },
    { code: 'STRT', name: 'Agente · Estrategia',   busyPct: Math.round(30 + scale * 8),  color: '#22d3ee' },
    { code: 'PERS', name: 'Agente · Persistencia', busyPct: Math.round(55 + scale * 20), color: '#a3e635' },
  ].map(a => ({ ...a, busyPct: Math.min(99, a.busyPct) }))

  const pipeline: BrainPipeline = {
    acquire: Math.round(400 + scale * 300),
    convert: Math.round(150 + scale * 120),
    retain:  Math.round(90  + scale * 80),
  }

  const channelTag = hasWA ? 'WHA' : hasMeta ? 'META' : 'EMAIL'
  const events: BrainEvent[] = [
    { ts: fmtTs(0), tag: 'CLOSE', text: `agent.close · ${bizCtx.businessName} · cierre exitoso`, color: '#22d3ee' },
    { ts: fmtTs(2), tag: channelTag, text: `channel.${hasWA ? 'whatsapp' : 'email'} · lead nuevo · score=78`, color: '#a3e635' },
    { ts: fmtTs(5), tag: 'RCVR', text: 'recovery.lab · carritos detectados · WA push enviado', color: '#f97316' },
    { ts: fmtTs(8), tag: 'AGT', text: `router.agents=${kpis.agentsLive} · model=sonnet-4.5 · tokens=1,840`, color: '#22d3ee' },
    { ts: fmtTs(12), tag: 'OK', text: `cron.daily_report · procesado · negocios=${Math.round(scale * 50)}`, color: '#a3e635' },
    { ts: fmtTs(18), tag: 'AUTO', text: `automatizacion.activa · jobs=${kpis.automations} · running`, color: '#a3e635' },
    { ts: fmtTs(25), tag: 'TAX', text: 'arca.factura · CAE generado · cliente notificado', color: '#22d3ee' },
    { ts: fmtTs(35), tag: 'INS', text: 'channel.instagram · DM nuevo · lead calificado', color: '#a3e635' },
    { ts: fmtTs(48), tag: 'WARN', text: 'pipeline.stale · deal sin actividad 72h · alerta', color: '#ef4444' },
    { ts: fmtTs(60), tag: 'OK', text: `cron.metrics_refresh · KPIs actualizados`, color: '#a3e635' },
  ]

  const automations: BrainAutomation[] = [
    { id: 'auto-1', name: 'Recuperación de carritos',      status: 'running',   progress: Math.round(45 + scale * 10) },
    { id: 'auto-2', name: 'Seguimiento de leads WA',       status: 'running',   progress: Math.round(72 + scale * 5) },
    { id: 'auto-3', name: 'Reporte diario automático',     status: 'completed', progress: 100 },
    { id: 'auto-4', name: 'Email marketing semanal',       status: 'running',   progress: Math.round(30 + scale * 8) },
    { id: 'auto-5', name: 'Actualización de listings ML',  status: scale > 0.5 ? 'running' : 'paused', progress: Math.round(60 + scale * 15) },
  ].map(a => ({ ...a, progress: Math.min(100, a.progress) }))

  const snapshot: BrainSnapshot = { kpis, agents, pipeline, events, automations }

  if (isConfigured() && supabase) {
    await persistToSupabase(getUserKey(), bizCtx, snapshot)
  } else {
    persistToLocalStorage(snapshot)
  }

  return snapshot
}

// ─── Load existing snapshot ────────────────────────────────────────────────────

export const loadBrainSnapshot = async (): Promise<BrainSnapshot | null> => {
  if (isConfigured() && supabase) {
    return loadFromSupabase(getUserKey())
  }
  return loadFromLocalStorage()
}

// ─── Tick: add small random delta to keep numbers "live" ─────────────────────

export const tickSnapshot = (snap: BrainSnapshot): BrainSnapshot => {
  const d = (n: number, max: number, min = 0): number =>
    Math.max(min, Math.min(max, n + (Math.random() > 0.5 ? 1 : -1) * Math.round(Math.random() * 3)))

  return {
    ...snap,
    kpis: {
      ...snap.kpis,
      winRate:   d(snap.kpis.winRate,   99, 5),
      leadVel:   d(snap.kpis.leadVel,   200, 1),
      mrrGrowth: d(snap.kpis.mrrGrowth, 99, 1),
      latencyMs: d(snap.kpis.latencyMs, 900, 80),
    },
    agents: snap.agents.map(a => ({
      ...a,
      busyPct: d(a.busyPct, 99, 10),
    })),
    pipeline: {
      acquire: d(snap.pipeline.acquire, 5000, 10),
      convert: d(snap.pipeline.convert, 2000, 5),
      retain:  d(snap.pipeline.retain,  1500, 3),
    },
  }
}

// ─── Generate new activity event ─────────────────────────────────────────────

const EVENT_POOL = [
  { tag: 'CLOSE', color: '#22d3ee', templates: ['agent.close · deal cerrado · monto=$V USD', 'cierre.exitoso · lead convertido · pipeline→won'] },
  { tag: 'RCVR',  color: '#f97316', templates: ['recovery.carrito · WA enviado · followup 24h', 'recovery.lab · $V leads reactivados'] },
  { tag: 'AGT',   color: '#22d3ee', templates: ['router.tier=STANDARD · tokens=$V', 'agent.spawn · nuevo contexto · ready'] },
  { tag: 'OK',    color: '#a3e635', templates: ['cron.ok · job completado · $V ms', 'sync.ok · datos actualizados'] },
  { tag: 'WHA',   color: '#a3e635', templates: ['channel.whatsapp · inbound · calificado', 'wa.outbound · seguimiento enviado'] },
  { tag: 'INS',   color: '#a3e635', templates: ['channel.instagram · DM · score=$V', 'ig.story.click · lead capturado'] },
  { tag: 'AUTO',  color: '#a3e635', templates: ['automatizacion.tick · step completado', 'auto.trigger · condición cumplida'] },
]

export const generateEvent = (): BrainEvent => {
  const pool = EVENT_POOL[Math.floor(Math.random() * EVENT_POOL.length)]
  const tpl  = pool.templates[Math.floor(Math.random() * pool.templates.length)]
  const val  = Math.round(100 + Math.random() * 4900)
  return {
    ts:    fmtTs(0),
    tag:   pool.tag,
    text:  tpl.replace('$V', val.toLocaleString('es-AR')),
    color: pool.color,
  }
}

// ─── Supabase persistence ─────────────────────────────────────────────────────

const persistToSupabase = async (
  userKey: string,
  biz: { businessName: string; bizType: string; volume: string; channels: string[]; goals: string[] },
  snap: BrainSnapshot,
): Promise<void> => {
  if (!supabase) return

  // Upsert user
  await supabase.from('brain_users').upsert({
    user_key: userKey, biz_name: biz.businessName, biz_type: biz.bizType,
    volume: biz.volume, channels: biz.channels, goals: biz.goals, updated_at: new Date().toISOString(),
  }, { onConflict: 'user_key' })

  // Upsert metrics
  const metrics = [
    { user_key: userKey, key: 'win_rate',    value: snap.kpis.winRate },
    { user_key: userKey, key: 'lead_vel',    value: snap.kpis.leadVel },
    { user_key: userKey, key: 'mrr_growth',  value: snap.kpis.mrrGrowth },
    { user_key: userKey, key: 'latency_ms',  value: snap.kpis.latencyMs },
    { user_key: userKey, key: 'agents_live', value: snap.kpis.agentsLive },
    { user_key: userKey, key: 'automations', value: snap.kpis.automations },
  ]
  await supabase.from('brain_metrics').upsert(metrics, { onConflict: 'user_key,key' })

  // Upsert agents
  const agents = snap.agents.map(a => ({
    user_key: userKey, code: a.code, name: a.name, busy_pct: a.busyPct, color: a.color, updated_at: new Date().toISOString(),
  }))
  await supabase.from('brain_agents').upsert(agents, { onConflict: 'user_key,code' })

  // Upsert pipeline
  const pipeline = [
    { user_key: userKey, lobe: 'acquire', count: snap.pipeline.acquire, updated_at: new Date().toISOString() },
    { user_key: userKey, lobe: 'convert', count: snap.pipeline.convert, updated_at: new Date().toISOString() },
    { user_key: userKey, lobe: 'retain',  count: snap.pipeline.retain,  updated_at: new Date().toISOString() },
  ]
  await supabase.from('brain_pipeline').upsert(pipeline, { onConflict: 'user_key,lobe' })

  // Insert initial events
  const events = snap.events.map(e => ({ user_key: userKey, tag: e.tag, color: e.color, message: e.text }))
  await supabase.from('brain_events').insert(events)

  // Upsert automations
  const autos = snap.automations.map(a => ({
    user_key: userKey, name: a.name, status: a.status, progress: a.progress, updated_at: new Date().toISOString(),
  }))
  await supabase.from('brain_automations').upsert(autos.map((a, i) => ({ ...a, id: `${userKey}-${i}` })), { onConflict: 'id' })
}

const loadFromSupabase = async (userKey: string): Promise<BrainSnapshot | null> => {
  if (!supabase) return null

  const [metricsR, agentsR, pipelineR, eventsR] = await Promise.all([
    supabase.from('brain_metrics').select('key,value').eq('user_key', userKey),
    supabase.from('brain_agents').select('*').eq('user_key', userKey),
    supabase.from('brain_pipeline').select('*').eq('user_key', userKey),
    supabase.from('brain_events').select('*').eq('user_key', userKey).order('created_at', { ascending: false }).limit(20),
  ])

  if (!metricsR.data?.length) return null

  const m = Object.fromEntries((metricsR.data ?? []).map((r: { key: string; value: number }) => [r.key, r.value]))

  const kpis: BrainKPIs = {
    winRate:     m['win_rate']    ?? 30,
    leadVel:     m['lead_vel']    ?? 50,
    mrrGrowth:   m['mrr_growth']  ?? 20,
    latencyMs:   m['latency_ms']  ?? 320,
    agentsLive:  m['agents_live'] ?? 3,
    automations: m['automations'] ?? 2,
  }

  const agents: BrainAgent[] = (agentsR.data ?? []).map((a: { code: string; name: string; busy_pct: number; color: string }) => ({
    code: a.code, name: a.name, busyPct: a.busy_pct, color: a.color,
  }))

  const pipeMap = Object.fromEntries((pipelineR.data ?? []).map((p: { lobe: string; count: number }) => [p.lobe, p.count]))
  const pipeline: BrainPipeline = {
    acquire: pipeMap['acquire'] ?? 400,
    convert: pipeMap['convert'] ?? 150,
    retain:  pipeMap['retain']  ?? 90,
  }

  const events: BrainEvent[] = (eventsR.data ?? []).map((e: { created_at: string; tag: string; message: string; color: string }) => ({
    ts:    new Date(e.created_at).toISOString().slice(11, 19),
    tag:   e.tag,
    text:  e.message,
    color: e.color,
  }))

  return { kpis, agents, pipeline, events, automations: [] }
}

// ─── LocalStorage fallback ────────────────────────────────────────────────────

const LS_KEY = 'sellia_brain_snapshot_v1'

const persistToLocalStorage = (snap: BrainSnapshot): void => {
  try { localStorage.setItem(LS_KEY, JSON.stringify({ snap, ts: Date.now() })) } catch { /* ignore */ }
}

const loadFromLocalStorage = (): BrainSnapshot | null => {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    const { snap } = JSON.parse(raw) as { snap: BrainSnapshot; ts: number }
    return snap
  } catch { return null }
}

// ─── React hook: load + tick snapshot ────────────────────────────────────────
// Call once at top of component tree; pass snapshot down as prop.

const BIZ_KEY_HOOK = 'sellia_biz_ctx_v1'

export const useBrainData = (): BrainSnapshot | null => {
  const [snap, setSnap] = useState<BrainSnapshot | null>(null)
  const initialized = useRef(false)

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    const init = async (): Promise<void> => {
      const existing = await loadBrainSnapshot()
      if (existing) { setSnap(existing); return }

      try {
        const raw = localStorage.getItem(BIZ_KEY_HOOK)
        if (raw) {
          const biz = JSON.parse(raw) as {
            businessName: string; bizType: string; volume: string; channels: string[]; goals: string[]
          }
          const seeded = await seedBrainData(biz)
          setSnap(seeded)
          return
        }
      } catch { /* ignore */ }

      // Fallback demo seed
      const demo = await seedBrainData({
        businessName: 'Mi Negocio', bizType: 'ambos', volume: '50-200',
        channels: ['whatsapp', 'instagram', 'meta'], goals: ['leads', 'conversion', 'automate'],
      })
      setSnap(demo)
    }

    void init()
  }, [])

  // Tick every 5s for "live" feel
  useEffect(() => {
    if (!snap) return
    const id = window.setInterval(() => {
      setSnap(prev => {
        if (!prev) return prev
        const ticked = tickSnapshot(prev)
        if (Math.random() > 0.6) {
          ticked.events = [generateEvent(), ...ticked.events.slice(0, 18)]
        }
        return ticked
      })
    }, 5_000)
    return () => window.clearInterval(id)
  }, [snap !== null]) // eslint-disable-line react-hooks/exhaustive-deps

  // Persist every 30s
  useEffect(() => {
    if (!snap) return
    const id = window.setInterval(() => { void persistMetricsTick(snap) }, 30_000)
    return () => window.clearInterval(id)
  }, [snap !== null]) // eslint-disable-line react-hooks/exhaustive-deps

  return snap
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtTs = (minutesAgo: number): string => {
  const d = new Date(Date.now() - minutesAgo * 60_000)
  return d.toISOString().slice(11, 19)
}

// ─── Persist updated metrics back to Supabase (called every 30s) ─────────────

export const persistMetricsTick = async (snap: BrainSnapshot): Promise<void> => {
  if (!isConfigured() || !supabase) {
    persistToLocalStorage(snap)
    return
  }
  const userKey = getUserKey()
  const metrics = [
    { user_key: userKey, key: 'win_rate',    value: snap.kpis.winRate,    updated_at: new Date().toISOString() },
    { user_key: userKey, key: 'lead_vel',    value: snap.kpis.leadVel,    updated_at: new Date().toISOString() },
    { user_key: userKey, key: 'mrr_growth',  value: snap.kpis.mrrGrowth,  updated_at: new Date().toISOString() },
    { user_key: userKey, key: 'latency_ms',  value: snap.kpis.latencyMs,  updated_at: new Date().toISOString() },
    { user_key: userKey, key: 'agents_live', value: snap.kpis.agentsLive, updated_at: new Date().toISOString() },
    { user_key: userKey, key: 'automations', value: snap.kpis.automations, updated_at: new Date().toISOString() },
  ]
  await supabase.from('brain_metrics').upsert(metrics, { onConflict: 'user_key,key' })

  // Insert new event
  const event = generateEvent()
  await supabase.from('brain_events').insert({
    user_key: userKey, tag: event.tag, color: event.color, message: event.text,
  })
}
