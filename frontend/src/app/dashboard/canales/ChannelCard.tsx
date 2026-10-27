'use client'

import { Check, Clock, Copy, Loader2, Trash2, Zap, AlertCircle, CheckCircle2, PauseCircle } from 'lucide-react'
import type { ChannelConnection } from '@/lib/channels'
import { platformMeta, STATUS_STYLE } from './catalog'

const STATUS_ICON = {
  connected: CheckCircle2,
  pending: Clock,
  error: AlertCircle,
  disabled: PauseCircle,
} as const

const fmtDate = (iso: string | null): string => (iso ? new Date(iso).toLocaleString('es-AR', { dateStyle: 'medium', timeStyle: 'short' }) : null) ?? ''

interface Props {
  channel: ChannelConnection
  testing: boolean
  copied: boolean
  onTest: () => void
  onDelete: () => void
  onCopyWebhook: (url: string) => void
}

export function ChannelCard({ channel, testing, copied, onTest, onDelete, onCopyWebhook }: Props) {
  const meta = platformMeta(channel.platform)
  const style = STATUS_STYLE[channel.status] ?? STATUS_STYLE.pending
  const StatusIcon = STATUS_ICON[channel.status] ?? Clock
  const Icon = meta.icon

  return (
    <article className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${meta.tile}`} aria-hidden="true">
          <Icon className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold text-slate-900">{channel.name}</h3>
          <p className="truncate text-sm text-slate-500">{meta.label}</p>
        </div>
        <button
          type="button"
          onClick={onDelete}
          aria-label={`Desconectar ${channel.name}`}
          title="Desconectar"
          className="-mr-1 -mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      <div className="mt-4">
        <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${style.pill}`}>
          <StatusIcon className="h-3.5 w-3.5" aria-hidden="true" />
          {style.label}
        </span>
      </div>

      {channel.status === 'error' && channel.status_message && (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-800">{channel.status_message}</p>
      )}

      {channel.webhook_url && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2">
          <p className="min-w-0 flex-1 truncate font-mono text-xs text-slate-500" title={channel.webhook_url}>
            {channel.webhook_url}
          </p>
          <button
            type="button"
            onClick={() => onCopyWebhook(channel.webhook_url as string)}
            aria-label="Copiar URL del webhook"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-slate-500 hover:bg-slate-200 hover:text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
          >
            {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
          </button>
        </div>
      )}

      <div className="mt-auto flex items-center justify-between gap-3 pt-4">
        <p className="text-xs text-slate-400">
          {channel.last_sync_at ? `Última verificación: ${fmtDate(channel.last_sync_at)}` : 'Sin verificar todavía'}
        </p>
        <button
          type="button"
          onClick={onTest}
          disabled={testing}
          className="inline-flex h-10 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange disabled:opacity-50"
        >
          {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
          Probar
        </button>
      </div>
    </article>
  )
}
