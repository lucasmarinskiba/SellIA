'use client'

import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { conversationsApi, ConversationWithPreview, Message, MessageDirection } from '@/lib/conversations'
import { businessApi, Business } from '@/lib/business'
import { MessageSquare, Send, User, Phone, Mail, Archive, Check, CheckCheck, Clock } from 'lucide-react'

export default function ConversacionesPage() {
  const searchParams = useSearchParams()
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState<string>(searchParams?.get('business') || '')
  const [conversations, setConversations] = useState<ConversationWithPreview[]>([])
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    loadBusinesses()
  }, [])

  useEffect(() => {
    if (selectedBusiness) {
      loadConversations()
    }
  }, [selectedBusiness])

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
      const data = await conversationsApi.list(selectedBusiness)
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
          <p className="text-gray-500 mt-1">Inbox unificado de todos tus canales</p>
        </div>
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
                <p className="text-sm text-gray-500">No hay conversaciones aún</p>
                <p className="text-xs text-gray-400 mt-1">Conecta un canal para empezar</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv.id)}
                  className={`w-full text-left p-4 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                    selectedConversation === conv.id ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {conv.lead_name || 'Desconocido'}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {conv.lead_source && (
                          <span className="capitalize">{conv.lead_source}</span>
                        )}
                      </p>
                      {conv.last_message_preview && (
                        <p className="text-sm text-gray-500 mt-1 truncate">
                          {conv.last_message_preview}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-gray-400 ml-2 shrink-0">
                      {conv.message_count > 0 && `${conv.message_count}`}
                    </span>
                  </div>
                </button>
              ))
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
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                        msg.direction === 'outbound'
                          ? 'bg-primary-600 text-white rounded-br-none'
                          : 'bg-gray-100 text-gray-900 rounded-bl-none'
                      }`}
                    >
                      <p className="text-sm">{msg.content}</p>
                      <div className={`flex items-center justify-end gap-1 mt-1 ${
                        msg.direction === 'outbound' ? 'text-primary-200' : 'text-gray-400'
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
                ))}
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
