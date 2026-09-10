'use client'

import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { conversationsApi, ConversationWithPreview, Message, MessageDirection } from '@/lib/conversations'
import { businessApi, Business } from '@/lib/business'
import { platformMeta, PLATFORM_META } from '@/lib/platformMeta'
import { MessageSquare, Send, User, Phone, Mail, Archive, Check, CheckCheck, Clock, Bot, ChevronDown } from 'lucide-react'
import PlatformBots from '@/components/chatbots/PlatformBots'

export function ConversacionesContent() {
  const searchParams = useSearchParams()
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState<string>(searchParams?.get('business') || '')
  const [conversations, setConversations] = useState<ConversationWithPreview[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  // Bots panel is collapsed by default: this page's job is the inbox, and
  // the fixed-height layout has no room to give up permanently.
  const [showBots, setShowBots] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [platformFilter, setPlatformFilter] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadBusinesses()
  }, [])

  useEffect(() => {
    if (selectedBusiness) {
      loadConversations()
    }
  }, [selectedBusiness, platformFilter])

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation)
    }
  }, [selectedConversation])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadBusinesses = async () => {
    try {
      const data = await businessApi.list()
      setBusinesses(data)
      if (!selectedBusiness && data.length > 0) {
        setSelectedBusiness(data[0].id)
      }
    } catch {
      setLoading(false)
    }
  }

  const loadConversations = async () => {
    setLoading(true)
    try {
      const data = await conversationsApi.list(selectedBusiness, undefined, platformFilter || undefined)
      setConversations(data)
      if (data.length > 0 && !selectedConversation) {
        setSelectedConversation(data[0].id)
      }
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async (convId: string) => {
    try {
      const data = await conversationsApi.getMessages(selectedBusiness, convId)
      setMessages(data)
    } catch {
      // handled by interceptor
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !selectedConversation) return

    setSending(true)
    try {
      await conversationsApi.sendMessage(selectedBusiness, selectedConversation, {
        direction: 'outbound',
        content: newMessage,
      })
      setNewMessage('')
      await loadMessages(selectedConversation)
      await loadConversations()
    } catch {
      // handled by interceptor
    } finally {
      setSending(false)
    }
  }

  const currentConversation = conversations.find((c) => c.id === selectedConversation)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'sent': return <Check className="w-3 h-3 text-gray-400" />
      case 'delivered': return <CheckCheck className="w-3 h-3 text-gray-400" />
      case 'read': return <CheckCheck className="w-3 h-3 text-blue-500" />
      default: return <Clock className="w-3 h-3 text-gray-400" />
    }
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Conversaciones</h1>
          <p className="text-gray-500 mt-1">
            Inbox unificado de todos tus canales · prueba en vivo de que la IA responde de verdad
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowBots((v) => !v)}
          className="ml-auto mr-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <Bot className="w-4 h-4 text-blue-600" />
          Chatbots por plataforma
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showBots ? 'rotate-180' : ''}`} />
        </button>
        <select
          value={selectedBusiness}
          onChange={(e) => {
            setSelectedBusiness(e.target.value)
            setSelectedConversation(null)
            setMessages([])
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          {businesses.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </div>

      {showBots && (
        <div className="max-h-[55vh] overflow-y-auto pr-1">
          <PlatformBots />
        </div>
      )}

      {/* Real summary + platform filter -- this is what proves the bot is
          actually running per channel, not just a claim in the UI copy */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Bot className="w-3.5 h-3.5 text-emerald-600" />
          <span className="font-medium text-gray-900">
            {conversations.filter((c) => c.ai_responded).length}
          </span>
          de {conversations.length} conversaciones respondidas por la IA
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setPlatformFilter('')}
            className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              platformFilter === '' ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
          >
            Todas
          </button>
          {Object.entries(PLATFORM_META)
            .filter(([key]) => ['whatsapp', 'instagram', 'mercadolibre', 'amazon', 'hotmart', 'email', 'webchat'].includes(key))
            .map(([key, meta]) => (
              <button
                key={key}
                onClick={() => setPlatformFilter(key)}
                className="px-2.5 py-1 rounded-full text-xs font-medium border transition-colors"
                style={
                  platformFilter === key
                    ? { background: meta.color, color: '#0A0E1A', borderColor: meta.color }
                    : { background: 'white', color: meta.color, borderColor: `${meta.color}55` }
                }
              >
                {meta.label}
              </button>
            ))}
        </div>
      </div>

      <div className="flex-1 bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden flex">
        {/* Lista de conversaciones */}
        <div className="w-80 border-r border-gray-100 flex flex-col">
          <div className="p-3 border-b border-gray-100">
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar conversación..."
                className="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              <MessageSquare className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-8 text-center">
                <MessageSquare className="w-10 h-10 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">
                  {platformFilter ? `Sin conversaciones en ${platformMeta(platformFilter).label}` : 'No hay conversaciones aún'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {platformFilter ? 'Probá con otra plataforma o esperá a que lleguen mensajes reales.' : 'Conecta un canal para empezar'}
                </p>
              </div>
            ) : (
              conversations.map((conv) => {
                const meta = platformMeta(conv.platform)
                return (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv.id)}
                  className={`w-full text-left p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                    selectedConversation === conv.id ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <p className="font-medium text-gray-900 truncate">
                          {conv.lead_name || 'Desconocido'}
                        </p>
                        <span
                          className="text-[10px] font-semibold px-1.5 py-0.5 rounded shrink-0"
                          style={{ background: `${meta.color}22`, color: meta.color }}
                        >
                          {meta.label}
                        </span>
                        {conv.ai_responded && (
                          <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded shrink-0 bg-emerald-100 text-emerald-700">
                            <Bot className="w-2.5 h-2.5" /> IA
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {conv.lead_source && (
                          <span className="capitalize">{conv.lead_source}</span>
                        )}
                      </p>
                      {conv.last_message_preview && (
                        <p className="text-sm text-gray-500 mt-1 truncate">
                          {conv.last_direction === 'inbound' && (
                            <span className="text-amber-600 font-medium">Esperando respuesta · </span>
                          )}
                          {conv.last_message_preview}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 ml-2 shrink-0">
                      {conv.message_count > 0 && `${conv.message_count}`}
                    </span>
                  </div>
                </button>
                )
              })
            )}
          </div>
        </div>

        {/* Chat */}
        <div className="flex-1 flex flex-col">
          {currentConversation ? (
            <>
              <div className="p-4 border-b border-gray-100 flex items-center gap-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {currentConversation.lead_name || 'Desconocido'}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    {currentConversation.lead_phone && (
                      <span className="flex items-center gap-1">
                        <Phone className="w-3 h-3" />
                        {currentConversation.lead_phone}
                      </span>
                    )}
                    {currentConversation.lead_email && (
                      <span className="flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        {currentConversation.lead_email}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg) => {
                  // Real marker set by backend/app/domains/channels/services.py's
                  // send_outbound_message(generated_by="ai") -- only present when
                  // the AI bot actually composed this reply, never for a message
                  // a human typed through this same inbox. This is the concrete,
                  // per-message proof (not just a UI claim) that the bot works.
                  const isAiReply = msg.direction === 'outbound' && msg.extra_data?.generated_by === 'ai'
                  return (
                  <div
                    key={msg.id}
                    className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[70%] ${msg.direction === 'outbound' ? 'items-end' : 'items-start'} flex flex-col gap-0.5`}>
                      {isAiReply && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 pr-1">
                          <Bot className="w-3 h-3" /> Respondido por la IA
                        </span>
                      )}
                      <div
                        className={`px-4 py-2 rounded-2xl ${
                          msg.direction === 'outbound'
                            ? isAiReply
                              ? 'bg-emerald-600 text-white rounded-br-none'
                              : 'bg-primary-600 text-white rounded-br-none'
                            : 'bg-gray-100 text-gray-900 rounded-bl-none'
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                        <div className={`flex items-center justify-end gap-1 mt-1 ${
                          msg.direction === 'outbound' ? (isAiReply ? 'text-emerald-100' : 'text-primary-200') : 'text-gray-400'
                        }`}>
                          <span className="text-xs">
                            {new Date(msg.created_at).toLocaleTimeString('es-AR', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          {msg.direction === 'outbound' && getStatusIcon(msg.status)}
                        </div>
                      </div>
                    </div>
                  </div>
                  )
                })}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-100">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Escribe un mensaje..."
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                  />
                  <button
                    type="submit"
                    disabled={sending || !newMessage.trim()}
                    className="bg-primary-600 text-white p-2.5 rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Selecciona una conversación para ver los mensajes</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


