'use client'

/**
 * SEO — estado real del posicionamiento de la cuenta.
 *
 * Antes esta página mostraba "Search Visibility 45% · Organic Traffic +28% ·
 * Avg Ranking #4.2" y un roadmap con semanas marcadas como completadas: todo
 * hardcodeado, igual para cualquier cuenta, sin nada detrás. Lo que se ve acá
 * ahora sale de GET /businesses/{id}/seo/audit, que evalúa las filas reales
 * del sitio y el dominio del negocio (meta title/description, imagen social,
 * dominio verificado, sitio publicado, contenido cargado).
 */

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { CheckCircle2, XCircle, Loader2, TrendingUp, ExternalLink, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'
import { businessApi, type Business } from '@/lib/business'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'

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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    const load = async (): Promise<void> => {
      try {
        const list = await businessApi.list()
        const biz = list[0] ?? null
        if (!alive) return
        setBusiness(biz)
        if (!biz) return
        // Router montado en /api/v1/seo, con rutas propias /businesses/{id}/seo/...
        const res = await api.get<SeoAudit>(`/seo/businesses/${biz.id}/seo/audit`)
        if (alive) setAudit(res.data)
      } catch {
        if (alive) setError('No se pudo leer el estado SEO de tu sitio.')
      } finally {
        if (alive) setLoading(false)
      }
    }
    void load()
    return () => { alive = false }
  }, [])

  const scoreColor = (score: number): string =>
    score >= 80 ? 'text-emerald-600' : score >= 50 ? 'text-amber-600' : 'text-red-600'

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-1">SEO</h1>
        <p className="text-slate-600">
          Estado real del sitio de tu negocio: qué está listo para que Google te encuentre y qué falta.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 py-16 justify-center">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo el estado de tu sitio…
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-slate-900">{error}</p>
            <p className="text-sm text-slate-600 mt-1">
              No se muestran métricas estimadas: si no se puede medir, no se inventa.
            </p>
          </div>
        </div>
      )}

      {!loading && !error && !business && (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center">
          <p className="text-lg font-semibold text-slate-900 mb-2">Todavía no tenés un negocio creado</p>
          <p className="text-slate-600 mb-5">
            El SEO se mide sobre tu sitio real. Creá tu negocio y reclamá tu subdominio para empezar a medirlo.
          </p>
          <Link
            href="/sellia-onboarding"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
          >
            Configurar mi negocio <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      )}

      {!loading && !error && business && audit && (
        <div className="space-y-6">
          {/* Score real: cuántos chequeos concretos pasan hoy */}
          <div className="rounded-xl border border-slate-200 bg-white p-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-sm font-medium text-slate-600">Estado SEO de {business.name}</p>
                <p className={`text-4xl font-bold ${scoreColor(audit.score)}`}>{audit.score}%</p>
                <p className="text-sm text-slate-600 mt-1">
                  {audit.passed} de {audit.total} chequeos cumplidos
                </p>
              </div>
              {snapshot?.verification.subdomain && (
                <div className="text-right">
                  <p className="text-sm text-slate-500">Tu subdominio</p>
                  <p className="font-mono text-slate-900">{snapshot.verification.subdomain}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {snapshot.verification.website_published ? 'Sitio publicado' : 'Sitio sin publicar'}
                    {' · '}
                    {snapshot.verification.domain_verified ? 'dominio verificado' : 'dominio sin verificar'}
                  </p>
                </div>
              )}
            </div>
            <div className="mt-4 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`h-full ${audit.score >= 80 ? 'bg-emerald-500' : audit.score >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                style={{ width: `${audit.score}%` }}
              />
            </div>
          </div>

          {/* Checklist real, con la acción concreta que falta en cada punto */}
          <div className="rounded-xl border border-slate-200 bg-white divide-y divide-slate-100">
            <div className="p-5">
              <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" /> Qué falta para posicionar mejor
              </h2>
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

          <p className="text-xs text-slate-500">
            Core Web Vitals, tráfico orgánico y posiciones de keywords no se muestran porque esta
            instalación no tiene conectada una API que los mida (PageSpeed/Search Console). Cuando se
            conecte, aparecen acá con datos reales.
          </p>
        </div>
      )}
    </div>
  )
}
