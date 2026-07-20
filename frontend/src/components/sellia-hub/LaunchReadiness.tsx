'use client'

/**
 * LAUNCH READINESS
 *
 * Dashboard de production-readiness · qué falta para vender comercialmente.
 * 6 categorías × items con progress bars + acción concreta por gap.
 */

import { useState, useMemo } from 'react'
import {
  Rocket, CheckCircle2, Circle, AlertCircle, Lock, Server,
  Plug, ShieldCheck, CreditCard, Users, Hash, Filter, Clock
} from 'lucide-react'

type Category = 'infra' | 'integrations' | 'compliance' | 'product' | 'billing' | 'devops'
type ItemStatus = 'done' | 'wip' | 'todo' | 'blocked'

interface Item {
  id: string
  emoji: string
  title: string
  category: Category
  status: ItemStatus
  progress: number // 0-100
  effort: string
  blocker?: string
  nextStep?: string
}

const ITEMS: Item[] = [
  // INFRA
  { id: 'i1', emoji: '🐘', title: 'PostgreSQL prod cluster',         category: 'infra', status: 'wip',  progress: 60, effort: '3 días',   nextStep: 'Migrate schema → Neon/Supabase' },
  { id: 'i2', emoji: '🔴', title: 'Redis cluster + persistence',     category: 'infra', status: 'wip',  progress: 70, effort: '1 día',    nextStep: 'Upstash redis HA' },
  { id: 'i3', emoji: '🧭', title: 'Qdrant vector DB',                 category: 'infra', status: 'todo', progress: 0,  effort: '2 días',   nextStep: 'Deploy en Hetzner CCX' },
  { id: 'i4', emoji: '🦙', title: 'Ollama GPU cluster',                category: 'infra', status: 'todo', progress: 10, effort: '5 días',   nextStep: 'Hetzner GPU pool 4×A100' },
  { id: 'i5', emoji: '🐳', title: 'CUA sandboxes (Firecracker/Docker)',category: 'infra', status: 'todo', progress: 5,  effort: '7 días',   nextStep: 'E2B + browser-use isolation' },
  { id: 'i6', emoji: '☁️', title: 'CDN + R2 storage',                 category: 'infra', status: 'done', progress: 100, effort: 'done',     nextStep: 'Cloudflare R2 activo' },
  { id: 'i7', emoji: '🏗', title: 'Multi-tenant isolation (RLS)',     category: 'infra', status: 'wip',  progress: 40, effort: '5 días',   nextStep: 'Row-Level Security policies' },

  // INTEGRATIONS
  { id: 'g1', emoji: '🟣', title: 'Stripe Connect (multi-vendor)',    category: 'integrations', status: 'wip',  progress: 50, effort: '4 días',  nextStep: 'Onboarding Express + payouts' },
  { id: 'g2', emoji: '🟡', title: 'Mercado Pago marketplace',          category: 'integrations', status: 'todo', progress: 20, effort: '5 días',  nextStep: 'MP marketplace approval' },
  { id: 'g3', emoji: '💚', title: 'WhatsApp Business Cloud API',       category: 'integrations', status: 'blocked', progress: 30, effort: '2-3 sem', blocker: 'Meta Business verification pendiente', nextStep: 'Subir docs CUIT + dominio' },
  { id: 'g4', emoji: '◼️', title: 'Meta Ads API + token review',       category: 'integrations', status: 'blocked', progress: 25, effort: '2-4 sem', blocker: 'App review Meta requerido', nextStep: 'Privacy policy + terms públicos' },
  { id: 'g5', emoji: '🔍', title: 'Google Ads API + dev token',         category: 'integrations', status: 'blocked', progress: 30, effort: '1-3 sem', blocker: 'Google dev token approval', nextStep: 'Aplicar dev token con MCC' },
  { id: 'g6', emoji: '🎵', title: 'TikTok Marketing API',                category: 'integrations', status: 'todo', progress: 10, effort: '2 sem',   nextStep: 'TikTok for Business app submit' },
  { id: 'g7', emoji: '📦', title: 'Amazon SP-API + LWA',                 category: 'integrations', status: 'todo', progress: 0,  effort: '3-4 sem', nextStep: 'AWS IAM + Selling Partner approval' },
  { id: 'g8', emoji: '🟡', title: 'Mercado Libre OAuth app',             category: 'integrations', status: 'wip',  progress: 55, effort: '1 sem',   nextStep: 'App review · public approval' },
  { id: 'g9', emoji: '🛍', title: 'Shopify Partner App público',         category: 'integrations', status: 'wip',  progress: 65, effort: '2 sem',   nextStep: 'Shopify App Store review' },
  { id: 'g10',emoji: '🧾', title: 'AFIP WSAA · cert per CUIT',            category: 'integrations', status: 'wip',  progress: 70, effort: '1 día/user', nextStep: 'Onboarding wizard cert' },
  { id: 'g11',emoji: '🚚', title: 'Couriers (Andreani · OCA · DHL)',     category: 'integrations', status: 'todo', progress: 15, effort: '1 sem c/u', nextStep: 'Andreani primero · API key' },

  // BROWSER EXTENSIONS
  { id: 'e1', emoji: '🌐', title: 'Chrome Web Store · publicada',        category: 'integrations', status: 'todo', progress: 25, effort: '2-4 sem', blocker: 'Web Store review · MV3 audit', nextStep: 'Build + privacy disclosures' },
  { id: 'e2', emoji: '🦊', title: 'Firefox AMO · publicada',             category: 'integrations', status: 'todo', progress: 15, effort: '1-2 sem', nextStep: 'AMO submit + review' },
  { id: 'e3', emoji: '🌊', title: 'Edge Add-ons · publicada',             category: 'integrations', status: 'todo', progress: 20, effort: '1 sem',   nextStep: 'Partner Center submit' },
  { id: 'e4', emoji: '🧭', title: 'Safari App Store · publicada',         category: 'integrations', status: 'todo', progress: 5,  effort: '3-4 sem', blocker: 'Apple Developer + macOS wrapper', nextStep: 'WKWebView + Swift bridge' },

  // COMPLIANCE
  { id: 'c1', emoji: '📋', title: 'Terms of Service + Privacy Policy',  category: 'compliance', status: 'wip',  progress: 60, effort: '3 días',  nextStep: 'Legal review · LATAM + EU' },
  { id: 'c2', emoji: '🇪🇺', title: 'GDPR + LGPD compliance',              category: 'compliance', status: 'wip',  progress: 45, effort: '2 sem',   nextStep: 'DPO + DPA per integration' },
  { id: 'c3', emoji: '🛡', title: 'KYC para nuevos users',                category: 'compliance', status: 'todo', progress: 10, effort: '1 sem',   nextStep: 'Persona + Onfido integrar' },
  { id: 'c4', emoji: '📜', title: 'SOC 2 Type 1',                          category: 'compliance', status: 'todo', progress: 0,  effort: '3-6 meses',nextStep: 'Vanta · audit prep' },
  { id: 'c5', emoji: '🏦', title: 'PCI DSS (vía Stripe SAQ-A)',           category: 'compliance', status: 'done', progress: 100, effort: 'done',    nextStep: 'Stripe Elements maneja todo' },

  // PRODUCT
  { id: 'p1', emoji: '🚪', title: 'Onboarding wizard funcional',         category: 'product',    status: 'wip',  progress: 55, effort: '1 sem',   nextStep: 'Conectar 1er canal end-to-end' },
  { id: 'p2', emoji: '🎯', title: '1 vertical pre-templated funcional',  category: 'product',    status: 'wip',  progress: 40, effort: '2 sem',   nextStep: 'Retail Shopify + WA · MVP' },
  { id: 'p3', emoji: '📞', title: 'Soporte tickets + status page',        category: 'product',    status: 'todo', progress: 20, effort: '4 días',  nextStep: 'Crisp.chat + StatusPage.io' },
  { id: 'p4', emoji: '📚', title: 'Docs públicas + help center',          category: 'product',    status: 'todo', progress: 15, effort: '1 sem',   nextStep: 'Mintlify docs deploy' },
  { id: 'p5', emoji: '🎓', title: 'Onboarding email drip (14d)',          category: 'product',    status: 'todo', progress: 10, effort: '3 días',  nextStep: 'Loops.so + email templates' },

  // BILLING
  { id: 'b1', emoji: '💳', title: 'Stripe Subscriptions',                category: 'billing',    status: 'wip',  progress: 65, effort: '2 días',  nextStep: 'Test mode · prod keys' },
  { id: 'b2', emoji: '💰', title: 'Pricing pages + checkout',            category: 'billing',    status: 'wip',  progress: 50, effort: '3 días',  nextStep: 'Tiers Starter/Pro/Scale' },
  { id: 'b3', emoji: '🔁', title: 'Dunning · failed payment recovery',   category: 'billing',    status: 'todo', progress: 5,  effort: '1 sem',   nextStep: 'Stripe Smart Retries + emails' },
  { id: 'b4', emoji: '📊', title: 'Usage metering (tokens/MMU)',         category: 'billing',    status: 'todo', progress: 25, effort: '1 sem',   nextStep: 'Stripe Meters · usage events' },
  { id: 'b5', emoji: '🎁', title: 'Free trial 14 días + paywalls',        category: 'billing',    status: 'todo', progress: 30, effort: '3 días',  nextStep: 'Trial logic + cancel anytime' },

  // DEVOPS
  { id: 'd1', emoji: '🚀', title: 'CI/CD pipeline (GitHub Actions)',     category: 'devops',     status: 'done', progress: 100, effort: 'done',    nextStep: 'Deploy preview activo' },
  { id: 'd2', emoji: '📈', title: 'Observability (Sentry + PostHog)',    category: 'devops',     status: 'wip',  progress: 60, effort: '2 días',  nextStep: 'Sessions replay + error tracking' },
  { id: 'd3', emoji: '🔔', title: 'Alerting (Datadog · Better Stack)',   category: 'devops',     status: 'todo', progress: 20, effort: '3 días',  nextStep: 'PagerDuty integration' },
  { id: 'd4', emoji: '🔐', title: 'Secrets management (Vault · Doppler)', category: 'devops',    status: 'wip',  progress: 50, effort: '1 día',   nextStep: 'Doppler integrar al deploy' },
  { id: 'd5', emoji: '💾', title: 'Backups automáticos + DR plan',        category: 'devops',     status: 'todo', progress: 15, effort: '1 sem',   nextStep: 'Daily Postgres snapshots + R2' },
]

const CATEGORY_CONFIG: Record<Category, { label: string; icon: React.ElementType; color: string }> = {
  infra:        { label: 'Infraestructura', icon: Server,     color: '#a855f7' },
  integrations: { label: 'Integraciones',   icon: Plug,       color: '#3b82f6' },
  compliance:   { label: 'Compliance',      icon: ShieldCheck, color: '#dc2626' },
  product:      { label: 'Producto',        icon: Rocket,     color: '#10b981' },
  billing:      { label: 'Billing',         icon: CreditCard, color: '#84cc16' },
  devops:       { label: 'DevOps',          icon: Hash,       color: '#fbbf24' },
}

const STATUS_CONFIG: Record<ItemStatus, { label: string; color: string; icon: React.ElementType }> = {
  done:    { label: 'DONE',     color: '#22c55e', icon: CheckCircle2 },
  wip:     { label: 'WIP',      color: '#3b82f6', icon: Clock },
  todo:    { label: 'TODO',     color: '#fbbf24', icon: Circle },
  blocked: { label: 'BLOCKED',  color: '#ef4444', icon: Lock },
}

export default function LaunchReadiness() {
  const [filter, setFilter] = useState<Category | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<ItemStatus | 'all'>('all')

  const filtered = useMemo(() => {
    let list = filter === 'all' ? ITEMS : ITEMS.filter(i => i.category === filter)
    if (statusFilter !== 'all') list = list.filter(i => i.status === statusFilter)
    return list
  }, [filter, statusFilter])

  const stats = useMemo(() => {
    const overall = Math.round(ITEMS.reduce((s, i) => s + i.progress, 0) / ITEMS.length)
    const done = ITEMS.filter(i => i.status === 'done').length
    const wip = ITEMS.filter(i => i.status === 'wip').length
    const blocked = ITEMS.filter(i => i.status === 'blocked').length
    return { overall, done, wip, blocked, total: ITEMS.length }
  }, [])

  const categoryProgress = useMemo(() => {
    const map: Record<Category, { done: number; total: number; avg: number }> = {} as any
    for (const cat of Object.keys(CATEGORY_CONFIG) as Category[]) {
      const items = ITEMS.filter(i => i.category === cat)
      const sum = items.reduce((s, i) => s + i.progress, 0)
      map[cat] = { done: items.filter(i => i.status === 'done').length, total: items.length, avg: Math.round(sum / Math.max(items.length, 1)) }
    }
    return map
  }, [])

  return (
    <section className="relative rounded-2xl border border-amber-500/30 bg-gradient-to-br from-[#1a1408]/85 via-[#0a0e1a]/92 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-amber-400/80 via-emerald-400/60 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/25 to-emerald-500/15 border border-amber-500/40 flex items-center justify-center">
            <Rocket className="w-5 h-5 text-amber-400" style={{ filter: 'drop-shadow(0 0 8px rgba(251,191,36,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-amber-400 via-emerald-400 to-amber-400 bg-clip-text text-transparent">LAUNCH READINESS</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  Qué falta para vender comercialmente</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono uppercase tracking-widest" style={{
                background: stats.overall > 70 ? 'rgba(16,185,129,0.15)' : 'rgba(251,191,36,0.15)',
                border: `1px solid ${stats.overall > 70 ? 'rgba(16,185,129,0.3)' : 'rgba(251,191,36,0.3)'}`,
                color: stats.overall > 70 ? '#22c55e' : '#fbbf24',
              }}>
                {stats.overall}% READY
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">{stats.done}/{stats.total} done · {stats.wip} WIP · {stats.blocked} blocked · ~3-5 meses ETA GA</p>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-2 text-center">
          <Stat label="Done" value={stats.done} color="#22c55e" />
          <Stat label="WIP" value={stats.wip} color="#3b82f6" />
          <Stat label="TODO" value={ITEMS.filter(i => i.status === 'todo').length} color="#fbbf24" />
          <Stat label="Blocked" value={stats.blocked} color="#ef4444" />
        </div>
      </div>

      {/* Big progress bar */}
      <div className="px-5 py-3 border-b border-white/[0.06]">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] uppercase tracking-widest text-white/40 font-bold">PROGRESO GLOBAL</span>
          <span className="text-sm font-black tabular-nums" style={{ color: stats.overall > 70 ? '#22c55e' : '#fbbf24' }}>{stats.overall}%</span>
        </div>
        <div className="h-2.5 bg-white/5 rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all" style={{
            width: `${stats.overall}%`,
            background: `linear-gradient(90deg, ${stats.overall > 70 ? '#22c55e' : '#fbbf24'}, ${stats.overall > 70 ? '#10b981' : '#f59e0b'})`,
            boxShadow: `0 0 8px ${stats.overall > 70 ? 'rgba(16,185,129,0.6)' : 'rgba(251,191,36,0.6)'}`,
          }} />
        </div>
      </div>

      {/* Category progress matrix */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 border-b border-white/[0.06]">
        {(Object.keys(CATEGORY_CONFIG) as Category[]).map(c => {
          const cfg = CATEGORY_CONFIG[c]
          const p = categoryProgress[c]
          const Icon = cfg.icon
          return (
            <button
              key={c}
              onClick={() => setFilter(filter === c ? 'all' : c)}
              className={`p-3 text-left border-r border-white/[0.04] last:border-r-0 transition-all ${filter === c ? '' : 'hover:bg-white/[0.02]'}`}
              style={{ background: filter === c ? `${cfg.color}10` : 'transparent' }}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className="w-3 h-3" style={{ color: cfg.color }} />
                <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold truncate">{cfg.label}</p>
              </div>
              <div className="flex items-baseline gap-1 mb-1">
                <p className="text-lg font-black tabular-nums" style={{ color: cfg.color }}>{p.avg}%</p>
                <p className="text-[9px] text-white/30">· {p.done}/{p.total}</p>
              </div>
              <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${p.avg}%`, background: cfg.color }} />
              </div>
            </button>
          )
        })}
      </div>

      {/* Status filters */}
      <div className="px-5 py-2 border-b border-white/[0.06] flex items-center gap-2 flex-wrap">
        <Filter className="w-3 h-3 text-white/30 shrink-0" />
        <button
          onClick={() => setStatusFilter('all')}
          className={`shrink-0 px-2.5 py-0.5 rounded-full text-[9px] font-bold border ${
            statusFilter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
          }`}
        >
          Todos · {ITEMS.length}
        </button>
        {(Object.keys(STATUS_CONFIG) as ItemStatus[]).map(s => {
          const cfg = STATUS_CONFIG[s]
          const active = statusFilter === s
          const count = ITEMS.filter(i => i.status === s).length
          return (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className="shrink-0 px-2.5 py-0.5 rounded-full text-[9px] font-bold border"
              style={
                active
                  ? { background: `${cfg.color}20`, borderColor: `${cfg.color}50`, color: cfg.color }
                  : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }
              }
            >
              {cfg.label} · {count}
            </button>
          )
        })}
      </div>

      {/* Items list */}
      <div className="p-4 space-y-1.5 max-h-[480px] overflow-y-auto">
        {filtered.map(item => {
          const cat = CATEGORY_CONFIG[item.category]
          const status = STATUS_CONFIG[item.status]
          const StatusIcon = status.icon
          return (
            <div key={item.id} className="rounded-lg border bg-white/[0.02] p-3"
              style={{ borderColor: item.status === 'blocked' ? 'rgba(239,68,68,0.25)' : 'rgba(255,255,255,0.06)' }}>
              <div className="flex items-start gap-2.5">
                <span className="text-xl shrink-0">{item.emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <p className="text-xs font-bold text-white">{item.title}</p>
                    <span className="text-[8px] px-1 py-0.5 rounded font-mono uppercase font-bold" style={{ background: `${status.color}18`, color: status.color }}>
                      <StatusIcon className="w-2 h-2 inline mr-0.5" />
                      {status.label}
                    </span>
                    <span className="text-[8px] px-1 py-0.5 rounded font-mono uppercase" style={{ background: `${cat.color}15`, color: cat.color }}>
                      {cat.label}
                    </span>
                    <span className="text-[9px] text-white/40 ml-auto">⏱ {item.effort}</span>
                  </div>

                  {/* Progress bar */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${item.progress}%`, background: status.color }} />
                    </div>
                    <span className="text-[9px] tabular-nums font-bold w-8 text-right" style={{ color: status.color }}>{item.progress}%</span>
                  </div>

                  {item.blocker && (
                    <div className="flex items-start gap-1 mb-1 p-1.5 rounded bg-red-500/[0.06] border border-red-500/15">
                      <Lock className="w-2.5 h-2.5 text-red-400 shrink-0 mt-0.5" />
                      <p className="text-[10px] text-red-300">{item.blocker}</p>
                    </div>
                  )}
                  {item.nextStep && (
                    <p className="text-[10px] text-emerald-400/80">→ {item.nextStep}</p>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="border-t border-white/[0.06] bg-amber-500/[0.04] px-5 py-3 text-center">
        <p className="text-[11px] text-white/70 leading-snug">
          <AlertCircle className="w-3 h-3 inline text-amber-400 mr-1" />
          MVP single-tenant en <span className="text-amber-300 font-bold">~4 semanas</span> · Multi-tenant + billing en <span className="text-amber-300 font-bold">~8 semanas</span> · GA público <span className="text-amber-300 font-bold">3-5 meses</span>.
        </p>
      </div>
    </section>
  )
}

const Stat = ({ label, value, color }: { label: string; value: number; color: string }) => (
  <div className="text-center">
    <p className="text-lg font-black tabular-nums" style={{ color }}>{value}</p>
    <p className="text-[8px] uppercase tracking-widest text-white/40 font-mono">{label}</p>
  </div>
)
