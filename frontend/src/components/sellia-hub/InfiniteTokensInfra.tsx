'use client'

/**
 * INFINITE TOKENS INFRA
 *
 * Sistema con tokens "infinitos" via:
 *   1. Local LLMs · Ollama + LM Studio + vLLM + Llamafile (self-hosted, $0)
 *   2. Open models cloud · OpenRouter, Together, Groq, Cerebras, Replicate
 *   3. Cloud premium · Anthropic, OpenAI, Mistral (solo cuando vale la pena)
 *   4. Cost router · decide qué proveedor usar según complejidad
 *   5. DB infra · Postgres + Redis + Qdrant + Pinecone + ClickHouse
 *   6. Caching tiers · semantic cache + prompt cache + KV cache
 */

import { useState, useMemo, useEffect } from 'react'
import {
  Cpu, Server, Cloud, Database, Cog, Activity, Sparkles, Zap,
  CheckCircle2, AlertCircle, Hash, Filter, ChevronRight, GitBranch,
  DollarSign, TrendingDown, Layers
} from 'lucide-react'

type ProviderTier = 'local' | 'open-cloud' | 'cloud-premium'
type ProviderStatus = 'online' | 'idle' | 'error'

interface Provider {
  id: string
  name: string
  tier: ProviderTier
  models: string[]
  tokensPerSec: number
  costPerMTok: number // USD per million tokens (0 for local)
  contextWindow: string
  status: ProviderStatus
  emoji: string
  color: string
  share: number // % of total traffic
}

const PROVIDERS: Provider[] = [
  // LOCAL · self-hosted ($0)
  { id: 'ollama',    name: 'Ollama',                tier: 'local',         models: ['Llama 3.3 70B', 'Qwen 2.5 72B', 'DeepSeek V3', 'Mistral Large'], tokensPerSec: 84,  costPerMTok: 0,    contextWindow: '128k',  status: 'online', emoji: '🦙', color: '#84cc16', share: 47 },
  { id: 'lmstudio',  name: 'LM Studio',             tier: 'local',         models: ['Qwen2.5-Coder', 'Phi-4', 'Gemma 3'],                              tokensPerSec: 67,  costPerMTok: 0,    contextWindow: '64k',   status: 'online', emoji: '💻', color: '#22c55e', share: 12 },
  { id: 'vllm',      name: 'vLLM cluster',           tier: 'local',         models: ['Llama 4 Scout', 'Mistral 8x22B', 'Qwen3-Coder'],                tokensPerSec: 247, costPerMTok: 0,    contextWindow: '256k',  status: 'online', emoji: '⚡', color: '#16a34a', share: 14 },
  { id: 'llamafile', name: 'Llamafile (edge)',      tier: 'local',         models: ['Llama 3.2 1B', 'TinyLlama'],                                     tokensPerSec: 142, costPerMTok: 0,    contextWindow: '8k',    status: 'online', emoji: '📦', color: '#10b981', share: 4 },

  // OPEN CLOUD · cheap APIs
  { id: 'groq',      name: 'Groq · LPU',            tier: 'open-cloud',    models: ['Llama 3.3 70B', 'Mixtral 8x7B', 'Gemma 2 9B'],                   tokensPerSec: 847, costPerMTok: 0.59, contextWindow: '128k',  status: 'online', emoji: '⚡', color: '#f97316', share: 8 },
  { id: 'cerebras',  name: 'Cerebras · WaferScale', tier: 'open-cloud',    models: ['Llama 3.3 70B', 'Qwen 2.5 32B'],                                 tokensPerSec: 2247,costPerMTok: 0.60, contextWindow: '128k',  status: 'online', emoji: '🌊', color: '#06b6d4', share: 3 },
  { id: 'together',  name: 'Together AI',           tier: 'open-cloud',    models: ['Llama 3.3 70B', 'DeepSeek V3', 'Qwen 2.5'],                       tokensPerSec: 184, costPerMTok: 0.88, contextWindow: '128k',  status: 'online', emoji: '🤝', color: '#0ea5e9', share: 4 },
  { id: 'openrouter',name: 'OpenRouter',            tier: 'open-cloud',    models: ['200+ models routing'],                                            tokensPerSec: 156, costPerMTok: 0.50, contextWindow: 'varies',status: 'online', emoji: '🔀', color: '#a855f7', share: 3 },
  { id: 'replicate', name: 'Replicate',             tier: 'open-cloud',    models: ['Multi-model platform'],                                           tokensPerSec: 89,  costPerMTok: 1.20, contextWindow: '32k',   status: 'idle',   emoji: '🔁', color: '#3b82f6', share: 1 },
  { id: 'deepinfra', name: 'DeepInfra',             tier: 'open-cloud',    models: ['Llama 3.3', 'Mixtral', 'Qwen'],                                   tokensPerSec: 124, costPerMTok: 0.30, contextWindow: '64k',   status: 'online', emoji: '🌐', color: '#14b8a6', share: 2 },

  // CLOUD PREMIUM · cuando vale la pena
  { id: 'anthropic', name: 'Anthropic Claude',      tier: 'cloud-premium', models: ['Sonnet 4.7', 'Opus 4.6', 'Haiku 3.5'],                            tokensPerSec: 67,  costPerMTok: 3.00, contextWindow: '500k',  status: 'online', emoji: '✨', color: '#ec4899', share: 1.5 },
  { id: 'openai',    name: 'OpenAI',                tier: 'cloud-premium', models: ['GPT-5', 'GPT-5-mini', 'o3'],                                     tokensPerSec: 78,  costPerMTok: 2.50, contextWindow: '256k',  status: 'online', emoji: '🟢', color: '#10b981', share: 0.4 },
  { id: 'mistral',   name: 'Mistral AI',            tier: 'cloud-premium', models: ['Mistral Large 2', 'Codestral'],                                  tokensPerSec: 89,  costPerMTok: 2.00, contextWindow: '128k',  status: 'idle',   emoji: '🇫🇷', color: '#fbbf24', share: 0.1 },
]

interface DBNode {
  id: string
  name: string
  emoji: string
  role: string
  size: string
  qps: number
  color: string
}

const DB_INFRA: DBNode[] = [
  { id: 'pg',     name: 'PostgreSQL',       emoji: '🐘', role: 'OLTP · main store',          size: '847 GB · 12.4M rows',  qps: 1247, color: '#3b82f6' },
  { id: 'redis',  name: 'Redis',            emoji: '🔴', role: 'Hot cache · sessions · queues', size: '64 GB RAM',           qps: 8947, color: '#dc2626' },
  { id: 'qdrant', name: 'Qdrant',           emoji: '🧭', role: 'Vector search · embeddings',  size: '847M vectors',         qps: 423,  color: '#a855f7' },
  { id: 'pine',   name: 'Pinecone (backup)',emoji: '🌲', role: 'Vector backup · multi-region', size: '847M vectors',         qps: 89,   color: '#14b8a6' },
  { id: 'click',  name: 'ClickHouse',       emoji: '📊', role: 'Analytics OLAP · events',      size: '4.2 TB · 184M events', qps: 678,  color: '#fbbf24' },
  { id: 's3',     name: 'S3 / R2',          emoji: '☁️', role: 'Object store · screenshots/audio', size: '12 TB',           qps: 234,  color: '#f59e0b' },
  { id: 'neo4j',  name: 'Neo4j',            emoji: '🕸',  role: 'Knowledge graph · relationships', size: '4.7M nodes · 18M edges', qps: 47, color: '#06b6d4' },
  { id: 'kafka',  name: 'Kafka',            emoji: '📡', role: 'Event stream backbone',       size: '8 brokers · 184 topics', qps: 12847, color: '#000' },
]

interface CacheTier {
  emoji: string
  name: string
  hitRate: number
  scope: string
  savings: string
  color: string
}

const CACHES: CacheTier[] = [
  { emoji: '🧠', name: 'Semantic cache · query similarity',  hitRate: 47, scope: 'Cross-session embedded',     savings: '$2,847/mes', color: '#a855f7' },
  { emoji: '📝', name: 'Prompt cache · system prompts',      hitRate: 92, scope: 'Within tenant',              savings: '$1,247/mes', color: '#06b6d4' },
  { emoji: '⚙️', name: 'KV cache · attention states',         hitRate: 78, scope: 'Sequential conversation',    savings: '$847/mes',   color: '#fbbf24' },
  { emoji: '💾', name: 'Result cache · tool outputs',         hitRate: 64, scope: 'Idempotent ops',              savings: '$589/mes',   color: '#10b981' },
]

const TIER_CONFIG: Record<ProviderTier, { label: string; color: string; bg: string }> = {
  'local':         { label: 'LOCAL · $0',        color: '#22c55e', bg: 'bg-emerald-500/[0.05]' },
  'open-cloud':    { label: 'OPEN CLOUD · CHEAP',color: '#3b82f6', bg: 'bg-blue-500/[0.05]' },
  'cloud-premium': { label: 'CLOUD PREMIUM',     color: '#ec4899', bg: 'bg-pink-500/[0.05]' },
}

export default function InfiniteTokensInfra() {
  const [tierFilter, setTierFilter] = useState<ProviderTier | 'all'>('all')
  const [pulse, setPulse] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setPulse(p => (p + 1) % 100), 60)
    return () => clearInterval(id)
  }, [])

  const filtered = useMemo(
    () => tierFilter === 'all' ? PROVIDERS : PROVIDERS.filter(p => p.tier === tierFilter),
    [tierFilter]
  )

  const stats = useMemo(() => {
    const localShare = PROVIDERS.filter(p => p.tier === 'local').reduce((s, p) => s + p.share, 0)
    const openShare = PROVIDERS.filter(p => p.tier === 'open-cloud').reduce((s, p) => s + p.share, 0)
    const premiumShare = PROVIDERS.filter(p => p.tier === 'cloud-premium').reduce((s, p) => s + p.share, 0)
    const totalTps = PROVIDERS.reduce((s, p) => s + p.tokensPerSec, 0)
    const onlineCount = PROVIDERS.filter(p => p.status === 'online').length
    // mock token consumption
    const tokensPerDay = 847_000_000
    const costSavedVsAllPremium = 2547
    const actualCost = 47
    return { localShare, openShare, premiumShare, totalTps, onlineCount, tokensPerDay, costSavedVsAllPremium, actualCost, total: PROVIDERS.length }
  }, [])

  const tierCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const p of PROVIDERS) c[p.tier] = (c[p.tier] || 0) + 1
    return c
  }, [])

  return (
    <section className="relative rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-[#0a1808]/85 via-[#0a0e1a]/90 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/80 via-cyan-400/60 to-transparent" />

      {/* Header */}
      <div className="relative px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/25 to-cyan-500/15 border border-emerald-500/40 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-emerald-400" style={{ filter: 'drop-shadow(0 0 8px rgba(16,185,129,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">INFINITE TOKENS</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  Ollama + open + premium routing</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                {stats.onlineCount}/{stats.total} ONLINE
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">{(stats.tokensPerDay / 1_000_000).toFixed(0)}M tokens/día procesados · {stats.totalTps.toLocaleString()} tok/s capacidad</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Stat label="Local share" value={`${stats.localShare}%`} sub="$0 cost" color="#22c55e" />
          <Stat label="Costo real" value={`$${stats.actualCost}`} sub="vs premium" color="#06b6d4" />
          <Stat label="Ahorro/mes" value={`$${stats.costSavedVsAllPremium}`} sub="por routing" color="#fbbf24" highlight />
        </div>
      </div>

      {/* Tier distribution bar */}
      <div className="px-5 py-3 border-b border-white/[0.06]">
        <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold mb-2">DISTRIBUCIÓN DE TRÁFICO · LOCAL FIRST</p>
        <div className="flex h-4 rounded-full overflow-hidden border border-white/10">
          <div className="flex items-center justify-center text-[9px] font-bold text-emerald-950" style={{ width: `${stats.localShare}%`, background: '#22c55e' }}>
            LOCAL {stats.localShare}%
          </div>
          <div className="flex items-center justify-center text-[9px] font-bold text-blue-950" style={{ width: `${stats.openShare}%`, background: '#3b82f6' }}>
            OPEN {stats.openShare}%
          </div>
          <div className="flex items-center justify-center text-[9px] font-bold text-pink-950" style={{ width: `${stats.premiumShare * 10}%`, background: '#ec4899' }}>
            PREMIUM {stats.premiumShare.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Tier filter */}
      <div className="px-5 py-3 border-b border-white/[0.06] flex items-center gap-2 overflow-x-auto no-scrollbar">
        <Filter className="w-3 h-3 text-white/30 shrink-0" />
        <button
          onClick={() => setTierFilter('all')}
          className={`shrink-0 px-3 py-1 rounded-full text-[10px] font-bold border ${
            tierFilter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
          }`}
        >
          Todos · {PROVIDERS.length}
        </button>
        {(Object.keys(TIER_CONFIG) as ProviderTier[]).map(t => {
          const cfg = TIER_CONFIG[t]
          const active = tierFilter === t
          return (
            <button
              key={t}
              onClick={() => setTierFilter(t)}
              className="shrink-0 px-3 py-1 rounded-full text-[10px] font-bold border"
              style={
                active
                  ? { background: `${cfg.color}20`, borderColor: `${cfg.color}50`, color: cfg.color }
                  : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }
              }
            >
              {cfg.label} · {tierCounts[t] || 0}
            </button>
          )
        })}
      </div>

      {/* Providers grid */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {filtered.map(p => {
          const tier = TIER_CONFIG[p.tier]
          return (
            <div key={p.id} className="rounded-xl border p-3 transition-all"
              style={{
                background: p.status === 'online' ? `${p.color}08` : 'rgba(255,255,255,0.02)',
                borderColor: `${p.color}25`,
                opacity: p.status === 'online' ? 1 : 0.5,
              }}>
              <div className="flex items-start gap-2 mb-2">
                <span className="text-2xl shrink-0">{p.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-xs font-bold text-white truncate">{p.name}</p>
                    {p.status === 'online' && <div className="w-1.5 h-1.5 rounded-full animate-pulse shrink-0" style={{ background: p.color }} />}
                  </div>
                  <span className="text-[8px] px-1 py-0.5 rounded font-mono uppercase tracking-wider mt-0.5 inline-block" style={{ background: `${tier.color}18`, color: tier.color }}>
                    {tier.label.split(' ·')[0]}
                  </span>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-black tabular-nums" style={{ color: p.color }}>{p.tokensPerSec.toLocaleString()}</p>
                  <p className="text-[8px] text-white/40 font-mono">tok/s</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-1 mb-2">
                {p.models.slice(0, 3).map(m => (
                  <span key={m} className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] text-white/70 font-mono">
                    {m}
                  </span>
                ))}
                {p.models.length > 3 && (
                  <span className="text-[9px] text-white/30">+{p.models.length - 3}</span>
                )}
              </div>

              <div className="flex items-center justify-between text-[10px]">
                <span className="text-white/40">
                  <Hash className="w-2.5 h-2.5 inline mr-0.5" />
                  {p.contextWindow}
                </span>
                <span style={{ color: p.costPerMTok === 0 ? '#22c55e' : p.color }}>
                  {p.costPerMTok === 0 ? '$0 · GRATIS' : `$${p.costPerMTok.toFixed(2)}/M`}
                </span>
                <span className="text-white/40">{p.share}% traffic</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Cost router intelligence */}
      <div className="px-5 py-4 border-t border-white/[0.06] bg-black/30">
        <div className="flex items-center gap-2 mb-3">
          <GitBranch className="w-4 h-4 text-emerald-400" />
          <h3 className="text-[11px] uppercase tracking-widest font-bold text-emerald-400">COST ROUTER · DECISIÓN POR TAREA</h3>
          <span className="text-[10px] text-emerald-400/70 ml-auto">cascada local-first</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <RouteCard
            emoji="🟢"
            level="Simple"
            desc="Mensajes WA, respuestas FAQ, clasificación"
            provider="Ollama · Llama 3.3 70B"
            cost="$0"
            traffic="61%"
            color="#22c55e"
          />
          <RouteCard
            emoji="🔵"
            level="Medio"
            desc="Listing optim, copy ads, análisis ROI"
            provider="Groq · Llama 3.3 70B"
            cost="$0.59/M"
            traffic="37%"
            color="#3b82f6"
          />
          <RouteCard
            emoji="🟣"
            level="Complejo"
            desc="High-stakes deals, legal, propuestas custom"
            provider="Anthropic · Claude Sonnet 4.7"
            cost="$3/M"
            traffic="2%"
            color="#ec4899"
          />
        </div>
      </div>

      {/* Cache tiers */}
      <div className="px-5 py-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 mb-3">
          <Layers className="w-4 h-4 text-amber-400" />
          <h3 className="text-[11px] uppercase tracking-widest font-bold text-amber-400">CACHING TIERS · 4 NIVELES</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {CACHES.map(c => (
            <div key={c.name} className="rounded-xl border p-3" style={{ background: `${c.color}08`, borderColor: `${c.color}25` }}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{c.emoji}</span>
                  <div>
                    <p className="text-xs font-bold text-white">{c.name}</p>
                    <p className="text-[9px] text-white/40">{c.scope}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-base font-black tabular-nums" style={{ color: c.color }}>{c.hitRate}%</p>
                  <p className="text-[8px] text-white/40 uppercase">hit rate</p>
                </div>
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <div className="flex-1 h-1 bg-white/5 rounded-full mr-2 overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${c.hitRate}%`, background: c.color }} />
                </div>
                <span className="text-emerald-400 font-bold">{c.savings}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* DB Infra */}
      <div className="px-5 py-4 border-t border-white/[0.06] bg-black/30">
        <div className="flex items-center gap-2 mb-3">
          <Database className="w-4 h-4 text-blue-400" />
          <h3 className="text-[11px] uppercase tracking-widest font-bold text-blue-400">DATABASE INFRA · {DB_INFRA.length} NODOS</h3>
          <span className="text-[10px] text-white/40 ml-auto">{DB_INFRA.reduce((s, d) => s + d.qps, 0).toLocaleString()} qps total</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {DB_INFRA.map(d => (
            <div key={d.id} className="rounded-lg p-2.5 bg-white/[0.02] border" style={{ borderColor: `${d.color}25` }}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{d.emoji}</span>
                <p className="text-[11px] font-bold text-white truncate">{d.name}</p>
              </div>
              <p className="text-[9px] text-white/40 leading-snug mb-1">{d.role}</p>
              <div className="flex items-center justify-between text-[9px]">
                <span className="text-white/30 font-mono truncate">{d.size}</span>
                <span className="font-bold tabular-nums shrink-0" style={{ color: d.color }}>{d.qps.toLocaleString()} qps</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-white/[0.06] bg-emerald-500/[0.04] px-5 py-3 text-center">
        <p className="text-[11px] text-white/70 leading-snug">
          <TrendingDown className="w-3 h-3 inline text-emerald-400 mr-1" />
          <span className="text-emerald-400 font-bold">98% del tráfico</span> corre en <span className="text-white font-bold">infra propia o cloud barato</span>. Premium solo cuando vale. <span className="text-white">Tokens infinitos · costos mínimos.</span>
        </p>
      </div>
    </section>
  )
}

const Stat = ({ label, value, sub, color, highlight }: { label: string; value: string; sub: string; color: string; highlight?: boolean }) => (
  <div className={`text-center ${highlight ? 'rounded-lg px-2 py-1 bg-amber-500/10 border border-amber-500/25' : ''}`}>
    <p className="text-lg font-black tabular-nums" style={{ color }}>{value}</p>
    <p className="text-[8px] uppercase tracking-widest text-white/40 font-mono">{label}</p>
    <p className="text-[9px] text-white/40">{sub}</p>
  </div>
)

const RouteCard = ({ emoji, level, desc, provider, cost, traffic, color }: {
  emoji: string; level: string; desc: string; provider: string; cost: string; traffic: string; color: string
}) => (
  <div className="rounded-xl border p-3" style={{ background: `${color}08`, borderColor: `${color}30` }}>
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        <span className="text-2xl">{emoji}</span>
        <div>
          <p className="text-xs font-bold text-white">{level}</p>
          <p className="text-[9px] font-mono" style={{ color }}>{traffic} del tráfico</p>
        </div>
      </div>
    </div>
    <p className="text-[10px] text-white/55 mb-2 leading-snug">{desc}</p>
    <div className="rounded-md px-2 py-1.5 bg-black/30">
      <p className="text-[10px] font-mono font-bold truncate" style={{ color }}>{provider}</p>
      <p className="text-[9px] text-white/40 mt-0.5">{cost}</p>
    </div>
  </div>
)
