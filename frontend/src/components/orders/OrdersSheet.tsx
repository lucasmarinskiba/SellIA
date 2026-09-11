'use client'

/**
 * The orders spreadsheet.
 *
 * Sorting, filtering and paging all happen on the server, over every order the
 * filter matches — not over whatever page happens to be loaded. That matters:
 * a client-side sort of 50 visible rows out of 900 shows "the largest order" of
 * a page, which is not the largest order.
 *
 * Three things are deliberately visible rather than hidden: the per-currency
 * totals (never summed across currencies), the backend's own notes about what
 * it could not do, and the per-order reason when a bulk action skips a row.
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Columns3, Download,
  Filter, Info, Loader2, RotateCw, Search, X,
} from 'lucide-react'
import { logger } from '@/lib/logger'
import {
  ordersApi, type BulkStatusResult, type OrderRow, type OrdersTable, type OrdersTableParams,
} from '@/lib/orders'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  paid: 'Pagada',
  shipped: 'Enviada',
  delivered: 'Entregada',
  cancelled: 'Cancelada',
  refunded: 'Reembolsada',
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#F59E0B',
  paid: '#22C55E',
  shipped: '#3B82F6',
  delivered: '#00D4AA',
  cancelled: '#EF4444',
  refunded: '#64748B',
}

const PAYMENT_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  processing: 'Procesando',
  completed: 'Cobrado',
  failed: 'Fallido',
  refunded: 'Devuelto',
}

/** Columns shown before the seller touches anything. The rest are opt-in. */
const DEFAULT_COLUMNS = [
  'order_number', 'created_at', 'customer_name', 'items_label',
  'total_amount', 'status', 'payment_status', 'external_platform',
]

const NUMERIC_COLUMNS = new Set(['total_amount', 'items_count', 'units', 'age_days', 'hours_to_payment'])
const DATE_COLUMNS = new Set(['created_at', 'paid_at', 'shipped_at', 'delivered_at'])

const FACET_LABELS: Record<string, string> = {
  status: 'Estado',
  payment_status: 'Pago',
  external_platform: 'Plataforma',
  source_channel: 'Canal',
  currency: 'Moneda',
}

const FACET_PARAM: Record<string, keyof OrdersTableParams> = {
  status: 'status_in',
  payment_status: 'payment_status',
  external_platform: 'platform',
  source_channel: 'channel',
  currency: 'currency',
}

interface Props {
  businessId: string
}

const OrdersSheet = ({ businessId }: Props): React.JSX.Element => {
  const [data, setData] = useState<OrdersTable | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkResult, setBulkResult] = useState<BulkStatusResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [showColumns, setShowColumns] = useState(false)
  const [showFilters, setShowFilters] = useState(true)
  const [visible, setVisible] = useState<string[]>(DEFAULT_COLUMNS)
  const [facetFilters, setFacetFilters] = useState<Record<string, string[]>>({})
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [amountMin, setAmountMin] = useState('')
  const [amountMax, setAmountMax] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const firstLoad = useRef(true)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 350)
    return () => clearTimeout(timer)
  }, [search])

  const params = useMemo((): OrdersTableParams => {
    const built: OrdersTableParams = { sort_by: sortBy, sort_dir: sortDir, page, page_size: pageSize }
    if (debouncedSearch.trim()) built.search = debouncedSearch.trim()
    Object.entries(facetFilters).forEach(([facet, values]) => {
      if (values.length) {
        const key = FACET_PARAM[facet]
        if (key) (built as Record<string, unknown>)[key] = values.join(',')
      }
    })
    if (dateFrom) built.date_from = new Date(dateFrom).toISOString()
    if (dateTo) {
      // The seller means "through the end of that day", not 00:00 of it.
      const end = new Date(dateTo)
      end.setHours(23, 59, 59, 999)
      built.date_to = end.toISOString()
    }
    if (amountMin) built.amount_min = Number(amountMin)
    if (amountMax) built.amount_max = Number(amountMax)
    return built
  }, [debouncedSearch, facetFilters, dateFrom, dateTo, amountMin, amountMax, sortBy, sortDir, page, pageSize])

  const load = useCallback(async (): Promise<void> => {
    if (!businessId) return
    setLoading(true)
    setError(null)
    try {
      const result = await ordersApi.getTable(businessId, params)
      setData(result)
    } catch (e) {
      logger.error(String(e))
      setError('No se pudieron cargar las órdenes.')
    } finally {
      setLoading(false)
      firstLoad.current = false
    }
  }, [businessId, params])

  useEffect(() => { void load() }, [load])

  // Any change to the filter invalidates the page number: staying on page 7 of
  // a result that now has 2 pages shows an empty sheet and looks like data loss.
  useEffect(() => { setPage(1) }, [debouncedSearch, facetFilters, dateFrom, dateTo, amountMin, amountMax, pageSize])

  const toggleSort = (column: string): void => {
    if (!data?.columns.find(c => c.key === column)?.sortable) return
    if (sortBy === column) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortDir(NUMERIC_COLUMNS.has(column) || DATE_COLUMNS.has(column) ? 'desc' : 'asc')
    }
  }

  const toggleFacet = (facet: string, value: string): void => {
    setFacetFilters(prev => {
      const current = prev[facet] || []
      const next = current.includes(value) ? current.filter(v => v !== value) : [...current, value]
      return { ...prev, [facet]: next }
    })
  }

  const clearFilters = (): void => {
    setFacetFilters({})
    setDateFrom('')
    setDateTo('')
    setAmountMin('')
    setAmountMax('')
    setSearch('')
  }

  const activeFilterCount =
    Object.values(facetFilters).reduce((sum, values) => sum + values.length, 0) +
    (dateFrom ? 1 : 0) + (dateTo ? 1 : 0) + (amountMin ? 1 : 0) + (amountMax ? 1 : 0)

  const rows = useMemo((): OrderRow[] => data?.rows ?? [], [data])
  const allSelected = rows.length > 0 && rows.every(r => selected.has(r.id))

  const toggleAll = (): void => {
    setSelected(prev => {
      const next = new Set(prev)
      if (allSelected) rows.forEach(r => next.delete(r.id))
      else rows.forEach(r => next.add(r.id))
      return next
    })
  }

  /** What every selected order could legally become, per the backend's own map. */
  const bulkOptions = useMemo((): string[] => {
    if (!data || selected.size === 0) return []
    const chosen = rows.filter(r => selected.has(r.id))
    if (!chosen.length) return []
    const sets = chosen.map(r => new Set(data.transitions[r.status || 'pending'] || []))
    return Object.keys(STATUS_LABELS).filter(status => sets.every(s => s.has(status)))
  }, [data, rows, selected])

  const moveOne = async (orderId: string, status: string): Promise<void> => {
    setBusy(true)
    try {
      const result = await ordersApi.bulkStatus([orderId], status)
      // Same endpoint as the bulk bar, so a refused move comes back with the
      // backend's own reason instead of silently doing nothing.
      if (!result.updated) setError(result.results[0]?.reason || 'No se pudo cambiar el estado.')
      else setError(null)
      await load()
    } catch (e) {
      logger.error(String(e))
      setError('No se pudo cambiar el estado.')
    } finally {
      setBusy(false)
    }
  }

  const runBulk = async (status: string): Promise<void> => {
    setBusy(true)
    setBulkResult(null)
    try {
      const result = await ordersApi.bulkStatus(Array.from(selected), status)
      setBulkResult(result)
      setSelected(new Set())
      await load()
    } catch (e) {
      logger.error(String(e))
      setError('No se pudo aplicar el cambio masivo.')
    } finally {
      setBusy(false)
    }
  }

  const exportCsv = async (): Promise<void> => {
    setBusy(true)
    try {
      await ordersApi.downloadCsv(businessId, { ...params, page: undefined, page_size: undefined })
    } catch (e) {
      logger.error(String(e))
      setError('No se pudo exportar el CSV.')
    } finally {
      setBusy(false)
    }
  }

  const renderCell = (row: OrderRow, key: string): React.JSX.Element | string => {
    const value = (row as unknown as Record<string, unknown>)[key]
    if (key === 'status' || key === 'payment_status') {
      const raw = String(value || '')
      const labels = key === 'status' ? STATUS_LABELS : PAYMENT_LABELS
      const color = key === 'status' ? (STATUS_COLORS[raw] || '#64748B') : '#94A3B8'
      return (
        <span
          className="inline-block px-2 py-0.5 rounded-md text-[10px] font-medium whitespace-nowrap"
          style={{ background: `${color}1A`, color }}
        >
          {labels[raw] || raw || '—'}
        </span>
      )
    }
    if (key === 'total_amount') {
      return (
        <span className="tabular-nums font-medium text-white">
          {Number(value || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
        </span>
      )
    }
    if (DATE_COLUMNS.has(key)) {
      if (!value) return '—'
      return new Date(String(value)).toLocaleString('es-AR', {
        day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit',
      })
    }
    if (NUMERIC_COLUMNS.has(key)) {
      return value === null || value === undefined ? '—' : <span className="tabular-nums">{String(value)}</span>
    }
    const text = value === null || value === undefined || value === '' ? '—' : String(value)
    return <span title={text}>{text.length > 42 ? `${text.slice(0, 40)}…` : text}</span>
  }

  const columns = (data?.columns ?? []).filter(c => visible.includes(c.key))

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar orden, cliente, email, tracking, producto…"
            className="w-full pl-9 pr-8 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`px-3 py-2.5 rounded-xl border text-sm flex items-center gap-2 transition-colors ${
            activeFilterCount ? 'bg-brand-orange/10 border-brand-orange/30 text-brand-orange' : 'bg-white/5 border-white/10 text-white/60 hover:text-white'
          }`}
        >
          <Filter className="w-4 h-4" />
          Filtros{activeFilterCount ? ` (${activeFilterCount})` : ''}
        </button>
        <div className="relative">
          <button
            onClick={() => setShowColumns(!showColumns)}
            className="px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white/60 hover:text-white flex items-center gap-2"
          >
            <Columns3 className="w-4 h-4" />
            Columnas
          </button>
          {showColumns && (
            <div className="absolute right-0 mt-2 w-64 max-h-80 overflow-y-auto z-20 p-2 rounded-xl bg-[#0A0E1A] border border-white/10 shadow-xl">
              {(data?.columns ?? []).map(col => (
                <label key={col.key} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-white/5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={visible.includes(col.key)}
                    onChange={() => setVisible(prev => prev.includes(col.key) ? prev.filter(k => k !== col.key) : [...prev, col.key])}
                    className="accent-brand-orange"
                  />
                  <span className="text-xs text-white/70">{col.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={() => void exportCsv()}
          disabled={busy || !rows.length}
          className="px-3 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm text-white/60 hover:text-white disabled:opacity-40 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Excel / CSV
        </button>
        <button
          onClick={() => void load()}
          className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-white/60 hover:text-white"
          title="Actualizar"
        >
          <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filters */}
      {showFilters && data && (
        <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Object.entries(FACET_LABELS).map(([facet, label]) => {
              const options = data.facets[facet] || []
              if (!options.length) return null
              return (
                <div key={facet}>
                  <p className="text-[10px] uppercase tracking-wide text-white/30 mb-1.5">{label}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {options.map(option => {
                      const active = (facetFilters[facet] || []).includes(option.value)
                      const label2 = facet === 'status' ? (STATUS_LABELS[option.value] || option.value)
                        : facet === 'payment_status' ? (PAYMENT_LABELS[option.value] || option.value)
                        : option.value
                      return (
                        <button
                          key={option.value}
                          onClick={() => toggleFacet(facet, option.value)}
                          className={`px-2 py-1 rounded-lg text-[11px] border transition-colors ${
                            active
                              ? 'bg-brand-orange/15 border-brand-orange/40 text-brand-orange'
                              : 'bg-white/5 border-white/10 text-white/50 hover:text-white/80'
                          }`}
                        >
                          {label2} <span className="opacity-50">{option.count}</span>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
            <div>
              <p className="text-[10px] uppercase tracking-wide text-white/30 mb-1.5">Fecha</p>
              <div className="flex gap-2">
                <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                  className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white" />
                <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
                  className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white" />
              </div>
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-white/30 mb-1.5">Monto</p>
              <div className="flex gap-2">
                <input type="number" value={amountMin} onChange={e => setAmountMin(e.target.value)} placeholder="mín"
                  className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white placeholder:text-white/20" />
                <input type="number" value={amountMax} onChange={e => setAmountMax(e.target.value)} placeholder="máx"
                  className="flex-1 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white placeholder:text-white/20" />
              </div>
            </div>
          </div>
          {activeFilterCount > 0 && (
            <button onClick={clearFilters} className="text-xs text-white/40 hover:text-white/70 underline">
              Limpiar filtros
            </button>
          )}
        </div>
      )}

      {/* Totals, one line per currency */}
      {data && data.totals.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {data.totals.map(total => (
            <div key={total.currency} className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] min-w-[190px]">
              <p className="text-[10px] uppercase tracking-wide text-white/30">{total.currency} · {total.orders} órdenes</p>
              <p className="text-lg font-semibold text-white tabular-nums">
                {total.revenue.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-white/40">
                Cobrado {total.paid_revenue.toLocaleString('es-AR', { minimumFractionDigits: 2 })} · ticket {total.avg_order.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
              </p>
            </div>
          ))}
          {data.totals.length > 1 && (
            <div className="px-4 py-3 rounded-xl border border-dashed border-white/10 text-[11px] text-white/30 max-w-[230px] flex items-center">
              Hay ventas en {data.totals.length} monedas. No se suman entre sí: sin un tipo de cambio propio, el total sería inventado.
            </div>
          )}
        </div>
      )}

      {/* What the backend could not do */}
      {data?.notes.map(note => (
        <div key={note} className="flex items-start gap-2 px-3 py-2 rounded-xl bg-amber-500/[0.07] border border-amber-500/20 text-[11px] text-amber-200/80">
          <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          {note}
        </div>
      ))}

      {error && (
        <div className="px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300">{error}</div>
      )}

      {/* Bulk bar */}
      {selected.size > 0 && (
        <div className="flex flex-wrap items-center gap-2 px-4 py-3 rounded-xl bg-brand-orange/[0.08] border border-brand-orange/20">
          <span className="text-sm text-white">{selected.size} seleccionadas</span>
          {bulkOptions.length === 0 ? (
            <span className="text-xs text-white/40">
              No hay una acción común: las órdenes elegidas están en estados que no permiten el mismo paso.
            </span>
          ) : bulkOptions.map(status => (
            <button
              key={status}
              disabled={busy}
              onClick={() => void runBulk(status)}
              className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-xs text-white disabled:opacity-40"
            >
              Marcar como {STATUS_LABELS[status]}
            </button>
          ))}
          <button onClick={() => setSelected(new Set())} className="ml-auto text-xs text-white/40 hover:text-white/70">
            Deseleccionar
          </button>
        </div>
      )}

      {bulkResult && (
        <div className="px-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-xs space-y-1">
          <p className="text-white">
            {bulkResult.updated} actualizadas · {bulkResult.skipped} sin cambios de {bulkResult.requested}
          </p>
          {bulkResult.results.filter(r => !r.changed).slice(0, 5).map(r => (
            <p key={r.order_id} className="text-white/40">· {r.order_id.slice(0, 8)}: {r.reason}</p>
          ))}
          <button onClick={() => setBulkResult(null)} className="text-white/30 hover:text-white/60 underline">cerrar</button>
        </div>
      )}

      {/* Sheet */}
      <div className="border border-white/[0.06] rounded-2xl overflow-hidden">
        <div className="overflow-x-auto max-h-[70vh] overflow-y-auto">
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-[#0D1220]">
                <th className="px-3 py-2.5 border-b border-white/10 w-8">
                  <input type="checkbox" checked={allSelected} onChange={toggleAll} className="accent-brand-orange" />
                </th>
                {columns.map(col => {
                  const active = sortBy === col.key
                  return (
                    <th
                      key={col.key}
                      onClick={() => toggleSort(col.key)}
                      className={`px-3 py-2.5 border-b border-white/10 text-left font-medium whitespace-nowrap ${
                        col.sortable ? 'cursor-pointer hover:text-white' : 'cursor-default'
                      } ${active ? 'text-brand-orange' : 'text-white/40'}`}
                    >
                      <span className="inline-flex items-center gap-1">
                        {col.label}
                        {active && (sortDir === 'asc' ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />)}
                      </span>
                    </th>
                  )
                })}
                <th className="px-3 py-2.5 border-b border-white/10 text-left font-medium text-white/40 whitespace-nowrap">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr
                  key={row.id}
                  className={`border-b border-white/[0.04] hover:bg-white/[0.04] ${index % 2 ? 'bg-white/[0.012]' : ''} ${
                    selected.has(row.id) ? 'bg-brand-orange/[0.06]' : ''
                  }`}
                >
                  <td className="px-3 py-2">
                    <input
                      type="checkbox"
                      checked={selected.has(row.id)}
                      onChange={() => setSelected(prev => {
                        const next = new Set(prev)
                        if (next.has(row.id)) next.delete(row.id)
                        else next.add(row.id)
                        return next
                      })}
                      className="accent-brand-orange"
                    />
                  </td>
                  {columns.map(col => (
                    <td
                      key={col.key}
                      className={`px-3 py-2 text-white/70 whitespace-nowrap ${NUMERIC_COLUMNS.has(col.key) ? 'text-right' : ''}`}
                    >
                      {renderCell(row, col.key)}
                    </td>
                  ))}
                  <td className="px-3 py-2 whitespace-nowrap">
                    <div className="flex gap-1">
                      {(data?.transitions[row.status || 'pending'] || []).map(next => (
                        <button
                          key={next}
                          disabled={busy}
                          onClick={() => void moveOne(row.id, next)}
                          className="px-2 py-0.5 rounded-md bg-white/[0.07] hover:bg-white/[0.14] text-[10px] text-white/70 disabled:opacity-30"
                        >
                          {STATUS_LABELS[next]}
                        </button>
                      ))}
                      {(data?.transitions[row.status || 'pending'] || []).length === 0 && (
                        <span className="text-[10px] text-white/20">estado final</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {loading && firstLoad.current && (
          <div className="flex items-center justify-center py-12 text-white/30 text-sm">
            <Loader2 className="w-4 h-4 animate-spin mr-2" /> Cargando órdenes…
          </div>
        )}

        {!loading && rows.length === 0 && (
          <div className="text-center py-12">
            <p className="text-sm text-white/30">
              {activeFilterCount || debouncedSearch ? 'Ninguna orden coincide con el filtro' : 'Todavía no hay órdenes'}
            </p>
            <p className="text-xs text-white/20 mt-1">
              {activeFilterCount || debouncedSearch
                ? 'Probá quitar algún filtro.'
                : 'Aparecen solas cuando entra una venta por cualquier plataforma conectada.'}
            </p>
          </div>
        )}

        {/* Paging */}
        {data && data.total > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-t border-white/[0.06] text-xs text-white/40">
            <span>
              {(data.page - 1) * data.page_size + 1}–{Math.min(data.page * data.page_size, data.total)} de {data.total}
            </span>
            <div className="flex items-center gap-2">
              <select
                value={pageSize}
                onChange={e => setPageSize(Number(e.target.value))}
                className="px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-white/60"
              >
                {[25, 50, 100, 200].map(size => (
                  <option key={size} value={size} className="bg-[#0A0E1A]">{size} filas</option>
                ))}
              </select>
              <button
                disabled={data.page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg bg-white/5 border border-white/10 disabled:opacity-30"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span>{data.page} / {data.pages}</span>
              <button
                disabled={data.page >= data.pages}
                onClick={() => setPage(p => p + 1)}
                className="p-1.5 rounded-lg bg-white/5 border border-white/10 disabled:opacity-30"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      <p className="text-[10px] text-white/20">
        Los datos del cliente se muestran enmascarados, acá y en el CSV: la base los guarda cifrados y la app no los expone
        completos en ninguna pantalla. La búsqueda sí mira el dato real.
      </p>
    </div>
  )
}

export default OrdersSheet
