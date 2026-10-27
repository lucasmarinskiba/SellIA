'use client'

/**
 * Plataformas — la misma información de Canales, vista por plataforma.
 *
 * Lee las mismas conexiones reales (channel_connections) que Canales y decide el estado con la MISMA función
 * (`lib/channelState`), así que una plataforma nunca figura "Conectada" acá y "Por verificar" o "Sin completar"
 * en Canales. Conectar, completar o administrar siempre lleva al flujo único de Canales; lo que se hace allá se
 * ve acá al instante porque es la misma fila. Además muestra la actividad real de cada una (conversaciones y
 * respuestas de la IA), que Canales no muestra.
 */

import Link from 'next/link'
import { ArrowRight, Loader2, Plug } from 'lucide-react'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'
import { CATEGORIES, PLATFORMS, channelState, platformMeta, stateBadge, STATE_LABEL, type ChannelState } from '@/lib/channelCatalog'
import { useChannels } from '@/lib/useChannels'

const SUMMARY: Exclude<ChannelState, 'other'>[] = ['connected', 'toVerify', 'incomplete', 'error']

const ACTION: Record<ChannelState | 'none', string> = {
  none: 'Conectar',
  incomplete: 'Completar conexión',
  toVerify: 'Probar en Canales',
  error: 'Resolver en Canales',
  connected: 'Administrar en Canales',
  other: 'Ver en Canales',
}

export default function PlatformsPage() {
  const { channels, businessId, loading: loadingChannels, unavailable } = useChannels()
  const { snapshot, loading: loadingSnapshot } = useBusinessSnapshot()
  const loading = loadingChannels || loadingSnapshot
  const activity = snapshot?.channels ?? []

  const counts = SUMMARY.map((state) => ({ state, n: channels.filter((c) => channelState(c) === state).length }))

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Plataformas</h1>
          <p className="mt-1 text-slate-600">Qué está realmente conectado a tu cuenta y qué actividad tuvo, por plataforma.</p>
        </div>
        <Link
          href="/dashboard/canales"
          className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2"
        >
          <Plug className="h-4 w-4" aria-hidden="true" /> Administrar canales <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </header>

      {loading && (
        <div className="flex items-center gap-3 py-10 text-slate-500">
          <Loader2 className="h-5 w-5 animate-spin" /> Leyendo tus conexiones…
        </div>
      )}

      {!loading && unavailable && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
          <p className="mt-1 text-sm text-slate-600">No se marca ninguna plataforma como conectada sin poder verificarlo.</p>
        </div>
      )}

      {!loading && !unavailable && (
        <>
          <section aria-label="Resumen" className="flex flex-wrap gap-2">
            {counts.map(({ state, n }) => (
              <Link
                key={state}
                href="/dashboard/canales"
                className="inline-flex h-10 items-center gap-2 rounded-full border border-slate-200 bg-white px-4 text-sm text-slate-700 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
              >
                <strong className="tabular-nums text-slate-900">{n}</strong> {STATE_LABEL[state]}
              </Link>
            ))}
          </section>

          {CATEGORIES.map((cat) => {
            const items = Object.keys(PLATFORMS).filter((p) => PLATFORMS[p].category === cat.key)
            return (
              <section key={cat.key} aria-labelledby={`cat-${cat.key}`} className="space-y-3">
                <h2 id={`cat-${cat.key}`} className="text-sm font-semibold text-slate-700">
                  {cat.label} <span className="font-normal text-slate-400">· {cat.hint}</span>
                </h2>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {items.map((platform) => {
                    const meta = platformMeta(platform)
                    const Icon = meta.icon
                    const mine = channels.filter((c) => c.platform === platform)
                    const conn = mine[0]
                    const badge = conn ? stateBadge(conn) : null
                    const seen = conn ? activity.find((a) => a.platform === conn.platform && a.name === conn.name) : undefined
                    const action = ACTION[conn ? badge!.state : 'none']
                    const href = !conn || badge!.state === 'incomplete' ? `/dashboard/canales?connect=${platform}` : '/dashboard/canales'
                    return (
                      <article key={platform} className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                        <div className="flex items-start gap-3">
                          <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${meta.tile}`} aria-hidden="true">
                            <Icon className="h-5 w-5" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                              <h3 className="font-semibold text-slate-900">{meta.label}</h3>
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${
                                  badge ? badge.pill : 'bg-slate-50 text-slate-600 ring-slate-200'
                                }`}
                              >
                                {badge ? badge.label : 'Sin conectar'}
                              </span>
                            </div>
                            <p className="mt-0.5 truncate text-sm text-slate-500">{conn?.account?.name ?? meta.description}</p>
                          </div>
                        </div>

                        {conn && badge!.state !== 'incomplete' && (
                          <p className="mt-3 text-xs text-slate-600">
                            {seen
                              ? `${seen.conversations} conversación(es) · ${seen.ai_replies} respondidas por la IA`
                              : 'Sin actividad registrada todavía'}
                            {mine.length > 1 && <span className="text-slate-400"> · +{mine.length - 1} conexión(es) más</span>}
                          </p>
                        )}

                        <Link
                          href={href}
                          className={`mt-4 inline-flex h-10 items-center justify-center gap-2 self-start rounded-lg px-4 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange ${
                            !conn || badge!.state === 'incomplete'
                              ? 'bg-brand-orange text-white hover:bg-brand-orange-dark'
                              : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                          }`}
                        >
                          {action} <ArrowRight className="h-4 w-4" aria-hidden="true" />
                        </Link>
                      </article>
                    )
                  })}
                </div>
              </section>
            )
          })}

          {!businessId && (
            <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-600">
              Todavía no configuraste tu negocio, así que no hay conexiones para mostrar.{' '}
              <Link href="/sellia-onboarding" className="font-semibold text-brand-orange underline">Configurarlo ahora</Link>.
            </p>
          )}
        </>
      )}
    </div>
  )
}
