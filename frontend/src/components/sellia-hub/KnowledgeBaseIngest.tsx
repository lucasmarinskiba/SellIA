'use client'

/**
 * KNOWLEDGE BASE INGEST
 *
 * User sube docs (PDF · web · sheets · video transcripts) · IA aprende biz.
 * Vector embeddings → RAG queries · self-improving knowledge over time.
 */

import { useState, useMemo } from 'react'
import {
  BookOpen, FileText, Globe, FileSpreadsheet, Video, Mic, Plus,
  Sparkles, CheckCircle2, RefreshCw, Bot, Filter
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

type DocKind = 'pdf' | 'web' | 'sheet' | 'video' | 'audio' | 'doc' | 'image'
type IngestStatus = 'queued' | 'processing' | 'indexed' | 'failed'

interface Doc {
  id: string
  emoji: string
  name: string
  kind: DocKind
  size: string
  pages: number
  chunks: number
  embeddings: number
  status: IngestStatus
  ingestedAt: string
  queriesAgainst: number
  topic: string
}

const DOCS: Doc[] = [
  { id: 'd1',  emoji: '📕', name: 'Manual de producto · Pack Premium.pdf',         kind: 'pdf',    size: '4.2 MB', pages: 47,  chunks: 184, embeddings: 184,  status: 'indexed',    ingestedAt: 'Hace 12 días', queriesAgainst: 847, topic: 'producto' },
  { id: 'd2',  emoji: '🌐', name: 'https://tudominio.com/faq',                      kind: 'web',    size: '180 KB', pages: 1,   chunks: 47,  embeddings: 47,   status: 'indexed',    ingestedAt: 'Hace 8 días',  queriesAgainst: 1247,topic: 'FAQ' },
  { id: 'd3',  emoji: '📊', name: 'Pricing matrix 2025.xlsx',                       kind: 'sheet',  size: '218 KB', pages: 4,   chunks: 28,  embeddings: 28,   status: 'indexed',    ingestedAt: 'Hace 5 días',  queriesAgainst: 412, topic: 'pricing' },
  { id: 'd4',  emoji: '🎬', name: 'Demo producto v3 · YouTube.com',                  kind: 'video',  size: '12 min', pages: 1,   chunks: 78,  embeddings: 78,   status: 'indexed',    ingestedAt: 'Hace 3 días',  queriesAgainst: 234, topic: 'demo' },
  { id: 'd5',  emoji: '📞', name: 'Llamadas cierre Q1 · transcripts',                 kind: 'audio',  size: '4.7 h',  pages: 23,  chunks: 412, embeddings: 412,  status: 'indexed',    ingestedAt: 'Hace 1 día',   queriesAgainst: 89,  topic: 'sales calls' },
  { id: 'd6',  emoji: '📋', name: 'Políticas devolución v2.docx',                   kind: 'doc',    size: '98 KB',  pages: 8,   chunks: 24,  embeddings: 24,   status: 'indexed',    ingestedAt: 'Hace 4 días',  queriesAgainst: 142, topic: 'políticas' },
  { id: 'd7',  emoji: '🌐', name: 'Términos legales.pdf',                            kind: 'pdf',    size: '212 KB', pages: 12,  chunks: 41,  embeddings: 0,    status: 'processing', ingestedAt: 'hace 4min',     queriesAgainst: 0,   topic: 'legal' },
  { id: 'd8',  emoji: '🖼', name: 'Catálogo otoño-invierno.jpg (×24)',               kind: 'image',  size: '18 MB',  pages: 24,  chunks: 24,  embeddings: 24,   status: 'indexed',    ingestedAt: 'Hace 7 días',  queriesAgainst: 187, topic: 'catálogo' },
  { id: 'd9',  emoji: '📕', name: 'Onboarding Guide v4.pdf',                         kind: 'pdf',    size: '8.1 MB', pages: 84,  chunks: 0,   embeddings: 0,    status: 'queued',     ingestedAt: 'pendiente',     queriesAgainst: 0,   topic: 'onboarding' },
]

const KIND_CONFIG: Record<DocKind, { color: string; icon: React.ElementType; label: string }> = {
  pdf:    { color: '#ef4444', icon: FileText,        label: 'PDF' },
  web:    { color: '#06b6d4', icon: Globe,           label: 'Web' },
  sheet:  { color: '#22c55e', icon: FileSpreadsheet, label: 'Sheet' },
  video:  { color: '#a855f7', icon: Video,           label: 'Video' },
  audio:  { color: '#fbbf24', icon: Mic,             label: 'Audio' },
  doc:    { color: '#3b82f6', icon: FileText,        label: 'Doc' },
  image:  { color: '#ec4899', icon: FileText,        label: 'Image' },
}

const STATUS_CONFIG: Record<IngestStatus, { color: string; label: string }> = {
  queued:     { color: '#94a3b8', label: 'QUEUED' },
  processing: { color: '#3b82f6', label: 'PROCESSING' },
  indexed:    { color: '#22c55e', label: 'INDEXED' },
  failed:     { color: '#ef4444', label: 'FAILED' },
}

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function KnowledgeBaseIngest() {
  const [filter, setFilter] = useState<DocKind | 'all'>('all')

  const filtered = useMemo(() => filter === 'all' ? DOCS : DOCS.filter(d => d.kind === filter), [filter])

  const stats = useMemo(() => ({
    docs: DOCS.length,
    chunks: DOCS.reduce((s, d) => s + d.chunks, 0),
    embeddings: DOCS.reduce((s, d) => s + d.embeddings, 0),
    queries: DOCS.reduce((s, d) => s + d.queriesAgainst, 0),
  }), [])

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, ${T.cyan}, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(6,182,212,0.12)', border: `1px solid rgba(6,182,212,0.30)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <BookOpen style={{ width: 20, height: 20, color: T.cyan, filter: `drop-shadow(0 0 8px rgba(6,182,212,0.6))` }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              KNOWLEDGE <span style={{ color: T.cyan }}>BASE</span>
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· IA aprende tu negocio · RAG</span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>
              {stats.docs} docs · {stats.chunks} chunks · {stats.embeddings} embeddings · <span style={{ color: T.emerald, fontWeight: 700 }}>{stats.queries} queries</span>
            </p>
          </div>
        </div>
        <button style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px', borderRadius: 999, background: 'rgba(6,182,212,0.12)', border: `1px solid rgba(6,182,212,0.35)`, color: T.cyan, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
          <Plus style={{ width: 14, height: 14 }} /> Subir documento
        </button>
      </div>

      {/* Filter chips */}
      <div style={{ padding: '12px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub }} />
        <button onClick={() => setFilter('all')}
          style={{
            fontSize: 10, padding: '4px 10px', borderRadius: 999, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer',
            background: filter === 'all' ? 'rgba(255,255,255,0.10)' : T.bgCard,
            border: filter === 'all' ? '1px solid rgba(255,255,255,0.20)' : `1px solid ${T.border}`,
            color: filter === 'all' ? T.textPrim : T.textSub,
          }}>
          Todos · {DOCS.length}
        </button>
        {(Object.keys(KIND_CONFIG) as DocKind[]).map(k => {
          const cfg = KIND_CONFIG[k]
          const Icon = cfg.icon
          const count = DOCS.filter(d => d.kind === k).length
          const active = filter === k
          return (
            <button key={k} onClick={() => setFilter(k)}
              style={{
                display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, padding: '4px 10px', borderRadius: 999, fontWeight: 700, textTransform: 'uppercase', cursor: 'pointer',
                background: active ? `${cfg.color}20` : T.bgCard,
                border: active ? `1px solid ${cfg.color}50` : `1px solid ${T.border}`,
                color: active ? cfg.color : T.textSub,
              }}>
              <Icon style={{ width: 10, height: 10 }} />
              {cfg.label} · {count}
            </button>
          )
        })}
      </div>

      {/* Drop zone */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}` }}>
        <div style={{ borderRadius: 12, border: `2px dashed rgba(6,182,212,0.30)`, background: 'rgba(6,182,212,0.03)', padding: '24px 20px', textAlign: 'center' }}>
          <Sparkles style={{ width: 24, height: 24, color: T.cyan, display: 'block', margin: '0 auto 8px' }} />
          <p style={{ fontSize: 14, fontWeight: 700, color: T.textPrim, margin: '0 0 4px' }}>Arrastrá archivos acá</p>
          <p style={{ fontSize: 11, color: T.textSub, margin: '0 0 6px' }}>PDF · DOCX · XLSX · MP4 · MP3 · URLs · Notion · Drive · max 50MB</p>
          <p style={{ fontSize: 11, color: T.cyan, margin: 0 }}>IA procesa en background · embeddings → Qdrant · listo en ~30s</p>
        </div>
      </div>

      {/* Docs list */}
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 480, overflowY: 'auto' }}>
        {filtered.map(d => {
          const kind = KIND_CONFIG[d.kind]
          const status = STATUS_CONFIG[d.status]
          const Icon = kind.icon
          return (
            <div key={d.id} style={{ ...card(), overflow: 'hidden' }}>
              <div style={{ height: 2, background: `linear-gradient(90deg, ${kind.color}, ${status.color}, transparent)` }} />
              <div style={{ padding: '14px 16px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                {/* Emoji icon box */}
                <div style={{ width: 40, height: 40, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0, background: `${kind.color}12`, border: `1px solid ${kind.color}25` }}>
                  {d.emoji}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Name + badges */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
                    <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, flex: 1, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', lineHeight: 1.3 }}>{d.name}</p>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, padding: '3px 7px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', background: `${kind.color}18`, color: kind.color, border: `1px solid ${kind.color}28`, flexShrink: 0 }}>
                      <Icon style={{ width: 8, height: 8 }} />
                      {kind.label}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, padding: '3px 7px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', background: `${status.color}15`, color: status.color, border: `1px solid ${status.color}28`, flexShrink: 0 }}>
                      {d.status === 'processing' && <RefreshCw style={{ width: 8, height: 8, animation: 'spin 1s linear infinite' }} />}
                      {d.status === 'indexed' && <CheckCircle2 style={{ width: 8, height: 8 }} />}
                      {status.label}
                    </span>
                  </div>

                  {/* Metadata chips */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 6, background: T.bgApp, border: `1px solid ${T.border}`, color: T.textSub, fontFamily: 'monospace' }}>{d.size}</span>
                    {d.pages > 0 && <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 6, background: T.bgApp, border: `1px solid ${T.border}`, color: T.textSub, fontFamily: 'monospace' }}>{d.pages} {d.kind === 'video' || d.kind === 'audio' ? 'min' : 'págs'}</span>}
                    {d.chunks > 0 && <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 6, background: T.bgApp, border: `1px solid ${T.border}`, color: T.textSub, fontFamily: 'monospace' }}>{d.chunks} chunks</span>}
                    <span style={{ fontSize: 9, padding: '2px 6px', borderRadius: 6, fontWeight: 700, textTransform: 'uppercase', background: `${kind.color}10`, color: kind.color, border: `1px solid ${kind.color}20` }}>{d.topic}</span>
                    <span style={{ fontSize: 9, color: T.textSub, marginLeft: 'auto' }}>{d.ingestedAt}</span>
                  </div>

                  {/* Processing bar */}
                  {d.status === 'processing' && (
                    <div style={{ marginTop: 8, height: 4, background: T.bgApp, borderRadius: 999, overflow: 'hidden' }}>
                      <div style={{ height: '100%', borderRadius: 999, width: '60%', background: status.color, animation: 'pulse 2s infinite' }} />
                    </div>
                  )}
                </div>

                {/* Query count */}
                {d.status === 'indexed' && d.queriesAgainst > 0 && (
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <p style={{ fontSize: 26, fontWeight: 900, fontVariantNumeric: 'tabular-nums', lineHeight: 1, margin: 0, color: T.cyan, textShadow: T.glowCyan }}>{d.queriesAgainst >= 1000 ? `${(d.queriesAgainst / 1000).toFixed(1)}k` : d.queriesAgainst}</p>
                    <p style={{ fontSize: 9, color: T.textSub, textTransform: 'uppercase', letterSpacing: '0.1em', fontFamily: 'monospace', margin: '4px 0 0' }}>queries</p>
                  </div>
                )}
                {d.status === 'queued' && (
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <p style={{ fontSize: 11, fontWeight: 700, color: T.textSub }}>en cola</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div style={{ borderTop: `1px solid ${T.border}`, padding: '14px 24px', background: 'rgba(6,182,212,0.03)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: T.textSub }}>
          <Bot style={{ width: 12, height: 12, color: T.cyan }} />
          <span>IA respondió <span style={{ color: T.cyan, fontWeight: 700 }}>{stats.queries.toLocaleString()} preguntas</span> usando esta KB · cada doc se vuelve más útil con cada uso (citation tracking).</span>
        </div>
      </div>
    </section>
  )
}
