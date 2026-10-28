'use client'

import { useState } from 'react'
import Button from '@/components/ui/Button'
import { harvey, type DomainCheck } from '@/lib/api/harvey'
import { card, Notice, useAction } from './ui'

const TONE: Record<string, string> = {
  ok: 'bg-emerald-50 text-emerald-800',
  warn: 'bg-amber-50 text-amber-800',
  bad: 'bg-red-50 text-red-800',
  unknown: 'bg-slate-100 text-slate-600',
}
const MARK: Record<string, string> = { ok: 'Bien', warn: 'Mejorable', bad: 'Falta', unknown: 'Sin confirmar' }

/** Will the connected mailbox's emails reach the inbox? Plain-words result with what to do for each item. */
export function DeliverabilityCard({ bid }: { bid: string }) {
  const [result, setResult] = useState<DomainCheck | null>(null)
  const { busy, notice, run } = useAction()

  return (
    <section className={`${card} space-y-3`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="font-semibold text-slate-900">¿Llegan tus emails a la bandeja?</h2>
          <p className="mt-1 text-sm text-slate-600">
            Revisamos la configuración pública de tu dominio. Si falta algo, muchos emails terminan en spam.
          </p>
        </div>
        <Button size="sm" variant="secondary" isLoading={busy === 'check'}
          onClick={() => run('check', () => harvey.deliverability(bid), () => 'Revisión lista').then((r) => r && setResult(r))}>
          Revisar mi dominio
        </Button>
      </div>
      <Notice notice={notice} />
      {result?.free_mail && (
        <p className="text-sm text-slate-700">
          Tu casilla es de un proveedor grande (Gmail, Outlook…): ellos ya configuran todo esto por vos. No hay nada que revisar.
        </p>
      )}
      {result && !result.free_mail && (
        <ul className="space-y-2">
          {result.items.map((i) => (
            <li key={i.key} className="rounded-lg border border-slate-200 p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${TONE[i.status]}`}>{MARK[i.status]}</span>
                <span className="font-medium text-slate-900">{i.title}</span>
              </div>
              <p className="mt-1 text-slate-600">{i.detail}</p>
              {i.fix && i.status !== 'ok' && <p className="mt-1 text-slate-800"><strong>Qué hacer:</strong> {i.fix}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
