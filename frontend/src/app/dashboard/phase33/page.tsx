'use client'

/**
 * Vendedor Multiplataforma — estado real por plataforma.
 *
 * Antes esta página mostraba "$550k GMV · 350 listings · 8.0% conversión ·
 * 8+ best sellers" con gráficos de barras: eran constantes hardcodeadas en el
 * front (fallback "demo") más un backend que rellenaba ratings inventados
 * (4.8/4.7/4.9) cuando no había datos. Ninguna cuenta tenía esos números.
 *
 * Ahora todo sale del snapshot real de la cuenta: qué canales están
 * conectados de verdad (channel_connections), cuántas conversaciones y
 * cuántas respuestas generó la IA en cada uno, y qué facturación real hay
 * registrada en órdenes. Sin ventas cargadas, muestra cero y lo explica.
 */

import React from 'react'
import Link from 'next/link'
import { Loader2, Plug, Bot, ShoppingBag, ExternalLink } from 'lucide-react'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'
import { platformMeta } from '@/lib/platformMeta'
import ChannelConnectPanel from '@/components/channels/ChannelConnectPanel'
import MultiPlatformSeller from '@/components/platform-commerce/MultiPlatformSeller'

export default function VendedorMultiplataformaPage(): React.JSX.Element {
  const { snapshot, loading, unavailable } = useBusinessSnapshot()

  const channels = snapshot?.channels ?? []

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-1">Vendedor Multiplataforma</h1>
        <p className="text-slate-600">
          Qué plataformas tenés realmente conectadas, qué respondió la IA en cada una y qué se vendió.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 py-16 justify-center">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tus plataformas…
        </div>
      )}

      {!loading && unavailable && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6">
          <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
          <p className="text-sm text-slate-600 mt-1">
            No se muestran cifras de ejemplo mientras tanto.
          </p>
        </div>
      )}

      {!loading && !unavailable && snapshot && (
        <div className="space-y-6">
          {/* Números reales por plataforma: qué puede hacer SellIA en cada
              una (derivado del conector), qué vendió y cuál es su margen. */}
          <MultiPlatformSeller />

          {/* Conectar de verdad: formulario real por plataforma + prueba real
              de credenciales contra la propia plataforma. */}
          <ChannelConnectPanel />

          {/* Detalle real por canal conectado */}
          <div className="rounded-xl border border-slate-200 bg-white">
            <div className="p-5 border-b border-slate-100">
              <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                <Plug className="w-4 h-4 text-blue-600" /> Tus canales
              </h2>
            </div>

            {channels.length === 0 ? (
              <div className="p-8 text-center">
                <ShoppingBag className="w-8 h-8 text-slate-300 mx-auto mb-3" />
                <p className="font-semibold text-slate-900 mb-1">No hay plataformas conectadas todavía</p>
                <p className="text-slate-600 text-sm mb-5">
                  Conectá MercadoLibre, Amazon, Hotmart, WhatsApp o Instagram y acá vas a ver, por cada una,
                  las conversaciones reales y cuáles contestó la IA.
                </p>
                <Link
                  href="/dashboard/canales"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
                >
                  Conectar una plataforma <ExternalLink className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {channels.map(ch => {
                  const meta = platformMeta(ch.platform)
                  return (
                    <div key={`${ch.platform}-${ch.name}`} className="p-5 flex items-center gap-4 flex-wrap">
                      <span
                        className="px-2.5 py-1 rounded-md text-xs font-bold"
                        style={{ background: `${meta.color}1A`, color: meta.color }}
                      >
                        {meta.label}
                      </span>
                      <div className="flex-1 min-w-[180px]">
                        <p className="font-medium text-slate-900">{ch.name}</p>
                        <p className="text-xs text-slate-500">
                          Estado: {ch.status}
                          {ch.last_message_at
                            ? ` · último mensaje ${new Date(ch.last_message_at).toLocaleString('es-AR')}`
                            : ' · sin mensajes todavía'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-slate-900">{ch.conversations}</p>
                        <p className="text-xs text-slate-500">conversaciones</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-emerald-600 flex items-center gap-1 justify-end">
                          <Bot className="w-4 h-4" /> {ch.ai_replies}
                        </p>
                        <p className="text-xs text-slate-500">respondidas por IA</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <p className="text-xs text-slate-500">
            Ranking de best sellers y tasa de conversión por marketplace todavía no se muestran: eso
            necesita que la plataforma reporte visitas e impresiones por publicación, y sólo algunos
            conectores lo exponen. Facturación, costos y margen ya salen de tus órdenes reales.
          </p>
        </div>
      )}
    </div>
  )
}
