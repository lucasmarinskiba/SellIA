'use client'

import { ToggleAuditLogResponse } from '@/lib/api/toggles'
import { formatDistanceToNow } from 'date-fns'
import { es } from 'date-fns/locale'

interface AuditPanelProps {
  logs: ToggleAuditLogResponse[]
  onClose: () => void
}

export const AuditPanel = ({ logs, onClose }: AuditPanelProps) => {
  if (!logs.length) {
    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-2xl max-h-96 overflow-y-auto shadow-lg">
          <h2 className="text-lg font-bold mb-4 text-slate-900 dark:text-white">Historial</h2>
          <p className="text-slate-600 dark:text-slate-400">Sin cambios registrados</p>
          <button
            onClick={onClose}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Cerrar
          </button>
        </div>
      </div>
    )
  }

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'enabled':
        return <span className="px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100 text-xs font-semibold rounded">Habilitado</span>
      case 'disabled':
        return <span className="px-2 py-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100 text-xs font-semibold rounded">Deshabilitado</span>
      case 'limit_changed':
        return <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100 text-xs font-semibold rounded">Límite Cambiado</span>
      default:
        return <span className="px-2 py-1 bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-100 text-xs font-semibold rounded">{action}</span>
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto shadow-lg">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 p-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Historial de Cambios</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Últimos {logs.length} cambios
          </p>
        </div>

        {/* Logs List */}
        <div className="divide-y divide-slate-200 dark:divide-slate-700">
          {logs.map((log) => (
            <div key={log.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getActionBadge(log.action)}
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    {log.changed_by_email}
                  </span>
                </div>
                <span className="text-xs text-slate-500 dark:text-slate-500">
                  {formatDistanceToNow(new Date(log.created_at), {
                    addSuffix: true,
                    locale: es,
                  })}
                </span>
              </div>

              {/* Old/New Values */}
              {log.old_value && log.new_value && (
                <div className="mt-2 space-y-1 text-xs">
                  {Object.entries(log.new_value).map(([key, newVal]) => {
                    const oldVal = (log.old_value as Record<string, any>)[key]
                    if (oldVal === newVal) return null
                    return (
                      <div key={key} className="text-slate-600 dark:text-slate-400">
                        <span className="font-mono">
                          {key}: {oldVal} → {newVal}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Reason */}
              {log.reason && (
                <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 italic">
                  "{log.reason}"
                </p>
              )}

              {/* Impact */}
              {log.leads_affected && (
                <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
                  <strong>Impacto:</strong> {log.leads_affected} leads afectados
                  {log.estimated_impact_pct && ` (~${log.estimated_impact_pct}%)`}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 dark:border-slate-700 p-4">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
