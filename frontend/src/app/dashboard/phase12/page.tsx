'use client'

/**
 * SEO — posicionamiento real de las webs y publicaciones de cada usuario.
 *
 * Primera versión: métricas hardcodeadas ("Search Visibility 45%") iguales para
 * todos. Segunda: honesta, pero sólo miraba el sitio hosteado en SellIA, así que
 * a quien vende en su propia web o en MercadoLibre no le servía de nada.
 *
 * Ahora audita las URLs reales del usuario: descarga cada página, la parsea y
 * reporta lo que realmente tiene (title, meta description, H1, alt de imágenes,
 * JSON-LD, Open Graph, HTTPS, tiempo de respuesta medido) con la corrección
 * concreta de cada hallazgo. Ver backend/app/domains/web_presence/analyzer.py.
 */

import React, { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import {
  AlertTriangle, Check, CheckCircle2, ChevronDown, Copy, ExternalLink, Loader2, Sparkles,
  TrendingUp, XCircle,
} from 'lucide-react'
import { api } from '@/lib/api'
import { businessApi, type Business } from '@/lib/business'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'
import LinksManager from '@/components/web-presence/LinksManager'
import { webPresenceApi, SEVERITY_STYLE, scoreColor, type SeoReport } from '@/lib/webPresence'

interface SeoCheck {
  label: string
  passed: boolean
  recommendation: string
}

interface SeoAudit {
  score: number
  passed: number
  total: number
  checks: Record<string, SeoCheck>
}

export default function SeoPage(): React.JSX.Element {
  const { snapshot } = useBusinessSnapshot()
  const [business, setBusiness] = useState<Business | null>(null)
  const [audit, setAudit] = useState<SeoAudit | null>(null)
  const [report, setReport] = useState<SeoReport | null>(null)
  const [schema, setSchema] = useState<{ available: boolean; reason?: string; json_ld?: Record<string, unknown> } | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [loading, setLoading] = useState(true)

  const loadReport = useCallback(async (): Promise<void> => {
    const [rep, sch] = await Promise.all([
      webPresenceApi.seoReport().catch(() => null),
      webPresenceApi.structuredData().catch(() => null),
    ])
    setReport(rep)
    setSchema(sch)
  }, [])

  useEffect(() => {
    let alive = true
    const load = async (): Promise<void> => {
      try {
        const list = await businessApi.list().catch(() => [])
        const biz = list[0] ?? null
        if (!alive) return
        setBusiness(biz)
        if (biz) {
          const res = await api
            .get<SeoAudit>(`/seo/businesses/${biz.id}/seo/audit`)
            .catch(() => null)
          if (alive && res) setAudit(res.data)
        }
        await loadReport()
      } finally {
        if (alive) setLoading(false)
      }
    }
    void load()
    return () => { alive = false }
  }, [loadReport])

  const copySchema = async (): Promise<void> => {
    if (!schema?.json_ld) return
    const snippet = `<script type="application/ld+json">\n${JSON.stringify(schema.json_ld, null, 2)}\n</script>`
    await navigator.clipboard.writeText(snippet)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-1">SEO</h1>
        <p className="text-slate-600">
          Analizamos tus páginas reales —tu web, tu landing, tus publicaciones— y te decimos
          exactamente qué corregir para que Google te encuentre antes que a tu competencia.
        </p>
      </div>

      <div className="space-y-6">
        <LinksManager onChanged={loadReport} />

        {loading && (
          <div className="flex items-center gap-3 text-slate-500 py-10 justify-center">
            <Loader2 className="w-5 h-5 animate-spin" /> Leyendo el estado de tus páginas…
          </div>
        )}

        {/* ── Resultado real del análisis de SUS páginas ── */}
        {report && report.pages_analyzed > 0 && (
          <>
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-600">Promedio de tus páginas analizadas</p>
                  <p className={`text-4xl font-bold ${scoreColor(report.average_score)}`}>
                    {report.average_score}
                    <span className="text-lg text-slate-400 font-semibold">/100</span>
                  </p>
                  <p className="text-sm text-slate-600 mt-1">
                    {report.pages_analyzed} de {report.links_total} links pudieron analizarse
                  </p>
                </div>
                {snapshot?.verification.subdomain && (
                  <div className="text-right">
                    <p className="text-sm text-slate-500">Tu subdominio SellIA</p>
                    <p className="font-mono text-slate-900">{snapshot.verification.subdomain}</p>
                  </div>
                )}
              </div>
            </div>

            {report.priorities.length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white">
                <div className="p-5 border-b border-slate-100">
                  <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-600" /> Qué arreglar primero
                  </h2>
                  <p className="text-sm text-slate-600 mt-0.5">
                    Ordenado por impacto y por cuántas de tus páginas lo tienen.
                  </p>
                </div>
                <ul className="divide-y divide-slate-100">
                  {report.priorities.map(p => {
                    const style = SEVERITY_STYLE[p.severity]
                    return (
                      <li key={p.key} className="p-5 flex gap-3">
                        <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="font-medium text-slate-900">{p.title}</p>
                            <span className={`text-[11px] px-2 py-0.5 rounded-full border ${style.chip}`}>
                              {style.label}
                            </span>
                            <span className="text-xs text-slate-500">
                              {p.pages} {p.pages === 1 ? 'página' : 'páginas'}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">{p.fix}</p>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}

            <div className="rounded-xl border border-slate-200 bg-white">
              <div className="p-5 border-b border-slate-100">
                <h2 className="font-semibold text-slate-900">Página por página</h2>
              </div>
              <ul className="divide-y divide-slate-100">
                {report.pages.map(page => (
                  <li key={page.id}>
                    <button
                      type="button"
                      onClick={() => setExpanded(expanded === page.id ? null : page.id)}
                      className="w-full p-5 flex items-center gap-3 text-left hover:bg-slate-50"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 truncate">
                          {page.title || page.url}
                        </p>
                        <p className="text-xs text-slate-500 truncate">{page.url}</p>
                        {page.unverifiable_reason && (
                          <p className="text-xs text-amber-700 mt-1">{page.unverifiable_reason}</p>
                        )}
                      </div>
                      {page.score !== null && (
                        <span className={`text-xl font-bold ${scoreColor(page.score)}`}>{page.score}</span>
                      )}
                      {page.issues.length > 0 && (
                        <span className="text-xs text-slate-500 shrink-0">
                          {page.issues.length} hallazgos
                        </span>
                      )}
                      <ChevronDown
                        className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${
                          expanded === page.id ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    {expanded === page.id && (
                      <div className="px-5 pb-5 space-y-3">
                        {page.issues.length === 0 && (
                          <p className="text-sm text-emerald-700 flex items-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Sin hallazgos: esta página pasa todos los chequeos que podemos medir.
                          </p>
                        )}
                        {page.issues.map(issue => {
                          const style = SEVERITY_STYLE[issue.severity]
                          return (
                            <div key={issue.key} className="rounded-lg border border-slate-200 p-4">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                                <p className="font-medium text-slate-900">{issue.title}</p>
                                <span className={`text-[11px] px-2 py-0.5 rounded-full border ${style.chip}`}>
                                  {style.label}
                                </span>
                              </div>
                              <p className="text-sm text-slate-600 mt-1.5">{issue.detail}</p>
                              <p className="text-sm text-slate-900 mt-2 flex gap-2">
                                <Sparkles className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                                <span><strong className="font-medium">Cómo se corrige:</strong> {issue.fix}</span>
                              </p>
                            </div>
                          )
                        })}
                        {page.json_ld_types.length > 0 && (
                          <p className="text-xs text-slate-500">
                            Datos estructurados detectados: {page.json_ld_types.join(', ')}
                          </p>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {/* ── JSON-LD generado con SUS datos reales ── */}
        {schema?.available && schema.json_ld && (
          <div className="rounded-xl border border-slate-200 bg-white">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between flex-wrap gap-3">
              <div>
                <h2 className="font-semibold text-slate-900">Tu marca, lista para Google</h2>
                <p className="text-sm text-slate-600 mt-0.5">
                  Generado con tus datos y tus perfiles reales. Pegalo en el &lt;head&gt; de tu sitio:
                  une tu web, tus redes y tus tiendas como un mismo negocio.
                </p>
              </div>
              <button
                type="button"
                onClick={copySchema}
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copiado' : 'Copiar código'}
              </button>
            </div>
            <pre className="p-5 text-xs text-slate-700 overflow-x-auto bg-slate-50 rounded-b-xl">
{JSON.stringify(schema.json_ld, null, 2)}
            </pre>
          </div>
        )}

        {/* ── Sitio hosteado en SellIA (chequeos sobre las filas reales) ── */}
        {business && audit && (
          <div className="rounded-xl border border-slate-200 bg-white divide-y divide-slate-100">
            <div className="p-5 flex items-center justify-between flex-wrap gap-3">
              <h2 className="font-semibold text-slate-900">
                Tu sitio en SellIA · {audit.passed}/{audit.total} chequeos
              </h2>
              <span className={`text-xl font-bold ${scoreColor(audit.score)}`}>{audit.score}%</span>
            </div>
            {Object.entries(audit.checks).map(([key, check]) => (
              <div key={key} className="p-5 flex gap-3">
                {check.passed
                  ? <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                  : <XCircle className="w-5 h-5 text-slate-300 shrink-0 mt-0.5" />}
                <div>
                  <p className={`font-medium ${check.passed ? 'text-slate-900' : 'text-slate-700'}`}>
                    {check.label}
                  </p>
                  <p className="text-sm text-slate-600 mt-0.5">{check.recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !business && (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
            <p className="text-lg font-semibold text-slate-900 mb-2">Todavía no tenés un negocio creado</p>
            <p className="text-slate-600 mb-5">
              Podés auditar tus links igual, pero creando tu negocio sumás el sitio de SellIA y los
              datos estructurados con tu marca.
            </p>
            <Link
              href="/sellia-onboarding"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
            >
              Configurar mi negocio <ExternalLink className="w-4 h-4" />
            </Link>
          </div>
        )}

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 flex gap-3">
          <AlertTriangle className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <p className="text-xs text-slate-600">
            Volumen de búsqueda, dificultad de keywords y Core Web Vitals de laboratorio necesitan una
            API paga (Search Console, PageSpeed, SemRush) que esta instalación no tiene conectada, así
            que no se muestran. Todo lo de arriba —incluido el tiempo de respuesta— se mide
            descargando tus páginas de verdad.
          </p>
        </div>
      </div>
    </div>
  )
}
