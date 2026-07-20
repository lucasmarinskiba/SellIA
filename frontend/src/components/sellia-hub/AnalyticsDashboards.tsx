'use client'

/**
 * ANALYTICS DASHBOARDS — RETAIN lobe
 *
 * KPIs, funnels, retention, P&L, exports.
 */

import { useState, useMemo } from 'react'
import { BarChart3, TrendingUp, DollarSign, Activity, Users, Download, RefreshCw } from 'lucide-react'

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

type Period = '7d' | '30d' | '90d'

const KPI_DATA: Record<Period, { mrr: number; cac: number; ltv: number; churn: number; mrrTrend: number; cacTrend: number; ltvTrend: number; churnTrend: number }> = {
  '7d':  { mrr: 31200, cac: 127, ltv: 2840, churn: 2.1, mrrTrend: 8.4,  cacTrend: -3.2,  ltvTrend: 5.7,  churnTrend: -0.3 },
  '30d': { mrr: 48700, cac: 142, ltv: 3120, churn: 1.8, mrrTrend: 14.2, cacTrend: -5.1,  ltvTrend: 9.4,  churnTrend: -0.5 },
  '90d': { mrr: 62400, cac: 118, ltv: 3680, churn: 1.4, mrrTrend: 24.7, cacTrend: -11.3, ltvTrend: 18.2, churnTrend: -0.9 },
}

const SPARKLINE_7D = [2840, 3120, 2470, 4180, 5247, 6892, 5847]
const SPARKLINE_MRR = [38400, 41200, 39800, 44700, 48200, 47100, 48700]

const FUNNEL = [
  { label: 'Visitas',    value: 48200, color: '#06B6D4' },
  { label: 'Leads',      value: 8400,  color: '#10B981' },
  { label: 'Clientes',   value: 1247,  color: '#F59E0B' },
  { label: 'Habituales', value: 384,   color: '#8B5CF6' },
]

const COHORTS = [
  { cohort: 'Ene', w1: 100, w2: 87, w3: 78, w4: 72, w8: 68, w12: 64 },
  { cohort: 'Feb', w1: 100, w2: 89, w3: 82, w4: 76, w8: 71, w12: 0  },
  { cohort: 'Mar', w1: 100, w2: 91, w3: 84, w4: 79, w8: 0,  w12: 0  },
  { cohort: 'Abr', w1: 100, w2: 88, w3: 83, w4: 0,  w8: 0,  w12: 0  },
]

const mkSparkPath = (vals: number[], w = 120, h = 32): string => {
  const max = Math.max(...vals)
  const min = Math.min(...vals)
  const range = max - min || 1
  return vals.map((v, i) => {
    const x = (i / (vals.length - 1)) * w
    const y = h - ((v - min) / range) * (h - 4) - 2
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

const TrendArrow = ({ val, unit = '%' }: { val: number; unit?: string }) => {
  const up = val >= 0
  return (
    <span style={{ fontSize: 11, color: up ? T.emerald : T.rose, fontFamily: 'JetBrains Mono,monospace' }}>
      {up ? '▲' : '▼'} {Math.abs(val)}{unit}
    </span>
  )
}

export default function AnalyticsDashboards() {
  const [period, setPeriod] = useState<Period>('30d')
  const kpi = KPI_DATA[period]

  const funnelMax = useMemo(() => FUNNEL[0].value, [])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #10B98180, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.emerald + '22', border: '1px solid ' + T.emerald + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BarChart3 style={{ width: 20, height: 20, color: T.emerald, filter: 'drop-shadow(0 0 6px #10B98188)' }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Analytics Dashboards
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· KPIs · Funnel · Retención</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>MRR · CAC · LTV · Churn · Cohort retention</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {(['7d', '30d', '90d'] as Period[]).map(p => (
            <button key={p} onClick={() => setPeriod(p)}
              style={{ padding: '4px 12px', borderRadius: 6, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', cursor: 'pointer', transition: 'all .15s', background: period === p ? T.emerald + '22' : 'transparent', border: '1px solid ' + (period === p ? T.emerald + '66' : T.border), color: period === p ? T.emerald : T.textSub }}>
              {p}
            </button>
          ))}
          <button style={{ padding: '4px 10px', borderRadius: 6, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', cursor: 'pointer', background: T.cyan + '18', border: '1px solid ' + T.cyan + '40', color: T.cyan, display: 'flex', alignItems: 'center', gap: 4 }}>
            <Download style={{ width: 12, height: 12 }} /> CSV
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, padding: '16px 20px' }}>
        {[
          { label: 'MRR', value: '$' + kpi.mrr.toLocaleString(), trend: kpi.mrrTrend, color: T.emerald, glow: T.glowEmerald, spark: SPARKLINE_MRR, icon: DollarSign },
          { label: 'CAC', value: '$' + kpi.cac, trend: kpi.cacTrend, color: T.cyan, glow: T.glowCyan, spark: SPARKLINE_7D.map(v => v * 0.05), icon: Activity },
          { label: 'LTV', value: '$' + kpi.ltv.toLocaleString(), trend: kpi.ltvTrend, color: T.amber, glow: T.glowAmber, spark: SPARKLINE_7D.map(v => v * 0.4), icon: TrendingUp },
          { label: 'Churn', value: kpi.churn + '%', trend: kpi.churnTrend, color: T.rose, glow: '0 0 22px rgba(239,68,68,0.45)', spark: [3.2, 2.9, 2.8, 2.4, 2.1, 1.9, kpi.churn], icon: Users },
        ].map(({ label, value, trend, color, glow, spark, icon: Icon }) => (
          <div key={label} style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{label}</div>
              <Icon style={{ width: 14, height: 14, color }} />
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color, textShadow: '0 0 20px ' + color + '88', marginBottom: 4 }}>{value}</div>
            <TrendArrow val={trend} />
            <svg viewBox={`0 0 120 32`} style={{ width: '100%', height: 32, marginTop: 8 }}>
              <path d={mkSparkPath(spark)} fill="none" stroke={color} strokeWidth="1.5" opacity=".7" />
              <path d={mkSparkPath(spark) + ` L120,32 L0,32 Z`} fill={color} opacity=".08" />
            </svg>
          </div>
        ))}
      </div>

      {/* Funnel + Cohort row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, padding: '0 20px 16px' }}>

        {/* Funnel */}
        <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 12 }}>Funnel de conversión</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {FUNNEL.map((row, i) => {
              const pct = (row.value / funnelMax) * 100
              const conv = i > 0 ? ((row.value / FUNNEL[i - 1].value) * 100).toFixed(1) + '%' : '—'
              return (
                <div key={row.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: T.textPrim }}>{row.label}</span>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span style={{ fontSize: 12, fontWeight: 700, color: row.color, textShadow: '0 0 20px ' + row.color + '88' }}>{row.value.toLocaleString()}</span>
                      {i > 0 && <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'monospace', background: row.color + '18', border: '1px solid ' + row.color + '28', color: row.color }}>{conv}</span>}
                    </div>
                  </div>
                  <div style={{ height: 6, background: T.border, borderRadius: 4, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: pct + '%', background: row.color, borderRadius: 4, boxShadow: '0 0 8px ' + row.color + '88', transition: 'width .5s ease' }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Cohort retention mini-table */}
        <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 12 }}>Cohort retention heatmap</div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 9 }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', color: T.textSub, fontFamily: 'monospace', fontWeight: 600, paddingBottom: 6 }}>Cohort</th>
                {['W1', 'W2', 'W3', 'W4', 'W8', 'W12'].map(w => (
                  <th key={w} style={{ textAlign: 'center', color: T.textSub, fontFamily: 'monospace', fontWeight: 600, paddingBottom: 6 }}>{w}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COHORTS.map(c => (
                <tr key={c.cohort}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 700, color: T.textPrim, paddingBottom: 4, paddingRight: 6 }}>{c.cohort}</td>
                  {[c.w1, c.w2, c.w3, c.w4, c.w8, c.w12].map((v, i) => (
                    <td key={i} style={{ padding: '2px 2px' }}>
                      <div style={{ aspectRatio: '1', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 4, fontSize: 9, fontFamily: 'monospace', fontWeight: 700, background: v === 0 ? T.border + '44' : `rgba(16,185,129,${(v / 100) * 0.55 + 0.08})`, color: v === 0 ? T.textSub + '66' : T.textPrim, minWidth: 28, minHeight: 20 }}>
                        {v === 0 ? '—' : v + '%'}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* P&L summary bar */}
      <div style={{ borderTop: '1px solid ' + T.border, padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
        <RefreshCw style={{ width: 12, height: 12, color: T.emerald }} />
        {[
          { label: 'Revenue (período)', value: '$' + (kpi.mrr * 1.12).toFixed(0), color: T.emerald },
          { label: 'Gross margin', value: '94.5%', color: T.cyan },
          { label: 'LTV / CAC ratio', value: (kpi.ltv / kpi.cac).toFixed(1) + 'x', color: T.amber },
          { label: 'Retención W4 avg', value: '76.8%', color: T.violet },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 11, color: T.textSub }}>{label}:</span>
            <span style={{ fontSize: 13, fontWeight: 700, color, textShadow: '0 0 20px ' + color + '88' }}>{value}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
