'use client'

import { useEffect, useState } from 'react'
import { MessageCircle, Send, AlertCircle, Check, Loader } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface PlatformStatus {
  whatsapp: { connected: boolean }
  telegram: { connected: boolean }
}

interface Conversation {
  contact_id: string
  contact_name: string
  last_message_at: string
  message_count: number
  unread_count: number
  status: string
}

interface Message {
  id: string
  direction: string
  content: string
  status: string
  timestamp: string
}

interface ChannelStats {
  total_messages: number
  inbound: number
  outbound: number
  delivery_rate: string
  avg_response_time: string
  active_conversations: number
  last_activity: string
}

export default function IntegrationPanel({ userId }: { userId: string }) {
  const [status, setStatus] = useState<PlatformStatus>({ whatsapp: { connected: false }, telegram: { connected: false } })
  const [selectedPlatform, setSelectedPlatform] = useState<'whatsapp' | 'telegram'>('whatsapp')
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [stats, setStats] = useState<ChannelStats | null>(null)
  const [messageInput, setMessageInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)

  useEffect(() => {
    fetchIntegrationStatus()
    fetchChannelStats()
    fetchConversations()
  }, [userId, selectedPlatform])

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const fetchIntegrationStatus = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/integrations/status/${userId}`)
      if (res.ok) {
        const data = await res.json()
        setStatus(data.platforms)
      }
    } catch (error) {
      console.error('Status fetch error:', error)
    }
  }

  const fetchChannelStats = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/integrations/stats/${userId}?platform=${selectedPlatform}`)
      if (res.ok) {
        const data = await res.json()
        setStats(data.stats)
      }
    } catch (error) {
      console.error('Stats fetch error:', error)
    }
  }

  const fetchConversations = async () => {
    try {
      setLoading(true)
      const res = await fetch(
        `${apiUrl}/api/v1/integrations/conversations/${userId}?platform=${selectedPlatform}&limit=20`
      )
      if (res.ok) {
        const data = await res.json()
        setConversations(data.conversations || [])
      }
    } catch (error) {
      console.error('Conversations fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchMessages = async (contact_id: string) => {
    try {
      const res = await fetch(
        `${apiUrl}/api/v1/integrations/messages/${userId}?platform=${selectedPlatform}&contact_id=${contact_id}&limit=50`
      )
      if (res.ok) {
        const data = await res.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Messages fetch error:', error)
    }
  }

  const handleSendMessage = async () => {
    if (!selectedConversation || !messageInput.trim()) return

    try {
      const res = await fetch(`${apiUrl}/api/v1/integrations/send-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          platform: selectedPlatform,
          contact_id: selectedConversation.contact_id,
          content: messageInput,
        }),
      })

      if (res.ok) {
        setMessageInput('')
        fetchMessages(selectedConversation.contact_id)
      }
    } catch (error) {
      console.error('Send message error:', error)
    }
  }

  const handleConnectPlatform = async () => {
    setConnecting(true)
    try {
      const res = await fetch(`${apiUrl}/api/v1/integrations/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          platform: selectedPlatform,
          account_id: 'account_123',
          api_key: 'key_' + Math.random().toString(36).substr(2, 9),
          api_secret: 'secret_' + Math.random().toString(36).substr(2, 9),
        }),
      })

      if (res.ok) {
        fetchIntegrationStatus()
      }
    } catch (error) {
      console.error('Connect error:', error)
    } finally {
      setConnecting(false)
    }
  }

  const isConnected = status[selectedPlatform]?.connected || false

  return (
    <div className="space-y-6">
      {/* Platform Selector & Status */}
      <div className="flex gap-4 flex-wrap">
        {['whatsapp', 'telegram'].map((platform) => (
          <button
            key={platform}
            onClick={() => {
              setSelectedPlatform(platform as 'whatsapp' | 'telegram')
              setSelectedConversation(null)
            }}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedPlatform === platform
                ? 'border-brand-orange bg-orange-50'
                : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            <div className="flex items-center gap-3">
              <MessageCircle className="w-5 h-5" />
              <div className="text-left">
                <p className="font-semibold text-brand-night capitalize">{platform}</p>
                <p className={`text-xs ${isConnected ? 'text-green-600' : 'text-slate-600'}`}>
                  {isConnected ? '✓ Connected' : '○ Not connected'}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Connection Card */}
      {!isConnected ? (
        <Card className="p-6 border-l-4 border-l-orange-500 bg-orange-50">
          <div className="flex items-start justify-between">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-1" />
              <div>
                <p className="font-semibold text-brand-night">Connect {selectedPlatform.charAt(0).toUpperCase() + selectedPlatform.slice(1)}</p>
                <p className="text-sm text-slate-600 mt-1">
                  {selectedPlatform === 'whatsapp'
                    ? 'Connect your WhatsApp Business Account to send and receive messages'
                    : 'Connect your Telegram Bot to handle conversations'}
                </p>
              </div>
            </div>
            <button
              onClick={handleConnectPlatform}
              disabled={connecting}
              className="px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 flex items-center gap-2"
            >
              {connecting ? <Loader className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              {connecting ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        </Card>
      ) : (
        <>
          {/* Stats */}
          {stats && (
            <Card className="p-6">
              <h3 className="font-semibold text-brand-night mb-4">Channel Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-slate-600">Total Messages</p>
                  <p className="text-2xl font-bold text-brand-night">{stats.total_messages}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Delivery Rate</p>
                  <p className="text-2xl font-bold text-green-600">{stats.delivery_rate}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Avg Response</p>
                  <p className="text-2xl font-bold text-brand-night">{stats.avg_response_time}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Active Conversations</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.active_conversations}</p>
                </div>
              </div>
            </Card>
          )}

          {/* Conversations & Messages */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Conversation List */}
            <Card className="p-4">
              <h3 className="font-semibold text-brand-night mb-4">Conversations</h3>
              {loading ? (
                <div className="text-center py-8 text-slate-500">Loading...</div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">No conversations yet</div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {conversations.map((conv) => (
                    <button
                      key={conv.contact_id}
                      onClick={() => {
                        setSelectedConversation(conv)
                        fetchMessages(conv.contact_id)
                      }}
                      className={`w-full p-3 text-left rounded-lg transition-colors ${
                        selectedConversation?.contact_id === conv.contact_id
                          ? 'bg-orange-100 border border-brand-orange'
                          : 'bg-slate-100 hover:bg-slate-200'
                      }`}
                    >
                      <p className="font-medium text-sm text-brand-night">{conv.contact_name}</p>
                      <p className="text-xs text-slate-600 mt-1">{conv.message_count} messages</p>
                      {conv.unread_count > 0 && (
                        <span className="inline-block mt-2 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">
                          {conv.unread_count} unread
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </Card>

            {/* Message Thread */}
            <Card className="lg:col-span-2 p-4 flex flex-col">
              {selectedConversation ? (
                <>
                  <h3 className="font-semibold text-brand-night mb-4">{selectedConversation.contact_name}</h3>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto space-y-3 mb-4 max-h-64 bg-slate-50 p-4 rounded-lg">
                    {messages.length === 0 ? (
                      <p className="text-center text-slate-500 text-sm py-8">No messages</p>
                    ) : (
                      messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`px-3 py-2 rounded-lg text-sm max-w-xs ${
                              msg.direction === 'outbound'
                                ? 'bg-brand-orange text-white'
                                : 'bg-slate-200 text-brand-night'
                            }`}
                          >
                            <p>{msg.content}</p>
                            <p className="text-xs opacity-70 mt-1">
                              {new Date(msg.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      placeholder="Type message..."
                      className="flex-1 px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-brand-orange"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={!messageInput.trim()}
                      className="px-4 py-2 bg-brand-orange text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center h-64 text-slate-500">
                  <p>Select conversation to view messages</p>
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

