'use client'

import { useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse } from '@/lib/api/toggles'
import { ChevronDown } from 'lucide-react'

export interface AdvancedFilterParams {
  categories: string[]
  usage_min?: number
  usage_max?: number
  enabled_only?: boolean
  modified_after?: string
}

interface AdvancedToggleFilterProps {
  businessId: UUID
  allCategories: string[]
  onResults: (results: AutomationToggleResponse[]) => void
  onLoading: (loading: boolean) => void
  onError: (error: string | null) => void
}

export const AdvancedToggleFilter = ({
  businessId,
  allCategories,
  onResults,
  onLoading,
  onError,
}: AdvancedToggleFilterProps) => {
  const [expanded, setExpanded] = useState(false)
  const [filters, setFilters] = useState<AdvancedFilterParams>({
    categories: [],
    usage_min: undefined,
    usage_max: undefined,
    enabled_only: undefined,
    modified_after: undefined,
  })

  const handleCategoryToggle = (category: string) => {
    setFilters((prev) => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter((c) => c !== category)
        : [...prev.categories, category],
    }))
  }

  const handleApplyFilters = async () => {
    onLoading(true)
    onError(null)

    try {
      const params = new URLSearchParams()

      if (filters.categories.length > 0) {
        params.append('categories', filters.categories.join(','))
      }
      if (filters.usage_min !== undefined) {
        params.append('usage_min', filters.usage_min.toString())
      }
      if (filters.usage_max !== undefined) {
        params.append('usage_max', filters.usage_max.toString())
      }
      if (filters.enabled_only !== undefined) {
        params.append('enabled_only', filters.enabled_only.toString())
      }
      if (filters.modified_after) {
        params.append('modified_after', new Date(filters.modified_after).toISOString())
      }

      const res = await fetch(
        `/api/v1/automations/toggles/business/${businessId}/search?${params.toString()}`
      )

      if (!res.ok) {
        throw new Error('Error al filtrar toggles')
      }

      const data = await res.json()
      onResults(Array.isArray(data) ? data : [])
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      onLoading(false)
    }
  }

  const handleReset = () => {
    setFilters({
      categories: [],
      usage_min: undefined,
      usage_max: undefined,
      enabled_only: undefined,
      modified_after: undefined,
    })
    onError(null)
  }

  const hasActiveFilters =
    filters.categories.length > 0 ||
    filters.usage_min !== undefined ||
    filters.usage_max !== undefined ||
    filters.enabled_only !== undefined ||
    filters.modified_after

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold text-slate-900 dark:text-white">🔍 Filtrado Avanzado</span>
          {hasActiveFilters && (
            <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
              {filters.categories.length +
                (filters.usage_min !== undefined ? 1 : 0) +
                (filters.usage_max !== undefined ? 1 : 0) +
                (filters.enabled_only !== undefined ? 1 : 0) +
                (filters.modified_after ? 1 : 0)}{' '}
              filtros
            </span>
          )}
        </div>
        <ChevronDown
          size={20}
          className={`transition-transform text-slate-400 ${expanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Filters */}
      {expanded && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-4 space-y-4">
          {/* Categories */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Categorías
            </label>
            <div className="grid grid-cols-2 gap-2">
              {allCategories.map((cat) => (
                <label key={cat} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.categories.includes(cat)}
                    onChange={() => handleCategoryToggle(cat)}
                    className="w-4 h-4 rounded"
                  />
                  <span className="ml-2 text-sm text-slate-700 dark:text-slate-300 capitalize">
                    {cat}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Usage Range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Uso Mínimo
              </label>
              <input
                type="number"
                min="0"
                value={filters.usage_min ?? ''}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    usage_min: e.target.value ? parseInt(e.target.value) : undefined,
                  }))
                }
                placeholder="0"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Uso Máximo
              </label>
              <input
                type="number"
                min="0"
                value={filters.usage_max ?? ''}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    usage_max: e.target.value ? parseInt(e.target.value) : undefined,
                  }))
                }
                placeholder="Sin límite"
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
              />
            </div>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Estado
            </label>
            <select
              value={filters.enabled_only === undefined ? '' : filters.enabled_only.toString()}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  enabled_only: e.target.value === '' ? undefined : e.target.value === 'true',
                }))
              }
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
            >
              <option value="">Todos</option>
              <option value="true">Habilitados</option>
              <option value="false">Deshabilitados</option>
            </select>
          </div>

          {/* Modified After */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Modificado Después de
            </label>
            <input
              type="date"
              value={filters.modified_after ? filters.modified_after.slice(0, 10) : ''}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  modified_after: e.target.value ? new Date(e.target.value).toISOString().slice(0, 10) : undefined,
                }))
              }
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={handleApplyFilters}
              className="flex-1 px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 font-medium text-sm transition-colors"
            >
              Aplicar Filtros
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 font-medium text-sm transition-colors"
            >
              Limpiar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
