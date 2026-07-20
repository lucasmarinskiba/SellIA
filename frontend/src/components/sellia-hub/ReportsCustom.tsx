'use client'

/**
 * REPORTS CUSTOM — RETAIN lobe
 *
 * Template library, schedule picker, recipient email, generated reports list, AI suggestion.
 */

import { useState, useMemo } from 'react'
import { FileSpreadsheet, Download, Calendar, Sparkles, Filter, Bot, Mail, Plus, Clock } from 'lucide-react'

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

type Schedule = 'diario' | 'semanal' | 'mensual' | 'manual'
type Category = 'ventas' | 'leads' | 'finanzas' | 'marketing' | 'ops'

interface Template {
  id: string
  name: string
  desc: string
  category: Category
  outputs: string[]
  color: string
  aiSuggested?: boolean
}

const TEMPLATES: Template[] = [
  { id: 't1', name: 'Reporte de Ventas',        desc: 'Pipeline · deals cerrados · ticket promedio · win rate',     category: 'ventas',    outputs: ['pdf', 'xlsx'], color: '#10B981', aiSuggested: true },
  { id: 't2', name: 'Reporte de Leads',         desc: 'Nuevos leads · fuente · calificación · contactados vs conv', category: 'leads',     outputs: ['csv', 'pdf'],  color: '#06B6D4' },
  { id: 't3', name: 'Reporte MRR',              desc: 'Ingresos recurrentes · nuevos · expansión · churneados',     category: 'finanzas',  outputs: ['pdf', 'xlsx'], color: '#F59E0B', aiSuggested: true },
  { id: 't4', name: 'P&L Mensual',              desc: 'Revenue · COGS · OpEx · gross/net margin',                  category: 'finanzas',  outputs: ['pdf', 'xlsx'], color: '#8B5CF6' },
  { id: 't5', name: 'ROI por Canal',            desc: 'Spend vs revenue por canal · ROAS · CAC · LTV/CAC',         category: 'marketing', outputs: ['csv', 'pdf'],  color: '#ec4899' },
  { id: 't6', name: 'Cohort Retention',         desc: 'Retención 12 meses · LTV expansion · churn por segmento',   category: 'ops',       outputs: ['pdf', 'xlsx'], color: '#F59E0B' },
  { id: 't7', name: 'Cash Flow Forecast',       desc: 'Próximos 90 días · CxC/CxP · alertas liquidez',             category: 'finanzas',  outputs: ['pdf'],         color: '#10B981' },
  { id: 't8', name: 'Performance de Equipo',    desc: 'Top SDR · quota attainment · actividades por rep',          category: 'ventas',    outputs: ['xlsx'],        color: '#06B6D4' },
]

const RECENT: { name: string; date: string; size: string; format: string; color: string }[] = [
  { name: 'Reporte de Ventas · Mayo 2026',  date: '28 mayo 09:00', size: '184 KB', format: 'pdf',  color: '#10B981' },
  { name: 'Reporte MRR · Mayo 2026',        date: '28 mayo 09:00', size: '92 KB',  format: 'xlsx', color: '#F59E0B' },
  { name: 'ROI por Canal · W21',            date: '27 mayo 18:00', size: '67 KB',  format: 'csv',  color: '#ec4899' },
  { name: 'Reporte de Leads · Mayo 2026',   date: '27 mayo 08:00', size: '210 KB', format: 'pdf',  color: '#06B6D4' },
]

const CAT_COLORS: Record<Category, string> = {
  ventas:    '#10B981',
  leads:     '#06B6D4',
  finanzas:  '#F59E0B',
  marketing: '#ec4899',
  ops:       '#8B5CF6',
}

export default function ReportsCustom() {
  const [filterCat, setFilterCat] = useState<Category | 'all'>('all')
  const [schedule, setSchedule] = useState<Schedule>('semanal')
  const [email, setEmail] = useState('lucasdmarin@gmail.com')
  const [selected, setSelected] = useState<string | null>('t1')

  const filtered = useMemo(() =>
    filterCat === 'all' ? TEMPLATES : TEMPLATES.filter(t => t.category === filterCat),
  [filterCat])

  const aiSuggested = useMemo(() => TEMPLATES.filter(t => t.aiSuggested), [])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #10B98180, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.cyan + '22', border: '1px solid ' + T.cyan + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileSpreadsheet style={{ width: 20, height: 20, color: T.cyan, filter: 'drop-shadow(0 0 6px ' + T.cyan + '88)' }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Reports Custom
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· {TEMPLATES.length} plantillas · programados</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>Exports CSV · PDF · XLSX · schedule automático</div>
          </div>
        </div>
        <button style={{ padding: '6px 14px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', cursor: 'pointer', background: T.violet + '22', border: '1px solid ' + T.violet + '44', color: T.violet, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Plus style={{ width: 12, height: 12 }} /> Reporte custom
        </button>
      </div>

      {/* AI suggestion banner */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid ' + T.border, background: T.amber + '08', display: 'flex', alignItems: 'center', gap: 10 }}>
        <Bot style={{ width: 14, height: 14, color: T.amber, flexShrink: 0 }} />
        <span style={{ fontSize: 11, color: T.textSub }}>
          Sugerencia IA para tu negocio: &nbsp;
          {aiSuggested.map((t, i) => (
            <span key={t.id}>
              <button onClick={() => setSelected(t.id)} style={{ color: T.amber, fontWeight: 700, background: 'none', border: 'none', cursor: 'pointer', fontSize: 11 }}>{t.name}</button>
              {i < aiSuggested.length - 1 && <span style={{ color: T.textSub }}> · </span>}
            </span>
          ))}
          &nbsp;— generación en 1 click
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 0 }}>

        {/* Left: template library */}
        <div style={{ borderRight: '1px solid ' + T.border }}>
          {/* Filter bar */}
          <div style={{ padding: '10px 16px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <Filter style={{ width: 12, height: 12, color: T.textSub }} />
            {(['all', 'ventas', 'leads', 'finanzas', 'marketing', 'ops'] as const).map(cat => {
              const color = cat === 'all' ? T.textPrim : CAT_COLORS[cat as Category]
              const active = filterCat === cat
              return (
                <button key={cat} onClick={() => setFilterCat(cat)}
                  style={{ padding: '2px 10px', borderRadius: 4, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', cursor: 'pointer', background: active ? color + '22' : 'transparent', border: '1px solid ' + (active ? color + '55' : T.border), color: active ? color : T.textSub }}>
                  {cat === 'all' ? 'Todos' : cat}
                </button>
              )
            })}
          </div>

          <div style={{ padding: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {filtered.map(t => {
              const isSelected = selected === t.id
              return (
                <div key={t.id} onClick={() => setSelected(t.id)} style={{ background: isSelected ? t.color + '14' : T.bgApp, border: '1px solid ' + (isSelected ? t.color + '55' : T.border), borderRadius: 10, padding: 12, cursor: 'pointer', transition: 'all .15s', position: 'relative' }}>
                  {t.aiSuggested && (
                    <div style={{ position: 'absolute', top: 8, right: 8 }}>
                      <Sparkles style={{ width: 11, height: 11, color: T.amber }} />
                    </div>
                  )}
                  <div style={{ fontSize: 12, fontWeight: 700, color: t.color, marginBottom: 4 }}>{t.name}</div>
                  <div style={{ fontSize: 11, color: T.textSub, lineHeight: 1.4, marginBottom: 8 }}>{t.desc}</div>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'monospace', background: CAT_COLORS[t.category] + '18', border: '1px solid ' + CAT_COLORS[t.category] + '28', color: CAT_COLORS[t.category] }}>{t.category}</span>
                    {t.outputs.map(o => (
                      <span key={o} style={{ padding: '2px 6px', borderRadius: 4, fontSize: 9, fontFamily: 'monospace', background: T.border, color: T.textSub }}>{o}</span>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right: schedule + recipient + recent */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {/* Schedule picker */}
          <div style={{ padding: 16, borderBottom: '1px solid ' + T.border }}>
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Calendar style={{ width: 11, height: 11 }} /> Frecuencia
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {(['diario', 'semanal', 'mensual', 'manual'] as Schedule[]).map(s => (
                <button key={s} onClick={() => setSchedule(s)}
                  style={{ padding: '6px 0', borderRadius: 6, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.04em', textTransform: 'uppercase', cursor: 'pointer', background: schedule === s ? T.emerald + '22' : T.bgApp, border: '1px solid ' + (schedule === s ? T.emerald + '55' : T.border), color: schedule === s ? T.emerald : T.textSub }}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Recipient email */}
          <div style={{ padding: 16, borderBottom: '1px solid ' + T.border }}>
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Mail style={{ width: 11, height: 11 }} /> Destinatario
            </div>
            <input value={email} onChange={e => setEmail(e.target.value)}
              style={{ width: '100%', background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 6, padding: '7px 10px', fontSize: 12, color: T.textPrim, fontFamily: 'JetBrains Mono,monospace', outline: 'none', boxSizing: 'border-box' }} />
            <button style={{ marginTop: 8, width: '100%', padding: '8px 0', borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer', background: T.emerald + '22', border: '1px solid ' + T.emerald + '44', color: T.emerald, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
              <Clock style={{ width: 12, height: 12 }} /> Programar reporte
            </button>
          </div>

          {/* Recent reports */}
          <div style={{ padding: 16, flex: 1 }}>
            <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 10 }}>Generados recientemente</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {RECENT.map((r, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', borderRadius: 8, background: T.bgApp, border: '1px solid ' + T.border }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: r.color, boxShadow: '0 0 6px ' + r.color, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: T.textPrim, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.name}</div>
                    <div style={{ fontSize: 10, color: T.textSub }}>{r.date} · {r.size}</div>
                  </div>
                  <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: 9, fontFamily: 'monospace', background: r.color + '18', border: '1px solid ' + r.color + '28', color: r.color }}>{r.format}</span>
                  <button style={{ padding: 4, borderRadius: 6, background: 'transparent', border: 'none', cursor: 'pointer', color: T.textSub }}>
                    <Download style={{ width: 12, height: 12 }} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
