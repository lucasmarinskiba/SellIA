'use client'

import { Suspense, useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Zap,
  Globe,
  FileText,
  Code,
  Loader,
  Edit2,
  Copy,
} from 'lucide-react'

/* ============================================================
   SEO DASHBOARD — Tier 2 Meta Tags, Schema, Sitemap, robots.txt
   ============================================================ */

interface SEOMetadata {
  meta_title: string
  meta_description: string
  meta_keywords: string
  og_image_url: string
}

interface SEOAudit {
  score: number
  passed: number
  total: number
  checks: Record<string, {
    label: string
    passed: boolean
    recommendation: string
  }>
}

function SEODashboardContent() {
  const searchParams = useSearchParams()
  const businessId = searchParams?.get('businessId') || ''

  const [tab, setTab] = useState<'audit' | 'meta' | 'schema' | 'sitemap' | 'robots'>('audit')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)

  const [metadata, setMetadata] = useState<SEOMetadata | null>(null)
  const [audit, setAudit] = useState<SEOAudit | null>(null)
  const [schema, setSchema] = useState<any>(null)
  const [sitemap, setSitemap] = useState('')
  const [robotsTxt, setRobotsTxt] = useState('')

  const [editingMeta, setEditingMeta] = useState(false)
  const [metaForm, setMetaForm] = useState<SEOMetadata>({
    meta_title: '',
    meta_description: '',
    meta_keywords: '',
    og_image_url: '',
  })

  const [metaLoading, setMetaLoading] = useState(false)

  useEffect(() => {
    setMounted(true)
    if (businessId) {
      fetchData()
    }
  }, [businessId])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError('')

      const [metaRes, auditRes] = await Promise.all([
        fetch(`/api/v1/seo/businesses/${businessId}/seo/meta`),
        fetch(`/api/v1/seo/businesses/${businessId}/seo/audit`),
      ])

      if (!metaRes.ok || !auditRes.ok) {
        throw new Error('Error cargando datos SEO')
      }

      const metaData = await metaRes.json()
      const auditData = await auditRes.json()

      setMetadata(metaData)
      setAudit(auditData)
      setMetaForm(metaData)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchSchema = async () => {
    try {
      const res = await fetch(`/api/v1/seo/businesses/${businessId}/seo/schema`)
      if (!res.ok) throw new Error('Error cargando schema')
      const data = await res.json()
      setSchema(data)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const fetchSitemap = async () => {
    try {
      const res = await fetch(`/api/v1/seo/businesses/${businessId}/seo/sitemap.xml`)
      if (!res.ok) throw new Error('Error cargando sitemap')
      const text = await res.text()
      setSitemap(text)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const fetchRobots = async () => {
    try {
      const res = await fetch(`/api/v1/seo/businesses/${businessId}/seo/robots.txt`)
      if (!res.ok) throw new Error('Error cargando robots.txt')
      const text = await res.text()
      setRobotsTxt(text)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleUpdateMeta = async () => {
    setMetaLoading(true)
    try {
      const res = await fetch(`/api/v1/seo/businesses/${businessId}/seo/meta`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metaForm),
      })

      if (!res.ok) throw new Error('Error actualizando meta tags')

      const updated = await res.json()
      setMetadata(updated)
      setEditingMeta(false)
      setError('')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setMetaLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link
            href="/dashboard/websites"
            className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-900" />
          </Link>
          <div>
            <h1 className="text-4xl font-bold text-slate-900">SEO Setup</h1>
            <p className="text-lg text-slate-600">Optimiza tu website para buscadores</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Tabs */}
            <div className="flex gap-2 border-b border-slate-200 overflow-x-auto">
              {[
                { id: 'audit', label: 'Auditoría', icon: Zap },
                { id: 'meta', label: 'Meta Tags', icon: FileText },
                { id: 'schema', label: 'Schema', icon: Code },
                { id: 'sitemap', label: 'Sitemap', icon: Globe },
                { id: 'robots', label: 'Robots.txt', icon: FileText },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => {
                    setTab(t.id as any)
                    if (t.id === 'schema' && !schema) fetchSchema()
                    if (t.id === 'sitemap' && !sitemap) fetchSitemap()
                    if (t.id === 'robots' && !robotsTxt) fetchRobots()
                  }}
                  className={`px-4 py-3 font-semibold flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
                    tab === t.id
                      ? 'border-cyan-500 text-cyan-600'
                      : 'border-transparent text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <t.icon className="w-4 h-4" />
                  {t.label}
                </button>
              ))}
            </div>

            {/* Audit Tab */}
            {tab === 'audit' && audit && (
              <div className="space-y-6">
                {/* Score Card */}
                <div className="rounded-lg bg-white border border-slate-200 p-8">
                  <div className="flex items-center gap-8">
                    <div className="flex-1">
                      <h2 className="text-3xl font-bold text-slate-900 mb-2">
                        SEO Score: {audit.score}%
                      </h2>
                      <p className="text-slate-600">
                        {audit.passed} de {audit.total} checks completados
                      </p>
                      <div className="mt-4 h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all"
                          style={{ width: `${audit.score}%` }}
                        />
                      </div>
                    </div>

                    <div className="text-6xl font-bold text-cyan-500">{audit.score}</div>
                  </div>
                </div>

                {/* Checks */}
                <div className="space-y-3">
                  {Object.entries(audit.checks).map(([key, check]) => (
                    <div
                      key={key}
                      className="rounded-lg bg-white border border-slate-200 p-4 flex items-start gap-4"
                    >
                      {check.passed ? (
                        <CheckCircle2 className="w-6 h-6 text-emerald-500 mt-0.5 shrink-0" />
                      ) : (
                        <AlertCircle className="w-6 h-6 text-amber-500 mt-0.5 shrink-0" />
                      )}

                      <div className="flex-1">
                        <h3 className={`font-semibold ${check.passed ? 'text-emerald-900' : 'text-amber-900'}`}>
                          {check.label}
                        </h3>
                        <p className="text-sm text-slate-600 mt-1">{check.recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Meta Tags Tab */}
            {tab === 'meta' && metadata && (
              <div className="rounded-lg bg-white border border-slate-200 p-8">
                {editingMeta ? (
                  <div className="space-y-5">
                    <div>
                      <label className="block text-sm font-semibold text-slate-900 mb-2">
                        Meta Title (50-60 chars)
                      </label>
                      <input
                        type="text"
                        value={metaForm.meta_title}
                        onChange={(e) =>
                          setMetaForm({ ...metaForm, meta_title: e.target.value.slice(0, 60) })
                        }
                        className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        {metaForm.meta_title.length}/60
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-900 mb-2">
                        Meta Description (120-160 chars)
                      </label>
                      <textarea
                        value={metaForm.meta_description}
                        onChange={(e) =>
                          setMetaForm({
                            ...metaForm,
                            meta_description: e.target.value.slice(0, 160),
                          })
                        }
                        className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 resize-none h-24"
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        {metaForm.meta_description.length}/160
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-900 mb-2">
                        Keywords (opcional)
                      </label>
                      <input
                        type="text"
                        value={metaForm.meta_keywords}
                        onChange={(e) =>
                          setMetaForm({ ...metaForm, meta_keywords: e.target.value })
                        }
                        placeholder="palabra1, palabra2, palabra3"
                        className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                      />
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setEditingMeta(false)}
                        className="px-4 py-2 rounded-lg border border-slate-200 text-slate-900 font-semibold hover:bg-slate-50"
                      >
                        Cancelar
                      </button>
                      <button
                        onClick={handleUpdateMeta}
                        disabled={metaLoading}
                        className="px-4 py-2 rounded-lg bg-cyan-500 text-white font-semibold hover:bg-cyan-600 disabled:opacity-50"
                      >
                        {metaLoading ? 'Guardando...' : 'Guardar'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase mb-1">
                        Meta Title
                      </p>
                      <p className="text-lg text-cyan-600 font-semibold">{metadata.meta_title}</p>
                    </div>

                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase mb-1">
                        Meta Description
                      </p>
                      <p className="text-slate-700">{metadata.meta_description}</p>
                    </div>

                    <div>
                      <p className="text-xs font-semibold text-slate-500 uppercase mb-1">
                        Keywords
                      </p>
                      <p className="text-slate-700">{metadata.meta_keywords || '(Sin configurar)'}</p>
                    </div>

                    <button
                      onClick={() => setEditingMeta(true)}
                      className="mt-6 px-4 py-2 rounded-lg border border-slate-200 text-slate-900 font-semibold hover:bg-slate-50 flex items-center gap-2"
                    >
                      <Edit2 className="w-4 h-4" />
                      Editar
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Schema Tab */}
            {tab === 'schema' && schema && (
              <div className="space-y-6">
                {Object.entries(schema).map(([key, value]: any) => (
                  <div key={key} className="rounded-lg bg-white border border-slate-200 p-6">
                    <h3 className="font-semibold text-slate-900 mb-3 capitalize">
                      {key.replace(/_/g, ' ')}
                    </h3>
                    <pre className="bg-slate-900 text-slate-100 p-4 rounded overflow-x-auto text-sm">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}

            {/* Sitemap Tab */}
            {tab === 'sitemap' && (
              <div className="rounded-lg bg-white border border-slate-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900">sitemap.xml</h3>
                  <button
                    onClick={() => navigator.clipboard.writeText(sitemap)}
                    className="px-3 py-1 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    Copiar
                  </button>
                </div>
                <pre className="bg-slate-900 text-slate-100 p-4 rounded overflow-x-auto text-xs">
                  {sitemap}
                </pre>
              </div>
            )}

            {/* Robots.txt Tab */}
            {tab === 'robots' && (
              <div className="rounded-lg bg-white border border-slate-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-slate-900">robots.txt</h3>
                  <button
                    onClick={() => navigator.clipboard.writeText(robotsTxt)}
                    className="px-3 py-1 text-sm rounded-lg border border-slate-200 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    Copiar
                  </button>
                </div>
                <pre className="bg-slate-900 text-slate-100 p-4 rounded overflow-x-auto text-xs">
                  {robotsTxt}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function SEODashboardPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin">Loading...</div></div>}>
      <SEODashboardContent />
    </Suspense>
  )
}
