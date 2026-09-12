'use client'

import { useEffect, useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse } from '@/lib/api/toggles'
import { ToggleNotificationRuleForm } from './ToggleNotificationRuleForm'
import { Bell, Trash2, Edit2 } from 'lucide-react'

interface ToggleNotificationRule {
  id: UUID
  business_id: UUID
  toggle_id: UUID
  event_type: string
  usage_threshold_pct?: number
  notify_via_email: boolean
  notify_via_webhook: boolean
  notify_via_inapp: boolean
  email_recipients: string[]
  webhook_url?: string
  webhook_secret?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface ToggleNotificationRuleListProps {
  toggle: AutomationToggleResponse
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  enabled: 'Toggle Habilitado',
  disabled: 'Toggle Deshabilitado',
  schedule_executed: 'Programación Ejecutada',
  usage_limit_reached: 'Límite de Uso Alcanzado',
  usage_threshold: 'Umbral de Uso Alcanzado',
}

export const ToggleNotificationRuleList = ({ toggle }: ToggleNotificationRuleListProps) => {
  const [rules, setRules] = useState<ToggleNotificationRule[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingRule, setEditingRule] = useState<ToggleNotificationRule | null>(null)
  const [deletingId, setDeletingId] = useState<UUID | null>(null)

  useEffect(() => {
    loadRules()
  }, [toggle.id])

  const loadRules = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/automations/toggles/${toggle.id}/notification-rules`)
      if (res.ok) {
        const data = await res.json()
        setRules(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('Error loading rules:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (ruleId: UUID) => {
    if (!confirm('¿Eliminar esta regla de notificación?')) return

    setDeletingId(ruleId)
    try {
      const res = await fetch(`/api/v1/automations/notification-rule/${ruleId}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        await loadRules()
      }
    } catch (err) {
      console.error('Error deleting rule:', err)
    } finally {
      setDeletingId(null)
    }
  }

  const handleFormSuccess = async () => {
    await loadRules()
    setShowForm(false)
    setEditingRule(null)
  }

  if (loading) {
    return <div className="text-center py-4 text-slate-500">Cargando reglas...</div>
  }

  if (showForm) {
    return (
      <ToggleNotificationRuleForm
        toggle={toggle}
        editingRule={editingRule}
        onSuccess={handleFormSuccess}
        onCancel={() => {
          setShowForm(false)
          setEditingRule(null)
        }}
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 dark:text-white">Reglas de Notificación</h3>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1 rounded text-sm bg-blue-600 text-white hover:bg-blue-700"
        >
          + Nueva Regla
        </button>
      </div>

      {rules.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700">
          <Bell size={24} className="mx-auto mb-2 text-slate-400" />
          <p className="text-sm text-slate-600 dark:text-slate-400">Sin reglas de notificación</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                      {EVENT_TYPE_LABELS[rule.event_type] || rule.event_type}
                    </span>
                    {!rule.is_active && (
                      <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-400">
                        Inactivo
                      </span>
                    )}
                  </div>

                  <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                    {/* Channels */}
                    <div className="flex flex-wrap gap-2">
                      {rule.notify_via_email && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-xs">
                          📧 Email
                        </span>
                      )}
                      {rule.notify_via_webhook && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-xs">
                          🔗 Webhook
                        </span>
                      )}
                      {rule.notify_via_inapp && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-xs">
                          🔔 En app
                        </span>
                      )}
                    </div>

                    {/* Email Recipients */}
                    {rule.notify_via_email && rule.email_recipients.length > 0 && (
                      <p>
                        <strong>Emails:</strong> {rule.email_recipients.join(', ')}
                      </p>
                    )}

                    {/* Webhook URL */}
                    {rule.notify_via_webhook && rule.webhook_url && (
                      <p>
                        <strong>Webhook:</strong>{' '}
                        <code className="text-xs bg-slate-100 dark:bg-slate-900 px-1 rounded font-mono">
                          {rule.webhook_url}
                        </code>
                      </p>
                    )}

                    {/* Usage Threshold */}
                    {rule.event_type === 'usage_threshold' && rule.usage_threshold_pct && (
                      <p>
                        <strong>Umbral:</strong> {rule.usage_threshold_pct}%
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => {
                      setEditingRule(rule)
                      setShowForm(true)
                    }}
                    className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400"
                    title="Editar"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    disabled={deletingId === rule.id}
                    className="p-2 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 disabled:opacity-50"
                    title="Eliminar"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
