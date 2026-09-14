'use client'

/**
 * Nuevo listing — antes era un stub: handleSubmit sólo esperaba 1s con
 * setTimeout y redirigía, sin llamar a ningún endpoint real (nada se
 * guardaba). Ahora crea un CatalogItem real vía POST /catalog/{id}/items
 * -- el mismo catálogo que ahora lee /dashboard/listings y que ya usa el
 * SellIA Assistant para saber qué vende el negocio.
 */

import { ArrowLeft, Plus, AlertCircle } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { api } from '@/lib/api'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'

type CatalogItemType = 'service' | 'good' | 'digital'

const PLATFORMS = [
  { value: 'mercadolibre', label: 'Mercado Libre' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'hotmart', label: 'Hotmart' },
  { value: 'website', label: 'Sitio web propio' },
  { value: 'social', label: 'Redes sociales (Instagram/TikTok/Facebook)' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'direct', label: 'Servicios (sin plataforma específica)' },
  { value: 'other', label: 'Otro' },
]

export default function CreateListingPage() {
  const router = useRouter()
  const { snapshot } = useBusinessSnapshot()
  const businessId = snapshot?.business.id ?? null

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    name: '',
    description: '',
    type: 'good' as CatalogItemType,
    category: '',
    price: '',
    stock: '',
    platform: 'mercadolibre',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!businessId) { setError('Configurá tu negocio antes de crear un listing.'); return }
    setLoading(true)
    setError(null)
    try {
      await api.post(`/catalog/${businessId}/items`, {
        type: form.type,
        name: form.name,
        description: form.description || undefined,
        price: Number(form.price) || 0,
        currency: 'ARS',
        stock: form.type === 'good' ? Number(form.stock) || 0 : undefined,
        tags: form.category ? [form.category] : [],
        extra_data: { source_platform: form.platform },
      })
      router.push('/dashboard/listings')
    } catch {
      setError('No se pudo crear el listing. Revisá los datos e intentá de nuevo.')
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => router.back()} className="p-2 hover:bg-slate-100 rounded-lg">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-3xl font-black text-slate-900">Crear nuevo listing</h1>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="font-bold text-slate-900 mb-4">Información básica</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="ej. Consultoría de marketing, o iPhone 15 Pro"
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Descripción</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Describí qué ofrecés..."
                  rows={4}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Tipo</label>
                  <select
                    value={form.type}
                    onChange={(e) => setForm({ ...form, type: e.target.value as CatalogItemType })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="good">Físico</option>
                    <option value="service">Servicio</option>
                    <option value="digital">Digital</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Categoría/rubro</label>
                  <input
                    type="text"
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    placeholder="ej. electrónica, consultoría, cursos"
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="font-bold text-slate-900 mb-4">Precio{form.type === 'good' ? ' y stock' : ''}</h2>
            <div className={form.type === 'good' ? 'grid grid-cols-2 gap-4' : ''}>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Precio ($)</label>
                <input
                  type="number"
                  value={form.price}
                  onChange={(e) => setForm({ ...form, price: e.target.value })}
                  placeholder="999"
                  min="0"
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              {form.type === 'good' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Stock</label>
                  <input
                    type="number"
                    value={form.stock}
                    onChange={(e) => setForm({ ...form, stock: e.target.value })}
                    placeholder="10"
                    min="0"
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-bold text-slate-900 mb-4">Plataforma de venta</h3>
            <select
              value={form.platform}
              onChange={(e) => setForm({ ...form, platform: e.target.value })}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PLATFORMS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h3 className="font-bold text-slate-900 mb-4">Preview</h3>
            <div className="bg-slate-50 p-4 rounded-lg">
              <p className="font-medium text-slate-900 text-sm mb-1">{form.name || 'Nombre'}</p>
              <p className="text-slate-600 text-xs mb-2 line-clamp-2">
                {form.description || 'Descripción'}
              </p>
              <p className="font-bold text-slate-900">${form.price || '0'}</p>
              {form.type === 'good' && <p className="text-xs text-slate-500 mt-1">Stock: {form.stock || '0'}</p>}
              <p className="text-xs text-slate-500 mt-1">
                {PLATFORMS.find(p => p.value === form.platform)?.label}
              </p>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-slate-300 text-white rounded-lg font-bold flex items-center justify-center gap-2"
          >
            {loading ? 'Creando...' : <>
              <Plus size={18} />
              Crear listing
            </>}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="w-full px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-900 rounded-lg font-medium"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}
