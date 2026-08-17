'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, AlertCircle, Loader, Upload } from 'lucide-react'

/* ============================================================
   PRODUCT FORM — Create/edit products
   ============================================================ */

interface FormData {
  name: string
  description: string
  short_description: string
  price: number
  compare_at_price: number | null
  sku: string
  inventory_count: number
  featured_image_url: string
  status: 'DRAFT' | 'PUBLISHED'
}

export default function ProductForm({ productId, mode }: { productId?: string; mode: 'create' | 'edit' }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const businessId = searchParams.get('businessId') || ''

  const [loading, setLoading] = useState(mode === 'edit')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [mounted, setMounted] = useState(false)

  const [form, setForm] = useState<FormData>({
    name: '',
    description: '',
    short_description: '',
    price: 0,
    compare_at_price: null,
    sku: '',
    inventory_count: 0,
    featured_image_url: '',
    status: 'DRAFT',
  })

  useEffect(() => {
    setMounted(true)
    if (mode === 'edit' && productId) {
      fetchProduct()
    } else {
      setLoading(false)
    }
  }, [mode, productId])

  const fetchProduct = async () => {
    try {
      const res = await fetch(`/api/v1/businesses/${businessId}/products/${productId}`)
      if (!res.ok) throw new Error('Error cargando producto')

      const data = await res.json()
      setForm({
        name: data.name || '',
        description: data.description || '',
        short_description: data.short_description || '',
        price: data.price || 0,
        compare_at_price: data.compare_at_price || null,
        sku: data.sku || '',
        inventory_count: data.inventory_count || 0,
        featured_image_url: data.featured_image_url || '',
        status: data.status || 'DRAFT',
      })
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')

    try {
      const url =
        mode === 'create'
          ? `/api/v1/businesses/${businessId}/products`
          : `/api/v1/businesses/${businessId}/products/${productId}`

      const method = mode === 'create' ? 'POST' : 'PUT'

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      if (!res.ok) throw new Error('Error guardando producto')

      const data = await res.json()
      router.push(`/dashboard/websites/products?businessId=${businessId}`)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const updateForm = (field: keyof FormData, value: any) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setError('')
  }

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link
            href={`/dashboard/websites/products?businessId=${businessId}`}
            className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-900" />
          </Link>
          <div>
            <h1 className="text-4xl font-bold text-slate-900">
              {mode === 'create' ? 'Nuevo Producto' : 'Editar Producto'}
            </h1>
            <p className="text-lg text-slate-600">
              {mode === 'create' ? 'Crea un nuevo producto para tu tienda' : 'Actualiza los detalles del producto'}
            </p>
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
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
              <h2 className="text-xl font-bold text-slate-900">Información Básica</h2>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Nombre del Producto
                </label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => updateForm('name', e.target.value)}
                  placeholder="Ej: Polera Azul XL"
                  required
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Descripción Corta
                </label>
                <textarea
                  value={form.short_description}
                  onChange={(e) => updateForm('short_description', e.target.value)}
                  placeholder="Breve descripción que aparece en listas"
                  maxLength={500}
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 resize-none h-20"
                />
                <p className="text-xs text-slate-500 mt-1">{form.short_description.length}/500</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Descripción Completa
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => updateForm('description', e.target.value)}
                  placeholder="Descripción detallada del producto"
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 resize-none h-32"
                />
              </div>
            </div>

            {/* Pricing & Inventory */}
            <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
              <h2 className="text-xl font-bold text-slate-900">Precio e Inventario</h2>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-2">
                    Precio de Venta
                  </label>
                  <div className="flex items-center">
                    <span className="text-slate-600 mr-2">$</span>
                    <input
                      type="number"
                      value={form.price}
                      onChange={(e) => updateForm('price', parseFloat(e.target.value))}
                      placeholder="0.00"
                      step="0.01"
                      required
                      className="flex-1 px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-2">
                    Precio Original (opcional)
                  </label>
                  <div className="flex items-center">
                    <span className="text-slate-600 mr-2">$</span>
                    <input
                      type="number"
                      value={form.compare_at_price || ''}
                      onChange={(e) => updateForm('compare_at_price', e.target.value ? parseFloat(e.target.value) : null)}
                      placeholder="Para mostrar descuento"
                      step="0.01"
                      className="flex-1 px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-2">SKU</label>
                  <input
                    type="text"
                    value={form.sku}
                    onChange={(e) => updateForm('sku', e.target.value)}
                    placeholder="Código SKU único"
                    className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-2">
                    Stock Disponible
                  </label>
                  <input
                    type="number"
                    value={form.inventory_count}
                    onChange={(e) => updateForm('inventory_count', parseInt(e.target.value))}
                    placeholder="0"
                    min="0"
                    className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                  />
                </div>
              </div>
            </div>

            {/* Images */}
            <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
              <h2 className="text-xl font-bold text-slate-900">Imagen Principal</h2>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  URL de la Imagen
                </label>
                <input
                  type="url"
                  value={form.featured_image_url}
                  onChange={(e) => updateForm('featured_image_url', e.target.value)}
                  placeholder="https://ejemplo.com/imagen.jpg"
                  className="w-full px-4 py-2 rounded-lg border border-slate-200 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 mb-4"
                />

                {form.featured_image_url && (
                  <img
                    src={form.featured_image_url}
                    alt="Preview"
                    className="w-full max-w-xs rounded-lg border border-slate-200"
                  />
                )}
              </div>
            </div>

            {/* Status */}
            <div className="rounded-lg bg-white border border-slate-200 p-6 space-y-5">
              <h2 className="text-xl font-bold text-slate-900">Estado</h2>

              <div className="flex gap-4">
                {(['DRAFT', 'PUBLISHED'] as const).map((s) => (
                  <label key={s} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="status"
                      value={s}
                      checked={form.status === s}
                      onChange={(e) => updateForm('status', e.target.value as any)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm font-semibold text-slate-900">
                      {s === 'DRAFT' ? 'Borrador' : 'Publicado'}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <Link
                href={`/dashboard/websites/products?businessId=${businessId}`}
                className="flex-1 px-6 py-3 rounded-lg border border-slate-200 text-slate-900 font-semibold hover:bg-slate-50 transition-all"
              >
                Cancelar
              </Link>
              <button
                type="submit"
                disabled={saving}
                className="flex-1 px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-cyan-600 text-white font-semibold hover:from-cyan-400 hover:to-cyan-500 transition-all disabled:opacity-50"
              >
                {saving ? 'Guardando...' : 'Guardar Producto'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
