'use client'

import { useCallback, useEffect, useState } from 'react'
import { Check, Inbox, Pencil, Send, X } from 'lucide-react'
import Button from '@/components/ui/Button'
import { errMsg, harvey, type OutboxItem } from '@/lib/api/harvey'
import { Badge, card, fmtDate, input, Notice, useAction } from './ui'

const FILTERS: { value: string; label: string }[] = [
  { value: 'open', label: 'Pendientes' },
  { value: 'approved', label: 'Aprobados' },
  { value: 'sent', label: 'Enviados' },
  { value: 'all', label: 'Todos' },
]

const matches = (filter: string, status: string): boolean => {
  if (filter === 'all') return true
  if (filter === 'open') return status === 'pending_review' || status === 'blocked' || status === 'failed'
  return status === filter
}

function Draft({ bid, item, onUpdated }: { bid: string; item: OutboxItem; onUpdated: () => Promise<void> }) {
  const editable = item.status === 'pending_review' || item.status === 'blocked'
  const [subject, setSubject] = useState(item.subject)
  const [body, setBody] = useState(item.body)
  const { busy, notice, run } = useAction()
  const dirty = subject !== item.subject || body !== item.body

  useEffect(() => {
    setSubject(item.subject)
    setBody(item.body)
  }, [item.subject, item.body])

  const act = (key: string, fn: () => Promise<OutboxItem>, text: string) =>
    run(key, fn, () => text).then(() => onUpdated())

  return (
    <article className={`${card} space-y-3`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-slate-900">{item.to_email}</span>
          <Badge value={item.status} />
          <span className="text-xs text-slate-500">
            {item.kind === 'reply' ? 'Respuesta' : `Email ${item.step} de 3`} · {fmtDate(item.sent_at ?? item.created_at)}
          </span>
        </div>
      </div>

      {editable ? (
        <>
          <input className={input} value={subject} onChange={(e) => setSubject(e.target.value)} aria-label="Asunto" />
          <textarea
            className={`${input} min-h-[140px] font-sans`}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            aria-label="Cuerpo del email"
          />
        </>
      ) : (
        <div className="space-y-1">
          <p className="text-sm font-medium text-slate-900">{item.subject}</p>
          <p className="whitespace-pre-wrap text-sm text-slate-600">{item.body}</p>
        </div>
      )}

      {item.gate_reasons.length > 0 && (
        <ul className="list-disc space-y-0.5 pl-5 text-xs text-red-700">
          {item.gate_reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      )}
      {item.send_error && <p className="text-xs text-red-700">Último error de envío: {item.send_error}</p>}

      <div className="flex flex-wrap items-center gap-2">
        {editable && dirty && (
          <Button size="sm" variant="secondary" leftIcon={<Pencil className="h-4 w-4" />} isLoading={busy === 'edit'}
            onClick={() => act('edit', () => harvey.edit(bid, item.id, subject, body), 'Cambios guardados')}>
            Guardar cambios
          </Button>
        )}
        {item.status === 'pending_review' && !dirty && (
          <Button size="sm" leftIcon={<Check className="h-4 w-4" />} isLoading={busy === 'approve'}
            onClick={() => act('approve', () => harvey.approve(bid, item.id), 'Aprobado')}>
            Aprobar
          </Button>
        )}
        {(item.status === 'pending_review' || item.status === 'blocked') && (
          <Button size="sm" variant="ghost" leftIcon={<X className="h-4 w-4" />} isLoading={busy === 'reject'}
            onClick={() => act('reject', () => harvey.reject(bid, item.id), 'Rechazado')}>
            Rechazar
          </Button>
        )}
        {item.status === 'approved' && (
          <Button size="sm" leftIcon={<Send className="h-4 w-4" />} isLoading={busy === 'send'}
            onClick={() => act('send', () => harvey.send(bid, item.id), 'Enviado')}>
            Enviar ahora
          </Button>
        )}
      </div>
      <Notice notice={notice} />
    </article>
  )
}

export function ApprovalTab({ bid, onChange }: { bid: string; onChange: () => Promise<void> }) {
  const [items, setItems] = useState<OutboxItem[]>([])
  const [filter, setFilter] = useState('open')
  const [loadError, setLoadError] = useState<string | null>(null)
  const { busy, notice, run } = useAction()

  const load = useCallback(async () => {
    try {
      setItems(await harvey.outbox(bid))
      setLoadError(null)
    } catch (e) {
      setLoadError(errMsg(e))
    }
  }, [bid])

  useEffect(() => {
    void load()
  }, [load])

  const refreshAll = async () => {
    await load()
    await onChange()
  }

  const counts = (c: Record<string, number>) =>
    Object.entries(c)
      .filter(([, n]) => n > 0)
      .map(([k, n]) => `${n} ${k.replace(/_/g, ' ')}`)
      .join(', ') || 'nada para hacer'

  const visible = items.filter((i) => matches(filter, i.status))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" leftIcon={<Send className="h-4 w-4" />} isLoading={busy === 'send'}
          onClick={() => run('send', () => harvey.sendApproved(bid), (r) => `Envío: ${counts(r.counts)}`).then(refreshAll)}>
          Enviar aprobados
        </Button>
        <Button size="sm" variant="secondary" isLoading={busy === 'seq'}
          onClick={() => run('seq', () => harvey.runSequences(bid), (r) => `Seguimientos: ${counts(r.counts)}`).then(refreshAll)}>
          Redactar seguimientos
        </Button>
        <Button size="sm" variant="secondary" leftIcon={<Inbox className="h-4 w-4" />} isLoading={busy === 'sync'}
          onClick={() => run('sync', () => harvey.syncInbox(bid), (r) => `Bandeja: ${counts(r.counts)}`).then(refreshAll)}>
          Leer respuestas
        </Button>
        <select className={`${input} ml-auto w-auto`} value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filtro">
          {FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>
      <Notice notice={notice} />
      {loadError && <p className="text-sm text-red-700">{loadError}</p>}

      {visible.length === 0 ? (
        <p className={`${card} text-sm text-slate-500`}>
          No hay emails en esta vista. Cargá prospectos y redactá el primer borrador desde la pestaña Prospectos.
        </p>
      ) : (
        visible.map((item) => <Draft key={item.id} bid={bid} item={item} onUpdated={refreshAll} />)
      )}
    </div>
  )
}
