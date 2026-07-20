'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, MessageCircle, User, Bot } from 'lucide-react'

interface ChatMessage {
  role: 'user' | 'agent' | 'system'
  content: string
}

interface ComputerUseChatProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => void
  disabled?: boolean
}

export default function ComputerUseChat({ messages, onSendMessage, disabled }: ComputerUseChatProps) {
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSendMessage(input.trim())
    setInput('')
    inputRef.current?.focus()
  }

  return (
    <div className="flex flex-col h-full bg-[#0A0E1A] rounded-2xl border border-white/[0.08] overflow-hidden">
      <div className="px-4 py-3 border-b border-white/[0.06] flex items-center gap-2">
        <MessageCircle className="w-4 h-4 text-white/40" />
        <h3 className="text-sm font-semibold text-white/70">Supervisión</h3>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3 no-scrollbar">
        {messages.length === 0 && (
          <div className="text-center py-6">
            <Bot className="w-8 h-8 text-white/10 mx-auto mb-2" />
            <p className="text-xs text-white/20">El agente trabaja de forma autónoma.</p>
            <p className="text-xs text-white/20">Puedes enviar instrucciones en cualquier momento.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
              msg.role === 'user' ? 'bg-brand-orange/20' : msg.role === 'system' ? 'bg-white/10' : 'bg-brand-teal/20'
            }`}>
              {msg.role === 'user' ? (
                <User className="w-3 h-3 text-brand-orange" />
              ) : msg.role === 'system' ? (
                <MessageCircle className="w-3 h-3 text-white/40" />
              ) : (
                <Bot className="w-3 h-3 text-brand-teal" />
              )}
            </div>
            <div className={`max-w-[80%] px-3 py-2 rounded-xl text-xs ${
              msg.role === 'user'
                ? 'bg-brand-orange/10 text-white/80 border border-brand-orange/10'
                : msg.role === 'system'
                ? 'bg-white/5 text-white/50 border border-white/[0.04]'
                : 'bg-brand-teal/10 text-white/80 border border-brand-teal/10'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-3 border-t border-white/[0.06]">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={disabled ? 'Sesión finalizada' : 'Escribe una instrucción...'}
            disabled={disabled}
            className="flex-1 bg-white/5 border border-white/[0.08] rounded-xl px-3 py-2 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-brand-orange/30 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="p-2 bg-brand-orange/10 hover:bg-brand-orange/20 text-brand-orange rounded-xl border border-brand-orange/20 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  )
}
