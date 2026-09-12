'use client'

import { useEffect, useState } from 'react'
import { UUID } from 'crypto'
import { AutomationToggleResponse } from '@/lib/api/toggles'
import { ToggleScheduleForm } from './ToggleScheduleForm'
import { Clock, Trash2, Edit2 } from 'lucide-react'

interface ToggleSchedule {
  id: UUID
  business_id: UUID
  toggle_id: UUID
  start_time: string
  timezone: string
  recurring: boolean
  recurrence_rule?: string
  action: 'enable' | 'disable'
  reason?: string
  is_active: boolean
  last_executed_at?: string
  next_execution_at?: string
  execution_count: number
  failed_count: number
  last_error?: string
  created_at: string
  updated_at: string
}

interface ToggleScheduleListProps {
  toggle: AutomationToggleResponse
  businessId: UUID
}

export const ToggleScheduleList = ({ toggle, businessId }: ToggleScheduleListProps) => {
  const [schedules, setSchedules] = useState<ToggleSchedule[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<ToggleSchedule | null>(null)
  const [deletingId, setDeletingId] = useState<UUID | null>(null)

  useEffect(() => {
    loadSchedules()
  }, [toggle.id])

  const loadSchedules = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/automations/toggles/${toggle.id}/schedules`)
      if (res.ok) {
        const data = await res.json()
        setSchedules(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('Error loading schedules:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (scheduleId: UUID) => {
    if (!confirm('¿Eliminar esta programación?')) return

    setDeletingId(scheduleId)
    try {
      const res = await fetch(`/api/v1/automations/schedule/${scheduleId}`, {
        method: 'DELETE',
      })
      if (res.ok) {
        await loadSchedules()
      }
    } catch (err) {
      console.error('Error deleting schedule:', err)
    } finally {
      setDeletingId(null)
    }
  }

  const handleFormSuccess = async () => {
    await loadSchedules()
    setShowForm(false)
    setEditingSchedule(null)
  }

  if (loading) {
    return <div className="text-center py-4 text-slate-500">Cargando programaciones...</div>
  }

  if (showForm) {
    return (
      <ToggleScheduleForm
        toggle={toggle}
        businessId={businessId}
        editingSchedule={editingSchedule}
        onSuccess={handleFormSuccess}
        onCancel={() => {
          setShowForm(false)
          setEditingSchedule(null)
        }}
      />
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 dark:text-white">Programaciones</h3>
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1 rounded text-sm bg-blue-600 text-white hover:bg-blue-700"
        >
          + Programar
        </button>
      </div>

      {schedules.length === 0 ? (
        <div className="text-center py-8 bg-slate-50 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700">
          <Clock size={24} className="mx-auto mb-2 text-slate-400" />
          <p className="text-sm text-slate-600 dark:text-slate-400">Sin programaciones</p>
        </div>
      ) : (
        <div className="space-y-3">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className="bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        schedule.action === 'enable'
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}
                    >
                      {schedule.action === 'enable' ? 'Habilitar' : 'Deshabilitar'}
                    </span>
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        schedule.is_active
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-400'
                      }`}
                    >
                      {schedule.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>

                  <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                    <p>
                      <strong>Inicio:</strong>{' '}
                      {new Date(schedule.start_time).toLocaleString('es-AR', {
                        timeZone: schedule.timezone,
                      })}{' '}
                      ({schedule.timezone})
                    </p>

                    {schedule.recurring && (
                      <p>
                        <strong>Recurrencia:</strong> {schedule.recurrence_rule}
                      </p>
                    )}

                    {schedule.next_execution_at && (
                      <p>
                        <strong>Próxima ejecución:</strong>{' '}
                        {new Date(schedule.next_execution_at).toLocaleString('es-AR')}
                      </p>
                    )}

                    {schedule.execution_count > 0 && (
                      <p>
                        <strong>Ejecuciones:</strong> {schedule.execution_count}{' '}
                        {schedule.failed_count > 0 && (
                          <span className="text-red-600 dark:text-red-400">
                            ({schedule.failed_count} fallidas)
                          </span>
                        )}
                      </p>
                    )}

                    {schedule.reason && (
                      <p>
                        <strong>Razón:</strong> {schedule.reason}
                      </p>
                    )}

                    {schedule.last_error && (
                      <p className="text-red-600 dark:text-red-400">
                        <strong>Último error:</strong> {schedule.last_error}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => {
                      setEditingSchedule(schedule)
                      setShowForm(true)
                    }}
                    className="p-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400"
                    title="Editar"
                  >
                    <Edit2 size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(schedule.id)}
                    disabled={deletingId === schedule.id}
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
