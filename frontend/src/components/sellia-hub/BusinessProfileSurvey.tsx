'use client'

/**
 * BUSINESS PROFILE SURVEY
 *
 * Encuesta completa de perfil de negocio — 5 pasos.
 * Versión standalone (inline card, no modal overlay).
 * Lee/escribe localStorage 'sellia_biz_ctx_v1'.
 * Compatible con useBrainData() hook en brain-metrics.ts.
 */

import { useState, useEffect } from 'react'
import {
  CheckCircle2, ChevronRight, ChevronLeft,
  Zap, Bot, Gamepad2, Save, RefreshCw,
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:      '#0B0F19',
  bgCard:     '#151B2B',
  bgCardHov:  '#1A2235',
  border:     '#2A3441',
  textPrim:   '#F3F4F6',
  textSub:    '#9CA3AF',
  violet:     '#8B5CF6',
  emerald:    '#10B981',
  amber:      '#F59E0B',
  cyan:       '#06B6D4',
  lime:       '#CCFF33',
  rose:       '#ef4444',
  glowViolet:  '0 0 22px rgba(139,92,246,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowLime:    '0 0 22px rgba(204,255,51,0.45)',
} as const

// ── Types ──────────────────────────────────────────────────────────────────────
type BizType = 'productos' | 'servicios' | 'ambos'
type Volume  = 'ninguna' | 'irregular' | '<50' | '50-200' | '200-1000' | '1000+'
type Strategy = 'manual' | 'ia'

interface BizCtx {
  businessName: string
  productDesc:  string
  bizType:      BizType
  channels:     string[]
  volume:       Volume
  goals:        string[]
  strategy:     Strategy
  activeTasks:  string[]
  running:      boolean
}

// ── Constants ─────────────────────────────────────────────────────────────────
const BIZ_KEY = 'sellia_biz_ctx_v1'
const TOTAL_STEPS = 5

const CHANNELS_LIST = [
  { id: 'whatsapp',     label: 'WhatsApp',         e: '💬' },
  { id: 'instagram',    label: 'Instagram',         e: '📸' },
  { id: 'facebook',     label: 'Facebook',          e: '👥' },
  { id: 'tiktok',       label: 'TikTok',            e: '🎵' },
  { id: 'youtube',      label: 'YouTube',           e: '▶️' },
  { id: 'linkedin',     label: 'LinkedIn',          e: '💼' },
  { id: 'x',            label: 'X / Twitter',       e: '🐦' },
  { id: 'telegram',     label: 'Telegram',          e: '✈️' },
  { id: 'meta',         label: 'Meta Ads',          e: '🎯' },
  { id: 'google',       label: 'Google Ads',        e: '🔍' },
  { id: 'email_list',   label: 'Email Marketing',   e: '📧' },
  { id: 'web',          label: 'Sitio Web',         e: '🌐' },
  { id: 'mercadolibre', label: 'Mercado Libre',     e: '🛒' },
  { id: 'tiendanube',   label: 'Tienda Nube',       e: '☁️' },
  { id: 'shopify',      label: 'Shopify',           e: '🏪' },
  { id: 'amazon',       label: 'Amazon',            e: '📦' },
  { id: 'hotmart',      label: 'Hotmart',           e: '🔥' },
  { id: 'etsy',         label: 'Etsy',              e: '🎨' },
  { id: 'fisica',       label: 'Tienda física',     e: '🏬' },
  { id: 'puerta',       label: 'Puerta a puerta',   e: '🚪' },
  { id: 'ferias',       label: 'Ferias / Eventos',  e: '🎪' },
  { id: 'telefono',     label: 'Teléfono / Call',   e: '📞' },
  { id: 'rappi',        label: 'Rappi / PedidosYa', e: '🛵' },
]

const GOALS_LIST = [
  { id: 'leads',         label: 'Conseguir más leads',              i: '🎯' },
  { id: 'conversion',    label: 'Convertir más ventas',             i: '💰' },
  { id: 'retention',     label: 'Retener y fidelizar clientes',     i: '♻️' },
  { id: 'branding',      label: 'Construir mi marca',               i: '🎨' },
  { id: 'content',       label: 'Crear contenido de ventas',        i: '📱' },
  { id: 'automate',      label: 'Automatizar tareas repetitivas',   i: '🤖' },
  { id: 'costs',         label: 'Reducir costos operativos',        i: '⚡' },
  { id: 'scale',         label: 'Escalar el negocio',               i: '🚀' },
  { id: 'recurring',     label: 'Crear ingresos recurrentes',       i: '♾️' },
  { id: 'international', label: 'Llegar a otros países',            i: '🌍' },
]

const VOLUME_OPTIONS: [Volume, string, string][] = [
  ['ninguna',   'No tuve ventas todavía',                          '🌱'],
  ['irregular', 'Ventas irregulares (algunos meses sí, otros no)', '🌊'],
  ['<50',       'Hasta 50 ventas/mes',                             '📈'],
  ['50-200',    '50 a 200 ventas/mes',                             '🔥'],
  ['200-1000',  '200 a 1.000 ventas/mes',                         '⚡'],
  ['1000+',     'Más de 1.000 ventas/mes',                         '🚀'],
]

// ── Helpers ────────────────────────────────────────────────────────────────────
const loadCtx = (): BizCtx | null => {
  try {
    const s = localStorage.getItem(BIZ_KEY)
    return s ? (JSON.parse(s) as BizCtx) : null
  } catch { return null }
}

const saveCtx = (ctx: BizCtx): void => {
  try { localStorage.setItem(BIZ_KEY, JSON.stringify(ctx)) } catch { /* noop */ }
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function BusinessProfileSurvey(): React.JSX.Element {
  const [step, setStep]         = useState(0)
  const [name, setName]         = useState('')
  const [bizType, setBizType]   = useState<BizType>('productos')
  const [productDesc, setDesc]  = useState('')
  const [channels, setChannels] = useState<string[]>([])
  const [volume, setVolume]     = useState<Volume>('50-200')
  const [goals, setGoals]       = useState<string[]>([])
  const [strategy, setStrategy] = useState<Strategy>('ia')
  const [saved, setSaved]       = useState(false)
  const [hasExisting, setHasExisting] = useState(false)

  // Pre-fill from existing localStorage data
  useEffect(() => {
    const ctx = loadCtx()
    if (ctx) {
      setName(ctx.businessName)
      setBizType(ctx.bizType)
      setDesc(ctx.productDesc ?? '')
      setChannels(ctx.channels)
      setVolume(ctx.volume)
      setGoals(ctx.goals)
      setStrategy(ctx.strategy ?? 'ia')
      setHasExisting(true)
    }
  }, [])

  const toggleChannel = (id: string): void =>
    setChannels(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])

  const toggleGoal = (id: string): void =>
    setGoals(p => p.includes(id) ? p.filter(x => x !== id) : [...p, id])

  const handleSave = (strat: Strategy): void => {
    const existing = loadCtx()
    const ctx: BizCtx = {
      businessName: name.trim() || 'Mi negocio',
      productDesc:  productDesc.trim(),
      bizType,
      channels,
      volume,
      goals,
      strategy: strat,
      activeTasks: existing?.activeTasks ?? [],
      running:     existing?.running ?? false,
    }
    saveCtx(ctx)
    setStrategy(strat)
    setSaved(true)
  }

  const handleReset = (): void => {
    setSaved(false)
    setStep(0)
  }

  // ── Shared styles ─────────────────────────────────────────────────────────
  const btnBase: React.CSSProperties = {
    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
    padding: '11px 22px', borderRadius: 10, fontWeight: 700, fontSize: 14,
    cursor: 'pointer', border: 'none', transition: 'opacity .15s',
  }

  const chipActive = (col: string): React.CSSProperties => ({
    padding: '7px 13px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
    border: `1px solid ${col}`, background: `${col}22`, color: col, transition: 'all .12s',
  })

  const chipInactive = (col: string): React.CSSProperties => ({
    padding: '7px 13px', borderRadius: 20, fontSize: 13, fontWeight: 600, cursor: 'pointer',
    border: `1px solid ${col}40`, background: `${col}08`, color: T.textSub, transition: 'all .12s',
  })

  // ── Saved state ─────────────────────────────────────────────────────────
  if (saved) {
    return (
      <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.emerald}80, transparent)` }} />
        <div style={{ padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, textAlign: 'center' }}>
          <div style={{ width: 56, height: 56, borderRadius: 28, background: `${T.emerald}18`, border: `1px solid ${T.emerald}40`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CheckCircle2 size={28} style={{ color: T.emerald }} />
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", textShadow: `0 0 20px ${T.emerald}88` }}>
              ¡Perfil guardado!
            </div>
            <div style={{ fontSize: 13, color: T.textSub, marginTop: 6 }}>
              SellIA usará estos datos para personalizar todos los módulos y agentes.
            </div>
          </div>

          {/* Summary chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
            <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', background: `${T.cyan}15`, border: `1px solid ${T.cyan}30`, color: T.cyan }}>
              {name.trim() || 'Mi negocio'}
            </span>
            <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', background: `${T.violet}15`, border: `1px solid ${T.violet}30`, color: T.violet }}>
              {bizType}
            </span>
            <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', background: `${T.amber}15`, border: `1px solid ${T.amber}30`, color: T.amber }}>
              {channels.length} canales
            </span>
            <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', background: `${T.emerald}15`, border: `1px solid ${T.emerald}30`, color: T.emerald }}>
              {volume}
            </span>
            <span style={{ padding: '4px 12px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', background: `${T.rose}15`, border: `1px solid ${T.rose}30`, color: T.rose }}>
              {goals.length} metas
            </span>
          </div>

          <button type="button" onClick={handleReset}
            style={{ ...btnBase, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet }}>
            <RefreshCw size={14} /> Editar perfil
          </button>
        </div>
      </section>
    )
  }

  // ── Progress bar ────────────────────────────────────────────────────────
  const progress = ((step + 1) / TOTAL_STEPS) * 100

  return (
    <section style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: `linear-gradient(90deg, transparent, ${T.violet}80, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '18px 22px 14px', borderBottom: `1px solid ${T.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: `${T.violet}22`, border: `1px solid ${T.violet}44`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={17} style={{ color: T.violet }} />
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif" }}>
                Perfil de Negocio
              </div>
              <div style={{ fontSize: 10, color: T.textSub, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', marginTop: 1 }}>
                {hasExisting ? 'Editando perfil existente' : 'Configuración inicial'} · Paso {step + 1}/{TOTAL_STEPS}
              </div>
            </div>
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, color: T.violet, fontFamily: 'JetBrains Mono,monospace', textShadow: T.glowViolet }}>
            {Math.round(progress)}%
          </div>
        </div>

        {/* Progress dots */}
        <div style={{ display: 'flex', gap: 5 }}>
          {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
            <div key={i} style={{
              flex: 1, height: 3, borderRadius: 2,
              background: i <= step ? T.violet : `${T.border}`,
              transition: 'background .3s',
            }} />
          ))}
        </div>
      </div>

      {/* Step content */}
      <div style={{ padding: '22px 22px 18px' }}>

        {/* ── STEP 0 — Negocio ── */}
        {step === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 4 }}>
                ¡Hola! Soy SellIA 👋
              </div>
              <div style={{ fontSize: 13, color: T.textSub }}>
                Contame sobre tu negocio y voy a trabajar 24/7 para vos.
              </div>
            </div>

            {/* Nombre */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: T.textSub, marginBottom: 6, letterSpacing: '.06em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono,monospace' }}>
                Nombre de tu negocio
              </div>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="ej: TechStore, Estudio Diseño, Ferretería López…"
                style={{ width: '100%', padding: '11px 13px', background: `${T.border}22`, border: `1px solid ${T.border}`, borderRadius: 10, color: T.textPrim, fontSize: 14, outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit' }}
              />
            </div>

            {/* Tipo */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: T.textSub, marginBottom: 8, letterSpacing: '.06em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono,monospace' }}>
                ¿Qué tipo de negocio?
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {(['productos', 'servicios', 'ambos'] as BizType[]).map(t => (
                  <button key={t} type="button" onClick={() => setBizType(t)}
                    style={bizType === t ? chipActive(T.cyan) : chipInactive(T.cyan)}>
                    {t === 'productos' ? '📦' : t === 'servicios' ? '⚙️' : '🔀'} {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Descripción */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: T.textSub, marginBottom: 6, letterSpacing: '.06em', textTransform: 'uppercase', fontFamily: 'JetBrains Mono,monospace' }}>
                ¿Qué ofrecés exactamente?
              </div>
              <div style={{ fontSize: 12, color: T.textSub, marginBottom: 6 }}>
                {bizType === 'productos'
                  ? 'Describí tus productos: qué son, para quién, precio aprox.'
                  : bizType === 'servicios'
                    ? 'Describí tu servicio: qué hacés, para quién, cómo entregás.'
                    : 'Describí todo lo que vendés: productos Y servicios.'}
              </div>
              <textarea
                value={productDesc}
                onChange={e => setDesc(e.target.value)}
                rows={3}
                placeholder={
                  bizType === 'productos'
                    ? 'ej: Ropa deportiva para mujeres 18-35 años. Zapatillas running premium $120-$280. También accesorios gym…'
                    : bizType === 'servicios'
                      ? 'ej: Consultoría contable para pymes. Liquidación IVA, sueldos, balances. Clientes en Argentina y Uruguay…'
                      : 'ej: Cursos online de marketing digital ($97-$497) + consultoría 1 a 1 para emprendedores y agencias…'
                }
                style={{ width: '100%', padding: '11px 13px', background: `${T.border}22`, border: `1px solid ${T.border}`, borderRadius: 10, color: T.textPrim, fontSize: 13, outline: 'none', resize: 'vertical', boxSizing: 'border-box', lineHeight: 1.5, fontFamily: 'inherit' }}
              />
            </div>

            <button type="button" onClick={() => setStep(1)}
              style={{ ...btnBase, background: T.lime, color: '#050910' }}>
              Siguiente <ChevronRight size={15} />
            </button>
          </div>
        )}

        {/* ── STEP 1 — Canales ── */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 4 }}>
                ¿Dónde vendés? 🛒
              </div>
              <div style={{ fontSize: 13, color: T.textSub }}>
                Seleccioná todos los que usás o querés usar. Podés agregar más después.
              </div>
            </div>

            <div style={{ maxHeight: 260, overflowY: 'auto', display: 'flex', flexWrap: 'wrap', gap: 7, paddingRight: 4 }}>
              {CHANNELS_LIST.map(c => (
                <button key={c.id} type="button" onClick={() => toggleChannel(c.id)}
                  style={channels.includes(c.id) ? chipActive(T.violet) : chipInactive(T.violet)}>
                  {c.e} {c.label}
                </button>
              ))}
            </div>

            {channels.length > 0 && (
              <div style={{ fontSize: 12, color: T.lime, fontFamily: 'JetBrains Mono,monospace' }}>
                ✓ {channels.length} canal{channels.length !== 1 ? 'es' : ''} seleccionado{channels.length !== 1 ? 's' : ''}
              </div>
            )}

            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" onClick={() => setStep(0)}
                style={{ ...btnBase, flex: 1, background: `${T.border}44`, color: T.textSub, border: `1px solid ${T.border}` }}>
                <ChevronLeft size={14} /> Atrás
              </button>
              <button type="button" onClick={() => setStep(2)} disabled={channels.length === 0}
                style={{ ...btnBase, flex: 2, background: channels.length > 0 ? T.lime : `${T.border}44`, color: channels.length > 0 ? '#050910' : T.textSub, opacity: channels.length === 0 ? 0.5 : 1 }}>
                Siguiente <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 2 — Volumen ── */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 4 }}>
                ¿Cuánto vendés? 📊
              </div>
              <div style={{ fontSize: 13, color: T.textSub }}>
                Volumen mensual aproximado — si es variable, elegí la opción más cercana
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {VOLUME_OPTIONS.map(([v, label, emoji]) => (
                <button key={v} type="button" onClick={() => setVolume(v)}
                  style={{
                    padding: '12px 16px', borderRadius: 12, textAlign: 'left', cursor: 'pointer',
                    fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 12,
                    border: `1px solid ${volume === v ? T.emerald : `${T.emerald}30`}`,
                    background: volume === v ? `${T.emerald}16` : 'transparent',
                    color: volume === v ? T.textPrim : T.textSub,
                  }}>
                  <span style={{ fontSize: 18 }}>{emoji}</span>
                  {label}
                  {volume === v && <span style={{ marginLeft: 'auto', color: T.emerald, textShadow: T.glowEmerald }}>✓</span>}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" onClick={() => setStep(1)}
                style={{ ...btnBase, flex: 1, background: `${T.border}44`, color: T.textSub, border: `1px solid ${T.border}` }}>
                <ChevronLeft size={14} /> Atrás
              </button>
              <button type="button" onClick={() => setStep(3)}
                style={{ ...btnBase, flex: 2, background: T.lime, color: '#050910' }}>
                Siguiente <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 3 — Metas ── */}
        {step === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 4 }}>
                ¿Cuáles son tus metas? 🎯
              </div>
              <div style={{ fontSize: 13, color: T.textSub }}>
                Elegí todas las que aplican — SellIA priorizará en base a esto
              </div>
            </div>

            <div style={{ maxHeight: 300, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6, paddingRight: 4 }}>
              {GOALS_LIST.map(g => (
                <button key={g.id} type="button" onClick={() => toggleGoal(g.id)}
                  style={{
                    padding: '11px 16px', borderRadius: 12, textAlign: 'left', cursor: 'pointer',
                    fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 12,
                    border: `1px solid ${goals.includes(g.id) ? T.amber : `${T.amber}30`}`,
                    background: goals.includes(g.id) ? `${T.amber}14` : 'transparent',
                    color: goals.includes(g.id) ? T.textPrim : T.textSub,
                  }}>
                  <span style={{ fontSize: 17 }}>{g.i}</span>
                  {g.label}
                  {goals.includes(g.id) && <span style={{ marginLeft: 'auto', color: T.amber, textShadow: T.glowEmerald }}>✓</span>}
                </button>
              ))}
            </div>

            {goals.length > 0 && (
              <div style={{ fontSize: 12, color: T.lime, fontFamily: 'JetBrains Mono,monospace' }}>
                ✓ {goals.length} meta{goals.length !== 1 ? 's' : ''} seleccionada{goals.length !== 1 ? 's' : ''}
              </div>
            )}

            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" onClick={() => setStep(2)}
                style={{ ...btnBase, flex: 1, background: `${T.border}44`, color: T.textSub, border: `1px solid ${T.border}` }}>
                <ChevronLeft size={14} /> Atrás
              </button>
              <button type="button" onClick={() => setStep(4)} disabled={goals.length === 0}
                style={{ ...btnBase, flex: 2, background: goals.length > 0 ? T.lime : `${T.border}44`, color: goals.length > 0 ? '#050910' : T.textSub, opacity: goals.length === 0 ? 0.5 : 1 }}>
                Siguiente <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 4 — Estrategia ── */}
        {step === 4 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: T.textPrim, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 4 }}>
                ¿Cómo querés operar? 🤖
              </div>
              <div style={{ fontSize: 13, color: T.textSub }}>
                Podés cambiar esto en cualquier momento desde el panel
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {/* IA option */}
              <button type="button" onClick={() => handleSave('ia')}
                style={{ padding: 20, borderRadius: 14, textAlign: 'left', cursor: 'pointer', border: `1px solid ${T.lime}50`, background: `${T.lime}10`, color: T.textPrim, width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <Bot size={24} style={{ color: T.lime }} />
                  <div style={{ fontSize: 15, fontWeight: 700, color: T.lime, textShadow: T.glowLime }}>Dejar todo a la IA</div>
                </div>
                <div style={{ fontSize: 13, color: T.textSub, lineHeight: 1.5 }}>
                  SellIA activa y gestiona todo automáticamente. La mejor opción para maximizar resultados sin esfuerzo.
                </div>
              </button>

              {/* Manual option */}
              <button type="button" onClick={() => handleSave('manual')}
                style={{ padding: 20, borderRadius: 14, textAlign: 'left', cursor: 'pointer', border: `1px solid ${T.border}`, background: 'rgba(255,255,255,0.04)', color: T.textPrim, width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <Gamepad2 size={24} style={{ color: T.textSub }} />
                  <div style={{ fontSize: 15, fontWeight: 700, color: T.textPrim }}>Quiero decidir yo</div>
                </div>
                <div style={{ fontSize: 13, color: T.textSub, lineHeight: 1.5 }}>
                  Revisás y aprobás cada proceso antes de que SellIA actúe. Control total.
                </div>
              </button>
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button type="button" onClick={() => setStep(3)}
                style={{ ...btnBase, flex: 1, background: `${T.border}44`, color: T.textSub, border: `1px solid ${T.border}` }}>
                <ChevronLeft size={14} /> Atrás
              </button>
              <button type="button" onClick={() => handleSave(strategy)}
                style={{ ...btnBase, flex: 1, background: `${T.violet}18`, border: `1px solid ${T.violet}40`, color: T.violet }}>
                <Save size={14} /> Guardar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer info */}
      <div style={{ padding: '12px 22px', borderTop: `1px solid ${T.border}`, background: `${T.bgApp}80` }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Zap size={11} style={{ color: T.violet }} />
          <span style={{ fontSize: 11, color: T.textSub, fontFamily: 'JetBrains Mono,monospace' }}>
            Datos guardados en tu dispositivo · alimentan todos los módulos de SellIA
          </span>
        </div>
      </div>
    </section>
  )
}
