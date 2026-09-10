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
              <div className="mt-3">
                {test.ok ? (
                  <>
                    <p className="text-xs text-slate-500 mb-1">Respondería:</p>
                    <p className="text-sm text-slate-800 whitespace-pre-wrap rounded-lg bg-white border border-slate-200 p-3">
                      {test.reply}
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-amber-800">{test.reason}</p>
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
