'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { businessApi } from '@/lib/business'
import { ordersApi, Order } from '@/lib/orders'
import { shipmentsApi, Shipment, ShipmentConfig, CarrierInfo, ShipmentDetail } from '@/lib/shipments'
import Button from '@/components/ui/Button'
import {
  Truck, Package, MapPin, Search, Loader2, AlertCircle, X, Plus, Trash2, Edit3,
  RefreshCw, Send, Check, Clock, ChevronDown, ChevronUp, ExternalLink, BarChart3,
  Settings, FlaskConical, ArrowRight
} from 'lucide-react'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  label_created: 'Etiqueta creada',
  picked_up: 'Retirado',
  in_transit: 'En tránsito',
  out_for_delivery: 'En reparto',
  delivered: 'Entregado',
  exception: 'Excepción',
  returned: 'Devuelto',
  cancelled: 'Cancelado',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-slate-100 text-slate-600',
  label_created: 'bg-blue-50 text-blue-600',
  picked_up: 'bg-indigo-50 text-indigo-600',
  in_transit: 'bg-amber-50 text-amber-600',
  out_for_delivery: 'bg-orange-50 text-orange-600',
  delivered: 'bg-green-50 text-green-600',
  exception: 'bg-red-50 text-red-600',
  returned: 'bg-purple-50 text-purple-600',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function EnviosPage() {
  const { user } = useAuth()
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('')
  const [shipments, setShipments] = useState<Shipment[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [selectedShipment, setSelectedShipment] = useState<ShipmentDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Configs
  const [configs, setConfigs] = useState<ShipmentConfig[]>([])
  const [carriers, setCarriers] = useState<CarrierInfo[]>([])

  // Create form
  const [orders, setOrders] = useState<Order[]>([])
  const [createForm, setCreateForm] = useState<any>({
    order_id: '',
    config_id: '',
    carrier: 'local',
    service_type: 'standard',
    package: { weight_kg: 1, items: [] },
    auto_generate_label: false,
    notify_customer: true,
    notification_channel: 'whatsapp',
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
    loadShipments()
    loadConfigs()
    shipmentsApi.getCarriers().then(setCarriers).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBusinessId, statusFilter])

  const loadShipments = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await shipmentsApi.getShipments(selectedBusinessId, {
        status: statusFilter || undefined,
        search: search || undefined,
        limit: 50,
      })
      setShipments(resp.items)
      setTotal(resp.total)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al cargar envíos')
    } finally {
      setLoading(false)
    }
  }

  const loadConfigs = async () => {
    try {
      const c = await shipmentsApi.getConfigs(selectedBusinessId)
      setConfigs(c)
    } catch (e) { /* ignore */ }
  }

  const openCreateModal = async () => {
    setShowCreateModal(true)
    setCreateForm({
      order_id: '',
      config_id: configs[0]?.id || '',
      carrier: configs[0]?.carrier || 'local',
      service_type: 'standard',
      package: { weight_kg: 1, items: [] },
      auto_generate_label: true,
      notify_customer: true,
      notification_channel: 'whatsapp',
    })
    try {
      const resp = await ordersApi.getOrders(selectedBusinessId)
      // Filter paid orders without shipment or any order
      setOrders(resp.filter((o: Order) => ['paid', 'pending', 'shipped'].includes(o.status)))
    } catch (e) { /* ignore */ }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setError(null)
    try {
      await shipmentsApi.createShipment(createForm)
      setShowCreateModal(false)
      loadShipments()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al crear envío')
    } finally {
      setCreating(false)
    }
  }

  const openDetail = async (shipment: Shipment) => {
    setShowDetailModal(true)
    setDetailLoading(true)
    try {
      const detail = await shipmentsApi.getShipment(shipment.id)
      setSelectedShipment(detail)
    } catch (e) {
      setError('Error al cargar detalle')
    } finally {
      setDetailLoading(false)
    }
  }

  const handleRefresh = async (id: string) => {
    try {
      const res = await shipmentsApi.refreshTracking(id)
      if (res.success) {
        loadShipments()
        if (selectedShipment?.id === id) {
          openDetail(selectedShipment)
        }
      }
      alert(res.message)
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    }
  }

  const handleNotify = async (id: string) => {
    try {
      const res = await shipmentsApi.notifyCustomer(id)
      alert(res.message)
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('¿Cancelar este envío?')) return
    try {
      await shipmentsApi.deleteShipment(id)
      loadShipments()
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    }
  }

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-brand-night flex items-center gap-2">
            <Truck className="w-7 h-7 text-brand-orange" />
            Envíos
          </h1>
          <p className="text-slate-500 mt-1">
            Gestiona envíos regionales, nacionales e internacionales. Integrado con Andreani, Correo Argentino, DHL, FedEx, UPS y más.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={() => setShowConfigModal(true)} leftIcon={<Settings className="w-4 h-4" />}>
            Carriers
          </Button>
          <Button onClick={openCreateModal} leftIcon={<Plus className="w-4 h-4" />}>
            Nuevo Envío
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
        {['pending', 'in_transit', 'out_for_delivery', 'delivered', 'exception'].map(st => {
          const count = shipments.filter(s => s.status === st).length
          return (
            <button
              key={st}
              onClick={() => setStatusFilter(statusFilter === st ? '' : st)}
              className={`p-4 rounded-xl border text-left transition-all ${statusFilter === st ? 'border-brand-orange bg-brand-orange/5' : 'border-slate-200 bg-white hover:shadow-sm'}`}
            >
              <p className="text-2xl font-bold text-brand-night">{count}</p>
              <p className="text-xs text-slate-500">{STATUS_LABELS[st]}</p>
            </button>
          )
        })}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar por tracking o notas..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && loadShipments()}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          />
        </div>
        <Button variant="secondary" onClick={loadShipments} leftIcon={<RefreshCw className="w-4 h-4" />}>
          Actualizar
        </Button>
      </div>

      {/* Shipments Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Tracking</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Carrier</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Estado</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Destino</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Costo</th>
                <th className="text-right px-4 py-3 font-medium text-slate-600">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map(s => (
                <tr key={s.id} className="border-b border-slate-100 hover:bg-slate-50/50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-brand-night">{s.tracking_number || '—'}</div>
                    <div className="text-xs text-slate-400">{new Date(s.created_at).toLocaleDateString()}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="capitalize text-slate-700">{s.carrier.replace('_', ' ')}</span>
                    <div className="text-xs text-slate-400">{s.service_type}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[s.status] || 'bg-slate-100 text-slate-600'}`}>
                      {STATUS_LABELS[s.status] || s.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {s.to_address?.city || '—'}, {s.to_address?.state || ''}
                  </td>
                  <td className="px-4 py-3">
                    {s.shipping_cost ? `$${s.shipping_cost}` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {s.tracking_number && (
                        <button onClick={() => handleRefresh(s.id)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-brand-orange" title="Actualizar tracking">
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => handleNotify(s.id)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-blue-500" title="Notificar cliente">
                        <Send className="w-4 h-4" />
                      </button>
                      <button onClick={() => openDetail(s)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-brand-orange" title="Ver detalle">
                        <ArrowRight className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(s.id)} className="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500" title="Cancelar">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {shipments.length === 0 && (
                <tr>
                  <td colSpan={6} className="text-center py-16 text-slate-400">
                    <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p className="text-sm">No hay envíos registrados.</p>
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
              <h2 className="text-xl font-bold text-brand-night">Nuevo Envío</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Orden</label>
                <select
                  value={createForm.order_id}
                  onChange={e => setCreateForm({ ...createForm, order_id: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  required
                >
                  <option value="">Seleccionar orden...</option>
                  {orders.map(o => (
                    <option key={o.id} value={o.id}>#{o.order_number} — {o.customer_name} (${o.total_amount})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Carrier</label>
                  <select
                    value={createForm.carrier}
                    onChange={e => setCreateForm({ ...createForm, carrier: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  >
                    {carriers.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Servicio</label>
                  <select
                    value={createForm.service_type}
                    onChange={e => setCreateForm({ ...createForm, service_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  >
                    <option value="standard">Standard</option>
                    <option value="express">Express</option>
                    <option value="same_day">Same Day</option>
                    <option value="overnight">Overnight</option>
                    <option value="international">International</option>
                    <option value="economy">Economy</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Peso (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={createForm.package.weight_kg}
                  onChange={e => setCreateForm({ ...createForm, package: { ...createForm.package, weight_kg: parseFloat(e.target.value) || 0 } })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  required
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={createForm.auto_generate_label} onChange={e => setCreateForm({ ...createForm, auto_generate_label: e.target.checked })} className="rounded border-slate-300" />
                  Generar etiqueta
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input type="checkbox" checked={createForm.notify_customer} onChange={e => setCreateForm({ ...createForm, notify_customer: e.target.checked })} className="rounded border-slate-300" />
                  Notificar cliente
                </label>
              </div>

              {configs.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Configuración de carrier</label>
                  <select
                    value={createForm.config_id}
                    onChange={e => setCreateForm({ ...createForm, config_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                  >
                    <option value="">Sin config (modo demo)</option>
                    {configs.map(c => (
                      <option key={c.id} value={c.id}>{c.label || c.carrier} {c.is_test_mode ? '(test)' : ''}</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800">Cancelar</button>
                <Button type="submit" disabled={creating} leftIcon={creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}>
                  {creating ? 'Creando...' : 'Crear Envío'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedShipment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-slate-100">
              <h2 className="text-xl font-bold text-brand-night">Detalle del Envío</h2>
              <button onClick={() => setShowDetailModal(false)} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400"><X className="w-5 h-5" /></button>
            </div>
            {detailLoading ? (
              <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-orange" /></div>
            ) : (
              <div className="p-6 space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Tracking</p>
                    <p className="font-semibold text-brand-night">{selectedShipment.tracking_number || '—'}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[selectedShipment.status] || ''}`}>
                    {STATUS_LABELS[selectedShipment.status] || selectedShipment.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Carrier</p>
                    <p className="font-medium text-brand-night capitalize">{selectedShipment.carrier.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Servicio</p>
                    <p className="font-medium text-brand-night">{selectedShipment.service_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Costo</p>
                    <p className="font-medium text-brand-night">{selectedShipment.shipping_cost ? `$${selectedShipment.shipping_cost}` : '—'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Peso</p>
                    <p className="font-medium text-brand-night">{selectedShipment.package?.weight_kg} kg</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-slate-500 mb-1">Destino</p>
                  <div className="p-3 rounded-lg bg-slate-50 text-sm">
                    <p className="font-medium">{selectedShipment.to_address?.name}</p>
                    <p>{selectedShipment.to_address?.street}</p>
                    <p>{selectedShipment.to_address?.city}, {selectedShipment.to_address?.state} {selectedShipment.to_address?.zip}</p>
                    <p>{selectedShipment.to_address?.country}</p>
                  </div>
                </div>

                {selectedShipment.tracking_url && (
                  <a href={selectedShipment.tracking_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-brand-orange text-sm font-medium hover:underline">
                    <ExternalLink className="w-4 h-4" />
                    Ver tracking en {selectedShipment.carrier.replace('_', ' ')}
                  </a>
                )}

                {/* Tracking Timeline */}
                {selectedShipment.tracking_events && selectedShipment.tracking_events.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-slate-700 mb-3">Historial de Tracking</p>
                    <div className="space-y-3">
                      {selectedShipment.tracking_events.map((ev, i) => (
                        <div key={ev.id} className="flex gap-3">
                          <div className="flex flex-col items-center">
                            <div className={`w-2 h-2 rounded-full ${i === 0 ? 'bg-brand-orange' : 'bg-slate-300'}`} />
                            {i < selectedShipment.tracking_events.length - 1 && <div className="w-0.5 h-full bg-slate-200 mt-1" />}
                          </div>
                          <div className="pb-3">
                            <p className={`text-sm ${i === 0 ? 'font-medium text-brand-night' : 'text-slate-600'}`}>{ev.event_description}</p>
                            <p className="text-xs text-slate-400">{ev.location || ''} • {new Date(ev.event_at).toLocaleString()}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Config Modal */}
      {showConfigModal && (
        <ConfigModal
          businessId={selectedBusinessId}
          configs={configs}
          carriers={carriers}
          onClose={() => { setShowConfigModal(false); loadConfigs() }}
        />
      )}
    </div>
  )
}

/* ============================================================
   CONFIG MODAL
   ============================================================ */

function ConfigModal({ businessId, configs, carriers, onClose }: {
  businessId: string
  configs: ShipmentConfig[]
  carriers: CarrierInfo[]
  onClose: () => void
}) {
  const [form, setForm] = useState<any>({
    carrier: 'andreani',
    label: '',
    credentials: {},
    is_test_mode: true,
    is_active: true,
    default_service_type: 'standard',
  })
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await shipmentsApi.createConfig(businessId, form)
      setForm({ carrier: 'andreani', label: '', credentials: {}, is_test_mode: true, is_active: true, default_service_type: 'standard' })
      onClose()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async (configId: string) => {
    setTesting(configId)
    try {
      const res = await shipmentsApi.testConfig(configId)
      alert(res.message)
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error')
    } finally {
      setTesting(null)
    }
  }

  const selectedCarrier = carriers.find(c => c.id === form.carrier)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <h2 className="text-xl font-bold text-brand-night">Configurar Carriers</h2>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 text-slate-400"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 space-y-6">
          {error && <div className="p-3 rounded-lg bg-red-50 text-red-600 text-sm">{error}</div>}

          {/* Existing configs */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-slate-700">Conexiones existentes</h3>
            {configs.map(c => (
              <div key={c.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-200">
                <div>
                  <p className="font-medium text-brand-night">{c.label || c.carrier}</p>
                  <p className="text-xs text-slate-500">{c.is_test_mode ? 'Modo test' : 'Producción'} • {c.is_active ? 'Activo' : 'Inactivo'}</p>
                </div>
                <button onClick={() => handleTest(c.id)} disabled={testing === c.id} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 disabled:opacity-50">
                  {testing === c.id ? 'Probando...' : 'Probar'}
                </button>
              </div>
            ))}
            {configs.length === 0 && <p className="text-sm text-slate-400">No hay configuraciones. Agrega una abajo.</p>}
          </div>

          {/* Add form */}
          <form onSubmit={handleSubmit} className="space-y-4 p-4 rounded-xl border border-slate-200 bg-slate-50">
            <h3 className="text-sm font-semibold text-slate-700">Nueva conexión</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Carrier</label>
              <select
                value={form.carrier}
                onChange={e => setForm({ ...form, carrier: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              >
                {carriers.map(c => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nombre personalizado</label>
              <input
                type="text"
                value={form.label}
                onChange={e => setForm({ ...form, label: e.target.value })}
                placeholder="Ej: Mi Andreani"
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
              />
            </div>

            {/* Dynamic credential fields based on carrier */}
            {selectedCarrier?.id === 'andreani' && (
              <>
                <input type="text" placeholder="Usuario" value={form.credentials.username || ''} onChange={e => setForm({ ...form, credentials: { ...form.credentials, username: e.target.value } })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
                <input type="password" placeholder="Contraseña" value={form.credentials.password || ''} onChange={e => setForm({ ...form, credentials: { ...form.credentials, password: e.target.value } })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
                <input type="text" placeholder="Contrato" value={form.credentials.contrato || ''} onChange={e => setForm({ ...form, credentials: { ...form.credentials, contrato: e.target.value } })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
              </>
            )}
            {['dhl', 'fedex', 'ups'].includes(selectedCarrier?.id || '') && (
              <input type="text" placeholder="API Key" value={form.credentials.api_key || ''} onChange={e => setForm({ ...form, credentials: { ...form.credentials, api_key: e.target.value } })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
            )}
            {selectedCarrier?.id === 'correo_argentino' && (
              <input type="text" placeholder="API Key" value={form.credentials.api_key || ''} onChange={e => setForm({ ...form, credentials: { ...form.credentials, api_key: e.target.value } })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
            )}
            {selectedCarrier?.id === 'oca' && (
              <input type="text" placeholder="CUIT" value={form.credentials.cuit || ''} onChange={e => setForm({ ...form, credentials: { ...form.credentials, cuit: e.target.value } })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
            )}

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={form.is_test_mode} onChange={e => setForm({ ...form, is_test_mode: e.target.checked })} className="rounded border-slate-300" />
                Modo test
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={form.is_active} onChange={e => setForm({ ...form, is_active: e.target.checked })} className="rounded border-slate-300" />
                Activo
              </label>
            </div>

            <div className="flex items-center justify-end gap-2">
              <button type="button" onClick={() => setForm({ carrier: 'andreani', label: '', credentials: {}, is_test_mode: true, is_active: true, default_service_type: 'standard' })} className="px-3 py-2 text-sm text-slate-600">Limpiar</button>
              <Button type="submit" size="sm" disabled={saving} leftIcon={saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}>
                {saving ? 'Guardando...' : 'Agregar'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
