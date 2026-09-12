'use client'

import { useEffect, useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse } from '@/lib/api/toggles'

export interface ToggleNotificationRuleFormData {
  event_type: string
  usage_threshold_pct?: number
  notify_via_email: boolean
  notify_via_webhook: boolean
  notify_via_inapp: boolean
  email_recipients: string[]
  webhook_url?: string
  webhook_secret?: string
}

interface ToggleNotificationRuleFormProps {
  toggle: AutomationToggleResponse
  onSuccess?: (rule: any) => void
  onCancel?: () => void
  editingRule?: any
}

const EVENT_TYPES = [
  { value: 'enabled', label: 'Toggle Habilitado' },
  { value: 'disabled', label: 'Toggle Deshabilitado' },
  { value: 'schedule_executed', label: 'Programación Ejecutada' },
  { value: 'usage_limit_reached', label: 'Límite de Uso Alcanzado' },
  { value: 'usage_threshold', label: 'Umbral de Uso Alcanzado' },
]

export const ToggleNotificationRuleForm = ({
  toggle,
  onSuccess,
  onCancel,
  editingRule,
}: ToggleNotificationRuleFormProps) => {
  const [formData, setFormData] = useState<ToggleNotificationRuleFormData>({
    event_type: editingRule?.event_type || 'enabled',
    usage_threshold_pct: editingRule?.usage_threshold_pct || 80,
    notify_via_email: editingRule?.notify_via_email ?? true,
    notify_via_webhook: editingRule?.notify_via_webhook ?? false,
    notify_via_inapp: editingRule?.notify_via_inapp ?? true,
    email_recipients: editingRule?.email_recipients || [],
    webhook_url: editingRule?.webhook_url || '',
    webhook_secret: editingRule?.webhook_secret || '',
  })

  const [emailInput, setEmailInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (field: keyof ToggleNotificationRuleFormData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
    setError(null)
  }

  const addEmail = () => {
    if (!emailInput.trim()) return
    if (formData.email_recipients.includes(emailInput)) {
      setError('Email ya agregado')
      return
    }
    setFormData((prev) => ({
      ...prev,
      email_recipients: [...prev.email_recipients, emailInput],
    }))
    setEmailInput('')
  }

  const removeEmail = (email: string) => {
    setFormData((prev) => ({
      ...prev,
      email_recipients: prev.email_recipients.filter((e) => e !== email),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      if (formData.notify_via_email && formData.email_recipients.length === 0) {
        throw new Error('Agrega al menos un email para notificaciones por email')
      }

      if (formData.notify_via_webhook && !formData.webhook_url) {
        throw new Error('Ingresa URL del webhook')
      }

      const payload = {
        toggle_id: toggle.id,
        event_type: formData.event_type,
        usage_threshold_pct:
          formData.event_type === 'usage_threshold' ? formData.usage_threshold_pct : null,
        notify_via_email: formData.notify_via_email,
        notify_via_webhook: formData.notify_via_webhook,
        notify_via_inapp: formData.notify_via_inapp,
        email_recipients: formData.email_recipients,
        webhook_url: formData.webhook_url || null,
        webhook_secret: formData.webhook_secret || null,
      }

      const method = editingRule ? 'PATCH' : 'POST'
      const url = editingRule
        ? `/api/v1/automations/notification-rule/${editingRule.id}`
        : `/api/v1/automations/toggles/${toggle.id}/notification-rule`

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Error al guardar regla')
      }

      const created = await res.json()
      onSuccess?.(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6"
    >
      <div>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
          {editingRule ? 'Editar' : 'Nueva'} Regla de Notificación
        </h3>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3">
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Event Type */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Tipo de Evento
        </label>
        <select
          value={formData.event_type}
          onChange={(e) => handleChange('event_type', e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
        >
          {EVENT_TYPES.map((et) => (
            <option key={et.value} value={et.value}>
              {et.label}
            </option>
          ))}
        </select>
      </div>

      {/* Usage Threshold */}
      {formData.event_type === 'usage_threshold' && (
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Umbral de Uso (%)
          </label>
          <input
            type="number"
            min="1"
            max="100"
            value={formData.usage_threshold_pct || 80}
            onChange={(e) => handleChange('usage_threshold_pct', parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
          />
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Notificar cuando se alcance este % del límite mensual
          </p>
        </div>
      )}

      {/* Notification Channels */}
      <div className="space-y-3">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Canales</p>

        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.notify_via_email}
            onChange={(e) => handleChange('notify_via_email', e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="ml-2 text-sm text-slate-700 dark:text-slate-300">Email</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.notify_via_webhook}
            onChange={(e) => handleChange('notify_via_webhook', e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="ml-2 text-sm text-slate-700 dark:text-slate-300">Webhook</span>
        </label>

        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.notify_via_inapp}
            onChange={(e) => handleChange('notify_via_inapp', e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="ml-2 text-sm text-slate-700 dark:text-slate-300">En la app</span>
        </label>
      </div>

      {/* Email Recipients */}
      {formData.notify_via_email && (
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Destinatarios de Email
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="email"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addEmail())}
              placeholder="usuario@example.com"
              className="flex-1 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
            />
            <button
              type="button"
              onClick={addEmail}
              className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium"
            >
              Agregar
            </button>
          </div>

          {formData.email_recipients.length > 0 && (
            <div className="space-y-2">
              {formData.email_recipients.map((email) => (
                <div
                  key={email}
                  className="flex items-center justify-between bg-slate-100 dark:bg-slate-700 rounded px-3 py-2"
                >
                  <span className="text-sm text-slate-900 dark:text-white">{email}</span>
                  <button
                    type="button"
                    onClick={() => removeEmail(email)}
                    className="text-xs text-red-600 dark:text-red-400 hover:underline"
                  >
                    Eliminar
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Webhook URL */}
      {formData.notify_via_webhook && (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              URL del Webhook
            </label>
            <input
              type="url"
              value={formData.webhook_url}
              onChange={(e) => handleChange('webhook_url', e.target.value)}
              placeholder="https://example.com/webhook"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Secret (opcional)
            </label>
            <input
              type="password"
              value={formData.webhook_secret}
              onChange={(e) => handleChange('webhook_secret', e.target.value)}
              placeholder="Secret para HMAC-SHA256"
              className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm font-mono"
            />
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Si ingresa secret, se firmará el payload con HMAC-SHA256
            </p>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 justify-end pt-4 border-t border-slate-200 dark:border-slate-700">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Guardando...' : editingRule ? 'Actualizar' : 'Crear Regla'}
        </button>
      </div>
    </form>
  )
}
