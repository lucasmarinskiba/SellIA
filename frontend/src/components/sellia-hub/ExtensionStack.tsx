'use client'

/**
 * EXTENSION STACK
 *
 * Anatomía de cada browser extension: muestra que NO es un wrapper tonto.
 * Cada extension corre adentro su propio stack:
 *   - Computer Use bot (Playwright headless o real-tab)
 *   - Agent loop sense/think/act
 *   - Skills dinámicos cargados según contexto
 *   - Plugins conectores (Stripe, MP, AFIP, OAuth providers)
 *   - WebSocket bi-direccional al cerebro central
 *   - Interconexión con mobile/smartwatch/desktop
 */

import { useState, useEffect, useMemo } from 'react'
import {
  Layers, Bot, Cpu, Wifi, Sparkles, Plug, Activity, Eye,
  MousePointer2, FileCode, Hammer, Database, Smartphone, Monitor,
  Watch, Globe, Zap, ChevronRight, ArrowRight
} from 'lucide-react'

type StackLayer = 'ui' | 'content' | 'worker' | 'cua' | 'agent' | 'skills' | 'plugins' | 'transport' | 'sync'

interface Layer {
  id: StackLayer
  name: string
  emoji: string
  color: string
  description: string
  eventsPerSec: number
  techStack: string[]
  icon: React.ElementType
}

interface AgentInside {
  emoji: string
  name: string
  role: string
  status: 'running' | 'idle' | 'thinking'
  invocationsToday: number
  color: string
}

interface SkillLoaded {
  emoji: string
  name: string
  reason: string
  loadedAt: string
}

interface PluginConn {
  emoji: string
  name: string
  protocol: string
  status: 'ok' | 'syncing' | 'error'
  lastSync: string
  color: string
}

const LAYERS: Layer[] = [
  { id: 'ui',        name: 'UI Overlay',         emoji: '✨', color: '#ec4899', description: 'Panel flotante, badges, score widget en cada listing',                   eventsPerSec: 12, techStack: ['React 19', 'Tailwind', 'shadow DOM'],                  icon: Sparkles },
  { id: 'content',   name: 'Content Scripts',    emoji: '📜', color: '#fbbf24', description: 'DOM read/write · selectors específicos por tienda',                       eventsPerSec: 47, techStack: ['MutationObserver', 'CSS selectors', 'XPath'],          icon: FileCode },
  { id: 'worker',    name: 'Service Worker',     emoji: '⚙️', color: '#a855f7', description: 'Background persistente · maneja eventos cross-tab',                       eventsPerSec: 89, techStack: ['Manifest V3 SW', 'IndexedDB cache', 'Alarms API'],     icon: Cpu },
  { id: 'cua',       name: 'Computer Use Bot',    emoji: '🤖', color: '#f59e0b', description: 'CUA controla tabs · click/type/scroll/screenshot programático',          eventsPerSec: 23, techStack: ['Playwright-extra', 'CDP protocol', 'Anthropic CUA'],   icon: MousePointer2 },
  { id: 'agent',     name: 'Agent Loop',          emoji: '🧠', color: '#06b6d4', description: 'Sense → Think → Act recursivo · invoca skills dinámicos',                eventsPerSec: 18, techStack: ['ReAct framework', 'LangGraph', 'tool calling'],         icon: Bot },
  { id: 'skills',    name: 'Skills Engine',       emoji: '🛠', color: '#10b981', description: 'Carga skills según contexto · 142 disponibles · 38 cargados ahora',     eventsPerSec: 7,  techStack: ['Hot reload skills', 'Skill versioning', 'A/B variants'], icon: Hammer },
  { id: 'plugins',   name: 'Plugins / Connectors',emoji: '🔌', color: '#84cc16', description: 'Connectors a Stripe, MP, AFIP, Andreani, OCA y +200 servicios',         eventsPerSec: 14, techStack: ['OAuth 2.0', 'OpenAPI specs', 'webhook listeners'],     icon: Plug },
  { id: 'transport', name: 'WebSocket Transport', emoji: '📡', color: '#3b82f6', description: 'WS bi-direccional al brain · latencia <80ms · auto-reconnect',           eventsPerSec: 156, techStack: ['WebSocket', 'msgpack binary', 'compression'],          icon: Wifi },
  { id: 'sync',      name: 'Multi-device Sync',   emoji: '🔄', color: '#22c55e', description: 'Sync con mobile app + smartwatch + otros browsers del mismo user',      eventsPerSec: 31, techStack: ['CRDT', 'Yjs', 'IndexedDB', 'FCM/APNs'],                 icon: Layers },
]

const AGENTS_INSIDE: AgentInside[] = [
  { emoji: '👁', name: 'Page-Watcher',      role: 'Detecta cambios DOM en listing/checkout',         status: 'running',  invocationsToday: 847, color: '#06b6d4' },
  { emoji: '🎯', name: 'Lead-Sniffer',      role: 'Extrae profile data de IG/LinkedIn al hover',      status: 'running',  invocationsToday: 142, color: '#10b981' },
  { emoji: '✍️', name: 'Listing-Writer',     role: 'Sugiere título/desc/keywords al abrir form',      status: 'thinking', invocationsToday: 34,  color: '#f59e0b' },
  { emoji: '⭐', name: 'Review-Replier',    role: 'Responde reviews 1-star/5-star con tono adecuado', status: 'running',  invocationsToday: 56,  color: '#fbbf24' },
  { emoji: '💰', name: 'Price-Watcher',     role: 'Compara precio contra 8 competidores cada hora',   status: 'running',  invocationsToday: 192, color: '#ef4444' },
  { emoji: '🔔', name: 'Notifier-Dispatcher',role: 'Envía push a desktop + mobile + watch',           status: 'idle',     invocationsToday: 78,  color: '#a855f7' },
  { emoji: '🧾', name: 'AFIP-Bot',          role: 'Emite factura automática post-cobro',              status: 'idle',     invocationsToday: 14,  color: '#3b82f6' },
  { emoji: '🚚', name: 'Courier-Coordinator',role: 'Genera etiqueta envío + tracking',                status: 'running',  invocationsToday: 11,  color: '#84cc16' },
]

const SKILLS_LOADED: SkillLoaded[] = [
  { emoji: '🛒', name: 'Listing optimization · A9 SEO',     reason: 'Estás en Amazon Seller Central',           loadedAt: 'hace 2min' },
  { emoji: '👁', name: 'Competitor scraping live',          reason: 'Detecté tab abierta de competidor',         loadedAt: 'hace 4min' },
  { emoji: '✍️', name: 'Auto-fill listing',                  reason: 'Form "Crear producto" detectado',           loadedAt: 'hace 1min' },
  { emoji: '🏷', name: 'Pricing competitivo dinámico',       reason: 'Precio competencia bajó 8%',                loadedAt: 'hace 30s' },
  { emoji: '🎨', name: 'Product photography enhancement',    reason: 'Uploadeaste 3 fotos · 1 con bg malo',       loadedAt: 'hace 7min' },
  { emoji: '🧾', name: 'Facturación AFIP',                   reason: 'Pendiente: 2 ventas sin factura',            loadedAt: 'hace 12min' },
  { emoji: '🚚', name: 'Coordinación couriers',              reason: 'Tras factura: coordinar envío',              loadedAt: 'hace 12min' },
  { emoji: '⭐', name: 'Review management',                  reason: '1 review nueva 4-star detectada',            loadedAt: 'hace 18min' },
]

const PLUGINS_CONNECTED: PluginConn[] = [
  { emoji: '🟣', name: 'Stripe',          protocol: 'REST + Webhooks',     status: 'ok',      lastSync: 'hace 12s',  color: '#635bff' },
  { emoji: '🟡', name: 'Mercado Pago',     protocol: 'REST + OAuth 2.0',    status: 'ok',      lastSync: 'hace 8s',   color: '#fbbf24' },
  { emoji: '🅿️', name: 'PayPal',          protocol: 'REST + IPN',          status: 'ok',      lastSync: 'hace 34s',  color: '#0070ba' },
  { emoji: '🧾', name: 'AFIP (Argentina)', protocol: 'SOAP · WSAA',         status: 'syncing', lastSync: 'hace 1min', color: '#1e3a8a' },
  { emoji: '🇦🇷', name: 'Andreani',         protocol: 'REST · tracking',     status: 'ok',      lastSync: 'hace 22s',  color: '#dc2626' },
  { emoji: '📦', name: 'OCA',              protocol: 'REST · cotizar',      status: 'ok',      lastSync: 'hace 47s',  color: '#fbbf24' },
  { emoji: '✈️', name: 'DHL',              protocol: 'REST · multi-país',   status: 'ok',      lastSync: 'hace 2min', color: '#facc15' },
  { emoji: '📅', name: 'Google Calendar',  protocol: 'OAuth 2.0',           status: 'ok',      lastSync: 'hace 16s',  color: '#4285f4' },
  { emoji: '📊', name: 'Google Sheets',    protocol: 'OAuth 2.0',           status: 'ok',      lastSync: 'hace 31s',  color: '#0f9d58' },
  { emoji: '💬', name: 'WhatsApp Business',protocol: 'Cloud API',           status: 'ok',      lastSync: 'hace 4s',   color: '#25d366' },
  { emoji: '🤖', name: 'Anthropic API',    protocol: 'CUA + Messages',      status: 'ok',      lastSync: 'hace 1s',   color: '#ec4899' },
  { emoji: '🟢', name: 'OpenRouter',       protocol: 'OpenAI-compat',       status: 'ok',      lastSync: 'hace 3s',   color: '#10b981' },
]

const STATUS_CONFIG = {
  ok:      { color: '#22c55e', label: '✓ OK' },
  syncing: { color: '#3b82f6', label: '◌ SYNC' },
  error:   { color: '#ef4444', label: '⚠ ERROR' },
} as const

export default function ExtensionStack() {
  const [pulse, setPulse] = useState(0)
  const [selectedLayer, setSelectedLayer] = useState<StackLayer>('cua')

  useEffect(() => {
    const id = setInterval(() => setPulse(p => (p + 1) % 100), 100)
    return () => clearInterval(id)
  }, [])

  const totalEPS = useMemo(() => LAYERS.reduce((s, l) => s + l.eventsPerSec, 0), [])
  const selected = LAYERS.find(l => l.id === selectedLayer)!
  const runningAgents = AGENTS_INSIDE.filter(a => a.status === 'running').length
  const okPlugins = PLUGINS_CONNECTED.filter(p => p.status === 'ok').length

  return (
    <section className="relative rounded-2xl border border-purple-500/20 bg-gradient-to-br from-[#0c0a1a]/90 via-[#0a0e1a]/88 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-400/80 via-cyan-400/60 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/25 to-cyan-500/15 border border-purple-500/40 flex items-center justify-center">
            <Layers className="w-5 h-5 text-purple-400" style={{ filter: 'drop-shadow(0 0 8px rgba(168,85,247,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent">EXTENSION STACK</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  Anatomía de cada brazo</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                {totalEPS} ev/s
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Cada extensión = stack completo: UI · Content · Worker · CUA · Agents · Skills · Plugins · WS · Sync</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-white/50 flex-wrap">
          <span><span className="text-emerald-400 font-bold">{runningAgents}</span> agentes corriendo</span>
          <span>·</span>
          <span><span className="text-purple-300 font-bold">{SKILLS_LOADED.length}</span> skills cargados</span>
          <span>·</span>
          <span><span className="text-cyan-300 font-bold">{okPlugins}</span> plugins ok</span>
        </div>
      </div>

      {/* Stack visualization · 9 layers tower */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-5">
        {/* Stack tower */}
        <div className="lg:col-span-2 space-y-1.5">
          <p className="text-[10px] uppercase tracking-widest text-white/40 font-bold mb-2 flex items-center gap-1">
            <Cpu className="w-2.5 h-2.5" />
            STACK INTERNO · 9 CAPAS (top-down)
          </p>
          {LAYERS.map((l, i) => {
            const Icon = l.icon
            const isSelected = selectedLayer === l.id
            const intensity = 0.4 + (l.eventsPerSec / 200) * 0.6
            return (
              <button
                key={l.id}
                onClick={() => setSelectedLayer(l.id)}
                className="relative w-full text-left rounded-xl border transition-all p-3 group"
                style={{
                  background: `linear-gradient(90deg, ${l.color}${Math.round(intensity * 18).toString(16).padStart(2, '0')}, rgba(255,255,255,0.02))`,
                  borderColor: isSelected ? `${l.color}60` : 'rgba(255,255,255,0.06)',
                  boxShadow: isSelected ? `0 0 16px ${l.color}25` : 'none',
                }}
              >
                {/* Live pulse stripe */}
                <div className="absolute left-0 top-0 bottom-0 w-1 rounded-l-xl" style={{
                  background: l.color,
                  opacity: 0.3 + Math.sin((pulse + i * 11) * 0.1) * 0.3,
                  boxShadow: `0 0 8px ${l.color}80`,
                }} />

                <div className="flex items-center gap-3 ml-1">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0" style={{
                    background: `${l.color}15`,
                    border: `1px solid ${l.color}30`,
                  }}>
                    <Icon className="w-4 h-4" style={{ color: l.color }} />
                  </div>
                  <span className="text-2xl shrink-0">{l.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-xs font-bold text-white">{l.name}</p>
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold" style={{ background: `${l.color}20`, color: l.color }}>
                        L{i + 1}
                      </span>
                    </div>
                    <p className="text-[10px] text-white/55 leading-snug truncate">{l.description}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-base font-black tabular-nums" style={{ color: l.color }}>{l.eventsPerSec}</p>
                    <p className="text-[8px] uppercase tracking-widest text-white/40 font-mono">ev/s</p>
                  </div>
                  <ChevronRight className={`w-3 h-3 text-white/30 transition-transform shrink-0 ${isSelected ? 'rotate-90' : ''}`} />
                </div>

                {isSelected && (
                  <div className="mt-3 ml-1 pl-12">
                    <p className="text-[9px] uppercase tracking-widest font-bold mb-1.5" style={{ color: l.color }}>
                      TECH STACK
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {l.techStack.map(t => (
                        <span key={t} className="text-[10px] px-2 py-0.5 rounded-md font-mono" style={{
                          background: `${l.color}10`,
                          border: `1px solid ${l.color}25`,
                          color: `${l.color}cc`,
                        }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </button>
            )
          })}
        </div>

        {/* Right column: agents + skills + plugins */}
        <div className="space-y-3">
          {/* Agents inside */}
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.04] p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5 text-emerald-400" />
                <h3 className="text-[10px] uppercase tracking-widest font-bold text-emerald-400">AGENTES ADENTRO</h3>
              </div>
              <span className="text-[10px] text-white/40">{runningAgents}/{AGENTS_INSIDE.length}</span>
            </div>
            <div className="space-y-1.5 max-h-[220px] overflow-y-auto pr-1">
              {AGENTS_INSIDE.map((a, i) => (
                <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.03] border border-white/[0.05]">
                  <span className="text-lg shrink-0">{a.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-bold text-white truncate">{a.name}</p>
                    <p className="text-[9px] text-white/40 truncate">{a.role}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[10px] font-bold tabular-nums" style={{ color: a.color }}>{a.invocationsToday}</p>
                    {a.status === 'running' && <div className="w-1 h-1 rounded-full mx-auto animate-pulse" style={{ background: a.color }} />}
                    {a.status === 'thinking' && <div className="w-1 h-1 rounded-full mx-auto animate-bounce" style={{ background: a.color }} />}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Skills loaded */}
          <div className="rounded-xl border border-purple-500/20 bg-purple-500/[0.04] p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                <h3 className="text-[10px] uppercase tracking-widest font-bold text-purple-400">SKILLS CARGADOS AHORA</h3>
              </div>
              <span className="text-[10px] text-white/40">{SKILLS_LOADED.length}</span>
            </div>
            <div className="space-y-1.5 max-h-[200px] overflow-y-auto pr-1">
              {SKILLS_LOADED.map((s, i) => (
                <div key={i} className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.05]">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-base shrink-0">{s.emoji}</span>
                    <p className="text-[11px] font-bold text-white/90 truncate flex-1">{s.name}</p>
                    <span className="text-[9px] text-white/30 font-mono shrink-0">{s.loadedAt}</span>
                  </div>
                  <p className="text-[9px] text-white/50 italic ml-6">trigger: {s.reason}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Plugins/connectors strip */}
      <div className="p-5 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 mb-3">
          <Plug className="w-4 h-4 text-lime-400" />
          <h3 className="text-[11px] uppercase tracking-widest font-bold text-lime-400">PLUGINS / CONNECTORS ACTIVOS</h3>
          <span className="text-[10px] text-white/40 ml-auto">{okPlugins}/{PLUGINS_CONNECTED.length} ok</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {PLUGINS_CONNECTED.map(p => {
            const status = STATUS_CONFIG[p.status]
            return (
              <div key={p.name} className="rounded-lg p-2.5 bg-white/[0.02] border border-white/[0.05]">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="text-lg shrink-0">{p.emoji}</span>
                    <p className="text-[11px] font-bold text-white truncate">{p.name}</p>
                  </div>
                  <span className="text-[8px] px-1 py-0.5 rounded font-mono shrink-0" style={{ background: `${status.color}20`, color: status.color }}>
                    {status.label}
                  </span>
                </div>
                <p className="text-[9px] text-white/40 font-mono">{p.protocol}</p>
                <p className="text-[9px] text-white/30 mt-0.5">sync: {p.lastSync}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Interconnection diagram */}
      <div className="p-5 border-t border-white/[0.06] bg-black/30">
        <div className="flex items-center gap-2 mb-3">
          <Wifi className="w-4 h-4 text-cyan-400" />
          <h3 className="text-[11px] uppercase tracking-widest font-bold text-cyan-400">INTERCONEXIÓN MULTI-DEVICE</h3>
        </div>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <DeviceNode icon={Globe} label="Extension" color="#a855f7" />
          <ArrowFlow />
          <DeviceNode icon={Activity} label="Brain (cloud)" color="#ec4899" pulse />
          <ArrowFlow direction="both" />
          <DeviceNode icon={Monitor} label="Desktop App" color="#3b82f6" />
          <ArrowFlow />
          <DeviceNode icon={Smartphone} label="Mobile push" color="#10b981" />
          <ArrowFlow />
          <DeviceNode icon={Watch} label="Smartwatch" color="#fbbf24" />
        </div>
        <p className="text-center text-[10px] text-white/50 mt-3 italic">
          Estado sincronizado en <span className="text-cyan-300 font-bold">4 devices</span> · WebSocket bi-direccional · CRDT conflict-free
        </p>
      </div>
    </section>
  )
}

// ─── Helper components ───
const DeviceNode = ({ icon: Icon, label, color, pulse }: { icon: React.ElementType; label: string; color: string; pulse?: boolean }) => (
  <div className="flex flex-col items-center gap-1 shrink-0">
    <div className="relative w-12 h-12 rounded-xl flex items-center justify-center" style={{
      background: `${color}15`,
      border: `1.5px solid ${color}40`,
      boxShadow: `0 0 12px ${color}25`,
    }}>
      <Icon className="w-5 h-5" style={{ color }} />
      {pulse && <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full animate-ping" style={{ background: color }} />}
      {pulse && <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full" style={{ background: color }} />}
    </div>
    <span className="text-[9px] font-mono font-bold" style={{ color }}>{label}</span>
  </div>
)

const ArrowFlow = ({ direction = 'right' }: { direction?: 'right' | 'both' }) => (
  <div className="flex items-center gap-0.5 text-white/30 shrink-0">
    {direction === 'both' && <ArrowRight className="w-3 h-3 rotate-180" />}
    <div className="flex gap-0.5">
      <div className="w-1 h-1 rounded-full bg-cyan-400 animate-pulse" />
      <div className="w-1 h-1 rounded-full bg-cyan-400/60 animate-pulse" style={{ animationDelay: '0.2s' }} />
      <div className="w-1 h-1 rounded-full bg-cyan-400/30 animate-pulse" style={{ animationDelay: '0.4s' }} />
    </div>
    <ArrowRight className="w-3 h-3" />
  </div>
)
