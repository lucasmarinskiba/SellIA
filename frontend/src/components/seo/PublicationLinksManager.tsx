'use client'

import React, { useEffect, useState } from 'react'
import { Link2, Loader2, Plus, Trash2, X } from 'lucide-react'
import { seoConfigApi, type PublicationLink } from '@/lib/seoConfig'

interface PublicationLinksManagerProps {
  businessId: string
  onChanged?: () => void
}

const PLATFORM_SOURCES = [
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'mercado-libre', label: 'Mercado Libre' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'shopify', label: 'Shopify' },
  { value: 'hotmart', label: 'Hotmart' },
  { value: 'tiendanube', label: 'Tienda Nube' },
  { value: 'woocommerce', label: 'WooCommerce' },
  { value: 'etsy', label: 'Etsy' },
  { value: 'custom', label: 'Otro sitio' },
]

export function PublicationLinksManager({ businessId, onChanged }: PublicationLinksManagerProps): React.JSX.Element {
  const [links, setLinks] = useState<PublicationLink[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    url: '',
    title: '',
    platform_source: 'instagram',
  })
  const [submitting, setSubmitting] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)

  const loadLinks = async () => {
    try {
      const data = await seoConfigApi.listPublicationLinks(businessId)
      setLinks(data)
    } catch (error) {
      console.error('Error loading publication links:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadLinks()
  }, [businessId])

  const handleAddLink = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.url.trim() || !formData.title.trim()) return

    try {
      setSubmitting(true)
      const newLink = await seoConfigApi.createPublicationLink(businessId, {
        url: formData.url.trim(),
        title: formData.title.trim(),
        platform_source: formData.platform_source,
      })
      setLinks([newLink, ...links])
      setFormData({ url: '', title: '', platform_source: 'instagram' })
      setShowForm(false)
      onChanged?.()
    } catch (error) {
      console.error('Error adding publication link:', error)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteLink = async (linkId: string) => {
    try {
      setDeleting(linkId)
      await seoConfigApi.deletePublicationLink(businessId, linkId)
      setLinks(links.filter(l => l.id !== linkId))
      onChanged?.()
    } catch (error) {
      console.error('Error deleting publication link:', error)
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-3 text-slate-500 py-10 justify-center">
        <Loader2 className="w-5 h-5 animate-spin" /> Cargando publicaciones…
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Add Link Form */}
      {!showForm && (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="w-full px-4 py-3 rounded-lg border-2 border-dashed border-slate-200 text-slate-600 hover:border-blue-400 hover:text-blue-600 transition-colors flex items-center justify-center gap-2 text-sm font-medium"
        >
          <Plus className="w-4 h-4" />
          Agregar publicación para posicionar
        </button>
      )}

      {showForm && (
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <form onSubmit={handleAddLink} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-900 mb-1">
                Título de la publicación
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={e => setFormData({ ...formData, title: e.target.value })}
                placeholder="ej: Mi mejor producto en Instagram"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-900 mb-1">
                URL de la publicación
              </label>
              <input
                type="url"
                value={formData.url}
                onChange={e => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://instagram.com/p/..."
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-900 mb-1">
                Plataforma
              </label>
              <select
                value={formData.platform_source}
                onChange={e => setFormData({ ...formData, platform_source: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900"
              >
                {PLATFORM_SOURCES.map(p => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setFormData({ url: '', title: '', platform_source: 'instagram' })
                }}
                className="px-3 py-2 rounded-lg border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting || !formData.url.trim() || !formData.title.trim()}
                className="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 inline animate-spin" /> : 'Agregar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Links List */}
      {links.length > 0 && (
        <div className="space-y-2">
          {links.map(link => (
            <div
              key={link.id}
              className="rounded-lg border border-slate-200 bg-white p-4 flex items-start justify-between gap-4 group"
            >
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <Link2 className="w-4 h-4 text-slate-400 mt-1 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-900 truncate">{link.title}</p>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:text-blue-700 truncate block"
                  >
                    {link.url}
                  </a>
                  <p className="text-xs text-slate-500 mt-1">
                    {PLATFORM_SOURCES.find(p => p.value === link.platform_source)?.label || link.platform_source}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {link.seo_enabled && (
                  <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700 font-medium">
                    SEO activo
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => void handleDeleteLink(link.id)}
                  disabled={deleting === link.id}
                  className="p-1.5 rounded hover:bg-slate-100 text-slate-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100"
                >
                  {deleting === link.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
