'use client'

/**
 * BROWSER EXTENSIONS
 *
 * Extensiones para 6+ navegadores. Brazos del cerebro:
 *   - Conecta a tiendas virtuales del usuario directamente desde la sesión del navegador
 *   - Captura datos de competencia, reviews, inventario sin APIs
 *   - Auto-fill listings, responder reviews, monitorear precio
 *
 * Cada extensión = arm del sistema = alcance + conocimiento + ventas.
 */

import { useState, useMemo } from 'react'
import {
  Globe, Compass, Flame, Wifi, Sparkles, Bot, CheckCircle2,
  ArrowDownToLine, Activity, ShoppingBag, Eye, Hand, Zap, Lock,
  ChevronRight, Filter, Puzzle
} from 'lucide-react'

type BrowserId = 'chrome' | 'edge' | 'opera' | 'brave' | 'firefox' | 'safari' | 'arc' | 'vivaldi'

interface BrowserExt {
  id: BrowserId
  name: string
  emoji: string
  color: string
  marketName: string
  version: string
  size: string
  installed: boolean
  rating: number
  reviews: number
  storesConnected: string[]
  permissions: string[]
}

const BROWSERS: BrowserExt[] = [
  { id: 'chrome',  name: 'Chrome',          emoji: '🌐', color: '#4285F4', marketName: 'Chrome Web Store',  version: '2.4.1', size: '1.8 MB', installed: true,  rating: 4.9, reviews: 2847, storesConnected: ['Amazon Seller', 'Mercado Libre', 'Shopify', 'Etsy', 'eBay', 'Hotmart'], permissions: ['Active tab', 'Storage', 'Cookies', 'WebRequest'] },
  { id: 'edge',    name: 'Microsoft Edge',   emoji: '🌊', color: '#0078D4', marketName: 'Edge Add-ons',      version: '2.4.1', size: '1.8 MB', installed: true,  rating: 4.8, reviews: 1245, storesConnected: ['Amazon Seller', 'Shopify', 'WooCommerce'], permissions: ['Active tab', 'Storage', 'Cookies'] },
  { id: 'opera',   name: 'Opera',           emoji: '🎭', color: '#FF1B2D', marketName: 'Opera Add-ons',     version: '2.3.8', size: '1.9 MB', installed: false, rating: 4.7, reviews: 412,  storesConnected: ['Mercado Libre', 'TiendaNube'], permissions: ['Active tab', 'Storage'] },
  { id: 'brave',   name: 'Brave',           emoji: '🦁', color: '#FB542B', marketName: 'Chrome Web Store',  version: '2.4.1', size: '1.8 MB', installed: true,  rating: 4.9, reviews: 867,  storesConnected: ['Shopify', 'Etsy', 'WooCommerce'], permissions: ['Active tab', 'Storage', 'Cookies'] },
  { id: 'firefox', name: 'Firefox',         emoji: '🦊', color: '#FF7139', marketName: 'Mozilla Add-ons',   version: '2.3.5', size: '2.1 MB', installed: true,  rating: 4.6, reviews: 1647, storesConnected: ['Mercado Libre', 'Hotmart', 'Etsy'], permissions: ['Active tab', 'Storage'] },
  { id: 'safari',  name: 'Safari',          emoji: '🧭', color: '#0FB5EE', marketName: 'App Store · macOS', version: '1.9.3', size: '2.4 MB', installed: false, rating: 4.5, reviews: 234,  storesConnected: [], permissions: ['Active tab (limit)'] },
  { id: 'arc',     name: 'Arc Browser',     emoji: '🌈', color: '#FA4515', marketName: 'Chrome Web Store',  version: '2.4.1', size: '1.8 MB', installed: false, rating: 5.0, reviews: 89,   storesConnected: [], permissions: ['Active tab', 'Storage'] },
  { id: 'vivaldi', name: 'Vivaldi',         emoji: '🎻', color: '#EF3939', marketName: 'Chrome Web Store',  version: '2.4.1', size: '1.8 MB', installed: false, rating: 4.7, reviews: 56,   storesConnected: [], permissions: ['Active tab', 'Storage'] },
]

interface ExtPower {
  id: string
  emoji: string
  name: string
  detail: string
  category: 'capture' | 'automate' | 'monitor' | 'sync' | 'optimize'
  enabled: boolean
}

const POWERS: ExtPower[] = [
  // CAPTURE
  { id: 'p1',  emoji: '📸', name: 'Capturar productos competidores',     detail: '1-click guarda listing rival con precio, fotos, copy y reviews', category: 'capture',  enabled: true },
  { id: 'p2',  emoji: '⭐', name: 'Mining de reviews competencia',        detail: 'Extrae quejas/elogios para mejorar mi catálogo', category: 'capture',  enabled: true },
  { id: 'p3',  emoji: '🎯', name: 'Capturar leads de redes sociales',    detail: 'En IG/LinkedIn click → captura prospect al CRM', category: 'capture',  enabled: true },
  { id: 'p4',  emoji: '💬', name: 'Capturar conversaciones WhatsApp Web', detail: 'Sincroniza chats al CRM en tiempo real', category: 'capture',  enabled: true },

  // AUTOMATE
  { id: 'p5',  emoji: '✍️', name: 'Auto-completar listings nuevos',       detail: 'Carga título/desc/keywords optimizados al abrir formulario', category: 'automate', enabled: true },
  { id: 'p6',  emoji: '🤖', name: 'Responder preguntas/reviews auto',    detail: 'Botón "responder con IA" en ML, Amazon, Etsy', category: 'automate', enabled: true },
  { id: 'p7',  emoji: '📨', name: 'Outreach masivo LinkedIn',            detail: 'Auto-send connection requests + DM personalizados', category: 'automate', enabled: false },
  { id: 'p8',  emoji: '🧾', name: 'Auto-facturación AFIP',                detail: 'Tras venta, abre AFIP y emite factura automáticamente', category: 'automate', enabled: true },

  // MONITOR
  { id: 'p9',  emoji: '👁', name: 'Monitor precio competencia 24/7',     detail: 'Tab oculto refresca cada hora y alerta si bajan precio', category: 'monitor',  enabled: true },
  { id: 'p10', emoji: '🔔', name: 'Alertas de stock crítico',             detail: 'Notif desktop cuando inventario < umbral seguridad', category: 'monitor',  enabled: true },
  { id: 'p11', emoji: '📊', name: 'Dashboard flotante por tienda',        detail: 'Overlay con KPIs reales al estar dentro de Amazon/ML', category: 'monitor',  enabled: true },
  { id: 'p12', emoji: '⚠️', name: 'Detección de chargebacks',             detail: 'Avisa cuando aparece dispute en Stripe/MP/PayPal', category: 'monitor',  enabled: true },

  // SYNC
  { id: 'p13', emoji: '🔄', name: 'Sync inventario multi-tienda',         detail: 'Vendo en Shopify y reduce stock en Amazon/ML/Etsy al instante', category: 'sync',     enabled: true },
  { id: 'p14', emoji: '🏷', name: 'Sync precios cross-platform',           detail: 'Cambio precio en Web propia → propaga a 8 marketplaces', category: 'sync',     enabled: true },
  { id: 'p15', emoji: '📦', name: 'Sync órdenes a sistema central',       detail: 'Todas las órdenes a un solo dashboard SellIA', category: 'sync',     enabled: true },

  // OPTIMIZE
  { id: 'p16', emoji: '🔍', name: 'A/B testing live en listings',         detail: 'Roto 2 versiones de título cada 24h, gana el de mejor CTR', category: 'optimize', enabled: false },
  { id: 'p17', emoji: '📈', name: 'Sugerencias SEO en vivo',              detail: 'Mientras escribís listing, IA sugiere keywords ranking', category: 'optimize', enabled: true },
  { id: 'p18', emoji: '💎', name: 'Score de calidad de listing',          detail: 'Indicador 0-100 mostrando qué falta para max ranking', category: 'optimize', enabled: true },
  { id: 'p19', emoji: '🎨', name: 'Mejora automática de fotos',           detail: 'Detecta fotos malas y sugiere background/light fix', category: 'optimize', enabled: true },
]

const CATEGORY_CONFIG = {
  capture:  { label: 'Captura',     color: '#06b6d4', icon: Eye },
  automate: { label: 'Automatiza',  color: '#a855f7', icon: Hand },
  monitor:  { label: 'Monitorea',   color: '#fbbf24', icon: Activity },
  sync:     { label: 'Sincroniza',  color: '#10b981', icon: Wifi },
  optimize: { label: 'Optimiza',    color: '#ec4899', icon: Sparkles },
} as const

export default function BrowserExtensions() {
  const [selectedBrowser, setSelectedBrowser] = useState<BrowserId>('chrome')
  const [powerFilter, setPowerFilter] = useState<keyof typeof CATEGORY_CONFIG | 'all'>('all')

  const selected = BROWSERS.find(b => b.id === selectedBrowser)!

  const stats = useMemo(() => {
    const installed = BROWSERS.filter(b => b.installed).length
    const totalStoresConnected = BROWSERS.reduce((s, b) => s + b.storesConnected.length, 0)
    const enabledPowers = POWERS.filter(p => p.enabled).length
    return { installed, total: BROWSERS.length, stores: totalStoresConnected, powers: enabledPowers, totalPowers: POWERS.length }
  }, [])

  const filteredPowers = useMemo(
    () => powerFilter === 'all' ? POWERS : POWERS.filter(p => p.category === powerFilter),
    [powerFilter]
  )

  const powerCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const p of POWERS) c[p.category] = (c[p.category] || 0) + 1
    return c
  }, [])

  return (
    <section className="relative rounded-2xl border border-blue-500/20 bg-gradient-to-br from-[#080f1a]/90 via-[#0a0e1a]/85 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-blue-400/80 via-orange-400/60 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/25 to-orange-500/15 border border-blue-500/40 flex items-center justify-center">
            <Puzzle className="w-5 h-5 text-blue-400" style={{ filter: 'drop-shadow(0 0 8px rgba(59,130,246,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-orange-400 bg-clip-text text-transparent">BROWSER EXTENSIONS</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  Brazos del cerebro</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                {stats.installed}/{stats.total} INSTALADAS
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">8 navegadores · {stats.stores} tiendas conectadas · {stats.powers} poderes activos</p>
          </div>
        </div>
        <button className="text-[11px] px-3 py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/40 text-blue-300 font-bold flex items-center gap-1.5 hover:bg-blue-500/30 transition-all">
          <ArrowDownToLine className="w-3 h-3" />
          Instalar en todos los navegadores
        </button>
      </div>

      {/* Browser cards grid */}
      <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-2">
        {BROWSERS.map(b => {
          const isSelected = selectedBrowser === b.id
          return (
            <button
              key={b.id}
              onClick={() => setSelectedBrowser(b.id)}
              className="relative text-left rounded-xl border bg-white/[0.02] hover:bg-white/[0.04] transition-all p-3 overflow-hidden group"
              style={{
                borderColor: isSelected ? `${b.color}60` : 'rgba(255,255,255,0.06)',
                boxShadow: isSelected ? `0 0 16px ${b.color}25` : 'none',
              }}
            >
              {/* Brand accent corner */}
              <div className="absolute top-0 right-0 w-12 h-12 rounded-full blur-xl opacity-30" style={{ background: b.color }} />

              <div className="relative flex items-start justify-between mb-2">
                <span className="text-3xl">{b.emoji}</span>
                {b.installed ? (
                  <span className="flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono uppercase">
                    <CheckCircle2 className="w-2 h-2" />Instalado
                  </span>
                ) : (
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-white/40 font-mono uppercase">
                    No instalado
                  </span>
                )}
              </div>

              <p className="text-sm font-bold text-white mb-0.5">{b.name}</p>
              <p className="text-[9px] text-white/40 truncate">{b.marketName}</p>

              <div className="flex items-center gap-2 mt-2 text-[9px] text-white/40 font-mono">
                <span>v{b.version}</span>
                <span>·</span>
                <span>{b.size}</span>
                <span>·</span>
                <span style={{ color: b.color }}>⭐ {b.rating}</span>
              </div>

              {b.storesConnected.length > 0 && (
                <p className="text-[9px] mt-1.5" style={{ color: b.color }}>
                  {b.storesConnected.length} tiendas conectadas
                </p>
              )}
            </button>
          )
        })}
      </div>

      {/* Selected browser detail */}
      <div className="mx-4 mb-4 rounded-xl border p-4"
        style={{
          background: `linear-gradient(135deg, ${selected.color}08, transparent)`,
          borderColor: `${selected.color}30`,
        }}>
        <div className="flex items-start gap-4 flex-wrap">
          <span className="text-5xl shrink-0">{selected.emoji}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h3 className="text-lg font-black text-white">{selected.name} · SellIA Companion</h3>
              <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase tracking-wider" style={{ background: `${selected.color}20`, color: selected.color }}>
                v{selected.version}
              </span>
            </div>
            <p className="text-[11px] text-white/50 mb-2">{selected.marketName} · {selected.reviews.toLocaleString()} reviews · {selected.size}</p>

            <div className="flex items-center gap-2 flex-wrap mb-2">
              {selected.storesConnected.length > 0 ? (
                selected.storesConnected.map(s => (
                  <span key={s} className="text-[10px] px-2 py-0.5 rounded-md bg-white/[0.04] border border-white/[0.08] text-white/85 flex items-center gap-1">
                    <ShoppingBag className="w-2.5 h-2.5" /> {s}
                  </span>
                ))
              ) : (
                <span className="text-[10px] text-white/40 italic">Sin tiendas conectadas todavía</span>
              )}
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[9px] text-white/40 uppercase font-mono tracking-widest">Permisos:</span>
              {selected.permissions.map(p => (
                <span key={p} className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] text-white/60 font-mono flex items-center gap-1">
                  <Lock className="w-2 h-2" /> {p}
                </span>
              ))}
            </div>
          </div>

          {!selected.installed && (
            <button className="px-4 py-2 rounded-lg font-bold text-[11px] flex items-center gap-1.5 transition-all"
              style={{ background: `${selected.color}25`, border: `1px solid ${selected.color}60`, color: selected.color }}>
              <ArrowDownToLine className="w-3 h-3" />
              Instalar en {selected.name}
            </button>
          )}
        </div>
      </div>

      {/* Power matrix */}
      <div className="p-4 border-t border-white/[0.06]">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="text-[11px] uppercase tracking-widest font-bold text-amber-400">PODERES DE LA EXTENSIÓN</h3>
            <span className="text-[10px] text-white/40">· {stats.powers}/{stats.totalPowers} activos</span>
          </div>

          {/* Category filter */}
          <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
            <button
              onClick={() => setPowerFilter('all')}
              className={`shrink-0 px-2 py-0.5 rounded-full text-[9px] font-bold border ${
                powerFilter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
              }`}
            >
              Todos · {POWERS.length}
            </button>
            {(Object.keys(CATEGORY_CONFIG) as (keyof typeof CATEGORY_CONFIG)[]).map(c => {
              const cfg = CATEGORY_CONFIG[c]
              const Icon = cfg.icon
              const active = powerFilter === c
              return (
                <button
                  key={c}
                  onClick={() => setPowerFilter(c)}
                  className="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold border"
                  style={
                    active
                      ? { background: `${cfg.color}20`, borderColor: `${cfg.color}50`, color: cfg.color }
                      : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }
                  }
                >
                  <Icon className="w-2.5 h-2.5" />
                  {cfg.label} · {powerCounts[c] || 0}
                </button>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {filteredPowers.map(p => {
            const cat = CATEGORY_CONFIG[p.category]
            const Icon = cat.icon
            return (
              <div
                key={p.id}
                className="rounded-xl border p-3 transition-all"
                style={{
                  background: p.enabled ? `${cat.color}08` : 'rgba(255,255,255,0.02)',
                  borderColor: p.enabled ? `${cat.color}25` : 'rgba(255,255,255,0.06)',
                  opacity: p.enabled ? 1 : 0.55,
                }}
              >
                <div className="flex items-start gap-2 mb-1">
                  <span className="text-xl shrink-0">{p.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-white leading-tight">{p.name}</p>
                    <span className="inline-flex items-center gap-1 text-[8px] px-1 py-0.5 rounded mt-0.5" style={{ background: `${cat.color}18`, color: cat.color }}>
                      <Icon className="w-2 h-2" />
                      {cat.label}
                    </span>
                  </div>
                  {p.enabled && (
                    <div className="w-1.5 h-1.5 rounded-full animate-pulse shrink-0 mt-1" style={{ background: cat.color }} />
                  )}
                </div>
                <p className="text-[10px] text-white/55 leading-snug">{p.detail}</p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-white/[0.06] bg-black/30 px-5 py-3">
        <div className="flex items-center gap-2 mb-1">
          <Bot className="w-3.5 h-3.5 text-blue-400" />
          <p className="text-[10px] uppercase tracking-widest font-bold text-blue-300">EXTENSIONES = BRAZOS DEL CEREBRO</p>
        </div>
        <p className="text-[11px] text-white/60 leading-snug">
          Mientras navegás (o ni siquiera) las extensiones <span className="text-emerald-400 font-bold">capturan</span> · <span className="text-purple-400 font-bold">automatizan</span> · <span className="text-amber-400 font-bold">monitorean</span> · <span className="text-emerald-400 font-bold">sincronizan</span> · <span className="text-pink-400 font-bold">optimizan</span> tus tiendas en <span className="text-white font-bold">8 navegadores y 14 plataformas</span>. Vos solo sonreís al ver los números crecer.
        </p>
      </div>
    </section>
  )
}
