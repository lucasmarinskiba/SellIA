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
  AlertTriangle, Check, CheckCircle2, ChevronDown, Copy, ExternalLink, FileSearch, Loader2,
  Sparkles, Swords, Tags, TrendingUp, XCircle,
} from 'lucide-react'
import { api } from '@/lib/api'
import { businessApi, type Business } from '@/lib/business'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'
import LinksManager from '@/components/web-presence/LinksManager'
import {
  webPresenceApi, SEVERITY_STYLE, scoreColor, type CompareResult, type SeoReport,
} from '@/lib/webPresence'

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
  const [rivalUrl, setRivalUrl] = useState('')
  const [compare, setCompare] = useState<CompareResult | null>(null)
  const [comparing, setComparing] = useState(false)

  const runCompare = async (): Promise<void> => {
    if (!rivalUrl.trim()) return
    setComparing(true)
    try {
      setCompare(await webPresenceApi.compare(rivalUrl.trim()))
    } catch {
      setCompare({ ok: false, error: 'No se pudo completar la comparación.' })
    } finally {
      setComparing(false)
    }
  }

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

            {/* Progreso real: histórico de auditorías, no el valor actual redibujado */}
            {report.history.length > 1 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
                  <p className="font-medium text-slate-900">Tu progreso</p>
                  <p className="text-sm text-slate-600">
                    {(() => {
                      const first = report.history[0]
                      const last = report.history[report.history.length - 1]
                      const delta = Math.round((last.average_score - first.average_score) * 10) / 10
                      if (delta > 0) return `+${delta} puntos desde el ${first.date}`
                      if (delta < 0) return `${delta} puntos desde el ${first.date}`
                      return `sin cambios desde el ${first.date}`
                    })()}
                  </p>
                </div>
                <div className="flex items-end gap-1 h-20">
                  {report.history.map(point => (
                    <div
                      key={point.date}
                      title={`${point.date}: ${point.average_score}/100 · ${point.critical_issues} críticos`}
                      className="flex-1 bg-blue-500/80 rounded-t hover:bg-blue-600"
                      style={{ height: `${Math.max(4, point.average_score)}%` }}
                    />
                  ))}
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Cada barra es una corrida de análisis real, no una proyección.
                </p>
              </div>
            )}

            {/* robots.txt + sitemap: deciden si la página puede rankear siquiera */}
            {report.pages.filter(p => p.site_files).map(page => {
              const sf = page.site_files as NonNullable<typeof page.site_files>
              return (
                <div key={`sf-${page.id}`} className="rounded-xl border border-slate-200 bg-white p-5">
                  <p className="font-medium text-slate-900 flex items-center gap-2">
                    <FileSearch className="w-4 h-4 text-blue-600" /> Rastreo e indexación · {sf.origin}
                  </p>
                  <div className="grid sm:grid-cols-3 gap-3 mt-3">
                    <div className="flex gap-2 items-start">
                      {sf.blocks_this_page
                        ? <XCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                        : <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />}
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {sf.blocks_this_page ? 'robots.txt la bloquea' : 'Google puede rastrearla'}
                        </p>
                        {sf.blocking_rule && (
                          <p className="text-xs text-red-600 mt-0.5 font-mono">{sf.blocking_rule}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 items-start">
                      {sf.robots_found
                        ? <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                        : <XCircle className="w-5 h-5 text-slate-300 shrink-0 mt-0.5" />}
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {sf.robots_found ? 'robots.txt encontrado' : 'Sin robots.txt'}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {sf.sitemaps_declared.length > 0
                            ? `declara ${sf.sitemaps_declared.length} sitemap(s)`
                            : 'no declara sitemap'}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2 items-start">
                      {sf.sitemap_found
                        ? <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                        : <XCircle className="w-5 h-5 text-slate-300 shrink-0 mt-0.5" />}
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {sf.sitemap_found ? `Sitemap con ${sf.sitemap_url_count} URLs` : 'Sin sitemap'}
                        </p>
                        {sf.contains_this_page !== null && (
                          <p className="text-xs text-slate-500 mt-0.5">
                            {sf.contains_this_page ? 'incluye esta página' : 'no incluye esta página'}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  {sf.notes.map((note, i) => (
                    <p key={i} className="text-xs text-slate-500 mt-2">{note}</p>
                  ))}
                </div>
              )
            })}

            {/* Perfil de términos: de qué habla la página según la página misma */}
            {report.pages.filter(p => p.terms && p.terms.top_terms.length > 0).slice(0, 2).map(page => {
              const t = page.terms as NonNullable<typeof page.terms>
              const max = Math.max(...t.top_terms.map(x => x.score), 1)
              return (
                <div key={`terms-${page.id}`} className="rounded-xl border border-slate-200 bg-white p-5">
                  <p className="font-medium text-slate-900 flex items-center gap-2">
                    <Tags className="w-4 h-4 text-blue-600" /> De qué habla tu página
                  </p>
                  <p className="text-sm text-slate-600 mt-0.5 mb-3 truncate">{page.url}</p>
                  <div className="space-y-1.5">
                    {t.top_terms.slice(0, 8).map(term => (
                      <div key={term.term} className="flex items-center gap-3">
                        <span className="text-sm text-slate-700 w-48 truncate">{term.term}</span>
                        <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full ${term.in_title ? 'bg-blue-500' : 'bg-slate-300'}`}
                            style={{ width: `${(term.score / max) * 100}%` }}
                          />
                        </div>
                        {term.in_title && (
                          <span className="text-[11px] text-blue-600 shrink-0">en el título</span>
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-3">
                    Peso calculado sobre tu propio texto (título ×5, H1 ×4, descripción ×3, subtítulos ×2).
                    No es volumen de búsqueda: eso necesita una API paga y no se inventa acá.
                  </p>
                </div>
              )
            })}

            {report.duplicates.length > 0 && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                <p className="font-medium text-slate-900 flex items-center gap-2">
                  <Copy className="w-4 h-4 text-amber-600" /> Páginas que compiten entre sí
                </p>
                <div className="mt-3 space-y-3">
                  {report.duplicates.map((dup, i) => (
                    <div key={i}>
                      <p className="text-sm text-slate-900">
                        {dup.kind === 'title' ? 'Mismo título' : 'Misma meta description'}:
                        <span className="font-mono text-xs"> “{dup.value}”</span>
                      </p>
                      <ul className="text-xs text-slate-600 mt-1 space-y-0.5">
                        {dup.urls.map(u => <li key={u} className="truncate">· {u}</li>)}
                      </ul>
                      <p className="text-sm text-slate-700 mt-1">{dup.fix}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Comparación real contra un competidor */}
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <p className="font-medium text-slate-900 flex items-center gap-2">
                <Swords className="w-4 h-4 text-blue-600" /> Compararte con un competidor
              </p>
              <p className="text-sm text-slate-600 mt-0.5 mb-3">
                Pegá la URL de un competidor y la analizamos igual que la tuya, señal por señal.
              </p>
              <div className="flex gap-2 flex-wrap">
                <input
                  value={rivalUrl}
                  onChange={e => setRivalUrl(e.target.value)}
                  placeholder="https://competidor.com/producto"
                  className="flex-1 min-w-[220px] px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
                />
                <button
                  type="button"
                  onClick={runCompare}
                  disabled={comparing || !rivalUrl.trim()}
                  className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 disabled:opacity-50 inline-flex items-center gap-2"
                >
                  {comparing && <Loader2 className="w-4 h-4 animate-spin" />} Comparar
                </button>
              </div>

              {compare && !compare.ok && (
                <p className="text-sm text-amber-700 mt-3">
                  No se pudo analizar esa URL: {compare.error}
                </p>
              )}

              {compare?.ok && compare.rows && (
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-slate-600">
                      <tr className="border-b border-slate-200">
                        <th className="text-left font-medium py-2">Señal</th>
                        <th className="text-right font-medium py-2 px-3">Tu página</th>
                        <th className="text-right font-medium py-2 px-3">Competidor</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="py-2 font-medium text-slate-900">Score</td>
                        <td className={`py-2 px-3 text-right font-bold ${scoreColor(compare.mine?.score ?? null)}`}>
                          {compare.mine?.score ?? '—'}
                        </td>
                        <td className={`py-2 px-3 text-right font-bold ${scoreColor(compare.theirs?.score ?? null)}`}>
                          {compare.theirs?.score ?? '—'}
                        </td>
                      </tr>
                      {compare.rows.map(r => {
                        const mine = r.mine ?? 0
                        const theirs = r.theirs ?? 0
                        const iWin = r.higher_is_better ? mine >= theirs : mine <= theirs
                        return (
                          <tr key={r.label}>
                            <td className="py-2 text-slate-700">{r.label}</td>
                            <td className={`py-2 px-3 text-right ${iWin ? 'text-emerald-600 font-semibold' : 'text-slate-700'}`}>
                              {r.mine ?? '—'}
                            </td>
                            <td className={`py-2 px-3 text-right ${!iWin ? 'text-emerald-600 font-semibold' : 'text-slate-700'}`}>
                              {r.theirs ?? '—'}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  {compare.topics_they_cover && compare.topics_they_cover.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-slate-900">Temas que ellos cubren y vos no</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {compare.topics_they_cover.map(topic => (
                          <span key={topic} className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-700">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
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
