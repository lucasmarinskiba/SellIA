'use client'

/**
 * Manual order entry.
 *
 * Órdenes could only ever show what arrived from a connected platform or a
 * webhook, so a sale closed by WhatsApp, in person or over the counter never
 * existed for the dashboards — and every revenue number was short by exactly
 * those sales. This is how they get in.
 *
 * The total is computed from the lines, never typed: a total that disagrees with
 * its own items is the kind of number nothing downstream can reconcile.
 */

import React, { useMemo, useState } from 'react'
import { Loader2, Plus, Trash2, X } from 'lucide-react'
import { logger } from '@/lib/logger'
import { api } from '@/lib/api'

interface Line {
  name: string
  quantity: number
  unit_price: number
}

interface Props {
  businessId: string
  /** Platforms this business has connected, to label where the sale came from. */
  platforms: string[]
  onClose: () => void
  onCreated: () => void
}

const inputClass =
  'w-full px-3 py-2 rounded-lg bg-white/[0.05] border border-white/[0.08] text-sm text-white placeholder:text-white/25 focus:outline-none focus:ring-1 focus:ring-brand-orange'

const NewOrderForm = ({ businessId, platforms, onClose, onCreated }: Props): React.JSX.Element => {
  const [lines, setLines] = useState<Line[]>([{ name: '', quantity: 1, unit_price: 0 }])
  const [currency, setCurrency] = useState('ARS')
  const [platform, setPlatform] = useState('')
  const [status, setStatus] = useState('pending')
  const [paid, setPaid] = useState(false)
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [shipping, setShipping] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const itemsTotal = useMemo(
    () => lines.reduce((sum, line) => sum + (Number(line.quantity) || 0) * (Number(line.unit_price) || 0), 0),
    [lines],
  )
  const total = itemsTotal + (Number(shipping) || 0)

  const setLine = (index: number, changes: Partial<Line>): void => {
    setLines(prev => prev.map((line, i) => (i === index ? { ...line, ...changes } : line)))
  }

  const valid = total > 0 && lines.some(line => line.name.trim())

  const submit = async (): Promise<void> => {
    if (!valid) {
      setError('Agregá al menos un producto con nombre y precio.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await api.post('/orders', {
        business_id: businessId,
        total_amount: Number(total.toFixed(2)),
        subtotal: Number(itemsTotal.toFixed(2)),
        shipping_cost: shipping ? Number(shipping) : null,
        currency,
        status,
        // An order marked paid must carry the payment status too, or the
        // dashboards count it as sold and not collected.
        payment_status: paid || status === 'paid' ? 'completed' : 'pending',
        external_platform: platform || null,
        customer_name: customerName.trim() || null,
        customer_email: customerEmail.trim() || null,
        customer_phone: customerPhone.trim() || null,
        notes: notes.trim() || null,
        items: lines
          .filter(line => line.name.trim())
          .map(line => ({
            name: line.name.trim(),
            quantity: Number(line.quantity) || 1,
            unit_price: Number(line.unit_price) || 0,
            total_price: Number(((Number(line.quantity) || 1) * (Number(line.unit_price) || 0)).toFixed(2)),
          })),
      })
      onCreated()
      onClose()
    } catch (e: unknown) {
      logger.error(String(e))
      const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'No se pudo guardar la orden.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur-sm overflow-y-auto py-8 px-4">
      <div className="w-full max-w-2xl rounded-2xl bg-[#0A0E1A] border border-white/10 p-6 space-y-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">Nueva orden</h2>
            <p className="text-xs text-white/40 mt-0.5">
              Para las ventas que no entran por una plataforma conectada: mostrador, WhatsApp, en mano.
            </p>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white" aria-label="Cerrar">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Lines */}
        <div className="space-y-2">
          <p className="text-xs text-white/50">Productos</p>
          {lines.map((line, index) => (
            <div key={index} className="flex gap-2">
              <input
                value={line.name}
                onChange={e => setLine(index, { name: e.target.value })}
                placeholder="Qué vendiste"
                className={`${inputClass} flex-1`}
              />
              <input
                type="number"
                min={1}
                value={line.quantity}
                onChange={e => setLine(index, { quantity: Number(e.target.value) })}
                className={`${inputClass} w-20`}
                aria-label="Cantidad"
              />
              <input
                type="number"
                min={0}
                step="0.01"
                value={line.unit_price || ''}
                onChange={e => setLine(index, { unit_price: Number(e.target.value) })}
                placeholder="Precio"
                className={`${inputClass} w-28`}
              />
              <button
                onClick={() => setLines(prev => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev))}
                className="px-2 rounded-lg text-white/30 hover:text-red-400 disabled:opacity-20"
                disabled={lines.length === 1}
                aria-label="Quitar línea"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          <button
            onClick={() => setLines(prev => [...prev, { name: '', quantity: 1, unit_price: 0 }])}
            className="text-xs text-brand-orange hover:underline flex items-center gap-1"
          >
            <Plus className="w-3 h-3" /> Agregar producto
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-white/50 mb-1">Moneda</label>
            <input
              value={currency}
              onChange={e => setCurrency(e.target.value.toUpperCase().slice(0, 3))}
              className={`${inputClass} uppercase`}
            />
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Envío</label>
            <input
              type="number"
              min={0}
              step="0.01"
              value={shipping}
              onChange={e => setShipping(e.target.value)}
              placeholder="0"
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Origen</label>
            <select value={platform} onChange={e => setPlatform(e.target.value)} className={inputClass}>
              <option value="" className="bg-[#0A0E1A]">Manual</option>
              {platforms.map(p => (
                <option key={p} value={p} className="bg-[#0A0E1A]">{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Estado</label>
            <select value={status} onChange={e => setStatus(e.target.value)} className={inputClass}>
              <option value="pending" className="bg-[#0A0E1A]">Pendiente</option>
              <option value="paid" className="bg-[#0A0E1A]">Pagada</option>
              <option value="delivered" className="bg-[#0A0E1A]">Entregada</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-white/50 mb-1">Cliente</label>
            <input value={customerName} onChange={e => setCustomerName(e.target.value)} placeholder="Nombre" className={inputClass} />
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Email</label>
            <input value={customerEmail} onChange={e => setCustomerEmail(e.target.value)} placeholder="Para medir recompra" className={inputClass} />
          </div>
          <div>
            <label className="block text-xs text-white/50 mb-1">Teléfono</label>
            <input value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} placeholder="Opcional" className={inputClass} />
          </div>
        </div>
        <p className="text-[10px] text-white/25 -mt-2">
          El email o el teléfono son lo único que permite saber si un cliente volvió a comprar. Se guardan
          cifrados y se muestran enmascarados.
        </p>

        <div>
          <label className="block text-xs text-white/50 mb-1">Notas</label>
          <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} className={inputClass} />
        </div>

        {status !== 'pending' && (
          <label className="flex items-center gap-2 text-xs text-white/60">
            <input type="checkbox" checked={paid} onChange={e => setPaid(e.target.checked)} className="accent-brand-orange" />
            Ya cobraste esta orden
          </label>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-white/[0.08]">
          <div>
            <p className="text-xs text-white/40">Total que se va a guardar</p>
            <p className="text-xl font-bold text-white tabular-nums">
              {total.toLocaleString('es-AR', { minimumFractionDigits: 2 })} {currency}
            </p>
            <p className="text-[10px] text-white/25">
              Sale de los productos{shipping ? ' más el envío' : ''}, no se escribe a mano.
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-white/60 hover:text-white">
              Cancelar
            </button>
            <button
              onClick={() => void submit()}
              disabled={saving || !valid}
              className="px-4 py-2 rounded-xl bg-brand-orange/15 border border-brand-orange/30 text-brand-orange text-sm flex items-center gap-2 disabled:opacity-40"
            >
              {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Guardar orden
            </button>
          </div>
        </div>

        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>
    </div>
  )
}

export default NewOrderForm
