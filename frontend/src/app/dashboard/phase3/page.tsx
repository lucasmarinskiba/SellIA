'use client'

/**
 * Construya Autoridad — señales reales de confianza de la cuenta.
 *
 * Antes mostraba "Trust & Authority Score 82.5 GOLD" con barras llenas: ese
 * número venía de un backend que lo generaba con random.uniform() para
 * cualquier vendedor (y cambiaba en cada recarga), o directamente de un
 * fallback hardcodeado en el front. Ahora:
 *  - el score sale de /authority/trust-score/{negocio}, calculado sobre
 *    reseñas, testimonios y premios REALES; si no hay ninguno, lo dice.
 *  - las señales verificables (email, 2FA, dominio, sitio publicado, tasa de
 *    respuesta real de las conversaciones) salen del snapshot de la cuenta.
 */

import React, { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import {
  CheckCircle2, XCircle, Loader2, Award, MessageSquare, ExternalLink, Link2, Network, AlertCircle,
} from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'
import LinksManager from '@/components/web-presence/LinksManager'
import { webPresenceApi, type AuthorityReport } from '@/lib/webPresence'

interface TrustScore {
  available: boolean
  reason?: string
  trust_score?: number
  tier?: string
  components: Record<string, number>
  next_tier?: string | null
  points_to_next?: number
}

const TIER_LABEL: Record<string, string> = {
  bronze: 'Bronce', silver: 'Plata', gold: 'Oro', platinum: 'Platino',
}

export default function AutoridadPage(): React.JSX.Element {
  const { snapshot, loading: snapLoading, unavailable } = useBusinessSnapshot()
  const [trust, setTrust] = useState<TrustScore | null>(null)
  const [loadingTrust, setLoadingTrust] = useState(true)
  const [authority, setAuthority] = useState<AuthorityReport | null>(null)

  const businessId = snapshot?.business.id ?? null

  // La red de marca: si tu web, tus redes y tus tiendas no se enlazan entre sí,
  // Google las trata como negocios distintos y ninguna hereda la autoridad de
  // las otras. Esto se chequea sobre las páginas reales, no sobre una lista.
  const loadAuthority = useCallback((): void => {
    webPresenceApi.authorityReport().then(setAuthority).catch(() => setAuthority(null))
  }, [])

  useEffect(() => { loadAuthority() }, [loadAuthority])

  useEffect(() => {
    if (!businessId) { setLoadingTrust(false); return }
    let alive = true
    api.get<TrustScore>(`/authority/trust-score/${businessId}`)
      .then(res => { if (alive) setTrust(res.data) })
      .catch(() => { /* sin datos -> estado honesto abajo */ })
      .finally(() => { if (alive) setLoadingTrust(false) })
    return () => { alive = false }
  }, [businessId])

  const v = snapshot?.verification
  const c = snapshot?.conversations

  // Cada señal es verificable contra una fila real de la base.
  const signals = [
    { label: 'Email verificado', ok: !!v?.email_verified, help: 'Confirmá tu email desde Configuración.' },
    { label: 'Verificación en dos pasos', ok: !!v?.two_factor_enabled, help: 'Activá 2FA: es una señal de cuenta seria.' },
    { label: 'Negocio creado', ok: !!v?.has_business, help: 'Creá tu negocio para tener identidad propia.' },
    { label: 'Sitio publicado', ok: !!v?.website_published, help: 'Publicá tu sitio para que sea indexable y citable.' },
    { label: 'Dominio verificado', ok: !!v?.domain_verified, help: 'Verificá tu dominio para reclamar autoría del contenido.' },
    { label: 'Canal de atención conectado', ok: (snapshot?.channels.length ?? 0) > 0, help: 'Conectá al menos un canal (WhatsApp, Instagram, MercadoLibre…).' },
  ]
  const signalsOk = signals.filter(s => s.ok).length

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-1">Construya Autoridad</h1>
        <p className="text-slate-600">
          Señales E-E-A-T reales de tu cuenta: experiencia, respuesta a clientes y verificaciones.
        </p>
      </div>

      {snapLoading && (
        <div className="flex items-center gap-3 text-slate-500 py-16 justify-center">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo las señales de tu cuenta…
        </div>
      )}

      {!snapLoading && unavailable && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
          <p className="text-sm text-slate-600 mt-1">
            No se muestra un score estimado mientras tanto: sin datos reales, no hay número.
          </p>
        </div>
      )}

      {!snapLoading && !unavailable && snapshot && (
        <div className="space-y-6">
          {/* ── Red de marca: web + redes + e-commerce enlazados entre sí ── */}
          <div className="rounded-xl border border-slate-200 bg-white">
            <div className="p-6 flex items-start justify-between flex-wrap gap-4 border-b border-slate-100">
              <div className="max-w-xl">
                <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Network className="w-4 h-4 text-blue-600" /> Tu red de marca
                </h2>
                <p className="text-sm text-slate-600 mt-1">
                  Google reparte autoridad siguiendo enlaces. Si tu web no enlaza tus redes y tu
                  tienda —y no las declara como el mismo negocio— cada una posiciona sola, desde cero.
                </p>
              </div>
              {authority && (
                <div className="text-right">
                  <p className={`text-4xl font-bold ${
                    authority.score >= 75 ? 'text-emerald-600'
                      : authority.score >= 40 ? 'text-amber-600' : 'text-red-600'
                  }`}>{authority.score}%</p>
                  <p className="text-xs text-slate-500">de tu red conectada</p>
                </div>
              )}
            </div>

            {authority && (
              <div className="p-6 space-y-4">
                <div className="grid sm:grid-cols-2 gap-3">
                  {authority.checks.map(check => (
                    <div key={check.key} className="flex gap-2.5 items-start">
                      {check.passed
                        ? <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                        : <XCircle className="w-5 h-5 text-slate-300 shrink-0 mt-0.5" />}
                      <div>
                        <p className={`text-sm font-medium ${check.passed ? 'text-slate-900' : 'text-slate-700'}`}>
                          {check.title}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">{check.detail}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {authority.profiles.length > 0 && (
                  <div className="rounded-lg border border-slate-200 overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 text-slate-600">
                        <tr>
                          <th className="text-left font-medium px-4 py-2.5">Perfil / tienda</th>
                          <th className="text-center font-medium px-3 py-2.5">Enlazado desde tu web</th>
                          <th className="text-center font-medium px-3 py-2.5">Declarado en sameAs</th>
                          <th className="text-center font-medium px-3 py-2.5">Enlaza de vuelta</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {authority.profiles.map(p => (
                          <tr key={p.id}>
                            <td className="px-4 py-3">
                              <p className="font-medium text-slate-900">{p.platform}</p>
                              <p className="text-xs text-slate-500 truncate max-w-[260px]">{p.url}</p>
                              {p.unverifiable_reason && (
                                <p className="text-xs text-amber-700 mt-0.5 flex items-start gap-1">
                                  <AlertCircle className="w-3 h-3 shrink-0 mt-0.5" />
                                  {p.unverifiable_reason}
                                </p>
                              )}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {p.linked_from_hub
                                ? <CheckCircle2 className="w-4 h-4 text-emerald-500 inline" />
                                : <XCircle className="w-4 h-4 text-slate-300 inline" />}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {p.declared_same_as
                                ? <CheckCircle2 className="w-4 h-4 text-emerald-500 inline" />
                                : <XCircle className="w-4 h-4 text-slate-300 inline" />}
                            </td>
                            <td className="px-3 py-3 text-center">
                              {p.links_back_to_hub === null
                                ? <span className="text-xs text-slate-400">sin verificar</span>
                                : p.links_back_to_hub
                                  ? <CheckCircle2 className="w-4 h-4 text-emerald-500 inline" />
                                  : <XCircle className="w-4 h-4 text-slate-300 inline" />}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <Link
                  href="/dashboard/phase12"
                  className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:underline"
                >
                  <Link2 className="w-4 h-4" />
                  Generar el código que une tu marca (JSON-LD con sameAs)
                </Link>
              </div>
            )}
          </div>

          <LinksManager onChanged={loadAuthority} compact />

          {/* Señales verificables: nada acá es una estimación */}
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <div className="flex items-baseline justify-between flex-wrap gap-2 mb-4">
              <h2 className="font-semibold text-slate-900">Señales verificadas</h2>
              <p className="text-sm text-slate-600">{signalsOk} de {signals.length} cumplidas</p>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {signals.map(s => (
                <div key={s.label} className="flex gap-2.5 items-start">
                  {s.ok
                    ? <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                    : <XCircle className="w-5 h-5 text-slate-300 shrink-0 mt-0.5" />}
                  <div>
                    <p className={`text-sm font-medium ${s.ok ? 'text-slate-900' : 'text-slate-700'}`}>{s.label}</p>
                    {!s.ok && <p className="text-xs text-slate-500 mt-0.5">{s.help}</p>}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-4">
              Antigüedad de la cuenta: {v?.account_age_days ?? 0} día(s) — medida desde tu alta real, no estimada.
            </p>
          </div>

          {/* Respuesta a clientes: la señal E-E-A-T que sí podemos medir hoy */}
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
              <MessageSquare className="w-4 h-4 text-blue-600" /> Respuesta a clientes (real)
            </h2>
            {c && c.inbound > 0 ? (
              <div className="grid sm:grid-cols-3 gap-4">
                <div>
                  <p className="text-2xl font-bold text-slate-900">{c.response_rate}%</p>
                  <p className="text-sm text-slate-600">consultas respondidas ({c.answered} de {c.inbound})</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{c.ai_share}%</p>
                  <p className="text-sm text-slate-600">de esas respuestas las generó la IA</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-slate-900">{c.total}</p>
                  <p className="text-sm text-slate-600">conversaciones en total</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">
                Todavía no entraron consultas de clientes, así que no hay tasa de respuesta que mostrar.
                Aparece sola en cuanto llegue el primer mensaje a un canal conectado.
              </p>
            )}
          </div>

          {/* Reseñas / testimonios / premios: reales o nada */}
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <h2 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
              <Award className="w-4 h-4 text-amber-500" /> Reputación cargada
            </h2>
            {loadingTrust && (
              <p className="text-sm text-slate-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Leyendo reseñas y testimonios…
              </p>
            )}
            {!loadingTrust && trust?.available && (
              <div className="flex flex-wrap items-center gap-8">
                <div>
                  <p className="text-4xl font-bold text-amber-600">{trust.trust_score}</p>
                  <p className="text-sm text-slate-600">
                    Nivel {TIER_LABEL[trust.tier ?? ''] ?? trust.tier}
                    {trust.next_tier && ` · faltan ${trust.points_to_next} pts para ${TIER_LABEL[trust.next_tier] ?? trust.next_tier}`}
                  </p>
                </div>
                <div className="text-sm text-slate-700 space-y-1">
                  <p>{trust.components.review_count} reseñas · promedio {trust.components.review_rating}★</p>
                  <p>{trust.components.responded_reviews} respondidas ({trust.components.response_rate}%)</p>
                  <p>{trust.components.testimonial_count} testimonios · {trust.components.award_count} premios</p>
                </div>
              </div>
            )}
            {!loadingTrust && (!trust || trust.available === false) && (
              <p className="text-sm text-slate-600">
                {trust?.reason
                  ?? 'Todavía no hay reseñas, testimonios ni premios cargados para esta cuenta.'}
              </p>
            )}
          </div>

          {!v?.has_business && (
            <Link
              href="/sellia-onboarding"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
            >
              Configurar mi negocio <ExternalLink className="w-4 h-4" />
            </Link>
          )}
        </div>
      )}
    </div>
  )
}
