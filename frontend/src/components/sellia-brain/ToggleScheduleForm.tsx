'use client'

import { useEffect, useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse } from '@/lib/api/toggles'

export interface ToggleScheduleFormData {
  start_time: string
  timezone: string
  recurring: boolean
  recurrence_rule?: string
  action: 'enable' | 'disable'
  reason?: string
}

interface ToggleScheduleFormProps {
  toggle: AutomationToggleResponse
  businessId: UUID
  onSuccess?: (schedule: any) => void
  onCancel?: () => void
  editingSchedule?: any
}

const COMMON_TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Anchorage',
  'Pacific/Honolulu',
  'Europe/London',
  'Europe/Paris',
  'Europe/Madrid',
  'Europe/Berlin',
  'Europe/Rome',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Hong_Kong',
  'Asia/Singapore',
  'Australia/Sydney',
  'America/Argentina/Buenos_Aires',
  'America/Sao_Paulo',
  'America/Mexico_City',
]

const RRULE_PRESETS = [
  { label: 'Diariamente', value: 'FREQ=DAILY' },
  { label: 'Cada lunes', value: 'FREQ=WEEKLY;BYDAY=MO' },
  { label: 'Cada martes', value: 'FREQ=WEEKLY;BYDAY=TU' },
  { label: 'Cada miércoles', value: 'FREQ=WEEKLY;BYDAY=WE' },
  { label: 'Cada jueves', value: 'FREQ=WEEKLY;BYDAY=TH' },
  { label: 'Cada viernes', value: 'FREQ=WEEKLY;BYDAY=FR' },
  { label: 'Lunes a viernes (laborales)', value: 'FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR' },
  { label: 'Fines de semana', value: 'FREQ=WEEKLY;BYDAY=SA,SU' },
  { label: 'Cada 2 días', value: 'FREQ=DAILY;INTERVAL=2' },
  { label: 'Cada semana', value: 'FREQ=WEEKLY' },
  { label: 'Cada mes', value: 'FREQ=MONTHLY' },
]

export const ToggleScheduleForm = ({
  toggle,
  businessId,
  onSuccess,
  onCancel,
  editingSchedule,
}: ToggleScheduleFormProps) => {
  const [formData, setFormData] = useState<ToggleScheduleFormData>({
    start_time: editingSchedule?.start_time?.slice(0, 16) || new Date().toISOString().slice(0, 16),
    timezone: editingSchedule?.timezone || 'UTC',
    recurring: editingSchedule?.recurring || false,
    recurrence_rule: editingSchedule?.recurrence_rule || '',
    action: editingSchedule?.action || 'enable',
    reason: editingSchedule?.reason || '',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRrulePresets, setShowRrulePresets] = useState(false)

  const handleChange = (field: keyof ToggleScheduleFormData, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
    setError(null)
  }

  const applyRrulePreset = (preset: string) => {
    handleChange('recurrence_rule', preset)
    setShowRrulePresets(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const payload = {
        toggle_id: toggle.id,
        start_time: new Date(formData.start_time).toISOString(),
        timezone: formData.timezone,
        recurring: formData.recurring,
        recurrence_rule: formData.recurring ? formData.recurrence_rule : null,
        action: formData.action,
        reason: formData.reason || null,
      }

      const method = editingSchedule ? 'PATCH' : 'POST'
      const url = editingSchedule
        ? `/api/v1/automations/schedule/${editingSchedule.id}`
        : `/api/v1/automations/toggles/${toggle.id}/schedule`

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Error al guardar schedule')
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
          {editingSchedule ? 'Editar' : 'Programar'} {toggle.display_name}
        </h3>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3">
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Start Time */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Fecha y Hora
        </label>
        <input
          type="datetime-local"
          value={formData.start_time}
          onChange={(e) => handleChange('start_time', e.target.value)}
          required
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
        />
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Hora en tu zona horaria seleccionada
        </p>
      </div>

      {/* Timezone */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Zona Horaria
        </label>
        <select
          value={formData.timezone}
          onChange={(e) => handleChange('timezone', e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
        >
          {COMMON_TIMEZONES.map((tz) => (
            <option key={tz} value={tz}>
              {tz}
            </option>
          ))}
        </select>
      </div>

      {/* Action */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Acción
        </label>
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              name="action"
              value="enable"
              checked={formData.action === 'enable'}
              onChange={(e) => handleChange('action', e.target.value)}
              className="mr-2"
            />
            <span className="text-sm text-slate-700 dark:text-slate-300">Habilitar</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="action"
              value="disable"
              checked={formData.action === 'disable'}
              onChange={(e) => handleChange('action', e.target.value)}
              className="mr-2"
            />
            <span className="text-sm text-slate-700 dark:text-slate-300">Deshabilitar</span>
          </label>
        </div>
      </div>

      {/* Recurring */}
      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.recurring}
            onChange={(e) => handleChange('recurring', e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <span className="ml-2 text-sm font-medium text-slate-700 dark:text-slate-300">
            Es recurrente
          </span>
        </label>
      </div>

      {/* Recurrence Rule */}
      {formData.recurring && (
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Regla de Recurrencia (RFC 5545 RRULE)
          </label>
          <textarea
            value={formData.recurrence_rule}
            onChange={(e) => handleChange('recurrence_rule', e.target.value)}
            placeholder="Ej: FREQ=DAILY o FREQ=WEEKLY;BYDAY=MO,WE,FR"
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm font-mono"
            rows={2}
          />
          <button
            type="button"
            onClick={() => setShowRrulePresets(!showRrulePresets)}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-2"
          >
            {showRrulePresets ? 'Ocultar' : 'Mostrar'} plantillas predefinidas
          </button>

          {showRrulePresets && (
            <div className="mt-3 space-y-2 p-3 bg-slate-50 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700">
              {RRULE_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => applyRrulePreset(preset.value)}
                  className="w-full text-left px-3 py-2 rounded text-sm hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                >
                  {preset.label}
                  <span className="block text-xs text-slate-500 dark:text-slate-400 font-mono">
                    {preset.value}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reason */}
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Razón (opcional)
        </label>
        <textarea
          value={formData.reason}
          onChange={(e) => handleChange('reason', e.target.value)}
          placeholder="¿Por qué programas este cambio?"
          className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm"
          rows={2}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-end">
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
          {loading ? 'Guardando...' : editingSchedule ? 'Actualizar' : 'Programar'}
        </button>
      </div>
    </form>
  )
}
