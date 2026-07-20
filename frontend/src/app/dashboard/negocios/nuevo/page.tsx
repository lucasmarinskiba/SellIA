'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { businessApi } from '@/lib/business'
import { ArrowLeft, Briefcase, Package, FileText, Layers } from 'lucide-react'
import Link from 'next/link'

const businessTypes = [
  { value: 'services', label: 'Servicios', description: 'Vendo servicios profesionales (home office, presencial, etc.)', icon: Briefcase },
  { value: 'goods', label: 'Bienes / Productos', description: 'Vendo productos físicos con envío o retiro', icon: Package },
  { value: 'digital', label: 'Productos Digitales', description: 'Vendo archivos, cursos, templates, etc.', icon: FileText },
  { value: 'mixed', label: 'Mixto', description: 'Combino servicios, bienes y/o digitales', icon: Layers },
]

export default function NuevoNegocioPage() {
  const router = useRouter()
  const [name, setName] = useState('')
  const [type, setType] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await businessApi.create({
        name,
        type: type as any,
        description: description || undefined,
      })
      router.push('/dashboard/negocios')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear el negocio')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link href="/dashboard/negocios" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft className="w-4 h-4" />
          Volver a mis negocios
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Crear nuevo negocio</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl p-8 border border-gray-100 shadow-sm space-y-6">
        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Nombre del negocio</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors"
            placeholder="Ej: Mi Empresa de Servicios IA"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">¿Qué vendes?</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {businessTypes.map((bt) => {
              const Icon = bt.icon
              const isSelected = type === bt.value
              return (
                <button
                  key={bt.value}
                  type="button"
                  onClick={() => setType(bt.value)}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 text-left transition-colors ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Icon className={`w-5 h-5 mt-0.5 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`} />
                  <div>
                    <span className={`block font-medium ${isSelected ? 'text-primary-900' : 'text-gray-900'}`}>
                      {bt.label}
                    </span>
                    <span className={`block text-xs mt-1 ${isSelected ? 'text-primary-700' : 'text-gray-500'}`}>
                      {bt.description}
                    </span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Descripción (opcional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors"
            placeholder="Describe brevemente tu negocio..."
          />
        </div>

        <button
          type="submit"
          disabled={loading || !type}
          className="w-full bg-primary-600 text-white py-2.5 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Creando...' : 'Crear negocio'}
        </button>
      </form>
    </div>
  )
}
