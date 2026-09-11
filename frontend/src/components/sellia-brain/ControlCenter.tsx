'use client'

import { useEffect, useMemo, useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse, ToggleAuditLogResponse } from '@/lib/api/toggles'
import { ToggleSwitch } from './ToggleSwitch'
import { AuditPanel } from './AuditPanel'
import { QuickStats } from './QuickStats'
import { FeatureInfoModal } from './FeatureInfoModal'

interface ControlCenterProps {
  businessId: UUID
}

type FilterStatus = 'all' | 'enabled' | 'disabled'

export const ControlCenter = ({ businessId }: ControlCenterProps) => {
  const [toggles, setToggles] = useState<AutomationToggleResponse[]>([])
  const [selectedToggleId, setSelectedToggleId] = useState<UUID | null>(null)
  const [auditLog, setAuditLog] = useState<ToggleAuditLogResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<UUID | null>(null)
  const [selectedToggleForInfo, setSelectedToggleForInfo] = useState<AutomationToggleResponse | null>(
    null
  )

  // Search & Filter
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')

  const categories = useMemo(
    () => [...new Set(toggles.map((t) => t.category))].sort(),
    [toggles]
  )

  // Filtered toggles
  const filteredToggles = useMemo(() => {
    return toggles.filter((t) => {
      const matchesSearch = t.display_name.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesCategory = filterCategory === 'all' || t.category === filterCategory
      const matchesStatus =
        filterStatus === 'all' ||
        (filterStatus === 'enabled' && t.is_enabled) ||
        (filterStatus === 'disabled' && !t.is_enabled)

      return matchesSearch && matchesCategory && matchesStatus
    })
  }, [toggles, searchTerm, filterCategory, filterStatus])

  useEffect(() => {
    loadToggles()
  }, [businessId])

  const loadToggles = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/automations/toggles/business/${businessId}`)
      if (res.ok) {
        const data = await res.json()
        setToggles(data)
      }
    } catch (err) {
      console.error('Error loading toggles:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (toggleId: UUID, enabled: boolean, reason?: string) => {
    setUpdating(toggleId)
    try {
      const res = await fetch(`/api/v1/automations/toggles/${toggleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_enabled: enabled }, null, 0),
      })
      if (res.ok) {
        await loadToggles()
      }
    } catch (err) {
      console.error('Error toggling:', err)
    } finally {
      setUpdating(null)
    }
  }

  const handleLimitChange = async (toggleId: UUID, newLimit: number) => {
    setUpdating(toggleId)
    try {
      const res = await fetch(`/api/v1/automations/toggles/${toggleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ monthly_limit: newLimit }),
      })
      if (res.ok) {
        await loadToggles()
      }
    } catch (err) {
      console.error('Error updating limit:', err)
    } finally {
      setUpdating(null)
    }
  }

  const handleShowAudit = async (toggleId: UUID) => {
    setSelectedToggleId(toggleId)
    try {
      const res = await fetch(`/api/v1/automations/toggles/${toggleId}/audit`)
      if (res.ok) {
        const data = await res.json()
        setAuditLog(data)
      }
    } catch (err) {
      console.error('Error loading audit:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      {!loading && toggles.length > 0 && <QuickStats toggles={toggles} />}

      {/* Search & Filter Bar */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <input
            type="text"
            placeholder="Buscar toggle... (ej: Lead Scorer)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-500"
          />

          {/* Category Filter */}
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          >
            <option value="all">Todas las categorías</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
            className="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          >
            <option value="all">Todos</option>
            <option value="enabled">Habilitados</option>
            <option value="disabled">Deshabilitados</option>
          </select>
        </div>

        {/* Filter Summary */}
        {(searchTerm || filterCategory !== 'all' || filterStatus !== 'all') && (
          <div className="text-sm text-slate-600 dark:text-slate-400">
            Mostrando {filteredToggles.length} de {toggles.length} toggles
            {searchTerm && ` • Búsqueda: "${searchTerm}"`}
            {filterCategory !== 'all' && ` • ${filterCategory}`}
            {filterStatus !== 'all' && ` • ${filterStatus}`}
          </div>
        )}
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar: Categories */}
        <aside className="lg:col-span-1">
          <div className="bg-slate-50 dark:bg-slate-900 rounded-lg p-4 sticky top-4">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-4">Categorías</h3>
            <div className="space-y-3">
              {categories.map((category) => {
                const catToggles = toggles.filter((t) => t.category === category)
                const enabledCount = catToggles.filter((t) => t.is_enabled).length
                return (
                  <button
                    key={category}
                    onClick={() => setFilterCategory(filterCategory === category ? 'all' : category)}
                    className={`
                      w-full text-left p-3 rounded border transition-colors
                      ${
                        filterCategory === category
                          ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700'
                          : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                      }
                    `}
                  >
                    <p className="font-semibold text-slate-900 dark:text-white capitalize">
                      {category}
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {enabledCount} de {catToggles.length} activos
                    </p>
                  </button>
                )
              })}
            </div>
          </div>
        </aside>

        {/* Main: Filtered Toggles */}
        <main className="lg:col-span-3">
          {filteredToggles.length === 0 ? (
            <div className="text-center py-12 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <p className="text-slate-600 dark:text-slate-400">
                {toggles.length === 0 ? 'Sin toggles' : 'No hay resultados que coincidan con los filtros'}
              </p>
              {(searchTerm || filterCategory !== 'all' || filterStatus !== 'all') && (
                <button
                  onClick={() => {
                    setSearchTerm('')
                    setFilterCategory('all')
                    setFilterStatus('all')
                  }}
                  className="mt-4 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Limpiar filtros
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredToggles.map((toggle) => (
                <ToggleSwitch
                  key={toggle.id}
                  toggle={toggle}
                  loading={updating === toggle.id}
                  onToggle={(enabled) => handleToggle(toggle.id, enabled)}
                  onLimitChange={(newLimit) => handleLimitChange(toggle.id, newLimit)}
                  onShowAudit={() => handleShowAudit(toggle.id)}
                  onShowInfo={() => setSelectedToggleForInfo(toggle)}
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Audit Panel Modal */}
      {selectedToggleId && (
        <AuditPanel logs={auditLog} onClose={() => setSelectedToggleId(null)} />
      )}

      {/* Feature Info Modal */}
      {selectedToggleForInfo && (
        <FeatureInfoModal toggle={selectedToggleForInfo} onClose={() => setSelectedToggleForInfo(null)} />
      )}
    </div>
  )
}
