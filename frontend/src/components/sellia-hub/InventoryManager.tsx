'use client'

/**
 * INVENTORY MANAGER
 *
 * SKUs · stock por warehouse · alerts low-stock · auto-reorder rules.
 */

import { useState, useMemo } from 'react'
import { Package, AlertTriangle, RefreshCw, Warehouse, Filter, Plus, Bot, TrendingDown } from 'lucide-react'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  emerald:     '#10B981',
  cyan:        '#06B6D4',
  amber:       '#F59E0B',
  violet:      '#8B5CF6',
  rose:        '#ef4444',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowAmber:   '0 0 22px rgba(245,158,11,0.45)',
} as const

type StockStatus = 'ok' | 'low' | 'critical' | 'oos'

interface SKU {
  id: string
  emoji: string
  name: string
  sku: string
  warehouses: { name: string; stock: number; reserved: number }[]
  reorderPoint: number
  reorderQty: number
  leadDays: number
  velocity: number
  cost: number
  price: number
  autoReorder: boolean
  channels: string[]
  aiPrediction?: string
}

const SKUS: SKU[] = [
  { id: 's1', emoji: '👟', name: 'Sneakers Nike Air 42',   sku: 'NIKE-AIR-42',   warehouses: [{ name: 'CABA', stock: 2,   reserved: 1 }, { name: 'GBA', stock: 0,  reserved: 0 }], reorderPoint: 10, reorderQty: 24, leadDays: 5,  velocity: 1.8, cost: 87,  price: 184, autoReorder: true,  channels: ['Shopify', 'ML'],         aiPrediction: 'Se agota en 1d · orden auto disparada esta mañana' },
  { id: 's2', emoji: '🎒', name: 'Mochila X1 Premium',     sku: 'MOCH-X1-PREM', warehouses: [{ name: 'CABA', stock: 14,  reserved: 3 }, { name: 'GBA', stock: 8,  reserved: 2 }], reorderPoint: 8,  reorderQty: 20, leadDays: 3,  velocity: 1.2, cost: 42,  price: 89,  autoReorder: true,  channels: ['Shopify', 'ML', 'IG'],   aiPrediction: 'Stock saludable · próximo reorder en ~7d' },
  { id: 's3', emoji: '👜', name: 'Cartera Cuero Negro',    sku: 'CART-CUE-NEG', warehouses: [{ name: 'CABA', stock: 47,  reserved: 4 }, { name: 'GBA', stock: 23, reserved: 0 }], reorderPoint: 15, reorderQty: 30, leadDays: 7,  velocity: 0.8, cost: 35,  price: 78,  autoReorder: false, channels: ['Shopify', 'Local'],      aiPrediction: 'Exceso de stock · considera liquidar 20u con descuento' },
  { id: 's4', emoji: '⌚', name: 'Smartwatch SW-9',        sku: 'SW-9-BLK',     warehouses: [{ name: 'CABA', stock: 5,   reserved: 2 }, { name: 'GBA', stock: 1,  reserved: 1 }], reorderPoint: 8,  reorderQty: 15, leadDays: 4,  velocity: 0.9, cost: 65,  price: 149, autoReorder: true,  channels: ['ML', 'Shopify'],         aiPrediction: 'Stock crítico · reorder recomendado urgente' },
  { id: 's5', emoji: '🎧', name: 'Auriculares BT Pro',     sku: 'BT-PRO-WT',    warehouses: [{ name: 'CABA', stock: 184, reserved: 12}, { name: 'GBA', stock: 67, reserved: 4 }], reorderPoint: 20, reorderQty: 50, leadDays: 10, velocity: 2.4, cost: 18,  price: 47,  autoReorder: true,  channels: ['ML', 'Shopify', 'TikTok'], aiPrediction: 'Top seller · stock suficiente para 97d' },
  { id: 's6', emoji: '☕', name: 'Mate Imperial · acero',  sku: 'MATE-IMP-AC',  warehouses: [{ name: 'CABA', stock: 0,   reserved: 0 }, { name: 'GBA', stock: 0,  reserved: 0 }], reorderPoint: 5,  reorderQty: 12, leadDays: 14, velocity: 0.5, cost: 22,  price: 48,  autoReorder: false, channels: ['Local', 'ML'],           aiPrediction: 'OUT OF STOCK · reorder manual requerido' },
]

const statusOf = (s: SKU): StockStatus => {
  const total = s.warehouses.reduce((acc, w) => acc + w.stock - w.reserved, 0)
  if (total === 0)                        return 'oos'
  if (total < s.reorderPoint / 2)        return 'critical'
  if (total < s.reorderPoint)            return 'low'
  return 'ok'
}

const STATUS_CONFIG: Record<StockStatus, { color: string; label: string }> = {
  ok:       { color: T.emerald, label: 'OK' },
  low:      { color: T.amber,   label: 'LOW' },
  critical: { color: T.rose,    label: 'CRITICAL' },
  oos:      { color: '#dc2626', label: 'OUT-OF-STOCK' },
}

const CHANNEL_SYNC = [
  { name: 'Mercado Libre', emoji: '🟡', synced: true },
  { name: 'Shopify',       emoji: '🟢', synced: true },
  { name: 'TikTok Shop',   emoji: '🎵', synced: true },
  { name: 'Local',         emoji: '🏪', synced: false },
]

export default function InventoryManager() {
  const [filter, setFilter] = useState<StockStatus | 'all'>('all')

  const enriched = useMemo(() => SKUS.map(s => ({ ...s, status: statusOf(s) })), [])
  const filtered = filter === 'all' ? enriched : enriched.filter(s => s.status === filter)

  const stats = useMemo(() => {
    const totalSkus = SKUS.length
    const totalUnits = SKUS.reduce((s, sk) => s + sk.warehouses.reduce((a, w) => a + w.stock, 0), 0)
    const totalValue = SKUS.reduce((s, sk) => s + sk.warehouses.reduce((a, w) => a + w.stock, 0) * sk.cost, 0)
    const critical = enriched.filter(s => s.status === 'critical' || s.status === 'oos').length
    return { totalSkus, totalUnits, totalValue, critical }
  }, [enriched])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.amber + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.amber + '22', border: '1px solid ' + T.amber + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Warehouse size={18} style={{ color: T.amber, filter: 'drop-shadow(0 0 8px ' + T.amber + 'aa)' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>
              INVENTORY MANAGER <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>· Stock · warehouses · auto-reorder</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              {stats.totalSkus} SKUs · {stats.totalUnits} unidades · <span style={{ color: T.amber, fontWeight: 700, textShadow: T.glowAmber }}>${stats.totalValue.toLocaleString()}</span> valor inventario
            </p>
          </div>
        </div>
        <button style={{ padding: '6px 14px', borderRadius: 8, background: T.amber + '18', border: '1px solid ' + T.amber + '40', color: T.amber, fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Plus size={12} /> SKU nuevo
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: '1px solid ' + T.border }}>
        {[
          { label: 'SKUs activos',      value: String(stats.totalSkus),          color: T.amber },
          { label: 'Unidades total',    value: String(stats.totalUnits),          color: T.emerald },
          { label: 'SKUs críticos',     value: String(stats.critical),            color: T.rose },
          { label: 'Valor inventario',  value: `$${(stats.totalValue/1000).toFixed(1)}k`, color: T.violet },
        ].map(s => (
          <div key={s.label} style={{ padding: 16, borderRight: '1px solid ' + T.border, textAlign: 'center' }}>
            <p style={{ fontSize: 22, fontWeight: 900, color: s.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 18px ' + s.color + '88', marginBottom: 4 }}>{s.value}</p>
            <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{s.label}</p>
          </div>
        ))}
      </div>

      {/* Multi-channel sync */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub, letterSpacing: '.06em' }}>Sync canales:</span>
        {CHANNEL_SYNC.map(ch => (
          <div key={ch.name} style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 6, background: ch.synced ? T.emerald + '10' : T.amber + '10', border: '1px solid ' + (ch.synced ? T.emerald + '25' : T.amber + '25') }}>
            <span style={{ fontSize: 12 }}>{ch.emoji}</span>
            <span style={{ fontSize: 9, color: ch.synced ? T.emerald : T.amber, fontWeight: 600 }}>{ch.name}</span>
            <span style={{ fontSize: 8, color: ch.synced ? T.emerald : T.amber }}>{ch.synced ? '✓' : '!'}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter size={12} style={{ color: T.textSub }} />
        {(['all', 'ok', 'low', 'critical', 'oos'] as const).map(s => {
          const cfg = s === 'all' ? null : STATUS_CONFIG[s]
          const active = filter === s
          return (
            <button
              key={s}
              onClick={() => setFilter(s)}
              style={{ fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer', background: active ? (cfg ? cfg.color + '20' : 'rgba(255,255,255,0.12)') : T.bgApp, border: '1px solid ' + (active ? (cfg ? cfg.color + '50' : 'rgba(255,255,255,0.25)') : T.border), color: active ? (cfg?.color ?? T.textPrim) : T.textSub }}
            >
              {s}
            </button>
          )
        })}
      </div>

      {/* SKU list */}
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.map(s => {
          const total = s.warehouses.reduce((acc, w) => acc + w.stock - w.reserved, 0)
          const maxStock = Math.max(s.reorderQty * 2, total + 5)
          const stockPct = Math.min((total / maxStock) * 100, 100)
          const reorderPct = (s.reorderPoint / maxStock) * 100
          const daysLeft = s.velocity > 0 ? Math.floor(total / s.velocity) : 999
          const status = STATUS_CONFIG[s.status]
          const isCritical = s.status === 'critical' || s.status === 'oos'
          const daysColor = daysLeft < 7 ? T.rose : daysLeft < 14 ? T.amber : T.emerald

          return (
            <div
              key={s.id}
              style={{ borderRadius: 12, border: '1px solid ' + status.color + '28', background: status.color + '04', overflow: 'hidden' }}
            >
              {/* Top accent */}
              <div style={{ height: 2, background: 'linear-gradient(90deg, ' + status.color + ', transparent)' }} />

              <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <span style={{ fontSize: 24, flexShrink: 0, marginTop: 2 }}>{s.emoji}</span>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 2 }}>
                        <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{s.name}</p>
                        <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'monospace', background: status.color + '18', border: '1px solid ' + status.color + '28', color: status.color }}>{status.label}</span>
                        {s.autoReorder && (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 8, padding: '2px 6px', borderRadius: 4, color: T.emerald, background: T.emerald + '10', border: '1px solid ' + T.emerald + '25', fontWeight: 700 }}>
                            <RefreshCw size={8} />AUTO
                          </span>
                        )}
                      </div>
                      <code style={{ fontSize: 9, color: T.textSub, fontFamily: 'monospace' }}>{s.sku}</code>
                    </div>
                    <div style={{ display: 'flex', gap: 16, flexShrink: 0 }}>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: 22, fontWeight: 900, color: status.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 16px ' + status.color + '88', lineHeight: 1 }}>{total}</p>
                        <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub, marginTop: 2 }}>disponible</p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <p style={{ fontSize: 22, fontWeight: 900, color: daysColor, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 16px ' + daysColor + '88', lineHeight: 1 }}>
                          {daysLeft >= 999 ? '∞' : `${daysLeft}d`}
                        </p>
                        <p style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub, marginTop: 2 }}>runway</p>
                      </div>
                    </div>
                  </div>

                  {/* Warehouse chips */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    {s.warehouses.map(w => (
                      <span key={w.name} style={{ fontSize: 9, padding: '2px 8px', borderRadius: 4, background: T.bgApp, border: '1px solid ' + T.border, color: T.textSub }}>
                        {w.name}: <span style={{ fontWeight: 700, color: T.textPrim }}>{w.stock - w.reserved}</span>u
                      </span>
                    ))}
                    <span style={{ fontSize: 9, color: T.textSub }}>Lead: {s.leadDays}d · RP: {s.reorderPoint}u</span>
                    {/* Channel sync chips */}
                    {s.channels.map(ch => (
                      <span key={ch} style={{ fontSize: 8, padding: '1px 5px', borderRadius: 3, background: T.emerald + '10', border: '1px solid ' + T.emerald + '20', color: T.emerald }}>{ch}</span>
                    ))}
                  </div>

                  {/* Visual stock bar */}
                  <div style={{ position: 'relative', height: 12, background: T.border, borderRadius: 6, overflow: 'hidden', marginBottom: 4 }}>
                    {/* Reorder point marker */}
                    <div style={{ position: 'absolute', top: 0, bottom: 0, width: 2, background: 'rgba(255,255,255,0.2)', zIndex: 10, left: `${reorderPct}%` }} />
                    {/* Stock fill */}
                    <div style={{ height: '100%', borderRadius: 6, background: 'linear-gradient(90deg, ' + status.color + 'cc, ' + status.color + ')', width: `${stockPct}%`, boxShadow: '0 0 8px ' + status.color + '40', transition: 'width .5s' }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 8, color: T.textSub }}>
                    <span>0</span>
                    <span>RP:{s.reorderPoint}</span>
                    <span>{maxStock}</span>
                  </div>

                  {/* AI prediction */}
                  {s.aiPrediction && (
                    <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 8, background: T.violet + '08', border: '1px solid ' + T.violet + '20' }}>
                      <Bot size={10} style={{ color: T.violet, flexShrink: 0 }} />
                      <p style={{ fontSize: 10, color: T.violet }}>{s.aiPrediction}</p>
                    </div>
                  )}
                </div>
              </div>

              {isCritical && (
                <div style={{ margin: '0 14px 12px', display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', borderRadius: 10, background: T.rose + '08', border: '1px solid ' + T.rose + '28' }}>
                  <AlertTriangle size={14} style={{ color: T.rose, flexShrink: 0 }} />
                  <p style={{ fontSize: 11, color: T.rose }}>
                    {s.autoReorder
                      ? `IA disparó orden automática · ${s.reorderQty}u pedidas · ETA ${s.leadDays}d`
                      : '⚠ Reorder manual requerido — sin auto-reorder configurado'
                    }
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer AI insight */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid ' + T.border, background: T.bgApp, display: 'flex', alignItems: 'center', gap: 8 }}>
        <TrendingDown size={13} style={{ color: T.amber }} />
        <span style={{ fontSize: 11, color: T.textSub }}>
          IA predice <span style={{ color: T.amber, fontWeight: 700 }}>+34%</span> demanda próxima semana por temporada · sugiere reorder preventivo en <span style={{ color: T.amber, fontWeight: 700 }}>Auriculares BT Pro</span> y <span style={{ color: T.amber, fontWeight: 700 }}>Mochila X1</span>
        </span>
      </div>
    </section>
  )
}
