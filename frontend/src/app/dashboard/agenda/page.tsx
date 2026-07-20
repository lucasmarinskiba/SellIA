'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { businessApi } from '@/lib/business'
import { ordersApi, Order } from '@/lib/orders'
import { servicesApi, Appointment, MODALITY_LABELS, SOLUTION_TYPE_LABELS, APPOINTMENT_STATUS_LABELS } from '@/lib/services'
import Button from '@/components/ui/Button'
import {
  Calendar, Clock, MapPin, Video, Phone, Mail, User, Check, X, Loader2,
  AlertCircle, RefreshCw, Send, MessageSquare, Star, ChevronLeft, ChevronRight,
  Plus, Trash2, ArrowRight, Bell
} from 'lucide-react'

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-50 text-amber-600 border-amber-200',
  confirmed: 'bg-green-50 text-green-600 border-green-200',
  completed: 'bg-blue-50 text-blue-600 border-blue-200',
  cancelled: 'bg-red-50 text-red-600 border-red-200',
  no_show: 'bg-gray-100 text-gray-500 border-gray-200',
}

export default function AgendaPage() {
  const { user } = useAuth()
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('')
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'day'>('list')
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)

  // Create form
  const [orders, setOrders] = useState<Order[]>([])
  const [createForm, setCreateForm] = useState<any>({
    order_id: '',
    client_name: '',
    client_email: '',
    client_phone: '',
    start_time: '',
    end_time: '',
    modality: 'remote',
    service_name: '',
    meeting_url: '',
    location_address: { street: '', city: '', state: '' },
    preparation_notes: '',
  })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    businessApi.list().then(data => {
      setBusinesses(data)
      if (data.length > 0) setSelectedBusinessId(data[0].id)
    }).catch(() => setError('No se pudieron cargar los negocios'))
  }, [])

  useEffect(() => {
    if (!selectedBusinessId) return
    loadAppointments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId, selectedDate, viewMode])

  const loadAppointments = async () => {
    setLoading(true)
    setError(null)
    try {
      const fromDate = new Date(selectedDate)
      fromDate.setHours(0, 0, 0, 0)
      const toDate = new Date(selectedDate)
      toDate.setHours(23, 59, 59, 999)
      if (viewMode === 'day') {
        toDate.setDate(toDate.getDate() + 1)
      } else {
        toDate.setDate(toDate.getDate() + 30)
      }

      const resp = await servicesApi.getAppointments(selectedBusinessId, {
        from_date: fromDate.toISOString(),
        to_date: toDate.toISOString(),
        limit: 200,
      })
      setAppointments(resp.items)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar citas')
    } finally {
      setLoading(false)
    }
  }

  const openCreateModal = async () => {
    setShowCreateModal(true)
    try {
      const resp = await ordersApi.getOrders(selectedBusinessId)
      setOrders(resp.filter((o: Order) => ['paid', 'pending'].includes(o.status)))
    } catch (e) { /* ignore */ }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setError(null)
    try {
      await servicesApi.createAppointment({
        ...createForm,
        start_time: new Date(createForm.start_time).toISOString(),
        end_time: new Date(createForm.end_time).toISOString(),
      })
      setShowCreateModal(false)
      loadAppointments()
      setCreateForm({
        order_id: '', client_name: '', client_email: '', client_phone: '',
        start_time: '', end_time: '', modality: 'remote', service_name: '',
        meeting_url: '', location_address: { street: '', city: '', state: '' },
        preparation_notes: '',
      })
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al crear cita')
    } finally {
      setCreating(false)
    }
  }

  const handleAction = async (action: string, appt: Appointment) => {
    try {
      let res: any
      switch (action) {
        case 'confirm': res = await servicesApi.confirmAppointment(appt.id); break
        case 'complete': res = await servicesApi.completeAppointment(appt.id); break
        case 'cancel': res = await servicesApi.cancelAppointment(appt.id); break
        case 'no_show': res = await servicesApi.markNoShow(appt.id); break
        case 'reminder': res = await servicesApi.sendReminder(appt.id); break
        case 'confirmation': res = await servicesApi.requestConfirmation(appt.id); break
        case 'feedback': res = await servicesApi.requestFeedback(appt.id); break
      }
      if (res?.success) {
        loadAppointments()
        if (selectedAppointment?.id === appt.id) {
          setSelectedAppointment({ ...selectedAppointment, status: res.appointment?.status || selectedAppointment.status })
        }
      }
      alert(res?.message || 'Acción completada')
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    }
  }

  const getDayAppointments = () => {
    const dateStr = selectedDate
    return appointments.filter(a => a.start_time.startsWith(dateStr)).sort((a, b) =>
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    )
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-brand-night flex items-center gap-2">
            <Calendar className="w-7 h-7 text-brand-orange" />
            Agenda
          </h1>
          <p className="text-slate-500 mt-1">
            Gestiona citas, sesiones y entregas de servicios.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setViewMode(viewMode === 'list' ? 'day' : 'list')}>
            {viewMode === 'list' ? 'Vista día' : 'Vista lista'}
          </Button>
          <Button onClick={openCreateModal} leftIcon={<Plus className="w-4 h-4" />}>
            Nueva Cita
          </Button>
        </div>
      </div>

      {/* Business selector */}
      {businesses.length > 0 && (
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">Negocio:</span>
          <select
            value={selectedBusinessId}
            onChange={e => setSelectedBusinessId(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          >
            {businesses.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Date picker */}
      <div className="flex items-center gap-3">
        <button onClick={() => {
          const d = new Date(selectedDate)
          d.setDate(d.getDate() - 1)
          setSelectedDate(d.toISOString().split('T')[0])
        }} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400">
          <ChevronLeft className="w-5 h-5" />
        </button>
        <input
          type="date"
          value={selectedDate}
          onChange={e => setSelectedDate(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
        />
        <button onClick={() => {
          const d = new Date(selectedDate)
          d.setDate(d.getDate() + 1)
          setSelectedDate(d.toISOString().split('T')[0])
        }} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400">
          <ChevronRight className="w-5 h-5" />
        </button>
        <Button variant="secondary" size="sm" onClick={loadAppointments} leftIcon={<RefreshCw className="w-3 h-3" />}>
          Actualizar
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-50 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {['pending', 'confirmed', 'completed', 'cancelled', 'no_show'].map(st => {
          const count = appointments.filter(a => a.status === st).length
          return (
            <div key={st} className="p-4 rounded-xl border border-slate-200 bg-white">
              <p className="text-2xl font-bold text-brand-night">{count}</p>
              <p className="text-xs text-slate-500">{APPOINTMENT_STATUS_LABELS[st]}</p>
            </div>
          )
        })}
      </div>

      {/* Appointments */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : viewMode === 'day' ? (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-slate-100">
            <h2 className="font-semibold text-brand-night">
              {new Date(selectedDate).toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })}
            </h2>
          </div>
          <div className="divide-y divide-slate-100">
            {getDayAppointments().length === 0 ? (
              <div className="text-center py-16 text-slate-400">
                <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No hay citas para este día.</p>
              </div>
            ) : (
              getDayAppointments().map(appt => (
                <AppointmentCard
                  key={appt.id}
                  appt={appt}
                  onAction={handleAction}
                  onSelect={() => { setSelectedAppointment(appt); setShowDetailModal(true) }}
                />
              ))
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Hora</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Cliente</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Servicio</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Estado</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {appointments.sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()).map(appt => (
                <tr key={appt.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-brand-night">
                      {new Date(appt.start_time).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div className="text-xs text-slate-400">
                      {new Date(appt.start_time).toLocaleDateString('es-AR')}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-700">{appt.client_name || '—'}</div>
                    <div className="text-xs text-slate-400">{appt.client_phone || appt.client_email || ''}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-slate-700">{appt.service_name || '—'}</div>
                    <div className="text-xs text-slate-400">
                      {appt.modality ? (MODALITY_LABELS[appt.modality] || appt.modality) : ''}
                      {appt.solution_type ? ` · ${SOLUTION_TYPE_LABELS[appt.solution_type] || appt.solution_type}` : ''}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[appt.status] || 'bg-slate-100 text-slate-600'}`}>
                      {APPOINTMENT_STATUS_LABELS[appt.status] || appt.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {appt.status === 'pending' && (
                        <button onClick={() => handleAction('confirm', appt)} className="p-2 rounded-lg hover:bg-green-50 text-slate-400 hover:text-green-600" title="Confirmar">
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      {appt.status === 'confirmed' && (
                        <button onClick={() => handleAction('complete', appt)} className="p-2 rounded-lg hover:bg-blue-50 text-slate-400 hover:text-blue-600" title="Completar">
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => handleAction('reminder', appt)} className="p-2 rounded-lg hover:bg-amber-50 text-slate-400 hover:text-amber-600" title="Enviar recordatorio">
                        <Bell className="w-4 h-4" />
                      </button>
                      <button onClick={() => { setSelectedAppointment(appt); setShowDetailModal(true) }} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-brand-orange" title="Ver detalle">
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {appointments.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-16 text-slate-400">
                    <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay citas programadas.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h2 className="text-xl font-bold text-brand-night">Nueva Cita</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Orden (opcional)</label>
                <select
                  value={createForm.order_id}
                  onChange={e => {
                    const order = orders.find(o => o.id === e.target.value)
                    setCreateForm({
                      ...createForm,
                      order_id: e.target.value,
                      client_name: order?.customer_name || '',
                      client_email: order?.customer_email || '',
                      client_phone: order?.customer_phone || '',
                    })
                  }}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  <option value="">Sin orden vinculada</option>
                  {orders.map(o => (
                    <option key={o.id} value={o.id}>#{o.order_number} — {o.customer_name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Cliente</label>
                  <input
                    type="text"
                    value={createForm.client_name}
                    onChange={e => setCreateForm({ ...createForm, client_name: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Teléfono</label>
                  <input
                    type="tel"
                    value={createForm.client_phone}
                    onChange={e => setCreateForm({ ...createForm, client_phone: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nombre del servicio</label>
                <input
                  type="text"
                  value={createForm.service_name}
                  onChange={e => setCreateForm({ ...createForm, service_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                  placeholder="Ej: Consulta psicológica"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Inicio</label>
                  <input
                    type="datetime-local"
                    value={createForm.start_time}
                    onChange={e => setCreateForm({ ...createForm, start_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Fin</label>
                  <input
                    type="datetime-local"
                    value={createForm.end_time}
                    onChange={e => setCreateForm({ ...createForm, end_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Modalidad</label>
                <select
                  value={createForm.modality}
                  onChange={e => setCreateForm({ ...createForm, modality: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                >
                  {Object.entries(MODALITY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              {createForm.modality === 'remote' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Link de reunión</label>
                  <input
                    type="url"
                    value={createForm.meeting_url}
                    onChange={e => setCreateForm({ ...createForm, meeting_url: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                    placeholder="https://meet.google.com/..."
                  />
                </div>
              )}

              {['client_home', 'client_office', 'on_site'].includes(createForm.modality) && (
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700 mb-1">Dirección</label>
                  <input
                    type="text"
                    value={createForm.location_address.street}
                    onChange={e => setCreateForm({ ...createForm, location_address: { ...createForm.location_address, street: e.target.value } })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
                    placeholder="Calle y número"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      value={createForm.location_address.city}
                      onChange={e => setCreateForm({ ...createForm, location_address: { ...createForm.location_address, city: e.target.value } })}
                      className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                      placeholder="Ciudad"
                    />
                    <input
                      type="text"
                      value={createForm.location_address.state}
                      onChange={e => setCreateForm({ ...createForm, location_address: { ...createForm.location_address, state: e.target.value } })}
                      className="px-3 py-2 rounded-lg border border-slate-200 text-sm"
                      placeholder="Provincia"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800">Cancelar</button>
                <Button type="submit" disabled={creating} leftIcon={creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}>
                  {creating ? 'Creando...' : 'Crear Cita'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedAppointment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h2 className="text-xl font-bold text-brand-night">Detalle de Cita</h2>
              <button onClick={() => setShowDetailModal(false)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[selectedAppointment.status] || ''}`}>
                  {APPOINTMENT_STATUS_LABELS[selectedAppointment.status] || selectedAppointment.status}
                </span>
                <span className="text-sm text-slate-500">
                  {new Date(selectedAppointment.start_time).toLocaleString('es-AR')}
                </span>
              </div>

              <div>
                <p className="text-sm text-slate-500">Cliente</p>
                <p className="font-medium text-brand-night">{selectedAppointment.client_name || '—'}</p>
                {selectedAppointment.client_phone && <p className="text-sm text-slate-600">{selectedAppointment.client_phone}</p>}
                {selectedAppointment.client_email && <p className="text-sm text-slate-600">{selectedAppointment.client_email}</p>}
              </div>

              <div>
                <p className="text-sm text-slate-500">Servicio</p>
                <p className="font-medium text-brand-night">{selectedAppointment.service_name || '—'}</p>
                <p className="text-xs text-slate-400">
                  {selectedAppointment.modality ? (MODALITY_LABELS[selectedAppointment.modality] || selectedAppointment.modality) : ''}
                  {selectedAppointment.solution_type ? ` · ${SOLUTION_TYPE_LABELS[selectedAppointment.solution_type] || selectedAppointment.solution_type}` : ''}
                </p>
              </div>

              {selectedAppointment.meeting_url && (
                <a href={selectedAppointment.meeting_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-brand-orange text-sm font-medium hover:underline">
                  <Video className="w-4 h-4" />
                  Link de reunión
                </a>
              )}

              {selectedAppointment.location_address?.street && (
                <div className="flex items-start gap-2 text-sm text-slate-600">
                  <MapPin className="w-4 h-4 mt-0.5 text-slate-400" />
                  <span>{selectedAppointment.location_address.street}, {selectedAppointment.location_address.city}</span>
                </div>
              )}

              {selectedAppointment.provider_notes && (
                <div className="p-3 rounded-lg bg-slate-50 text-sm">
                  <p className="font-medium text-slate-700 mb-1">Notas del prestador</p>
                  <p className="text-slate-600">{selectedAppointment.provider_notes}</p>
                </div>
              )}

              <div className="flex flex-wrap gap-2 pt-2">
                {selectedAppointment.status === 'pending' && (
                  <Button size="sm" onClick={() => handleAction('confirm', selectedAppointment)} leftIcon={<Check className="w-3 h-3" />}>Confirmar</Button>
                )}
                {selectedAppointment.status === 'confirmed' && (
                  <Button size="sm" onClick={() => handleAction('complete', selectedAppointment)} leftIcon={<Check className="w-3 h-3" />}>Completar</Button>
                )}
                <Button size="sm" variant="secondary" onClick={() => handleAction('reminder', selectedAppointment)} leftIcon={<Bell className="w-3 h-3" />}>Recordatorio</Button>
                <Button size="sm" variant="secondary" onClick={() => handleAction('confirmation', selectedAppointment)} leftIcon={<Send className="w-3 h-3" />}>Pedir confirmación</Button>
                {selectedAppointment.status === 'completed' && (
                  <Button size="sm" variant="secondary" onClick={() => handleAction('feedback', selectedAppointment)} leftIcon={<Star className="w-3 h-3" />}>Pedir feedback</Button>
                )}
                {(selectedAppointment.status === 'pending' || selectedAppointment.status === 'confirmed') && (
                  <Button size="sm" variant="secondary" onClick={() => handleAction('cancel', selectedAppointment)} leftIcon={<X className="w-3 h-3" />}>Cancelar</Button>
                )}
                <Button size="sm" variant="secondary" onClick={() => handleAction('no_show', selectedAppointment)} leftIcon={<AlertCircle className="w-3 h-3" />}>No asistió</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ============================================================
   APPOINTMENT CARD (Day view)
   ============================================================ */

function AppointmentCard({ appt, onAction, onSelect }: {
  appt: Appointment
  onAction: (action: string, appt: Appointment) => void
  onSelect: () => void
}) {
  const start = new Date(appt.start_time)
  const end = new Date(appt.end_time)

  return (
    <div className="p-4 hover:bg-slate-50/50 transition-colors">
      <div className="flex items-start gap-4">
        <div className="flex flex-col items-center min-w-[60px]">
          <span className="text-lg font-bold text-brand-night">{start.getHours().toString().padStart(2, '0')}:{start.getMinutes().toString().padStart(2, '0')}</span>
          <span className="text-xs text-slate-400">{end.getHours().toString().padStart(2, '0')}:{end.getMinutes().toString().padStart(2, '0')}</span>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${STATUS_COLORS[appt.status] || ''}`}>
              {APPOINTMENT_STATUS_LABELS[appt.status] || appt.status}
            </span>
            <span className="text-xs text-slate-400">
              {appt.modality ? (MODALITY_LABELS[appt.modality] || appt.modality) : ''}
            </span>
          </div>
          <h3 className="font-semibold text-brand-night">{appt.service_name || 'Cita'}</h3>
          <p className="text-sm text-slate-500">{appt.client_name || 'Sin cliente'}</p>
          {appt.meeting_url && (
            <a href={appt.meeting_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-brand-orange hover:underline mt-1">
              <Video className="w-3 h-3" /> Link de reunión
            </a>
          )}
        </div>
        <div className="flex items-center gap-1">
          {appt.status === 'pending' && (
            <button onClick={() => onAction('confirm', appt)} className="p-2 rounded-lg hover:bg-green-50 text-slate-400 hover:text-green-600" title="Confirmar">
              <Check className="w-4 h-4" />
            </button>
          )}
          <button onClick={onSelect} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-brand-orange">
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
