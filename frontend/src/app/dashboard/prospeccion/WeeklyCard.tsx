'use client'

import { useEffect, useState } from 'react'
import { harvey, type WeeklySummary } from '@/lib/api/harvey'
import { card } from './ui'

const Stat = ({ value, label }: { value: string | number; label: string }) => (
  <div className="rounded-lg bg-slate-50 px-3 py-2">
    <p className="text-xl font-bold text-slate-900">{value}</p>
    <p className="text-xs text-slate-500">{label}</p>
  </div>
)

/** The last 7 days with Harvey and what to do next. Numbers come from the business's own data. */
export function WeeklyCard({ bid }: { bid: string }) {
  const [s, setS] = useState<WeeklySummary | null>(null)

  useEffect(() => {
    let cancelled = false
    harvey
      .weeklySummary(bid)
      .then((r) => !cancelled && setS(r))
      .catch(() => undefined) // a missing summary is not worth an error banner
    return () => {
      cancelled = true
    }
  }, [bid])

  if (!s) return null
  return (
    <section className={`${card} space-y-3`} aria-label="Tu semana con Harvey">
      <h2 className="font-semibold text-slate-900">Tu semana</h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        <Stat value={s.sent} label="emails enviados" />
        <Stat value={s.replies.total} label={`respuestas (${s.replies.interested} interesadas)`} />
        <Stat value={s.deals.created} label="oportunidades en el CRM" />
        <Stat value={s.meetings ?? 0} label="reuniones agendadas" />
        <Stat value={s.deals.won} label="ventas de Harvey" />
      </div>
      {s.next_steps.length > 0 && (
        <div>
          <h3 className="mb-1 text-sm font-semibold text-slate-900">Para hacer ahora</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {s.next_steps.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
