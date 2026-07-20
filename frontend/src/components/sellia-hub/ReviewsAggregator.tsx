'use client'

/**
 * REVIEWS AGGREGATOR
 *
 * Multi-source: Google · Trustpilot · Amazon · ML · IG · TikTok.
 * IA responde · clasifica sentiment · alertas críticas.
 */

import { useMemo, useState } from 'react'
import { Star, Filter, Bot, CheckCircle2, TrendingUp } from 'lucide-react'

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

interface Review {
  id: string
  source: string
  sourceEmoji: string
  sourceColor: string
  author: string
  rating: number
  text: string
  ts: string
  sentiment: 'positive' | 'neutral' | 'negative'
  responded: boolean
  aiResponse?: string
  flagged?: boolean
}

const REVIEWS: Review[] = [
  { id: 'r1', source: 'Google Business',  sourceEmoji: '🔵', sourceColor: '#4285F4', author: 'María L.',    rating: 5, text: '¡Excelente atención! El producto llegó perfecto y el seguimiento fue impecable. Volveré a comprar.', ts: 'hace 2h',     sentiment: 'positive', responded: true,  aiResponse: 'Gracias María! Nos alegra que la experiencia haya sido excelente · te enviamos cupón sorpresa.' },
  { id: 'r2', source: 'Trustpilot',        sourceEmoji: '⭐', sourceColor: '#00B67A', author: 'Tomás N.',    rating: 5, text: 'Mejor servicio que he probado en años. La IA respondió mi consulta en segundos.', ts: 'hace 5h',    sentiment: 'positive', responded: true,  aiResponse: 'Tomás, gracias por la confianza · te activamos programa Embajador con comisión 20%.' },
  { id: 'r3', source: 'Mercado Libre',     sourceEmoji: '🟡', sourceColor: '#FFE600', author: 'Pedro K.',     rating: 2, text: 'Llegó con demora de 12 días. La caja estaba abollada. No esperaba esto.', ts: 'hace 1 día',   sentiment: 'negative', responded: true,  aiResponse: 'Pedro, lamentamos la demora · ya tenemos tu refund parcial + envío gratis en próx compra. Equipo logística reasignado.', flagged: true },
  { id: 'r4', source: 'Amazon',             sourceEmoji: '📦', sourceColor: '#FF9900', author: 'CarlosR',      rating: 4, text: 'Buen producto pero el manual viene solo en inglés. Lo demás todo bien.', ts: 'hace 2 días', sentiment: 'neutral',  responded: true,  aiResponse: 'Carlos, gracias · te mandamos manual en español por email · feedback escalado al equipo producto.' },
  { id: 'r5', source: 'Instagram',          sourceEmoji: '📷', sourceColor: '#E1306C', author: '@anitas_arg',  rating: 5, text: 'Mejor pack que probé · 10/10 calidad-precio · super recomendable!', ts: 'hace 3 días', sentiment: 'positive', responded: true,  aiResponse: 'Gracias Ana ❤️ · te invitamos a unirte a nuestro programa creators.' },
  { id: 'r6', source: 'TikTok',             sourceEmoji: '🎵', sourceColor: '#FF0050', author: '@lucia.shops', rating: 5, text: 'Hicieron mi setup en 24h · increíble el servicio · subo video pronto', ts: 'hace 3 días', sentiment: 'positive', responded: false, aiResponse: 'Pendiente · IA generó respuesta · aprobación humana sugerida' },
  { id: 'r7', source: 'Google Business',    sourceEmoji: '🔵', sourceColor: '#4285F4', author: 'Anónimo',      rating: 1, text: 'Pésimo · me cobraron 2 veces y no responden.', ts: 'hace 4h',      sentiment: 'negative', responded: false, aiResponse: 'CRÍTICO · IA investigó · doble cobro detectado en Stripe · refund procesando · respuesta lista para aprobación', flagged: true },
  { id: 'r8', source: 'Trustpilot',          sourceEmoji: '⭐', sourceColor: '#00B67A', author: 'Mariana P.',   rating: 4, text: 'Producto muy bueno. La app podría ser más rápida.', ts: 'hace 5 días', sentiment: 'positive', responded: true,  aiResponse: 'Mariana gracias · update performance en próx release · te avisamos cuando salga.' },
]

const SENTIMENT_CONFIG = {
  positive: { color: T.emerald, emoji: '😊' },
  neutral:  { color: T.amber,   emoji: '😐' },
  negative: { color: T.rose,    emoji: '😟' },
} as const

type FilterType = 'all' | 'positive' | 'neutral' | 'negative' | 'unresponded'

export default function ReviewsAggregator() {
  const [filter, setFilter] = useState<FilterType>('all')

  const filtered = useMemo(() => {
    if (filter === 'all') return REVIEWS
    if (filter === 'unresponded') return REVIEWS.filter(r => !r.responded)
    return REVIEWS.filter(r => r.sentiment === filter)
  }, [filter])

  const stats = useMemo(() => {
    const total = REVIEWS.length
    const avg = REVIEWS.reduce((s, r) => s + r.rating, 0) / total
    const sentimentBreakdown = {
      positive: REVIEWS.filter(r => r.sentiment === 'positive').length,
      neutral:  REVIEWS.filter(r => r.sentiment === 'neutral').length,
      negative: REVIEWS.filter(r => r.sentiment === 'negative').length,
    }
    const unresponded = REVIEWS.filter(r => !r.responded).length
    const flagged     = REVIEWS.filter(r => r.flagged).length
    return { total, avg, sentimentBreakdown, unresponded, flagged }
  }, [])

  const PLATFORMS = [
    { name: 'Google',      emoji: '🔵', color: '#4285F4', rating: 4.7, count: 312 },
    { name: 'Trustpilot',  emoji: '⭐', color: '#00B67A', rating: 4.5, count: 98 },
    { name: 'Merc. Libre', emoji: '🟡', color: '#FFE600', rating: 4.3, count: 245 },
    { name: 'App Store',   emoji: '📱', color: '#007AFF', rating: 4.6, count: 67 },
  ]

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      {/* Top accent */}
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, ' + T.amber + '80, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.amber + '22', border: '1px solid ' + T.amber + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Star size={18} style={{ color: T.amber }} />
          </div>
          <div>
            <h2 style={{ fontSize: 13, fontWeight: 900, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase', margin: 0 }}>
              REVIEWS AGGREGATOR <span style={{ color: T.textSub, fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>· Google · Trustpilot · ML · IG</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>
              {stats.total} reviews · <span style={{ color: T.amber, fontWeight: 700 }}>{stats.unresponded}</span> sin responder · <span style={{ color: T.rose }}>{stats.flagged}</span> críticos
            </p>
          </div>
        </div>
        {/* Aggregate rating */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {[1,2,3,4,5].map(s => (
              <Star key={s} size={14} style={{ color: s <= Math.round(stats.avg) ? T.amber : T.border, fill: s <= Math.round(stats.avg) ? T.amber : 'transparent' }} />
            ))}
          </div>
          <p style={{ fontSize: 22, fontWeight: 900, color: T.amber, fontVariantNumeric: 'tabular-nums', textShadow: T.glowAmber }}>{stats.avg.toFixed(2)}</p>
          <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub }}>rating global</p>
        </div>
      </div>

      {/* Platform breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', borderBottom: '1px solid ' + T.border }}>
        {PLATFORMS.map(p => (
          <div key={p.name} style={{ padding: '12px 16px', borderRight: '1px solid ' + T.border, textAlign: 'center' }}>
            <span style={{ fontSize: 20, display: 'block', marginBottom: 4 }}>{p.emoji}</span>
            <p style={{ fontSize: 16, fontWeight: 900, color: p.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 16px ' + p.color + '88', marginBottom: 2 }}>{p.rating}</p>
            <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', textTransform: 'uppercase', color: T.textSub }}>{p.name}</p>
            <p style={{ fontSize: 9, color: T.textSub }}>{p.count} reseñas</p>
          </div>
        ))}
      </div>

      {/* Sentiment breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', borderBottom: '1px solid ' + T.border }}>
        {(['positive', 'neutral', 'negative'] as const).map(s => {
          const cfg = SENTIMENT_CONFIG[s]
          const count = stats.sentimentBreakdown[s]
          const pct = Math.round((count / stats.total) * 100)
          return (
            <div key={s} style={{ padding: 12, borderRight: '1px solid ' + T.border }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 16 }}>{cfg.emoji}</span>
                <p style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{s}</p>
              </div>
              <p style={{ fontSize: 20, fontWeight: 900, color: cfg.color, fontVariantNumeric: 'tabular-nums', textShadow: '0 0 16px ' + cfg.color + '88', marginBottom: 4 }}>
                {count} <span style={{ fontSize: 13, color: T.textSub }}>· {pct}%</span>
              </p>
              <div style={{ height: 4, background: T.border, borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: cfg.color, width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Filters */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter size={12} style={{ color: T.textSub }} />
        {(['all', 'positive', 'neutral', 'negative', 'unresponded'] as const).map(f => {
          const active = filter === f
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                fontSize: 9, padding: '2px 8px', borderRadius: 99, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer',
                background: active ? 'rgba(255,255,255,0.12)' : T.bgApp,
                border: '1px solid ' + (active ? 'rgba(255,255,255,0.25)' : T.border),
                color: active ? T.textPrim : T.textSub,
              }}
            >{f}</button>
          )
        })}
      </div>

      {/* Reviews list */}
      <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 500, overflowY: 'auto' }}>
        {filtered.map(r => {
          const sentiment = SENTIMENT_CONFIG[r.sentiment]
          return (
            <div
              key={r.id}
              style={{ borderRadius: 12, overflow: 'hidden', background: r.flagged ? T.rose + '06' : T.bgApp, border: '1px solid ' + (r.flagged ? T.rose + '28' : T.border) }}
            >
              {/* Source accent line */}
              <div style={{ height: 2, background: 'linear-gradient(90deg, ' + r.sourceColor + ', transparent)' }} />

              <div style={{ padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                {/* Source icon + rating */}
                <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 22 }}>{r.sourceEmoji}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {[1,2,3,4,5].map(s => (
                      <Star key={s} size={8} style={{ color: s <= r.rating ? T.amber : T.border, fill: s <= r.rating ? T.amber : 'transparent' }} />
                    ))}
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 900, color: T.amber, fontVariantNumeric: 'tabular-nums' }}>{r.rating}.0</span>
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Header */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{r.author}</p>
                      <span style={{ fontSize: 8, padding: '2px 6px', borderRadius: 4, fontWeight: 700, textTransform: 'uppercase', background: r.sourceColor + '18', color: r.sourceColor, border: '1px solid ' + r.sourceColor + '30' }}>{r.source}</span>
                      <span style={{ fontSize: 13 }}>{sentiment.emoji}</span>
                      {r.flagged && (
                        <span className="animate-pulse" style={{ fontSize: 8, padding: '2px 6px', borderRadius: 4, fontWeight: 700, textTransform: 'uppercase', background: T.rose + '20', color: T.rose, border: '1px solid ' + T.rose + '30' }}>🚨 CRÍTICO</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                      {r.responded
                        ? <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: T.emerald + '15', color: T.emerald, border: '1px solid ' + T.emerald + '28' }}>
                            <CheckCircle2 size={8} />Respondido
                          </span>
                        : <span style={{ fontSize: 8, fontWeight: 700, padding: '2px 6px', borderRadius: 4, background: T.amber + '15', color: T.amber, border: '1px solid ' + T.amber + '28' }}>Pendiente</span>
                      }
                      <span style={{ fontSize: 9, color: T.textSub }}>{r.ts}</span>
                    </div>
                  </div>

                  {/* Review text */}
                  <p style={{ fontSize: 12, color: T.textPrim, fontStyle: 'italic', lineHeight: 1.5, marginBottom: 8 }}>"{r.text}"</p>

                  {/* AI response */}
                  {r.aiResponse && (
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: '10px 12px', borderRadius: 10, background: T.violet + '08', border: '1px solid ' + T.violet + '22' }}>
                      <Bot size={13} style={{ color: T.violet, flexShrink: 0, marginTop: 1 }} />
                      <p style={{ fontSize: 11, color: T.violet, lineHeight: 1.4, flex: 1 }}>{r.aiResponse}</p>
                      {!r.responded && (
                        <button style={{ flexShrink: 0, padding: '4px 10px', borderRadius: 6, background: T.violet + '20', border: '1px solid ' + T.violet + '40', color: T.violet, fontSize: 9, fontWeight: 700, cursor: 'pointer' }}>
                          Aprobar
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer AI insight */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid ' + T.border, background: T.bgApp, display: 'flex', alignItems: 'center', gap: 8 }}>
        <TrendingUp size={13} style={{ color: T.emerald }} />
        <span style={{ fontSize: 11, color: T.textSub }}>
          IA respondió <span style={{ color: T.emerald, fontWeight: 700 }}>100%</span> de reviews en menos de 2min · satisfacción post-respuesta <span style={{ color: T.emerald, fontWeight: 700, textShadow: '0 0 14px ' + T.emerald + '88' }}>+34%</span>
        </span>
      </div>
    </section>
  )
}
