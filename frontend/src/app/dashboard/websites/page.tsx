'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Globe, Edit2, Eye, Share2, Zap, AlertCircle, CheckCircle2, Loader } from 'lucide-react'

/* ============================================================
   WEBSITES DASHBOARD — Manage seller websites
   ============================================================ */

interface Website {
  id: string
  business_id: string
  title: string
  template: string
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  domain?: {
    subdomain: string
    custom_domain?: string
  }
  created_at: string
  published_at?: string
}

export default function WebsitesDashboard() {
  const router = useRouter()
  const [websites, setWebsites] = useState<Website[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    fetchWebsites()
  }, [])

  const fetchWebsites = async () => {
    try {
      // TODO: fetch from /api/v1/websites/my-websites or similar
      setLoading(false)
    } catch (err: any) {
      setError('Error cargando websites')
      setLoading(false)
    }
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Mis Websites</h1>
          <p className="text-lg text-slate-600">Crea y gestiona los websites de tus negocios</p>
        </div>

        {/* Create button */}
        <div className="mb-8">
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-cyan-600 text-white font-semibold rounded-lg hover:from-cyan-400 hover:to-cyan-500 transition-all shadow-lg shadow-cyan-500/25"
          >
            <Zap className="w-5 h-5" />
            Crear Nuevo Website
          </Link>
        </div>

        {/* Websites grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader className="w-8 h-8 text-cyan-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex items-start gap-3 p-4 rounded-lg bg-red-50 border border-red-200">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <p className="text-red-800">{error}</p>
          </div>
        ) : websites.length === 0 ? (
          <div className="text-center py-20">
            <Globe className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Sin websites aún</h3>
            <p className="text-slate-600 mb-6">Crea tu primer website para empezar a vender online</p>
            <Link
              href="/onboarding"
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 text-white font-semibold rounded-lg hover:bg-cyan-600 transition-all"
            >
              <Zap className="w-5 h-5" />
              Empezar Ahora
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {websites.map((website) => (
              <div
                key={website.id}
                className="rounded-lg bg-white border border-slate-200 shadow-sm hover:shadow-md transition-all overflow-hidden"
              >
                {/* Card header */}
                <div className="p-6 pb-4">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-bold text-slate-900">{website.title}</h3>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        website.status === 'PUBLISHED'
                          ? 'bg-emerald-100 text-emerald-700'
                          : website.status === 'DRAFT'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {website.status === 'PUBLISHED' && <CheckCircle2 className="w-3 h-3 inline mr-1" />}
                      {website.status === 'PUBLISHED'
                        ? 'Publicado'
                        : website.status === 'DRAFT'
                        ? 'Borrador'
                        : 'Archivado'}
                    </span>
                  </div>

                  {/* Domain */}
                  <div className="flex items-center gap-2 text-sm text-slate-600 mb-4">
                    <Globe className="w-4 h-4" />
                    <span>{website.domain?.subdomain}.sellia.app</span>
                  </div>

                  {/* Template */}
                  <p className="text-xs text-slate-500 mb-4">Template: {website.template}</p>
                </div>

                {/* Card footer */}
                <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex gap-2">
                  <button
                    onClick={() => router.push(`/dashboard/websites/${website.id}/edit`)}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded hover:bg-slate-50 transition-all"
                  >
                    <Edit2 className="w-4 h-4" />
                    Editar
                  </button>
                  {website.status === 'PUBLISHED' && (
                    <button
                      onClick={() => window.open(`https://${website.domain?.subdomain}.sellia.app`)}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm font-semibold text-cyan-700 bg-cyan-50 border border-cyan-200 rounded hover:bg-cyan-100 transition-all"
                    >
                      <Eye className="w-4 h-4" />
                      Ver
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
