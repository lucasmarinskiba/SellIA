'use client'

import { useEffect, useMemo, useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse, ToggleAuditLogResponse } from '@/lib/api/toggles'
import { ToggleSwitch } from './ToggleSwitch'
import { AuditPanel } from './AuditPanel'

interface ControlCenterProps {
  businessId: UUID
}

export const ControlCenter = ({ businessId }: ControlCenterProps) => {
  const [toggles, setToggles] = useState<AutomationToggleResponse[]>([])
  const [selectedToggleId, setSelectedToggleId] = useState<UUID | null>(null)
  const [auditLog, setAuditLog] = useState<ToggleAuditLogResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<UUID | null>(null)

  const categories = useMemo(
    () => [...new Set(toggles.map((t) => t.category))].sort(),
    [toggles]
  )

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
                <div
                  key={category}
                  className="p-3 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700"
                >
                  <p className="font-semibold text-slate-900 dark:text-white capitalize">
                    {category}
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {enabledCount} de {catToggles.length} activos
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </aside>

      {/* Main: Toggles by Category */}
      <main className="lg:col-span-3 space-y-8">
        {categories.map((category) => (
          <section key={category}>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white capitalize mb-4">
              {category}
            </h2>
            <div className="space-y-3">
              {toggles
                .filter((t) => t.category === category)
                .map((toggle) => (
                  <ToggleSwitch
                    key={toggle.id}
                    toggle={toggle}
                    loading={updating === toggle.id}
                    onToggle={(enabled) => handleToggle(toggle.id, enabled)}
                    onLimitChange={(newLimit) => handleLimitChange(toggle.id, newLimit)}
                    onShowAudit={() => handleShowAudit(toggle.id)}
                  />
                ))}
            </div>
          </section>
        ))}
      </main>

      {/* Audit Panel Modal */}
      {selectedToggleId && (
        <AuditPanel logs={auditLog} onClose={() => setSelectedToggleId(null)} />
      )}
    </div>
  )
}
