'use client'

/**
 * Quién del equipo está haciendo el trabajo.
 *
 * This is the honest replacement for the XP leaderboard. Three rules it keeps:
 *
 * - No invented ranking: people are ordered by replies actually sent, and the
 *   count is shown next to the position so a first place built on three replies
 *   reads as what it is.
 * - A response-time median resting on fewer than five replies is greyed out and
 *   labelled, instead of being presented as that person's speed.
 * - Revenue per person is absent on purpose, and the page says why: orders record
 *   the conversation, not who closed it.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { Clock, Info, Loader2, MessageSquare, Trophy, UserRound } from 'lucide-react'
import { logger } from '@/lib/logger'
import { teamPerformanceApi, type TeamBoard } from '@/lib/teamPerformance'

const position = (index: number): string => `${index + 1}º`

const TeamPerformance = (): React.JSX.Element => {
  const [board, setBoard] = useState<TeamBoard | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)
  const [failed, setFailed] = useState(false)

  const load = useCallback(async (): Promise<void> => {
    setLoading(true)
    setFailed(false)
    try {
      setBoard(await teamPerformanceApi.get(days))
    } catch (e) {
      logger.error(String(e))
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => { void load() }, [load])

  if (loading && !board) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-5 flex items-center gap-3 text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin" /> Midiendo el trabajo del equipo…
      </div>
    )
  }

  if (failed || !board) {
    return (
      <div className="bg-white rounded-lg border border-amber-200 p-5">
        <p className="text-sm text-slate-700">No se pudo leer el rendimiento del equipo.</p>
        <p className="text-xs text-slate-500 mt-1">No se muestran posiciones de ejemplo mientras tanto.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Trophy className="w-4 h-4 text-slate-400" />
            <h2 className="font-bold text-slate-900">Rendimiento del equipo</h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">{board.headline}</p>
        </div>
        <div className="flex gap-1">
          {[7, 30, 90].map(option => (
            <button
              key={option}
              onClick={() => setDays(option)}
              className={`px-2.5 py-1 rounded-md text-xs border transition-colors ${
                days === option
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
              }`}
            >
              {option}d
            </button>
          ))}
        </div>
      </div>

      {board.members.length === 0 ? (
        <p className="text-sm text-slate-500 mt-4">Todavía no hay nadie para medir.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-xs">
                <th className="text-left py-2 pr-2">#</th>
                <th className="text-left py-2 pr-2">Persona</th>
                <th className="text-right py-2 px-2">Respuestas</th>
                <th className="text-right py-2 px-2">Conversaciones</th>
                <th className="text-right py-2 px-2">1ª respuesta</th>
                <th className="text-right py-2 pl-2">Deals ganados</th>
              </tr>
            </thead>
            <tbody>
              {board.members.map((member, index) => (
                <tr key={member.user_id} className="border-b border-slate-100">
                  <td className="py-2.5 pr-2 text-slate-400 text-xs">{position(index)}</td>
                  <td className="py-2.5 pr-2">
                    <div className="flex items-center gap-2">
                      <UserRound className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                      <div>
                        <p className="text-slate-900 font-medium">{member.name}</p>
                        <p className="text-[11px] text-slate-400">{member.role}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5 px-2 text-right tabular-nums text-slate-800">{member.replies}</td>
                  <td className="py-2.5 px-2 text-right tabular-nums text-slate-600">{member.conversations}</td>
                  <td className="py-2.5 px-2 text-right tabular-nums">
                    {member.median_first_reply_minutes === null ? (
                      <span className="text-slate-300">—</span>
                    ) : (
                      <span
                        className={member.speed_is_readable ? 'text-slate-800' : 'text-slate-400'}
                        title={
                          member.speed_is_readable
                            ? `Mediana sobre ${member.first_reply_sample} respuestas`
                            : `Solo ${member.first_reply_sample} respuesta(s): no alcanza para hablar de velocidad`
                        }
                      >
                        {member.median_first_reply_minutes} min
                        {!member.speed_is_readable && <span className="text-[10px]"> (pocas)</span>}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pl-2 text-right tabular-nums text-slate-600">
                    {member.deals_won}
                    {member.deals_assigned > 0 && (
                      <span className="text-[11px] text-slate-400"> / {member.deals_assigned}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(board.ai_replies ?? 0) > 0 && (
        <p className="text-xs text-slate-500 mt-3 flex items-center gap-1.5">
          <MessageSquare className="w-3.5 h-3.5 text-slate-400" />
          La IA respondió {board.ai_replies} veces en el mismo período; esas no se le cuentan a ninguna persona.
        </p>
      )}

      {(board.conversations_waiting ?? 0) > 0 && (
        <p className="text-xs text-amber-800 mt-1.5 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          {board.conversations_waiting} conversación(es) esperando a una persona ahora mismo.
        </p>
      )}

      {board.gaps.length > 0 && (
        <div className="mt-4 border-t border-slate-100 pt-3 space-y-1">
          {board.gaps.map(gap => (
            <p key={gap} className="text-[11px] text-slate-500 flex items-start gap-1.5">
              <Info className="w-3 h-3 mt-0.5 shrink-0 text-slate-400" />
              {gap}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

export default TeamPerformance
