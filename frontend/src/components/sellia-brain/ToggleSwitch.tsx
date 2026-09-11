'use client'

import { useState } from 'react'
import { AutomationToggleResponse } from '@/lib/api/toggles'

interface ToggleSwitchProps {
  toggle: AutomationToggleResponse
  loading?: boolean
  onToggle: (enabled: boolean, reason?: string) => Promise<void>
  onLimitChange?: (newLimit: number) => Promise<void>
  onShowAudit?: () => void
  onShowInfo?: () => void
}

export const ToggleSwitch = ({
  toggle,
  loading = false,
  onToggle,
  onLimitChange,
  onShowAudit,
  onShowInfo,
}: ToggleSwitchProps) => {
  const [isChanging, setIsChanging] = useState(false)
  const [showLimitForm, setShowLimitForm] = useState(false)
  const [newLimit, setNewLimit] = useState(toggle.monthly_limit || 0)
  const [reason, setReason] = useState('')

  const handleToggle = async () => {
    // Confirm dialog
    const action = toggle.is_enabled ? 'deshabilitar' : 'habilitar'
    const confirmed = window.confirm(
      `¿Estás seguro de que quieres ${action} "${toggle.display_name}"?`
    )
    if (!confirmed) return

    setIsChanging(true)
    try {
      await onToggle(!toggle.is_enabled, reason)
    } catch (err) {
      console.error('Error al cambiar toggle:', err)
    } finally {
      setIsChanging(false)
    }
  }

  const handleLimitUpdate = async () => {
    if (onLimitChange && newLimit !== toggle.monthly_limit) {
      try {
        await onLimitChange(newLimit)
        setShowLimitForm(false)
      } catch (err) {
        console.error('Error al actualizar límite:', err)
      }
    }
  }

  const usagePercent = toggle.monthly_limit
    ? Math.round((toggle.current_month_usage / toggle.monthly_limit) * 100)
    : 0

  const usageColor =
    usagePercent > 90 ? 'bg-red-500' : usagePercent > 70 ? 'bg-yellow-500' : 'bg-green-500'

  return (
    <div
      className={`
        relative flex items-start justify-between p-4 border rounded-lg hover:shadow-md transition-shadow
        ${toggle.is_enabled ? 'bg-white dark:bg-slate-800' : 'bg-slate-50 dark:bg-slate-900/50 opacity-60'}
      `}
    >
      {/* Warning Badge */}
      {usagePercent >= 90 && toggle.monthly_limit && (
        <div className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full text-white text-xs font-bold flex items-center justify-center shadow-lg" title={`${usagePercent}% del límite`}>
          !
        </div>
      )}

      {/* Left: Icon + Name + Description */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-2">
          <span className={`text-2xl flex-shrink-0 ${!toggle.is_enabled ? 'opacity-50' : ''}`}>
            {toggle.icon || '⚙️'}
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className={`font-semibold truncate ${!toggle.is_enabled ? 'text-slate-600 dark:text-slate-500 line-through' : 'text-slate-900 dark:text-white'}`}>
                {toggle.display_name}
              </h3>
              {!toggle.is_enabled && (
                <span className="text-xs px-2 py-0.5 bg-slate-300 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded">
                  Deshabilitado
                </span>
              )}
            </div>
            <p className={`text-sm line-clamp-2 ${!toggle.is_enabled ? 'text-slate-500 dark:text-slate-600' : 'text-slate-600 dark:text-slate-400'}`}>
              {toggle.description}
            </p>
          </div>
        </div>

        {/* Usage Bar */}
        {toggle.monthly_limit && (
          <div className="mt-3 space-y-1">
            <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400">
              <span>Uso mensual</span>
              <span className="font-mono">
                {toggle.current_month_usage} / {toggle.monthly_limit}
              </span>
            </div>
            <div className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${usageColor} transition-all`}
                style={{ width: `${Math.min(usagePercent, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Right: Buttons */}
      <div className="flex flex-col gap-2 ml-4 flex-shrink-0">
        {/* Toggle Button */}
        <button
          onClick={handleToggle}
          disabled={isChanging || loading}
          className={`
            relative inline-flex h-8 w-14 items-center rounded-full transition-colors
            ${toggle.is_enabled ? 'bg-green-500' : 'bg-slate-300'}
            ${isChanging || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-md'}
          `}
          title={toggle.is_enabled ? 'Desactivar' : 'Activar'}
        >
          <span
            className={`
              inline-block h-6 w-6 transform rounded-full bg-white shadow transition-transform
              ${toggle.is_enabled ? 'translate-x-7' : 'translate-x-1'}
            `}
          />
        </button>

        {/* Limit Button */}
        {toggle.monthly_limit && !showLimitForm && (
          <button
            onClick={() => setShowLimitForm(true)}
            className="px-2 py-1 text-xs font-medium border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Cambiar límite mensual"
          >
            Límite
          </button>
        )}

        {/* Info Button */}
        {onShowInfo && (
          <button
            onClick={onShowInfo}
            className="px-2 py-1 text-xs font-medium border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Ver información del feature"
          >
            ℹ️
          </button>
        )}

        {/* Audit Button */}
        <button
          onClick={onShowAudit}
          className="px-2 py-1 text-xs font-medium border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          title="Ver historial de cambios"
        >
          📋
        </button>
      </div>

      {/* Limit Form Modal */}
      {showLimitForm && (
        <div className="absolute z-50 right-4 top-full mt-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="text-xs font-semibold mb-2 text-slate-900 dark:text-white">
            Nuevo límite mensual
          </p>
          <input
            type="number"
            min="1"
            value={newLimit}
            onChange={(e) => setNewLimit(parseInt(e.target.value) || 0)}
            className="w-full px-2 py-1 border border-slate-300 dark:border-slate-600 rounded text-sm mb-2 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
            placeholder="Límite"
          />
          <div className="flex gap-2">
            <button
              onClick={handleLimitUpdate}
              className="flex-1 px-2 py-1 bg-blue-500 text-white text-xs font-medium rounded hover:bg-blue-600 transition-colors"
            >
              Guardar
            </button>
            <button
              onClick={() => setShowLimitForm(false)}
              className="flex-1 px-2 py-1 border border-slate-300 dark:border-slate-600 text-xs font-medium rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
