'use client'

import { useRef, useEffect } from 'react'
import {
  MousePointerClick, Type, ScrollText, Globe, Clock, Camera,
  CheckCircle2, XCircle, AlertCircle, MousePointer, MousePointer2
} from 'lucide-react'

interface LogEntry {
  step: number
  action_type: string
  params: Record<string, any>
  reason: string
  execution_result?: string
}

interface ComputerUseLogProps {
  logs: LogEntry[]
}

const ACTION_ICONS: Record<string, any> = {
  click: MousePointerClick,
  double_click: MousePointer2,
  right_click: MousePointer,
  type: Type,
  scroll: ScrollText,
  navigate: Globe,
  wait: Clock,
  screenshot: Camera,
  done: CheckCircle2,
  error: XCircle,
}

const ACTION_COLORS: Record<string, string> = {
  click: 'text-brand-orange',
  double_click: 'text-brand-orange',
  right_click: 'text-brand-orange',
  type: 'text-brand-teal',
  scroll: 'text-white/50',
  navigate: 'text-brand-violet',
  wait: 'text-white/30',
  screenshot: 'text-white/30',
  done: 'text-green-400',
  error: 'text-red-400',
}

export default function ComputerUseLog({ logs }: ComputerUseLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [logs])

  return (
    <div className="flex flex-col h-full bg-[#0A0E1A] rounded-2xl border border-white/[0.08] overflow-hidden">
      <div className="px-4 py-3 border-b border-white/[0.06]">
        <h3 className="text-sm font-semibold text-white/70">Log de acciones</h3>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2 no-scrollbar">
        {logs.length === 0 && (
          <p className="text-xs text-white/20 text-center py-4">Esperando acciones...</p>
        )}
        {logs.map((log, i) => {
          const Icon = ACTION_ICONS[log.action_type] || AlertCircle
          const colorClass = ACTION_COLORS[log.action_type] || 'text-white/40'
          const isError = log.execution_result && log.execution_result !== 'success'

          return (
            <div
              key={i}
              className={`flex items-start gap-2.5 p-2.5 rounded-xl text-xs transition-all ${
                i === logs.length - 1 ? 'bg-white/5 border border-white/[0.06]' : ''
              }`}
            >
              <div className="mt-0.5">
                <Icon className={`w-3.5 h-3.5 ${colorClass}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-white/20 font-mono">#{log.step}</span>
                  <span className={`font-medium capitalize ${colorClass}`}>{log.action_type.replace('_', ' ')}</span>
                </div>
                <p className="text-white/40 mt-0.5 truncate">{log.reason || 'Sin descripción'}</p>
                {log.params && Object.keys(log.params).length > 0 && log.action_type !== 'done' && log.action_type !== 'error' && (
                  <p className="text-[10px] text-white/20 mt-0.5 font-mono truncate">
                    {JSON.stringify(log.params)}
                  </p>
                )}
                {isError && (
                  <p className="text-[10px] text-red-400/70 mt-0.5">{log.execution_result}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
