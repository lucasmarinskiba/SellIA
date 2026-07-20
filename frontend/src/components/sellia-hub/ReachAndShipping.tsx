'use client'

/**
 * REACH & SHIPPING
 *
 * Donde vendés + cómo entregás:
 *   - Mapa de zonas de alcance: local, regional, nacional, internacional
 *   - 4 modelos de negocio: local físico · home office · servicios remotos · global
 *   - Couriers integrados: Andreani, OCA, Correo AR, DHL, FedEx, UPS, Mercado Envíos
 *   - Ruteo inteligente: IA elige el courier óptimo por destino/peso/urgencia
 */

import { useState, useMemo } from 'react'
import {
  MapPin, Truck, Globe, Home, Building2, Plane,
  CheckCircle2, Activity, Bot, Sparkles, Package, Clock,
  TrendingUp, Zap, ChevronRight, Hash, AlertCircle
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type BizModel = 'local-store' | 'national-ship' | 'services-remote' | 'global-digital'
type ReachZone = 'local' | 'regional' | 'national' | 'continental' | 'global'

interface ReachData {
  zone: ReachZone
  label: string
  description: string
  ordersWeek: number
  revenueWeek: number
  conversionRate: number
  growthDelta: number
  color: string
  emoji: string
}

interface Carrier {
  id: string
  name: string
  logo: string
  type: 'national' | 'international' | 'last-mile' | 'marketplace'
  status: 'live' | 'inactive' | 'setup'
  coverage: string
  avgDays: string
  avgCost: string
  ordersThisMonth: number
  rating: number
  brandColor: string
  bestFor: string
}

const REACH_ZONES: ReachData[] = [
  { zone: 'local',       label: 'Local · Ciudad',        description: 'CABA + GBA',                          ordersWeek: 47, revenueWeek: 8400,  conversionRate: 8.4, growthDelta: 12, color: '#22c55e', emoji: '🏪' },
  { zone: 'regional',    label: 'Regional · Provincia',  description: 'Buenos Aires + 3 prov vecinas',       ordersWeek: 28, revenueWeek: 12400, conversionRate: 4.8, growthDelta: 8,  color: '#3b82f6', emoji: '🗺' },
  { zone: 'national',    label: 'Nacional',              description: '24 provincias · todo el país',         ordersWeek: 18, revenueWeek: 14200, conversionRate: 3.2, growthDelta: 18, color: '#a855f7', emoji: '🇦🇷' },
  { zone: 'continental', label: 'Continental · LATAM',   description: 'Chile, Uruguay, Paraguay, México',     ordersWeek: 7,  revenueWeek: 9800,  conversionRate: 2.1, growthDelta: 42, color: '#ec4899', emoji: '🌎' },
  { zone: 'global',      label: 'Global',                description: 'USA + Europa (productos digitales)',  ordersWeek: 4,  revenueWeek: 6200,  conversionRate: 1.8, growthDelta: 87, color: '#fbbf24', emoji: '🌍' },
]

const BIZ_MODELS: { id: BizModel; emoji: string; label: string; description: string; recommendations: string[] }[] = [
  {
    id: 'local-store', emoji: '🏪', label: 'Local físico + envíos',
    description: 'Tenés un local y hacés delivery por la ciudad/región',
    recommendations: ['Configurar Mercado Envíos Flex para misma ciudad', 'Pedidos Ya / Rappi para hot delivery', 'OCA Pickit puntos cercanos', 'Cluster ads geo-targeted radio 15km'],
  },
  {
    id: 'national-ship', emoji: '📦', label: 'E-commerce nacional',
    description: 'Vendés productos físicos a todo el país',
    recommendations: ['Andreani + OCA + Correo AR multi-courier', 'Mercado Envíos cubre 90% destinos', 'Tarifa promedio + ETA por destino', 'Ads geo-targeted por interés × CP'],
  },
  {
    id: 'services-remote', emoji: '💻', label: 'Servicios remotos / Consultoría',
    description: 'No vendés productos físicos — consultoría, apps, programas',
    recommendations: ['Calendly + Zoom integrados con IA', 'LinkedIn outreach automático a ICP', 'Webinars de captura semanales', 'SEO geo-agnóstico + contenido in English'],
  },
  {
    id: 'global-digital', emoji: '🌍', label: 'Producto digital global',
    description: 'Vendés cursos, software o digital al mundo',
    recommendations: ['Hotmart + Gumroad + Stripe multi-currency', 'Tax compliance auto (IVA, GST, sales tax)', 'Soporte 24/7 en 6 idiomas vía IA', 'TikTok global + Reels en inglés/portugués'],
  },
]

const CARRIERS: Carrier[] = [
  { id: 'andreani', name: 'Andreani',         logo: '📮', type: 'national',     status: 'live',     coverage: 'Todo Argentina · 4000+ sucursales', avgDays: '2-4d', avgCost: '$1,890', ordersThisMonth: 87, rating: 92, brandColor: '#ED1C24', bestFor: 'Nacional · paquetes hasta 25kg' },
  { id: 'oca',      name: 'OCA',              logo: '📨', type: 'national',     status: 'live',     coverage: '23 provincias · 800 sucursales',     avgDays: '3-5d', avgCost: '$1,620', ordersThisMonth: 64, rating: 88, brandColor: '#1B4F8C', bestFor: 'Tarifa más económica · sin urgencia' },
  { id: 'correo',   name: 'Correo Argentino', logo: '📬', type: 'national',     status: 'live',     coverage: 'Universal · cubre 100% del país',     avgDays: '4-7d', avgCost: '$1,240', ordersThisMonth: 31, rating: 76, brandColor: '#FFC107', bestFor: 'Última milla zonas remotas' },
  { id: 'meli',     name: 'Mercado Envíos',   logo: '📦', type: 'marketplace',  status: 'live',     coverage: 'Integrado con Mercado Libre',         avgDays: '1-3d', avgCost: 'Variable', ordersThisMonth: 142, rating: 95, brandColor: '#FFE600', bestFor: 'Ventas vía ML · descuento alto' },
  { id: 'pedidosya', name: 'PedidosYa Envíos',logo: '🛵', type: 'last-mile',    status: 'live',     coverage: 'CABA + 15 ciudades grandes',         avgDays: '<2h',  avgCost: '$890',   ordersThisMonth: 23, rating: 84, brandColor: '#FA0050', bestFor: 'Same-day · misma ciudad' },
  { id: 'rappi',    name: 'Rappi Envíos',     logo: '🛴', type: 'last-mile',    status: 'inactive', coverage: 'CABA + 12 ciudades',                  avgDays: '<2h',  avgCost: '$1,100', ordersThisMonth: 0,  rating: 80, brandColor: '#FF6E1B', bestFor: 'Same-day · alternativa PYa' },
  { id: 'dhl',      name: 'DHL Express',      logo: '✈️', type: 'international', status: 'live',    coverage: '220+ países',                         avgDays: '3-6d', avgCost: '$24-180', ordersThisMonth: 12, rating: 96, brandColor: '#FFCC00', bestFor: 'Internacional rápido · paquetes valor alto' },
  { id: 'fedex',    name: 'FedEx',            logo: '🚀', type: 'international', status: 'live',    coverage: '220+ países',                         avgDays: '4-7d', avgCost: '$22-160', ordersThisMonth: 8,  rating: 94, brandColor: '#4D148C', bestFor: 'B2B internacional · trackeo premium' },
  { id: 'ups',      name: 'UPS',              logo: '🟫', type: 'international', status: 'live',    coverage: '200+ países',                         avgDays: '5-8d', avgCost: '$20-140', ordersThisMonth: 5,  rating: 91, brandColor: '#351C15', bestFor: 'USA + Europa · packs medianos' },
  { id: 'usps',     name: 'USPS Intl',        logo: '🇺🇸', type: 'international', status: 'setup',   coverage: 'USA → mundo',                          avgDays: '7-12d', avgCost: '$15-90',  ordersThisMonth: 0,  rating: 0,  brandColor: '#004B87', bestFor: 'Económico · USA → LATAM' },
]

const CARRIER_TYPE_CONFIG = {
  national:      { label: 'Nacional',       color: '#3b82f6', icon: Building2 },
  international: { label: 'Internacional',  color: '#fbbf24', icon: Globe },
  'last-mile':   { label: 'Last-Mile',      color: '#ec4899', icon: Zap },
  marketplace:   { label: 'Marketplace',    color: '#22c55e', icon: Package },
} as const

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function ReachAndShipping() {
  const [bizModel, setBizModel] = useState<BizModel>('national-ship')
  const [carrierFilter, setCarrierFilter] = useState<Carrier['type'] | 'all'>('all')

  const totalReach = useMemo(() => ({
    orders: REACH_ZONES.reduce((s, z) => s + z.ordersWeek, 0),
    revenue: REACH_ZONES.reduce((s, z) => s + z.revenueWeek, 0),
  }), [])

  const filteredCarriers = useMemo(
    () => carrierFilter === 'all' ? CARRIERS : CARRIERS.filter(c => c.type === carrierFilter),
    [carrierFilter]
  )

  const carrierStats = useMemo(() => ({
    live: CARRIERS.filter(c => c.status === 'live').length,
    totalOrders: CARRIERS.reduce((s, c) => s + c.ordersThisMonth, 0),
    avgRating: CARRIERS.filter(c => c.rating > 0).reduce((s, c) => s + c.rating, 0) / CARRIERS.filter(c => c.rating > 0).length,
  }), [])

  const selectedModel = BIZ_MODELS.find(m => m.id === bizModel)!

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, ${T.cyan}, #3b82f6, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(6,182,212,0.12)', border: '1px solid rgba(6,182,212,0.30)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Globe style={{ width: 20, height: 20, color: T.cyan, filter: 'drop-shadow(0 0 8px rgba(6,182,212,0.6))' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              REACH <span style={{ color: T.cyan }}>&amp;</span> SHIPPING
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· Dónde vendés + cómo entregás</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>5 zonas geográficas · 10 couriers integrados · ruteo IA óptimo</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ padding: '8px 14px', borderRadius: 10, background: T.bgCard, border: `1px solid ${T.border}` }}>
            <span style={{ fontSize: 10, color: T.textSub }}>Órdenes semana: </span>
            <span style={{ fontSize: 12, color: T.textPrim, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{totalReach.orders}</span>
          </div>
          <div style={{ padding: '8px 14px', borderRadius: 10, background: 'rgba(16,185,129,0.10)', border: `1px solid rgba(16,185,129,0.28)` }}>
            <span style={{ fontSize: 12, color: T.emerald, fontWeight: 700, fontVariantNumeric: 'tabular-nums', textShadow: T.glowEmerald }}>${(totalReach.revenue / 1000).toFixed(1)}k</span>
          </div>
        </div>
      </div>

      {/* Business model selector */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}` }}>
        <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Sparkles style={{ width: 10, height: 10 }} />
          ELEGÍ TU MODELO DE NEGOCIO · IA OPTIMIZA EN BASE A ESO
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
          {BIZ_MODELS.map(m => {
            const active = bizModel === m.id
            return (
              <button
                key={m.id}
                onClick={() => setBizModel(m.id)}
                style={{
                  padding: '14px 16px', borderRadius: 12, textAlign: 'left', cursor: 'pointer',
                  background: active ? 'rgba(6,182,212,0.10)' : T.bgCard,
                  border: active ? `1px solid rgba(6,182,212,0.40)` : `1px solid ${T.border}`,
                  color: active ? T.textPrim : T.textSub,
                }}
              >
                <div style={{ fontSize: 22, marginBottom: 6 }}>{m.emoji}</div>
                <p style={{ fontSize: 12, fontWeight: 700, color: active ? T.cyan : T.textPrim, margin: '0 0 4px' }}>{m.label}</p>
                <p style={{ fontSize: 10, color: T.textSub, lineHeight: 1.3, margin: 0, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{m.description}</p>
              </button>
            )
          })}
        </div>

        {/* AI recommendations */}
        <div style={{ marginTop: 12, padding: '14px 16px', borderRadius: 12, background: 'rgba(6,182,212,0.04)', border: `1px solid rgba(6,182,212,0.22)` }}>
          <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.cyan, fontWeight: 700, margin: '0 0 10px', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Bot style={{ width: 10, height: 10 }} />
            IA RECOMIENDA PARA TU MODELO
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 8 }}>
            {selectedModel.recommendations.map((r, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 10px', borderRadius: 8, background: T.bgApp, border: `1px solid ${T.border}` }}>
                <CheckCircle2 style={{ width: 12, height: 12, color: T.cyan, flexShrink: 0, marginTop: 2 }} />
                <p style={{ fontSize: 11, color: T.textPrim, lineHeight: 1.4, margin: 0 }}>{r}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Reach zones */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}` }}>
        <p style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: '0 0 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
          <MapPin style={{ width: 10, height: 10 }} />
          ZONAS DE ALCANCE · DÓNDE ESTÁS VENDIENDO
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 10 }}>
          {REACH_ZONES.map(z => (
            <div key={z.zone} style={{ ...card({ padding: 16 }), position: 'relative', overflow: 'hidden', boxShadow: `0 0 16px ${z.color}08` }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${z.color}, transparent)` }} />

              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontSize: 22 }}>{z.emoji}</span>
                <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.06em', background: `${z.color}20`, color: z.color }}>
                  {z.zone}
                </span>
              </div>

              <p style={{ fontSize: 12, fontWeight: 700, color: T.textPrim, margin: '0 0 2px' }}>{z.label}</p>
              <p style={{ fontSize: 10, color: T.textSub, margin: '0 0 12px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{z.description}</p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Órdenes/sem</span>
                  <span style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, fontVariantNumeric: 'tabular-nums' }}>{z.ordersWeek}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Revenue</span>
                  <span style={{ fontSize: 14, fontWeight: 900, fontVariantNumeric: 'tabular-nums', color: z.color }}>${(z.revenueWeek / 1000).toFixed(1)}k</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Conv</span>
                  <span style={{ fontSize: 12, fontWeight: 700, color: T.textPrim, fontVariantNumeric: 'tabular-nums' }}>{z.conversionRate}%</span>
                </div>
              </div>

              <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 4 }}>
                <TrendingUp style={{ width: 10, height: 10, color: T.emerald }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: T.emerald }}>+{z.growthDelta}%</span>
                <span style={{ fontSize: 10, color: T.textSub }}>vs mes</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Carriers */}
      <div style={{ padding: '20px 24px' }}>
        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
          {[
            { icon: CheckCircle2, label: 'Couriers conectados', value: `${carrierStats.live}/${CARRIERS.length}`, color: T.emerald, bg: 'rgba(16,185,129,0.06)', border: 'rgba(16,185,129,0.22)' },
            { icon: Package,      label: 'Envíos este mes',     value: `${carrierStats.totalOrders}`,            color: '#3b82f6',  bg: 'rgba(59,130,246,0.06)', border: 'rgba(59,130,246,0.22)' },
            { icon: Sparkles,     label: 'Rating promedio',     value: `${carrierStats.avgRating.toFixed(0)}/100`, color: T.amber,  bg: 'rgba(245,158,11,0.06)', border: 'rgba(245,158,11,0.22)' },
          ].map((s, i) => {
            const Icon = s.icon
            return (
              <div key={i} style={{ padding: '14px 16px', borderRadius: 12, background: s.bg, border: `1px solid ${s.border}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <Icon style={{ width: 12, height: 12, color: s.color }} />
                  <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: 0 }}>{s.label}</p>
                </div>
                <p style={{ fontSize: 22, fontWeight: 900, color: s.color, fontVariantNumeric: 'tabular-nums', margin: 0 }}>{s.value}</p>
              </div>
            )
          })}
        </div>

        {/* Filter chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, overflowX: 'auto' }}>
          <button
            onClick={() => setCarrierFilter('all')}
            style={{ flexShrink: 0, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: carrierFilter === 'all' ? 'rgba(255,255,255,0.10)' : T.bgCard, border: carrierFilter === 'all' ? '1px solid rgba(255,255,255,0.20)' : `1px solid ${T.border}`, color: carrierFilter === 'all' ? T.textPrim : T.textSub }}>
            Todos · {CARRIERS.length}
          </button>
          {(Object.keys(CARRIER_TYPE_CONFIG) as Carrier['type'][]).map(t => {
            const cfg = CARRIER_TYPE_CONFIG[t]
            const Icon = cfg.icon
            const active = carrierFilter === t
            const count = CARRIERS.filter(c => c.type === t).length
            return (
              <button
                key={t}
                onClick={() => setCarrierFilter(t)}
                style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: active ? `${cfg.color}20` : T.bgCard, border: active ? `1px solid ${cfg.color}50` : `1px solid ${T.border}`, color: active ? cfg.color : T.textSub }}
              >
                <Icon style={{ width: 10, height: 10 }} />
                {cfg.label} · {count}
              </button>
            )
          })}
        </div>

        {/* Carriers list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filteredCarriers.map(c => (
            <div key={c.id} style={{ ...card(), overflow: 'hidden' }}>
              <div style={{ height: 2, background: `linear-gradient(90deg, ${c.brandColor}${c.status === 'live' ? 'cc' : '44'}, transparent)` }} />
              <div style={{ padding: '14px 16px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <span style={{ fontSize: 22, flexShrink: 0 }}>{c.logo}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                    <p style={{ fontSize: 14, fontWeight: 700, color: T.textPrim, margin: 0 }}>{c.name}</p>
                    <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.06em', background: `${c.brandColor}20`, color: c.brandColor }}>
                      {CARRIER_TYPE_CONFIG[c.type].label}
                    </span>
                    {c.status === 'live' && (
                      <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', background: 'rgba(16,185,129,0.15)', color: T.emerald, border: `1px solid rgba(16,185,129,0.30)`, display: 'flex', alignItems: 'center', gap: 4 }}>
                        <div style={{ width: 4, height: 4, borderRadius: '50%', background: T.emerald, animation: 'pulse 2s infinite' }} />
                        Activo
                      </span>
                    )}
                    {c.status === 'inactive' && (
                      <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', background: T.bgApp, color: T.textSub, border: `1px solid ${T.border}` }}>Inactivo</span>
                    )}
                    {c.status === 'setup' && (
                      <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 5, fontFamily: 'monospace', textTransform: 'uppercase', background: 'rgba(245,158,11,0.15)', color: T.amber, border: `1px solid rgba(245,158,11,0.28)` }}>Setup pendiente</span>
                    )}
                  </div>
                  <p style={{ fontSize: 11, color: T.textSub, margin: '0 0 10px' }}>{c.coverage}</p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 10 }}>
                    {[
                      { label: 'Tiempo',    value: c.avgDays,          hl: false },
                      { label: 'Costo avg', value: c.avgCost,          hl: false },
                      { label: 'Envíos mes', value: `${c.ordersThisMonth}`, hl: c.ordersThisMonth > 0 },
                      { label: 'Rating',    value: c.rating > 0 ? `${c.rating}/100` : '—', hl: false },
                    ].map((s, i) => (
                      <div key={i} style={{ padding: '6px 8px', borderRadius: 8, background: T.bgApp, border: `1px solid ${T.border}` }}>
                        <p style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontFamily: 'monospace', margin: '0 0 2px' }}>{s.label}</p>
                        <p style={{ fontSize: 12, fontWeight: 900, fontVariantNumeric: 'tabular-nums', margin: 0, color: s.hl ? T.emerald : T.textPrim }}>{s.value}</p>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, padding: '8px 10px', borderRadius: 8, background: 'rgba(168,85,247,0.05)', border: `1px solid rgba(168,85,247,0.18)` }}>
                    <Bot style={{ width: 12, height: 12, color: '#c084fc', flexShrink: 0, marginTop: 2 }} />
                    <p style={{ fontSize: 10, color: '#c084fc', lineHeight: 1.4, margin: 0 }}>
                      <span style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Mejor para:</span> {c.bestFor}
                    </p>
                  </div>
                </div>

                {c.status === 'setup' && (
                  <button style={{ padding: '8px 14px', borderRadius: 10, background: 'rgba(245,158,11,0.12)', border: `1px solid rgba(245,158,11,0.35)`, color: T.amber, fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap', cursor: 'pointer', flexShrink: 0 }}>
                    Conectar
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Smart routing footer */}
        <div style={{ marginTop: 16, padding: '14px 16px', borderRadius: 12, background: 'rgba(168,85,247,0.05)', border: `1px solid rgba(168,85,247,0.22)` }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
            <Sparkles style={{ width: 16, height: 16, color: '#c084fc', flexShrink: 0, marginTop: 2 }} />
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, color: '#c084fc', textTransform: 'uppercase', letterSpacing: '0.08em', margin: '0 0 4px' }}>Ruteo inteligente IA</p>
              <p style={{ fontSize: 12, color: T.textSub, lineHeight: 1.5, margin: 0 }}>
                Para cada envío, la IA evalúa: destino, peso, urgencia, valor declarado, histórico del cliente, y elige automáticamente el courier óptimo. Esta semana: <span style={{ color: T.emerald, fontWeight: 700 }}>ahorro promedio del 18%</span> vs ruteo manual.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
