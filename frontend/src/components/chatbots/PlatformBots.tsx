'use client'

/**
 * Chatbots por plataforma, dentro de Conversaciones.
 *
 * One card per platform the account really has connected. Each card is both the
 * control (on/off, personality, what the bot is there to do, when to hand over
 * to a human) and the evidence (how many messages came in, how many the AI
 * actually answered, how many are still waiting).
 *
 * "Probar" runs the real generation path and shows what a buyer would receive,
 * without sending anything — and when the provider returns nothing it says so
 * rather than showing a sample written for the demo.
 */

import React, { useCallback, useEffect, useState } from 'react'
import {
  AlertTriangle, Bot, Check, ChevronDown, Loader2, MessageSquare, Play, Power, Users,
} from 'lucide-react'
import {
  chatbotsApi,
  type BotFocus, type BotsOverview, type Personality, type PlatformBot, type TestResult,
} from '@/lib/chatbots'
import { platformMeta } from '@/lib/platformMeta'

const FOCUS_HELP: Record<BotFocus, string> = {
  auto: 'Lee cada conversación y decide solo si toca atraer, cerrar o fidelizar.',
  acquisition: 'Prioriza despertar interés y sacar datos de contacto.',
  conversion: 'Prioriza resolver objeciones y cerrar la compra.',
  retention: 'Prioriza posventa: que vuelva y quede conforme.',
  expansion: 'Prioriza venderle más al que ya te compró.',
}

const BotCard = ({
  bot, personalities, onChanged,
}: {
  bot: PlatformBot
  personalities: Personality[]
  onChanged: () => void
}): React.JSX.Element => {
  const meta = platformMeta(bot.platform)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [question, setQuestion] = useState('')
  const [testing, setTesting] = useState(false)
  const [test, setTest] = useState<TestResult | null>(null)
  const [draft, setDraft] = useState({
    personality_slug: bot.personality_slug ?? '',
    focus: bot.focus,
    custom_instructions: bot.custom_instructions ?? '',
    handoff_keywords: (bot.handoff_keywords || []).join(', '),
    max_ai_replies: bot.max_ai_replies ?? '',
    // Hours are optional. Empty means "siempre", which is what a seller expects
    // when they never touched the field.
    hours_enabled: !!bot.active_hours,
    hours_from: bot.active_hours?.from ?? 9,
    hours_to: bot.active_hours?.to ?? 21,
    // Offered from the browser so the window is in the seller's own time, not
    // the server's: -(getTimezoneOffset()/60) is their real UTC offset.
    hours_offset: bot.active_hours?.utc_offset ?? -Math.round(new Date().getTimezoneOffset() / 60),
    after_hours_message: bot.after_hours_message ?? '',
    escalate_on_frustration: bot.escalate_on_frustration,
    hold_on_policy_violation: bot.hold_on_policy_violation,
  })

  const toggle = async (): Promise<void> => {
    setSaving(true)
    try {
      await chatbotsApi.update(bot.platform, { enabled: !bot.enabled })
      onChanged()
    } finally {
      setSaving(false)
    }
  }

  const save = async (): Promise<void> => {
    setSaving(true)
    try {
      await chatbotsApi.update(bot.platform, {
        personality_slug: draft.personality_slug || null,
        focus: draft.focus,
        custom_instructions: draft.custom_instructions || null,
        handoff_keywords: draft.handoff_keywords
          .split(',')
          .map(w => w.trim())
          .filter(Boolean),
        max_ai_replies: draft.max_ai_replies === '' ? null : Number(draft.max_ai_replies),
        active_hours: draft.hours_enabled
          ? { from: Number(draft.hours_from), to: Number(draft.hours_to), utc_offset: Number(draft.hours_offset) }
          : null,
        after_hours_message: draft.after_hours_message.trim() || null,
        escalate_on_frustration: draft.escalate_on_frustration,
        hold_on_policy_violation: draft.hold_on_policy_violation,
      })
      onChanged()
    } finally {
      setSaving(false)
    }
  }

  const runTest = async (): Promise<void> => {
    if (!question.trim()) return
    setTesting(true)
    try {
      setTest(await chatbotsApi.test(bot.platform, question.trim()))
    } catch {
      setTest({ ok: false, reason: 'No se pudo generar la respuesta.' })
    } finally {
      setTesting(false)
    }
  }

  const s = bot.stats
  const perf = bot.performance
  const book = bot.playbook

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      <div className="p-5 flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-3">
          <span
            className="w-9 h-9 rounded-lg grid place-items-center text-white text-xs font-bold shrink-0"
            style={{ background: meta.color }}
          >
            {meta.label.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <p className="font-semibold text-slate-900">{meta.label}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {bot.enabled
                ? `Respondiendo · ${bot.focus_label}`
                : bot.configured ? 'Apagado en esta plataforma' : 'Sin configurar'}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={toggle}
          disabled={saving}
          className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 ${
            bot.enabled
              ? 'bg-emerald-600 text-white hover:bg-emerald-700'
              : 'border border-slate-200 text-slate-700 hover:bg-slate-50'
          }`}
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Power className="w-4 h-4" />}
          {bot.enabled ? 'Encendido' : 'Encender'}
        </button>
      </div>

      <div className="px-5 pb-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Conversaciones', value: s.conversations, icon: Users },
          { label: 'Consultas recibidas', value: s.inbound, icon: MessageSquare },
          { label: 'Respondió la IA', value: s.ai_replies, icon: Bot },
          { label: 'Esperando respuesta', value: s.waiting, icon: AlertTriangle },
        ].map(stat => (
          <div key={stat.label} className="rounded-lg bg-slate-50 p-3">
            <p className="text-lg font-bold text-slate-900">{stat.value}</p>
            <p className="text-[11px] text-slate-600">{stat.label}</p>
          </div>
        ))}
      </div>

      {s.waiting > 0 && (
        <p className="px-5 pb-3 text-xs text-amber-800">
          Hay {s.waiting} conversación(es) cuyo último mensaje es del comprador y sigue sin respuesta.
        </p>
      )}

      {/* Qué logró, no cuánto escribió. Cada número con su denominador. */}
      {perf && perf.asked > 0 && (
        <div className="px-5 pb-4 space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-lg font-bold text-slate-900">
                {perf.coverage_percent !== null ? `${perf.coverage_percent}%` : '—'}
              </p>
              <p className="text-[11px] text-slate-600">Consultas que atendió la IA</p>
              <p className="text-[10px] text-slate-400">{perf.answered_by_ai} de {perf.asked}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-lg font-bold text-slate-900">
                {perf.median_first_reply_minutes !== null ? `${perf.median_first_reply_minutes} min` : '—'}
              </p>
              <p className="text-[11px] text-slate-600">Mediana hasta la 1ª respuesta</p>
              <p className="text-[10px] text-slate-400">
                {perf.latency_sample > 0 ? `n=${perf.latency_sample}` : 'todavía sin datos'}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-lg font-bold text-slate-900">{perf.held_for_human}</p>
              <p className="text-[11px] text-slate-600">Pasadas a una persona</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-lg font-bold text-slate-900">{perf.orders_after_ai}</p>
              <p className="text-[11px] text-slate-600">Órdenes donde la IA habló</p>
              <p className="text-[10px] text-slate-400">
                {Object.keys(perf.revenue_after_ai).length > 0
                  ? Object.entries(perf.revenue_after_ai)
                      .map(([cur, amount]) => `${amount.toLocaleString('es-AR', { maximumFractionDigits: 0 })} ${cur}`)
                      .join(' · ')
                  : 'sin ventas atribuidas'}
              </p>
            </div>
          </div>
          <p className="text-[11px] text-slate-500">{perf.coverage_reading}</p>
          {perf.orders_after_ai > 0 && (
            <p className="text-[11px] text-slate-400">{perf.attribution_note}</p>
          )}
          {perf.held_reasons.length > 0 && (
            <div className="text-[11px] text-slate-500">
              Por qué se pasó a una persona:
              <ul className="mt-0.5 space-y-0.5">
                {perf.held_reasons.map(r => (
                  <li key={r.reason}>· {r.reason} ({r.count})</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="px-5 pb-4">
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1"
        >
          Configurar y probar
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {open && (
        <div className="px-5 pb-5 space-y-4 border-t border-slate-100 pt-4">
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Personalidad</label>
              <select
                value={draft.personality_slug}
                onChange={e => setDraft(p => ({ ...p, personality_slug: e.target.value }))}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white text-slate-900"
              >
                <option value="">Por defecto</option>
                {personalities.map(p => (
                  <option key={p.slug} value={p.slug}>{p.emoji} {p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Para qué está este bot
              </label>
              <select
                value={draft.focus}
                onChange={e => setDraft(p => ({ ...p, focus: e.target.value as BotFocus }))}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white text-slate-900"
              >
                <option value="auto">Automático (según la conversación)</option>
                <option value="acquisition">Atraer clientes</option>
                <option value="conversion">Cerrar la venta</option>
                <option value="retention">Fidelizar / posventa</option>
                <option value="expansion">Venderle más al mismo cliente</option>
              </select>
              <p className="text-[11px] text-slate-500 mt-1">{FOCUS_HELP[draft.focus]}</p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Instrucciones tuyas
            </label>
            <textarea
              rows={3}
              value={draft.custom_instructions}
              onChange={e => setDraft(p => ({ ...p, custom_instructions: e.target.value }))}
              placeholder="Ej: nunca prometas envíos en menos de 48 h; si preguntan por talles, pedí la medida del pie."
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
            />
          </div>

          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Pasar a una persona si dicen…
              </label>
              <input
                value={draft.handoff_keywords}
                onChange={e => setDraft(p => ({ ...p, handoff_keywords: e.target.value }))}
                placeholder="reclamo, hablar con humano, estafa"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Separadas por coma. La IA deja de responder esa conversación y queda para vos.
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Máximo de respuestas seguidas de la IA
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={draft.max_ai_replies}
                onChange={e => setDraft(p => ({ ...p, max_ai_replies: e.target.value }))}
                placeholder="sin límite"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900"
              />
            </div>
          </div>

          {/* Horario: fuera de él el bot no contesta como si hubiera alguien. */}
          <div className="rounded-lg border border-slate-200 p-3 space-y-3">
            <label className="flex items-center gap-2 text-sm text-slate-800">
              <input
                type="checkbox"
                checked={draft.hours_enabled}
                onChange={e => setDraft(p => ({ ...p, hours_enabled: e.target.checked }))}
              />
              Responder solo en un horario
            </label>
            {draft.hours_enabled && (
              <>
                <div className="flex items-center gap-2 text-sm text-slate-700 flex-wrap">
                  <span>De</span>
                  <select
                    value={draft.hours_from}
                    onChange={e => setDraft(p => ({ ...p, hours_from: Number(e.target.value) }))}
                    className="px-2 py-1.5 rounded-lg border border-slate-200 bg-white"
                  >
                    {Array.from({ length: 24 }, (_, h) => <option key={h} value={h}>{h}:00</option>)}
                  </select>
                  <span>a</span>
                  <select
                    value={draft.hours_to}
                    onChange={e => setDraft(p => ({ ...p, hours_to: Number(e.target.value) }))}
                    className="px-2 py-1.5 rounded-lg border border-slate-200 bg-white"
                  >
                    {Array.from({ length: 24 }, (_, h) => <option key={h} value={h}>{h}:00</option>)}
                  </select>
                  <span className="text-xs text-slate-500">
                    en tu hora local (UTC{draft.hours_offset >= 0 ? '+' : ''}{draft.hours_offset})
                  </span>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    Qué decir fuera de horario (opcional)
                  </label>
                  <input
                    value={draft.after_hours_message}
                    onChange={e => setDraft(p => ({ ...p, after_hours_message: e.target.value }))}
                    placeholder="Gracias por escribir. Te responde una persona mañana a partir de las 9."
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Si lo dejás vacío, el bot no contesta nada y la conversación te queda marcada. Nunca
                    responde como si hubiera alguien atendiendo.
                  </p>
                </div>
              </>
            )}
          </div>

          <div className="space-y-2">
            <label className="flex items-start gap-2 text-sm text-slate-800">
              <input
                type="checkbox"
                checked={draft.escalate_on_frustration}
                onChange={e => setDraft(p => ({ ...p, escalate_on_frustration: e.target.checked }))}
                className="mt-0.5"
              />
              <span>
                Pasar a una persona si el comprador suena molesto
                <span className="block text-[11px] text-slate-500">
                  Aunque no use ninguna de las palabras de arriba.
                </span>
              </span>
            </label>
            <label className="flex items-start gap-2 text-sm text-slate-800">
              <input
                type="checkbox"
                checked={draft.hold_on_policy_violation}
                onChange={e => setDraft(p => ({ ...p, hold_on_policy_violation: e.target.checked }))}
                className="mt-0.5"
              />
              <span>
                Retener la respuesta si rompe las reglas de {meta.label}
                <span className="block text-[11px] text-slate-500">
                  Recomendado. Si la IA fuera a mandar un link o un teléfono donde la plataforma lo
                  prohíbe, queda para que lo revises en vez de salir.
                </span>
              </span>
            </label>
          </div>

          {/* Las reglas reales de esta plataforma: las mismas que aplica el backend. */}
          {book && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-sm font-medium text-slate-900">
                Reglas de {book.label}
                {book.is_default && (
                  <span className="text-[11px] text-slate-500 font-normal"> (perfil genérico)</span>
                )}
              </p>
              <p className="text-[11px] text-slate-600 mt-0.5">{book.why}</p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                <span className="text-[10px] px-1.5 py-0.5 rounded border border-slate-300 bg-white text-slate-600">
                  máx {book.max_chars} caracteres
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded border ${book.allow_links ? 'border-slate-300 bg-white text-slate-600' : 'border-amber-300 bg-amber-50 text-amber-800'}`}>
                  {book.allow_links ? 'links permitidos' : 'sin links'}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded border ${book.allow_contact_details ? 'border-slate-300 bg-white text-slate-600' : 'border-amber-300 bg-amber-50 text-amber-800'}`}>
                  {book.allow_contact_details ? 'puede dar contacto' : 'sin teléfono ni email'}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded border border-slate-300 bg-white text-slate-600">
                  tono {book.register}
                </span>
              </div>
              <ul className="mt-2 space-y-1">
                {book.rules.map(rule => (
                  <li key={rule} className="text-[11px] text-slate-600">· {rule}</li>
                ))}
              </ul>
            </div>
          )}

          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 disabled:opacity-50 inline-flex items-center gap-2"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            Guardar
          </button>

          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-900 mb-2">
              Probá qué contestaría
            </p>
            <div className="flex gap-2 flex-wrap">
              <input
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="¿Hacés envíos a Córdoba? ¿Cuánto sale?"
                className="flex-1 min-w-[220px] px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
              />
              <button
                type="button"
                onClick={runTest}
                disabled={testing || !question.trim()}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Probar
              </button>
            </div>
            {test && (
              <div className="mt-3 space-y-2">
                {test.ok ? (
                  <>
                    <p className="text-xs text-slate-500">
                      {test.would_send === false ? 'Generó esto, pero NO lo enviaría:' : 'Respondería:'}
                    </p>
                    <p className="text-sm text-slate-800 whitespace-pre-wrap rounded-lg bg-white border border-slate-200 p-3">
                      {test.reply}
                    </p>
                    {test.would_send === false && (
                      <p className="text-xs text-amber-800">
                        Quedaría para que lo revises vos: {(test.policy_problems || []).join('; ')}.
                      </p>
                    )}
                    {test.trimmed && (
                      <p className="text-[11px] text-slate-500">
                        Se recortó para entrar en el límite de la plataforma.
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-amber-800">{test.reason}</p>
                )}
                {/* Sirve para saber si lo que configuraste llega de verdad al bot. */}
                {test.brief_sources && test.brief_sources.length > 0 && (
                  <p className="text-[11px] text-slate-500">Usó: {test.brief_sources.join(' · ')}</p>
                )}
                {test.brief_missing && test.brief_missing.length > 0 && (
                  <p className="text-[11px] text-amber-700">
                    No se pudo leer: {test.brief_missing.join(' · ')}
                  </p>
                )}
                {test.within_hours === false && (
                  <p className="text-[11px] text-amber-700">
                    Ahora mismo el bot estaría {test.hours_note}: a un comprador real no le contestaría esto.
                  </p>
                )}
              </div>
            )}
            <p className="text-[11px] text-slate-500 mt-2">
              La prueba usa el mismo motor que responde a tus compradores y no le envía nada a nadie.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default function PlatformBots(): React.JSX.Element | null {
  const [data, setData] = useState<BotsOverview | null>(null)
  const [personalities, setPersonalities] = useState<Personality[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (): Promise<void> => {
    try {
      setData(await chatbotsApi.list())
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    chatbotsApi.personalities().then(setPersonalities).catch(() => setPersonalities([]))
  }, [load])

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 flex items-center gap-3 text-slate-500 text-sm">
        <Loader2 className="w-4 h-4 animate-spin" /> Leyendo tus chatbots…
      </div>
    )
  }

  if (!data || !data.has_business) return null

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-600" /> Tus chatbots de venta
        </h2>
        <p className="text-sm text-slate-600 mt-0.5">
          Uno por plataforma conectada. Cada uno lee en qué momento está la conversación —despertar
          interés, cerrar, fidelizar— y responde con el especialista que corresponde.
        </p>
      </div>

      {data.bots.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="font-medium text-slate-900">Todavía no conectaste ninguna plataforma</p>
          <p className="text-sm text-slate-600 mt-1">
            Conectá WhatsApp, Instagram o tu marketplace y acá vas a poder encender su chatbot.
          </p>
        </div>
      ) : (
        data.bots.map(bot => (
          <BotCard key={bot.platform} bot={bot} personalities={personalities} onChanged={load} />
        ))
      )}
    </div>
  )
}
