'use client'

import { useCallback, useEffect, useState } from 'react'
import { MessageSquareReply } from 'lucide-react'
import Button from '@/components/ui/Button'
import { errMsg, harvey, type HarveyReply } from '@/lib/api/harvey'
import { Badge, card, fmtDate, Notice, useAction } from './ui'

const ANSWERABLE = ['interested', 'question', 'objection']

export function RepliesTab({
  bid, onChange, goToApproval,
}: { bid: string; onChange: () => Promise<void>; goToApproval: () => void }) {
  const [replies, setReplies] = useState<HarveyReply[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const { busy, notice, run } = useAction()

  const load = useCallback(async () => {
    try {
      setReplies(await harvey.replies(bid))
      setLoadError(null)
    } catch (e) {
      setLoadError(errMsg(e))
    }
  }, [bid])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-4">
      <Notice notice={notice} />
      {loadError && <p className="text-sm text-red-700">{loadError}</p>}
      {replies.length === 0 && (
        <p className={`${card} text-sm text-slate-500`}>
          Todavía nadie respondió. Las respuestas se leen solas de tu casilla; también podés usar &quot;Leer respuestas&quot; en
          Aprobación.
        </p>
      )}
      {replies.map((r) => (
        <article key={r.id} className={`${card} space-y-3`}>
          <div className="flex flex-wrap items-center gap-2">
            <Badge value={r.classification} tone={ANSWERABLE.includes(r.classification) ? 'good' : undefined} />
            {r.needs_human && <Badge value="handoff" tone="warn" />}
            <span className="text-xs text-slate-500">{fmtDate(r.created_at)}</span>
          </div>
          <p className="whitespace-pre-wrap text-sm text-slate-700">{r.body}</p>
          {ANSWERABLE.includes(r.classification) && r.draft_answer && (
            <div className="space-y-2 border-t border-slate-200 pt-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Respuesta sugerida</p>
              <p className="whitespace-pre-wrap text-sm text-slate-600">{r.draft_answer}</p>
              <Button size="sm" leftIcon={<MessageSquareReply className="h-4 w-4" />} isLoading={busy === r.id}
                onClick={() =>
                  run(r.id, () => harvey.answerReply(bid, r.id), () => 'Respuesta lista para aprobar')
                    .then((item) => { if (item) goToApproval() })
                    .then(onChange)
                }>
                Preparar respuesta
              </Button>
            </div>
          )}
        </article>
      ))}
    </div>
  )
}
