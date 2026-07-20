'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { catalogApi } from '@/lib/catalog'
import { MODALITY_LABELS, SOLUTION_TYPE_LABELS } from '@/lib/services'
import { ArrowLeft, Briefcase, Package, FileText, Clock, MapPin, Shield, Check } from 'lucide-react'

const itemTypes = [
  { value: 'service', label: 'Servicio', description: 'Un servicio que prestas', icon: Briefcase },
  { value: 'good', label: 'Bien / Producto', description: 'Un producto físico', icon: Package },
  { value: 'digital', label: 'Producto Digital', description: 'Archivo descargable', icon: FileText },
]

const MODALITIES = Object.entries(MODALITY_LABELS).map(([value, label]) => ({ value, label }))
const SOLUTION_TYPES = Object.entries(SOLUTION_TYPE_LABELS).map(([value, label]) => ({ value, label }))

export default function NuevoItemPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const businessId = searchParams?.get('business') || ''

  const [type, setType] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState('')
  const [stock, setStock] = useState('')

  // Service fields
  const [selectedModalities, setSelectedModalities] = useState<string[]>([])
  const [selectedSolutions, setSelectedSolutions] = useState<string[]>([])
  const [durationMinutes, setDurationMinutes] = useState('60')
  const [bufferMinutes, setBufferMinutes] = useState('15')
  const [requiresPrep, setRequiresPrep] = useState(false)
  const [materialsNeeded, setMaterialsNeeded] = useState('')
  const [prerequisites, setPrerequisites] = useState('')
  const [serviceAreaKm, setServiceAreaKm] = useState('')
  const [travelIncluded, setTravelIncluded] = useState(false)
  const [onlineLink, setOnlineLink] = useState('')
  const [cancellationHours, setCancellationHours] = useState('24')
  const [rescheduleHours, setRescheduleHours] = useState('12')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleModality = (value: string) => {
    setSelectedModalities(prev =>
      prev.includes(value) ? prev.filter(v => v !== value) : [...prev, value]
    )
  }

  const toggleSolution = (value: string) => {
    setSelectedSolutions(prev =>
      prev.includes(value) ? prev.filter(v => v !== value) : [...prev, value]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload: any = {
        type: type as any,
        name,
        description: description || undefined,
        price: parseFloat(price),
        stock: type === 'good' ? parseInt(stock || '0') : undefined,
      }

      if (type === 'service') {
        payload.extra_data = {
          modalities: selectedModalities,
          solution_types: selectedSolutions,
          duration_minutes: parseInt(durationMinutes) || 60,
          buffer_minutes: parseInt(bufferMinutes) || 15,
          requires_prep: requiresPrep,
          materials_needed: materialsNeeded.split(',').map(s => s.trim()).filter(Boolean),
          prerequisites: prerequisites.split(',').map(s => s.trim()).filter(Boolean),
          service_area_km: serviceAreaKm ? parseFloat(serviceAreaKm) : null,
          travel_included: travelIncluded,
          online_meeting_link: onlineLink || null,
          cancellation_policy_hours: parseInt(cancellationHours) || 24,
          reschedule_policy_hours: parseInt(rescheduleHours) || 12,
        }
      }

      await catalogApi.create(businessId, payload)
      router.push(`/dashboard/catalogo?business=${businessId}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear el ítem')
    } finally {
      setLoading(false)
    }
  }

  if (!businessId) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <p className="text-gray-500">No se seleccionó un negocio.</p>
        <Link href="/dashboard/negocios" className="text-primary-600 hover:underline mt-2 inline-block">
          Ir a mis negocios
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <Link
          href={`/dashboard/catalogo?business=${businessId}`}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al catálogo
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Agregar ítem al catálogo</h1>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl p-8 border border-gray-100 shadow-sm space-y-6">
        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>
        )}

        {/* Type selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">Tipo de ítem</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {itemTypes.map((it) => {
              const Icon = it.icon
              const isSelected = type === it.value
              return (
                <button
                  key={it.value}
                  type="button"
                  onClick={() => setType(it.value)}
                  className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 text-center transition-colors ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <Icon className={`w-6 h-6 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`} />
                  <span className={`font-medium text-sm ${isSelected ? 'text-primary-900' : 'text-gray-900'}`}>
                    {it.label}
                  </span>
                  <span className={`text-xs ${isSelected ? 'text-primary-700' : 'text-gray-500'}`}>
                    {it.description}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Basic fields */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Nombre</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors"
            placeholder="Ej: Desarrollo de Apps con IA"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Descripción</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors"
            placeholder="Describe el ítem..."
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Precio</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors"
              placeholder="0.00"
            />
          </div>

          {type === 'good' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stock</label>
              <input
                type="number"
                min="0"
                value={stock}
                onChange={(e) => setStock(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors"
                placeholder="0"
              />
            </div>
          )}
        </div>

        {/* Service-specific fields */}
        {type === 'service' && (
          <div className="space-y-6 pt-4 border-t border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-primary-600" />
              Configuración del servicio
            </h3>

            {/* Modalities */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                Modalidades de atención
              </label>
              <div className="flex flex-wrap gap-2">
                {MODALITIES.map(m => (
                  <button
                    key={m.value}
                    type="button"
                    onClick={() => toggleModality(m.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      selectedModalities.includes(m.value)
                        ? 'bg-primary-50 border-primary-300 text-primary-700'
                        : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    {selectedModalities.includes(m.value) && <Check className="w-3 h-3 inline mr-1" />}
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Solution types */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipos de solución que ofrece
              </label>
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto p-1">
                {SOLUTION_TYPES.map(s => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => toggleSolution(s.value)}
                    className={`px-2.5 py-1 rounded-md text-xs border transition-colors ${
                      selectedSolutions.includes(s.value)
                        ? 'bg-violet-50 border-violet-300 text-violet-700'
                        : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                    }`}
                  >
                    {selectedSolutions.includes(s.value) && <Check className="w-3 h-3 inline mr-1" />}
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Duration & buffer */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  Duración (min)
                </label>
                <input
                  type="number"
                  min="1"
                  value={durationMinutes}
                  onChange={e => setDurationMinutes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Buffer entre citas (min)</label>
                <input
                  type="number"
                  min="0"
                  value={bufferMinutes}
                  onChange={e => setBufferMinutes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            {/* Materials & prerequisites */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Materiales necesarios</label>
                <input
                  type="text"
                  value={materialsNeeded}
                  onChange={e => setMaterialsNeeded(e.target.value)}
                  placeholder="Separados por coma"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Prerrequisitos</label>
                <input
                  type="text"
                  value={prerequisites}
                  onChange={e => setPrerequisites(e.target.value)}
                  placeholder="Separados por coma"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            {/* Location & policies */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Radio de servicio (km)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={serviceAreaKm}
                  onChange={e => setServiceAreaKm(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Link de reunión online</label>
                <input
                  type="url"
                  value={onlineLink}
                  onChange={e => setOnlineLink(e.target.value)}
                  placeholder="https://meet.google.com/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <Shield className="w-3.5 h-3.5" />
                  Cancelación (horas antes)
                </label>
                <input
                  type="number"
                  min="0"
                  value={cancellationHours}
                  onChange={e => setCancellationHours(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reagendamiento (horas antes)</label>
                <input
                  type="number"
                  min="0"
                  value={rescheduleHours}
                  onChange={e => setRescheduleHours(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={requiresPrep}
                  onChange={e => setRequiresPrep(e.target.checked)}
                  className="rounded border-gray-300"
                />
                Requiere preparación previa
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={travelIncluded}
                  onChange={e => setTravelIncluded(e.target.checked)}
                  className="rounded border-gray-300"
                />
                Incluye traslado
              </label>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !type}
          className="w-full bg-primary-600 text-white py-2.5 rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Guardando...' : 'Guardar ítem'}
        </button>
      </form>
    </div>
  )
}
