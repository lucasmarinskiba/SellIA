'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import {
  Camera as Instagram,
  Search,
  Calendar,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  Wand2,
  X,
  Hash,
  MousePointerClick,
  Type,
  AlignLeft,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/Dialog'
import { Textarea } from '@/components/ui/Textarea'
import { Badge } from '@/components/ui/Badge'

interface CalendarSlot {
  id: string
  platform: string
  content_type: string
  topic: string
  scheduled_at: string
  status: 'empty' | 'filled' | 'ai_generated' | 'published'
  hashtag_suggestions?: string[]
  content?: {
    hook: string
    body: string
    cta: string
    hashtags: string[]
  }
}

interface GeneratedContent {
  hook: string
  body: string
  cta: string
  hashtags: string[]
}

const CONTENT_TYPES = [
  { value: 'Post', label: 'Post' },
  { value: 'Carousel', label: 'Carousel' },
  { value: 'Story', label: 'Story' },
]

export default function SocialGrowthPage() {
  const { user, loading: authLoading } = useAuth()
  const [audit, setAudit] = useState<any>(null)
  const [auditLoading, setAuditLoading] = useState(false)
  const [handle, setHandle] = useState('')
  const [calendar, setCalendar] = useState<CalendarSlot[]>([])
  const [calendarLoading, setCalendarLoading] = useState(true)
  const [calendarError, setCalendarError] = useState<string | null>(null)

  // AI Content Modal state
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState<CalendarSlot | null>(null)
  const [topicInput, setTopicInput] = useState('')
  const [contentType, setContentType] = useState('Post')
  const [generating, setGenerating] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchCalendar()
  }, [])

  const fetchCalendar = async () => {
    setCalendarLoading(true)
    setCalendarError(null)
    try {
      const res = await api.get('/social-growth/calendar')
      setCalendar(res.data)
    } catch {
      // Mock calendar data if API fails
      const now = new Date()
      const mock: CalendarSlot[] = Array.from({ length: 7 }).map((_, i) => ({
        id: `slot-${i}`,
        platform: 'instagram',
        content_type: ['Post', 'Carousel', 'Story'][i % 3],
        topic: ['Tips de ventas', 'Caso de éxito', 'Behind the scenes', 'Producto del mes', 'Preguntas frecuentes', 'Tendencias', 'Tutorial'][i],
        scheduled_at: new Date(now.getTime() + i * 86400000).toISOString(),
        status: i % 3 === 0 ? 'ai_generated' : i % 2 === 0 ? 'filled' : 'empty',
        hashtag_suggestions: ['ventas', 'marketing', 'emprendedores', 'negocios'],
        ...(i % 3 === 0
          ? {
              content: {
                hook: '¿Sabías que el 80% de las ventas se pierden por no seguir leads?',
                body: 'Hoy te comparto 3 técnicas probadas para recuperar clientes potenciales y convertirlos en ventas reales.',
                cta: 'Guardá este post y empezá a aplicarlas hoy.',
                hashtags: ['#ventas', '#leads', '#marketingdigital', '#emprendedores'],
              },
            }
          : {}),
      }))
      setCalendar(mock)
    } finally {
      setCalendarLoading(false)
    }
  }

  const runAudit = async () => {
    if (!handle) return
    setAuditLoading(true)
    try {
      const res = await api.post('/social-growth/audit', null, { params: { platform: 'instagram', handle } })
      setAudit(res.data)
    } catch {
      // silent
    } finally {
      setAuditLoading(false)
    }
  }

  const openAIModal = (slot: CalendarSlot) => {
    setSelectedSlot(slot)
    setTopicInput(slot.topic || '')
    setContentType(slot.content_type === 'story' ? 'Story' : slot.content_type === 'carousel' ? 'Carousel' : 'Post')
    setGeneratedContent(null)
    setGenerateError(null)
    setModalOpen(true)
  }

  const generateContent = async () => {
    if (!topicInput.trim()) return
    setGenerating(true)
    setGenerateError(null)
    try {
      const endpointMap: Record<string, string> = {
        Post: '/social-content/post',
        Carousel: '/social-content/carousel',
        Story: '/social-content/story',
      }
      const res = await api.post(endpointMap[contentType] || '/social-content/post', {
        topic: topicInput,
        platform: selectedSlot?.platform || 'instagram',
      })
      const data = res.data
      setGeneratedContent({
        hook: data.hook || data.content?.hook || '',
        body: data.body || data.content?.body || data.text || '',
        cta: data.cta || data.content?.cta || '',
        hashtags: data.hashtags || data.content?.hashtags || data.hashtag_suggestions || [],
      })
    } catch {
      // Fallback mock generation
      setTimeout(() => {
        setGeneratedContent({
          hook: `¿Te cuesta vender ${topicInput.toLowerCase()}? Esto te va a cambiar el juego.`,
          body: `Hoy te comparto insights clave sobre ${topicInput.toLowerCase()} que usan las marcas top para escalar sus ventas sin aumentar el presupuesto.`,
          cta: 'Doble tap si te sirvió y compartilo con alguien que lo necesite.',
          hashtags: ['#ventas', '#marketing', '#emprendedores', '#negocios', '#sellia'],
        })
      }, 800)
    } finally {
      setGenerating(false)
    }
  }

  const saveContent = async () => {
    if (!generatedContent || !selectedSlot) return
    setSaving(true)
    try {
      // Mock save - update local state
      setCalendar((prev) =>
        prev.map((slot) =>
          slot.id === selectedSlot.id
            ? {
                ...slot,
                status: 'ai_generated' as const,
                content: generatedContent,
                content_type: contentType.toLowerCase(),
                topic: topicInput,
              }
            : slot
        )
      )
      setModalOpen(false)
      setGeneratedContent(null)
      setSelectedSlot(null)
    } finally {
      setSaving(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const scoreBar = (score: number) => {
    if (score >= 80) return 'bg-emerald-400'
    if (score >= 60) return 'bg-yellow-400'
    return 'bg-red-400'
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 rounded-xl bg-pink-500/10">
            <Instagram className="w-6 h-6 text-pink-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Social Growth Toolkit</h1>
            <p className="text-sm text-white/50">Auditoría, calendario de contenidos y análisis de competencia</p>
          </div>
        </div>

        {/* Audit Section */}
        <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-3 mb-6">
            <Search className="w-5 h-5 text-white/50" />
            <h2 className="text-lg font-semibold text-white">Auditoría de Perfil</h2>
          </div>

          <div className="flex gap-3 mb-6">
            <div className="flex-1 relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30 text-sm">@</span>
              <input
                type="text"
                placeholder="usuario_de_instagram"
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                className="w-full pl-8 pr-4 py-3 rounded-xl bg-white/[0.05] border border-white/[0.08] text-white placeholder:text-white/30 text-sm focus:outline-none focus:border-pink-500/50"
              />
            </div>
            <button
              onClick={runAudit}
              disabled={auditLoading || !handle}
              className="px-6 py-3 rounded-xl bg-pink-500 text-white text-sm font-medium hover:bg-pink-500/90 transition-colors disabled:opacity-50"
            >
              {auditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Auditar'}
            </button>
          </div>

          {audit && (
            <div className="space-y-6">
              <div className="flex items-center gap-6">
                <div className="w-24 h-24 rounded-full border-4 border-white/[0.06] flex items-center justify-center relative">
                  <span className={`text-2xl font-bold ${scoreColor(audit.overall_score)}`}>{audit.overall_score}</span>
                  <span className="absolute -bottom-1 text-[10px] text-white/30">/100</span>
                </div>
                <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(audit.scores).map(([key, score]: [string, any]) => (
                    <div key={key} className="p-3 rounded-xl bg-white/[0.03]">
                      <p className="text-[10px] uppercase tracking-wider text-white/40 mb-1">{key}</p>
                      <p className={`text-lg font-bold ${scoreColor(score)}`}>{score}</p>
                      <div className="h-1 rounded-full bg-white/[0.05] mt-1">
                        <div className={`h-full rounded-full ${scoreBar(score)}`} style={{ width: `${score}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-white/70 mb-3">Hallazgos</h3>
                <div className="space-y-2">
                  {audit.findings.map((f: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                      <AlertCircle className={`w-4 h-4 mt-0.5 shrink-0 ${f.priority === 'high' ? 'text-red-400' : 'text-yellow-400'}`} />
                      <div>
                        <p className="text-sm text-white/80">{f.issue}</p>
                        <p className="text-xs text-white/50 mt-1">{f.suggestion}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-white/70 mb-3">Recomendaciones</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {audit.recommendations.map((r: any, i: number) => (
                    <div key={i} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                      <div className="flex items-center gap-2 mb-1">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <p className="text-sm text-white/80">{r.action}</p>
                      </div>
                      <p className="text-xs text-emerald-400/70 ml-5">{r.expected_impact}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Content Calendar */}
        <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-3 mb-6">
            <Calendar className="w-5 h-5 text-white/50" />
            <h2 className="text-lg font-semibold text-white">Calendario de Contenido AI</h2>
          </div>

          {calendarError && (
            <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-4">
              <AlertCircle className="w-4 h-4" />
              {calendarError}
              <button onClick={() => setCalendarError(null)} className="ml-auto">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {calendarLoading ? (
            <div className="flex items-center gap-2 text-white/50 py-8">
              <Loader2 className="w-4 h-4 animate-spin" />
              Cargando calendario...
            </div>
          ) : calendar.length === 0 ? (
            <div className="text-center py-8 text-white/40 text-sm">
              No hay slots de calendario generados todavía.
            </div>
          ) : (
            <div className="space-y-3">
              <AnimatePresence>
                {calendar.slice(0, 7).map((slot: CalendarSlot, idx: number) => (
                  <motion.div
                    key={slot.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] group"
                  >
                    <div className="w-12 h-12 rounded-lg bg-white/[0.05] flex items-center justify-center shrink-0 relative">
                      <Clock className="w-5 h-5 text-white/30" />
                      {slot.status === 'ai_generated' && (
                        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-brand-orange/20 flex items-center justify-center">
                          <Sparkles className="w-3 h-3 text-brand-orange" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs px-2 py-0.5 rounded bg-white/[0.05] text-white/50 capitalize">{slot.platform}</span>
                        <span className="text-xs px-2 py-0.5 rounded bg-white/[0.05] text-white/50 capitalize">{slot.content_type}</span>
                        {slot.status === 'ai_generated' && (
                          <Badge variant="orange" className="text-[10px]">
                            <Sparkles className="w-3 h-3 mr-1" />
                            IA
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-white font-medium truncate">{slot.topic}</p>
                      <p className="text-xs text-white/40">{new Date(slot.scheduled_at).toLocaleDateString('es-AR')}</p>
                      {slot.content && (
                        <p className="text-xs text-white/30 mt-1 truncate">{slot.content.hook}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="flex items-center gap-1">
                        {slot.hashtag_suggestions?.slice(0, 3).map((h: string) => (
                          <span key={h} className="text-[10px] px-2 py-1 rounded bg-white/[0.05] text-white/40">#{h}</span>
                        ))}
                      </div>
                      <button
                        onClick={() => openAIModal(slot)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-brand-orange bg-brand-orange/10 hover:bg-brand-orange/20 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                      >
                        <Wand2 className="w-3.5 h-3.5" />
                        {slot.status === 'ai_generated' ? 'Regenerar' : 'Generar con IA'}
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* AI Content Generation Modal */}
      <AnimatePresence>
        {modalOpen && (
          <Dialog open={modalOpen} onOpenChange={setModalOpen}>
            <DialogContent className="max-w-lg">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-brand-orange" />
                    Generar contenido con IA
                  </DialogTitle>
                  <DialogDescription>
                    {selectedSlot ? `Slot: ${selectedSlot.topic}` : 'Creá contenido para redes sociales'}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-2">
                  <div>
                    <label className="text-xs font-medium text-white/50 mb-1.5 block">Tema del contenido</label>
                    <Input
                      placeholder="Ej: Cómo aumentar ventas en Instagram"
                      value={topicInput}
                      onChange={(e) => setTopicInput(e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="text-xs font-medium text-white/50 mb-1.5 block">Tipo</label>
                    <Select value={contentType} onValueChange={setContentType}>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccioná un tipo" />
                      </SelectTrigger>
                      <SelectContent>
                        {CONTENT_TYPES.map((t) => (
                          <SelectItem key={t.value} value={t.value}>
                            {t.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {!generatedContent && (
                    <Button
                      onClick={generateContent}
                      disabled={generating || !topicInput.trim()}
                      isLoading={generating}
                      className="w-full"
                      leftIcon={<Wand2 className="w-4 h-4" />}
                    >
                      {generating ? 'Generando...' : 'Generar'}
                    </Button>
                  )}

                  {generateError && (
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      {generateError}
                    </div>
                  )}

                  <AnimatePresence>
                    {generatedContent && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="space-y-3 p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <Sparkles className="w-4 h-4 text-brand-orange" />
                          <span className="text-xs font-medium text-white/70">Vista previa</span>
                        </div>

                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <MousePointerClick className="w-3.5 h-3.5 text-brand-orange/60" />
                            <span className="text-[10px] uppercase tracking-wider text-white/40">Hook</span>
                          </div>
                          <p className="text-sm text-white/90">{generatedContent.hook}</p>
                        </div>

                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <AlignLeft className="w-3.5 h-3.5 text-brand-orange/60" />
                            <span className="text-[10px] uppercase tracking-wider text-white/40">Cuerpo</span>
                          </div>
                          <p className="text-sm text-white/80">{generatedContent.body}</p>
                        </div>

                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <Type className="w-3.5 h-3.5 text-brand-orange/60" />
                            <span className="text-[10px] uppercase tracking-wider text-white/40">CTA</span>
                          </div>
                          <p className="text-sm text-white/90">{generatedContent.cta}</p>
                        </div>

                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <Hash className="w-3.5 h-3.5 text-brand-orange/60" />
                            <span className="text-[10px] uppercase tracking-wider text-white/40">Hashtags</span>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {generatedContent.hashtags.map((h) => (
                              <span key={h} className="text-xs px-2 py-1 rounded bg-white/[0.05] text-white/50">
                                {h.startsWith('#') ? h : `#${h}`}
                              </span>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <DialogFooter className="gap-2">
                  {generatedContent ? (
                    <>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setGeneratedContent(null)
                          setGenerateError(null)
                        }}
                      >
                        Volver a generar
                      </Button>
                      <Button onClick={saveContent} isLoading={saving} leftIcon={<CheckCircle2 className="w-4 h-4" />}>
                        Usar contenido
                      </Button>
                    </>
                  ) : (
                    <Button variant="outline" onClick={() => setModalOpen(false)}>
                      Cancelar
                    </Button>
                  )}
                </DialogFooter>
              </motion.div>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>
    </div>
  )
}
