'use client'

import { Check, Clock, Copy, Loader2, Trash2, Zap, AlertCircle, CheckCircle2, PauseCircle } from 'lucide-react'
import type { ChannelConnection } from '@/lib/channels'
import { canSwitchAccount, channelTitle, isIncomplete, needsReconnect, platformMeta, stateBadge } from '@/lib/channelCatalog'

const STATE_ICON = {
  connected: CheckCircle2,
  toVerify: Clock,
  incomplete: PauseCircle,
  error: AlertCircle,
  other: PauseCircle,
} as const

const fmtDate = (iso: string | null): string => (iso ? new Date(iso).toLocaleString('es-AR', { dateStyle: 'medium', timeStyle: 'short' }) : null) ?? ''

interface Props {
  channel: ChannelConnection
  testing: boolean
  copied: boolean
  onTest: () => void
  onComplete: () => void
  onSwitchAccount: () => void
  onDelete: () => void
  onCopyWebhook: (url: string) => void
}

export function ChannelCard({ channel, testing, copied, onTest, onComplete, onSwitchAccount, onDelete, onCopyWebhook }: Props) {
  const meta = platformMeta(channel.platform)
  const incomplete = isIncomplete(channel)
  const reconnect = needsReconnect(channel)
  const style = stateBadge(channel)
  const StatusIcon = STATE_ICON[style.state]
  const switchable = canSwitchAccount(channel.platform) && !incomplete && !reconnect
  const title = channelTitle(channel)
  const Icon = meta.icon

  return (
    <article className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${meta.tile}`} aria-hidden="true">
          <Icon className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h3 className="font-semibold text-slate-900">{meta.label}</h3>
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${style.pill}`}>
              <StatusIcon className="h-3.5 w-3.5" aria-hidden="true" />
              {style.label}
            </span>
          </div>
          <p className="mt-0.5 truncate text-sm text-slate-500">{channel.account?.name ?? meta.description}</p>
        </div>
        <button
          type="button"
          onClick={onDelete}
          aria-label={`${incomplete ? 'Quitar' : 'Desconectar'} ${title}`}
          title={incomplete ? 'Quitar' : 'Desconectar'}
          className="-mr-1 -mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {!incomplete && (channel.account?.name ? (channel.account.id || channel.account.detail) : true) && (
        <div className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
          {channel.account?.name ? (
            <>
              {channel.account.id && channel.account.id !== channel.account.name && (
                <span className="block text-slate-500">ID {channel.account.id}</span>
              )}
              {channel.account.detail && <span className="block text-slate-500">{channel.account.detail}</span>}
            </>
          ) : reconnect ? (
            <>Figura conectado pero no hay credenciales guardadas. Autorizá de nuevo para que funcione.</>
          ) : (
            <>Cuenta no identificada. {canSwitchAccount(channel.platform) ? 'Volvé a autorizar para ver cuál es.' : ''}</>
          )}
        </div>
      )}

      {incomplete && (
        <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
          Empezaste a conectar esta cuenta pero no terminaste la autorización. Todavía no recibe ni envía nada.
        </p>
      )}

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

      <div className="mt-auto flex flex-wrap items-center justify-between gap-x-3 gap-y-2 pt-4">
        <p className="w-full text-xs text-slate-400">
          {incomplete
            ? ''
            : channel.last_sync_at
              ? `Última verificación: ${fmtDate(channel.last_sync_at)}`
              : channel.status === 'connected'
                ? 'Autorizado · todavía sin actividad'
                : 'Todavía no probaste la conexión'}
        </p>
        {incomplete || reconnect ? (
          <button
            type="button"
            onClick={onComplete}
            className="inline-flex h-10 items-center gap-1.5 rounded-lg bg-brand-orange px-3 text-sm font-semibold text-white transition-colors hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2"
          >
            {reconnect ? 'Reconectar' : 'Completar conexión'}
          </button>
        ) : (
          <button
            type="button"
            onClick={onTest}
            disabled={testing}
            className="inline-flex h-10 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange disabled:opacity-50"
          >
            {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            Probar
          </button>
        )}
        {switchable && (
          <button
            type="button"
            onClick={onSwitchAccount}
            className="inline-flex h-10 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
          >
            Cambiar de cuenta
          </button>
        )}
      </div>
    </article>
  )
}
