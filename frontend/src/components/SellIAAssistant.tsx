'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { assistantApi, AssistantAction, AssistantActionType } from '@/lib/assistant'
import { agentsApi } from '@/lib/agents'
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition'
import { useTextToSpeech } from '@/hooks/useTextToSpeech'
import {
  Sparkles, X, Send, Loader2, MessageSquare, ChevronRight,
  Mic, MicOff, Volume2, VolumeX, Trash2, Plus, PanelLeftClose,
  PanelLeft, Calendar, Bot, Zap, FileText, BarChart3, Users, Square,
  MonitorPlay, Target, Handshake, Package, Activity, TrendingUp,
  Shield, Award, AlertCircle, CheckCircle2
} from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  action?: AssistantAction
  timestamp?: string
}

interface Conversation {
  id: string
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

const ACTION_ICONS: Record<string, any> = {
  CREATE_SEQUENCE: FileText,
  SETUP_AUTOMATION: Zap,
  GENERATE_PLAYBOOK: FileText,
  ANALYZE_BUSINESS: BarChart3,
  CREATE_CONTENT_CALENDAR: Calendar,
  MULTI_AGENT_PANEL: Users,
  COMPUTER_USE: MonitorPlay,
  ACTIVATE_PIPELINE_AGENT: Target,
  NEGOTIATE: Handshake,
  BUILD_OFFER: Package,
  SYSTEM_HEALTH: Activity,
}

const ACTION_LABELS: Record<string, string> = {
  CREATE_SEQUENCE: 'Secuencia generada',
  SETUP_AUTOMATION: 'Automatización configurada',
  GENERATE_PLAYBOOK: 'Playbook generado',
  ANALYZE_BUSINESS: 'Análisis de negocio',
  CREATE_CONTENT_CALENDAR: 'Calendario de contenido',
  MULTI_AGENT_PANEL: 'Panel multi-experto',
  COMPUTER_USE: 'Caja de Cristal activada',
  ACTIVATE_PIPELINE_AGENT: 'Agente de Pipeline activado',
  NEGOTIATE: 'Estrategia de negociación lista',
  BUILD_OFFER: 'Grand Slam Offer generada',
  SYSTEM_HEALTH: 'Estado del sistema autónomo',
}

const STAGE_LABELS: Record<string, string> = {
  prospecting: '🎯 Prospección',
  qualifying: '🔍 Calificación',
  nurturing: '🌱 Nutrición',
  discovery: '💡 Diagnóstico',
  proposal: '📦 Propuesta',
  objection: '🛡️ Objeciones',
  closing: '🤝 Cierre',
  onboarding: '🚀 Bienvenida',
  retention: '💎 Retención',
}

const EXPERT_LABELS: Record<string, string> = {
  'chris-voss': '🎯 Chris Voss — FBI Never Split the Difference',
  'roger-fisher': '🏛️ Roger Fisher — Harvard Getting to Yes',
  'herb-cohen': '⚡ Herb Cohen — Power Negotiation',
  'stuart-diamond': '❤️ Stuart Diamond — Wharton Emotional',
  'william-ury': '🌉 William Ury — Getting Past No',
}

export default function SellIAAssistant({ businessId }: { businessId?: string }) {
  const [isOpen, setIsOpen] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [personalities, setPersonalities] = useState<any[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const abortStreamRef = useRef<(() => void) | null>(null)
  const router = useRouter()

  const { isSpeaking, speak, stop: stopTTS } = useTextToSpeech()

  const handleVoiceResult = useCallback((transcript: string) => {
    setInput(prev => {
      const combined = prev.trim() ? prev.trim() + ' ' + transcript : transcript
      return combined.trim()
    })
  }, [])

  const {
    isListening,
    isSupported: voiceSupported,
    startListening,
    stopListening,
    interimTranscript,
    error: voiceError,
    resetTranscript,
  } = useVoiceRecognition({
    language: 'es-ES',
    onResult: handleVoiceResult,
    onEnd: () => {
      // Auto-send after voice input
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    // Preload personalities
    agentsApi.getPersonalities().then(setPersonalities).catch(() => {})
  }, [])

  useEffect(() => {
    if (isOpen && conversations.length === 0) {
      loadConversations()
    }
  }, [isOpen])

  const loadConversations = async () => {
    try {
      const convs = await assistantApi.getConversations()
      setConversations(convs)
    } catch {
      // silent fail
    }
  }

  const startNewConversation = async () => {
    try {
      const conv = await assistantApi.createConversation()
      const newConv: Conversation = {
        id: conv.id,
        title: conv.title,
        message_count: (conv.messages || []).length,
        created_at: conv.created_at,
        updated_at: conv.updated_at,
      }
      setConversations(prev => [newConv, ...prev])
      setActiveConversationId(conv.id)
      setMessages([])
    } catch {
      // fallback: local-only conversation
      setActiveConversationId(null)
      setMessages([])
    }
  }

  const loadConversation = async (id: string) => {
    try {
      const conv = await assistantApi.getConversation(id)
      setActiveConversationId(id)
      const loadedMessages: Message[] = (conv.messages || []).map((m: any, idx: number) => ({
        id: `${id}-${idx}`,
        role: m.role,
        content: m.content,
        action: m.role === 'assistant' ? {
          action: m.action || 'ASK_CLARIFICATION',
          response: m.content,
          suggested_agents: m.suggested_agents,
          agent_slug: m.agent_slug,
          target: m.target,
        } : undefined,
        timestamp: m.created_at,
      }))
      setMessages(loadedMessages)
    } catch {
      // silent fail
    }
  }

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await assistantApi.deleteConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))
      if (activeConversationId === id) {
        setActiveConversationId(null)
        setMessages([])
      }
    } catch {
      // silent fail
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || loading || isStreaming) return
    const content = input.trim()
    setInput('')
    setLoading(true)
    setIsStreaming(true)
    resetTranscript()

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])

    try {
      const history = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content,
      }))

      // Ensure we have an active conversation
      let currentConvId = activeConversationId
      if (!currentConvId) {
        try {
          const conv = await assistantApi.createConversation()
          const newConv: Conversation = {
            id: conv.id,
            title: conv.title,
            message_count: (conv.messages || []).length,
            created_at: conv.created_at,
            updated_at: conv.updated_at,
          }
          setConversations(prev => [newConv, ...prev])
          setActiveConversationId(conv.id)
          currentConvId = conv.id
        } catch {
          // continue without persistent conversation
        }
      }

      const assistantMsgId = (Date.now() + 1).toString()
      let streamedContent = ''
      let finalAction: AssistantAction | undefined = undefined

      // Add empty assistant message that will be filled by stream
      setMessages(prev => [...prev, {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      }])

      abortStreamRef.current = assistantApi.chatStream(
        {
          message: content,
          business_id: businessId,
          conversation_history: history,
          conversation_id: currentConvId || undefined,
        },
        (event) => {
          if (event.type === 'token' && event.content) {
            streamedContent += event.content
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsgId
                  ? { ...m, content: streamedContent }
                  : m
              )
            )
          } else if (event.type === 'action' && event.data) {
            finalAction = event.data
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsgId
                  ? { ...m, content: event.data?.response || streamedContent, action: event.data }
                  : m
              )
            )
          } else if (event.type === 'error') {
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsgId
                  ? { ...m, content: streamedContent || 'Ups, algo salió mal.' }
                  : m
              )
            )
          }
        },
        () => {
          setLoading(false)
          setIsStreaming(false)
          abortStreamRef.current = null

          // Auto-title update
          if (currentConvId) {
            setConversations(prev =>
              prev.map(c =>
                c.id === currentConvId
                  ? { ...c, message_count: (c.message_count || 0) + 2, updated_at: new Date().toISOString() }
                  : c
              )
            )
          }

          // TTS
          if (ttsEnabled && streamedContent) {
            speak(streamedContent)
          }

          // Auto-navigate for CREATE_CONVERSATION
          if (finalAction?.action === 'CREATE_CONVERSATION') {
            handleAction(finalAction)
          }
        },
        (error) => {
          setLoading(false)
          setIsStreaming(false)
          abortStreamRef.current = null
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantMsgId
                ? { ...m, content: streamedContent || 'Ups, algo salió mal. ¿Probás de nuevo?' }
                : m
            )
          )
        }
      )
    } catch (e: any) {
      setLoading(false)
      setIsStreaming(false)
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: e.response?.data?.detail || 'Ups, algo salió mal. ¿Probás de nuevo?',
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMsg])
    }
  }

  const stopStream = () => {
    if (abortStreamRef.current) {
      abortStreamRef.current()
      abortStreamRef.current = null
    }
    setIsStreaming(false)
    setLoading(false)
  }

  const handleAction = async (action: AssistantAction) => {
    if (action.action === 'CREATE_CONVERSATION' && action.conversation_id && action.personality) {
      router.push(`/dashboard/agentes?conversation=${action.conversation_id}`)
      setIsOpen(false)
    } else if (action.action === 'CREATE_CONVERSATION' && action.agent_slug) {
      const personality = personalities.find(p => p.slug === action.agent_slug)
      if (personality && businessId) {
        try {
          const conv = await agentsApi.createConversation({
            business_id: businessId,
            personality_id: personality.id,
            title: `SellIA: ${personality.name}`,
          })
          router.push(`/dashboard/agentes?conversation=${conv.id}`)
          setIsOpen(false)
        } catch {
          router.push('/dashboard/agentes')
          setIsOpen(false)
        }
      } else {
        router.push('/dashboard/agentes')
        setIsOpen(false)
      }
    } else if (action.action === 'NAVIGATE' && action.target) {
      const navMap: Record<string, string> = {
        agentes: '/dashboard/agentes',
        negocios: '/dashboard/negocios',
        catalogo: '/dashboard/catalogo',
        analytics: '/dashboard/analytics',
        conversaciones: '/dashboard/conversaciones',
        automatizaciones: '/dashboard/automatizaciones',
        canales: '/dashboard/canales',
        planes: '/dashboard/planes',
        configuracion: '/dashboard/configuracion',
        pipeline: '/dashboard/pipeline',
        autonomo: '/dashboard/autonomo',
      }
      const target = navMap[action.target.toLowerCase()] || '/dashboard'
      router.push(target)
      setIsOpen(false)
    } else if (action.action === 'ACTIVATE_PIPELINE_AGENT' && action.stage) {
      router.push(`/dashboard/pipeline?stage=${action.stage}${action.deal_id ? `&deal=${action.deal_id}` : ''}`)
      setIsOpen(false)
    } else if (action.action === 'NEGOTIATE') {
      router.push(`/dashboard/agentes?section=negotiate${action.expert ? `&expert=${action.expert}` : ''}`)
      setIsOpen(false)
    } else if (action.action === 'BUILD_OFFER') {
      router.push(`/dashboard/agentes?section=offer${action.product_name ? `&product=${encodeURIComponent(action.product_name)}` : ''}`)
      setIsOpen(false)
    } else if (action.action === 'SYSTEM_HEALTH') {
      router.push('/dashboard/autonomo')
      setIsOpen(false)
    } else if (action.action === 'SETUP_AUTOMATION') {
      router.push('/dashboard/automatizaciones/builder')
      setIsOpen(false)
    } else if (action.action === 'COMPUTER_USE' && action.session_id) {
      router.push(`/dashboard/caja-de-cristal?session=${action.session_id}`)
      setIsOpen(false)
    } else if (action.action === 'MULTI_AGENT_PANEL' && action.agent_slugs && businessId) {
      // Open multiple conversations in sequence
      for (const slug of action.agent_slugs) {
        const personality = personalities.find(p => p.slug === slug)
        if (personality) {
          try {
            await agentsApi.createConversation({
              business_id: businessId,
              personality_id: personality.id,
              title: `SellIA: ${personality.name}`,
            })
          } catch {
            // skip failed ones
          }
        }
      }
      router.push('/dashboard/agentes')
      setIsOpen(false)
    }
  }

  const handleQuickOption = (option: string) => {
    setInput(option)
    setTimeout(() => sendMessage(), 50)
  }

  const toggleVoice = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const toggleTTS = () => {
    if (ttsEnabled) {
      stopTTS()
    }
    setTtsEnabled(prev => !prev)
  }

  const renderActionResult = (action: AssistantAction) => {
    const complexActions: AssistantActionType[] = [
      'CREATE_SEQUENCE', 'SETUP_AUTOMATION', 'GENERATE_PLAYBOOK',
      'ANALYZE_BUSINESS', 'CREATE_CONTENT_CALENDAR', 'MULTI_AGENT_PANEL',
      'COMPUTER_USE', 'ACTIVATE_PIPELINE_AGENT', 'NEGOTIATE',
      'BUILD_OFFER', 'SYSTEM_HEALTH',
    ]
    if (!complexActions.includes(action.action)) return null

    const Icon = ACTION_ICONS[action.action] || Sparkles
    const label = ACTION_LABELS[action.action] || 'Acción completada'
    const result = action.execution_result

    // Pipeline Agent Card
    if (action.action === 'ACTIVATE_PIPELINE_AGENT') {
      return (
        <div className="mt-2 p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-1.5">
            <Target className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[11px] font-medium text-emerald-400">{label}</span>
          </div>
          {action.stage && (
            <p className="text-[10px] text-white/60">Etapa: {STAGE_LABELS[action.stage] || action.stage}</p>
          )}
          {result?.prompt_preview && (
            <p className="text-[10px] text-white/40 mt-1 line-clamp-2">{result.prompt_preview}</p>
          )}
          {result?.next_suggested_stage && (
            <div className="mt-1.5 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-emerald-400/60" />
              <span className="text-[9px] text-emerald-400/60">Siguiente: {STAGE_LABELS[result.next_suggested_stage] || result.next_suggested_stage}</span>
            </div>
          )}
          <button
            onClick={() => handleAction(action)}
            className="mt-2 w-full py-1.5 text-[10px] bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-lg transition-colors flex items-center justify-center gap-1"
          >
            <Target className="w-3 h-3" /> Abrir pipeline
          </button>
        </div>
      )
    }

    // Negotiation Card
    if (action.action === 'NEGOTIATE') {
      return (
        <div className="mt-2 p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-1.5">
            <Handshake className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-[11px] font-medium text-blue-400">{label}</span>
          </div>
          {action.expert && (
            <p className="text-[10px] text-white/60">{EXPERT_LABELS[action.expert] || action.expert}</p>
          )}
          {result?.core_technique && (
            <p className="text-[10px] text-blue-300/70 mt-1 font-medium">{result.core_technique}</p>
          )}
          {result?.opening_move && (
            <p className="text-[10px] text-white/40 mt-0.5 italic">"{result.opening_move}"</p>
          )}
          {result?.tactical_tools && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {result.tactical_tools.slice(0, 3).map((tool: string, i: number) => (
                <span key={i} className="text-[9px] px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/20 rounded text-blue-300/60">{tool}</span>
              ))}
            </div>
          )}
        </div>
      )
    }

    // Build Offer Card
    if (action.action === 'BUILD_OFFER') {
      return (
        <div className="mt-2 p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-1.5">
            <Package className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-[11px] font-medium text-amber-400">{label}</span>
          </div>
          {result?.offer_name && (
            <p className="text-[10px] text-amber-300 font-semibold">{result.offer_name}</p>
          )}
          {result?.actual_price && (
            <div className="mt-1 flex items-center gap-2">
              <span className="text-[10px] text-white/30 line-through">${result.total_perceived_value?.toLocaleString()}</span>
              <span className="text-[12px] text-amber-400 font-bold">${result.actual_price?.toLocaleString()}</span>
            </div>
          )}
          {result?.guarantee && (
            <div className="mt-1 flex items-center gap-1">
              <Shield className="w-3 h-3 text-emerald-400" />
              <span className="text-[9px] text-emerald-400/70">{result.guarantee}</span>
            </div>
          )}
          {result?.value_stack && (
            <div className="mt-1.5 space-y-0.5">
              {result.value_stack.slice(0, 3).map((item: any, i: number) => (
                <div key={i} className="flex items-center gap-1">
                  <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400/60" />
                  <span className="text-[9px] text-white/40">{item.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }

    // System Health Card
    if (action.action === 'SYSTEM_HEALTH') {
      const score = result?.health_score ?? 0
      const statusColor = score >= 80 ? 'emerald' : score >= 60 ? 'yellow' : score >= 40 ? 'orange' : 'red'
      const statusLabel = score >= 80 ? '🟢 Óptimo' : score >= 60 ? '🟡 Estable' : score >= 40 ? '🟠 Degradado' : '🔴 Crítico'
      return (
        <div className="mt-2 p-2.5 bg-purple-500/10 border border-purple-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-1.5">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-[11px] font-medium text-purple-400">{label}</span>
          </div>
          <div className="flex items-center gap-3 mb-1.5">
            <div className="relative w-10 h-10">
              <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="14" fill="none"
                  stroke={score >= 80 ? '#10b981' : score >= 60 ? '#eab308' : score >= 40 ? '#f97316' : '#ef4444'}
                  strokeWidth="3"
                  strokeDasharray={`${(score / 100) * 88} 88`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-white">{score}</span>
            </div>
            <div>
              <p className="text-[10px] text-white/60">{statusLabel}</p>
              {result?.uptime && <p className="text-[9px] text-white/30">Uptime: {result.uptime}</p>}
            </div>
          </div>
          {result?.recommendations?.length > 0 && (
            <div className="space-y-0.5">
              {result.recommendations.slice(0, 2).map((rec: string, i: number) => (
                <div key={i} className="flex items-start gap-1">
                  <AlertCircle className="w-2.5 h-2.5 text-yellow-400/60 mt-0.5 shrink-0" />
                  <span className="text-[9px] text-white/40">{rec}</span>
                </div>
              ))}
            </div>
          )}
          <button
            onClick={() => handleAction(action)}
            className="mt-2 w-full py-1.5 text-[10px] bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg transition-colors flex items-center justify-center gap-1"
          >
            <Activity className="w-3 h-3" /> Ver panel autónomo
          </button>
        </div>
      )
    }

    return (
      <div className="mt-2 p-2.5 bg-white/5 border border-white/10 rounded-lg">
        <div className="flex items-center gap-2 mb-1.5">
          <Icon className="w-3.5 h-3.5 text-brand-orange" />
          <span className="text-[11px] font-medium text-brand-orange">{label}</span>
        </div>
        {action.sequence_name && (
          <p className="text-[10px] text-white/50">{action.sequence_name}</p>
        )}
        {action.automation_name && (
          <p className="text-[10px] text-white/50">{action.automation_name}</p>
        )}
        {action.topic && (
          <p className="text-[10px] text-white/50">{action.topic}</p>
        )}
        {action.platforms && (
          <p className="text-[10px] text-white/50">Plataformas: {action.platforms.join(', ')}</p>
        )}
        {action.agent_slugs && (
          <div className="flex flex-wrap gap-1 mt-1">
            {action.agent_slugs.map(slug => {
              const p = personalities.find((per: any) => per.slug === slug)
              return p ? (
                <span key={slug} className="text-[9px] px-1.5 py-0.5 bg-white/10 rounded text-white/60">
                  {p.emoji} {p.name}
                </span>
              ) : null
            })}
          </div>
        )}
        {action.steps && (
          <div className="mt-1.5 space-y-1">
            {action.steps.slice(0, 3).map((step, i) => (
              <div key={i} className="text-[10px] text-white/40 flex gap-2">
                <span className="text-white/20">Paso {step.step}</span>
                <span>{step.subject || step.content.substring(0, 50)}...</span>
              </div>
            ))}
            {action.steps.length > 3 && (
              <p className="text-[10px] text-white/20">+{action.steps.length - 3} pasos más</p>
            )}
          </div>
        )}
      </div>
    )
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 group"
      >
        <div className="relative">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-brand-orange to-brand-orange-dark flex items-center justify-center shadow-lg shadow-brand-orange/30 hover:shadow-brand-orange/50 transition-all duration-300 hover:scale-105">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div className="absolute inset-0 rounded-full bg-brand-orange/30 blur-xl animate-pulse" />
          <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-green-500 border-2 border-[#060812]" />
        </div>
        <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-white/10 backdrop-blur-sm border border-white/10 rounded-xl text-xs text-white/80 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          SellIA Assistant
        </span>
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[28rem] max-w-[calc(100vw-2rem)] h-[36rem] max-h-[calc(100vh-6rem)] flex rounded-2xl bg-[#0A0E1A]/95 backdrop-blur-xl border border-white/10 shadow-2xl shadow-black/50 overflow-hidden">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-56 border-r border-white/5 flex flex-col bg-[#060812]/50">
          <div className="flex items-center justify-between px-3 py-3 border-b border-white/5">
            <span className="text-[11px] font-medium text-white/60">Historial</span>
            <button
              onClick={() => setShowSidebar(false)}
              className="p-1 hover:bg-white/5 rounded transition-colors"
            >
              <PanelLeftClose className="w-3.5 h-3.5 text-white/30" />
            </button>
          </div>
          <div className="p-2">
            <button
              onClick={startNewConversation}
              className="flex items-center gap-2 w-full px-3 py-2 text-[11px] bg-brand-orange/20 hover:bg-brand-orange/30 text-brand-orange rounded-lg transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Nueva conversación
            </button>
          </div>
          <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-1">
            {conversations.map(conv => (
              <button
                key={conv.id}
                onClick={() => loadConversation(conv.id)}
                className={`flex items-center gap-2 w-full px-2.5 py-2 text-left rounded-lg transition-colors group ${
                  activeConversationId === conv.id
                    ? 'bg-white/10'
                    : 'hover:bg-white/5'
                }`}
              >
                <MessageSquare className="w-3 h-3 text-white/30 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] text-white/70 truncate">{conv.title}</p>
                  <p className="text-[9px] text-white/30">{conv.message_count} mensajes</p>
                </div>
                <button
                  onClick={e => deleteConversation(conv.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
                >
                  <Trash2 className="w-3 h-3 text-red-400/60" />
                </button>
              </button>
            ))}
            {conversations.length === 0 && (
              <p className="text-[10px] text-white/20 text-center py-4">Sin conversaciones aún</p>
            )}
          </div>
        </div>
      )}

      {/* Main Chat */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-brand-orange/20 to-transparent border-b border-white/5">
          <div className="flex items-center gap-2.5">
            {!showSidebar && (
              <button
                onClick={() => setShowSidebar(true)}
                className="p-1 hover:bg-white/5 rounded transition-colors"
              >
                <PanelLeft className="w-4 h-4 text-white/40" />
              </button>
            )}
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-orange to-brand-orange-dark flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">SellIA Assistant</h3>
              <p className="text-[10px] text-white/40">
                {activeConversationId ? 'Conversación activa' : 'Tu asistente de IA'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {voiceSupported && (
              <button
                onClick={toggleVoice}
                className={`p-1.5 rounded-lg transition-colors ${
                  isListening
                    ? 'bg-red-500/20 text-red-400 animate-pulse'
                    : 'hover:bg-white/5 text-white/40'
                }`}
                title={isListening ? 'Detener micrófono' : 'Usar micrófono'}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            )}
            <button
              onClick={toggleTTS}
              className={`p-1.5 rounded-lg transition-colors ${
                ttsEnabled ? 'bg-brand-orange/20 text-brand-orange' : 'hover:bg-white/5 text-white/40'
              }`}
              title={ttsEnabled ? 'Desactivar voz' : 'Leer respuestas en voz alta'}
            >
              {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
            <button
              onClick={() => {
                setIsOpen(false)
                stopTTS()
                if (isListening) stopListening()
              }}
              className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-white/40" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <div className="w-12 h-12 rounded-2xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-brand-orange" />
              </div>
              <h4 className="text-sm font-medium text-white mb-1">¡Hola! Soy SellIA</h4>
              <p className="text-xs text-white/40 leading-relaxed">
                Podés pedirme cosas como:
              </p>
              <div className="mt-3 space-y-1.5">
                {[
                  'Activá el agente de cierre para este lead',
                  'Negociá un precio con Chris Voss',
                  'Construí mi Grand Slam Offer',
                  'Estado de salud del sistema autónomo',
                  'Creá una secuencia de emails de venta',
                  'Generá un playbook de ventas',
                ].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => handleQuickOption(suggestion)}
                    className="block w-full text-left px-3 py-2 text-xs text-white/50 hover:text-white/80 hover:bg-white/5 rounded-lg transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-orange text-white rounded-br-md'
                    : 'bg-white/5 text-white/80 border border-white/5 rounded-bl-md'
                }`}
              >
                {msg.content}

                {/* Action Buttons */}
                {msg.action && msg.role === 'assistant' && (
                  <div className="mt-2.5 space-y-2">
                    {/* Clarification Options */}
                    {msg.action.action === 'ASK_CLARIFICATION' && msg.action.options && msg.action.options.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {msg.action.options.map(opt => (
                          <button
                            key={opt}
                            onClick={() => handleQuickOption(opt)}
                            className="px-3 py-1.5 text-[11px] bg-white/10 hover:bg-white/15 text-white/70 hover:text-white rounded-lg transition-colors border border-white/5"
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Suggested Agents */}
                    {msg.action.action === 'SUGGEST_AGENTS' && msg.action.suggested_agents && (
                      <div className="space-y-1.5">
                        {msg.action.suggested_agents.map(slug => {
                          const p = personalities.find((per: any) => per.slug === slug)
                          if (!p) return null
                          return (
                            <button
                              key={slug}
                              onClick={() => {
                                setInput(`Quiero hablar con ${p.name}`)
                                setTimeout(sendMessage, 50)
                              }}
                              className="flex items-center gap-2 w-full px-3 py-2 text-left bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/5"
                            >
                              <span className="text-sm">{p.emoji}</span>
                              <div className="flex-1 min-w-0">
                                <p className="text-[11px] font-medium text-white truncate">{p.name}</p>
                                <p className="text-[10px] text-white/40 truncate">{p.tagline}</p>
                              </div>
                              <ChevronRight className="w-3 h-3 text-white/20" />
                            </button>
                          )
                        })}
                      </div>
                    )}

                    {/* Create Conversation */}
                    {msg.action.action === 'CREATE_CONVERSATION' && (
                      <button
                        onClick={() => handleAction(msg.action!)}
                        className="flex items-center gap-2 px-3 py-2 text-[11px] bg-brand-orange/20 hover:bg-brand-orange/30 text-brand-orange rounded-lg transition-colors border border-brand-orange/10"
                      >
                        <MessageSquare className="w-3 h-3" />
                        Abrir conversación
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}

                    {/* Navigate */}
                    {msg.action.action === 'NAVIGATE' && msg.action.target && (
                      <button
                        onClick={() => handleAction(msg.action!)}
                        className="flex items-center gap-2 px-3 py-2 text-[11px] bg-white/10 hover:bg-white/15 text-white/70 rounded-lg transition-colors border border-white/5"
                      >
                        Ir a {msg.action.target}
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}

                    {/* Computer Use */}
                    {msg.action.action === 'COMPUTER_USE' && msg.action.session_id && (
                      <button
                        onClick={() => handleAction(msg.action!)}
                        className="flex items-center gap-2 px-3 py-2 text-[11px] bg-brand-orange/20 hover:bg-brand-orange/30 text-brand-orange rounded-lg transition-colors border border-brand-orange/10"
                      >
                        <MonitorPlay className="w-3 h-3" />
                        Abrir Caja de Cristal
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    )}

                    {/* Complex Actions */}
                    {renderActionResult(msg.action)}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Voice interim transcript */}
          {isListening && interimTranscript && (
            <div className="flex justify-start">
              <div className="bg-white/5 border border-white/5 rounded-2xl rounded-bl-md px-3.5 py-2.5">
                <p className="text-sm text-white/50 italic">{interimTranscript}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white/5 border border-white/5 rounded-2xl rounded-bl-md px-3.5 py-2.5">
                <div className="flex items-center gap-1.5">
                  <Loader2 className="w-3 h-3 text-white/30 animate-spin" />
                  <span className="text-xs text-white/30">SellIA está pensando...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Voice error */}
        {voiceError && (
          <div className="px-4 py-1.5 bg-red-500/10 border-t border-red-500/10">
            <p className="text-[10px] text-red-400">{voiceError}</p>
          </div>
        )}

        {/* Input */}
        <div className="px-4 py-3 border-t border-white/5 bg-white/[0.02]">
          <div className="flex items-center gap-2">
            {voiceSupported && (
              <button
                onClick={toggleVoice}
                className={`p-2 rounded-xl transition-all ${
                  isListening
                    ? 'bg-red-500/20 text-red-400 animate-pulse'
                    : 'bg-white/5 text-white/40 hover:text-white/60'
                }`}
              >
                {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            )}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder={isListening ? 'Escuchando... hablá ahora' : 'Escribí tu solicitud...'}
              className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange/30"
            />
            {isStreaming ? (
              <button
                onClick={stopStream}
                className="p-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-all active:scale-95 animate-pulse"
              >
                <Square className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="p-2 bg-brand-orange text-white rounded-xl hover:bg-brand-orange-dark transition-all active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
