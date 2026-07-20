'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { catalogApi, CatalogItem } from '@/lib/catalog'
import { businessApi, Business } from '@/lib/business'
import { Package, Plus, Pencil, Trash2, ArrowLeft, Briefcase, Clock } from 'lucide-react'
import { MODALITY_LABELS, SOLUTION_TYPE_LABELS } from '@/lib/services'

export default function CatalogoPage() {
  const searchParams = useSearchParams()
  const businessId = searchParams?.get('business')

  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState<string>(businessId || '')
  const [items, setItems] = useState<CatalogItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBusinesses()
  }, [])

  useEffect(() => {
    if (selectedBusiness) {
      loadItems(selectedBusiness)
    } else {
      setItems([])
      setLoading(false)
    }
  }, [selectedBusiness])

  const loadBusinesses = async () => {
    try {
      const data = await businessApi.list()
      setBusinesses(data)
      if (!selectedBusiness && data.length > 0) {
        setSelectedBusiness(data[0].id)
      }
    } catch {
      setLoading(false)
    }
  }

  const loadItems = async (bid: string) => {
    setLoading(true)
    try {
      const data = await catalogApi.list(bid)
      setItems(data)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (itemId: string) => {
    if (!confirm('¿Eliminar este ítem del catálogo?')) return
    try {
      await catalogApi.delete(selectedBusiness, itemId)
      setItems((prev) => prev.filter((i) => i.id !== itemId))
    } catch {
      // handled by interceptor
    }
  }

  const currentBusiness = businesses.find((b) => b.id === selectedBusiness)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Catálogo</h1>
          <p className="text-gray-500 mt-1">
            {currentBusiness ? `Gestionando: ${currentBusiness.name}` : 'Selecciona un negocio'}
          </p>
        </div>
        {selectedBusiness && (
          <Link
            href={`/dashboard/catalogo/nuevo?business=${selectedBusiness}`}
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Agregar ítem
          </Link>
        )}
      </div>

      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Negocio:</label>
        <select
          value={selectedBusiness}
          onChange={(e) => setSelectedBusiness(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
        >
          <option value="">Seleccionar...</option>
          {businesses.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : !selectedBusiness ? (
        <div className="bg-white rounded-xl p-12 text-center border border-gray-100">
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Selecciona un negocio</h3>
          <p className="text-gray-500 mt-1">Primero necesitas seleccionar o crear un negocio</p>
          <Link
            href="/dashboard/negocios/nuevo"
            className="inline-flex items-center gap-2 mt-6 text-primary-600 hover:text-primary-700 font-medium"
          >
            <ArrowLeft className="w-4 h-4" />
            Crear negocio
          </Link>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-xl p-12 text-center border border-gray-100">
          <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">Catálogo vacío</h3>
          <p className="text-gray-500 mt-1 mb-6">Agrega tu primer producto, servicio o archivo digital</p>
          <Link
            href={`/dashboard/catalogo/nuevo?business=${selectedBusiness}`}
            className="inline-flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Agregar ítem
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Nombre</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Tipo</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Precio</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Detalles</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Estado</th>
                <th className="px-6 py-3 text-xs font-semibold text-gray-500 uppercase text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{item.name}</div>
                    {item.description && (
                      <div className="text-sm text-gray-500 line-clamp-1">{item.description}</div>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize
                      bg-gray-100 text-gray-800">
                      {item.type === 'good' ? 'Bien' : item.type === 'service' ? 'Servicio' : 'Digital'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    ${item.price} {item.currency}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {item.type === 'good' ? (item.stock !== null ? item.stock : 'N/A') :
                     item.type === 'service' ? (
                       <div className="space-y-1">
                         {item.extra_data?.duration_minutes && (
                           <div className="flex items-center gap-1 text-xs text-gray-500">
                             <Clock className="w-3 h-3" />
                             {item.extra_data.duration_minutes} min
                           </div>
                         )}
                         {item.extra_data?.modalities && item.extra_data.modalities.length > 0 && (
                           <div className="flex flex-wrap gap-1">
                             {item.extra_data.modalities.slice(0, 2).map((m: string) => (
                               <span key={m} className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-[10px]">
                                 {MODALITY_LABELS[m] || m}
                               </span>
                             ))}
                             {item.extra_data.modalities.length > 2 && (
                               <span className="text-[10px] text-gray-400">+{item.extra_data.modalities.length - 2}</span>
                             )}
                           </div>
                         )}
                         {item.extra_data?.solution_types && item.extra_data.solution_types.length > 0 && (
                           <div className="flex flex-wrap gap-1">
                             {item.extra_data.solution_types.slice(0, 2).map((s: string) => (
                               <span key={s} className="px-1.5 py-0.5 bg-violet-50 text-violet-600 rounded text-[10px]">
                                 {SOLUTION_TYPE_LABELS[s] || s}
                               </span>
                             ))}
                             {item.extra_data.solution_types.length > 2 && (
                               <span className="text-[10px] text-gray-400">+{item.extra_data.solution_types.length - 2}</span>
                             )}
                           </div>
                         )}
                       </div>
                     ) : '—'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      item.is_available
                        ? 'bg-green-50 text-green-700'
                        : 'bg-red-50 text-red-700'
                    }`}>
                      {item.is_available ? 'Disponible' : 'No disponible'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button className="text-gray-400 hover:text-primary-600 transition-colors">
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
