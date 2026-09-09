'use client'

/**
 * Plataformas — estado real de conexión.
 *
 * Antes el botón "Conectar" hacía esto:
 *     setTimeout(() => marcar como conectada, 1500)
 * es decir, simulaba la conexión: la tarjeta quedaba en verde "Conectado"
 * sin que existiera ninguna credencial ni ningún canal, y el usuario se iba
 * creyendo que su MercadoLibre estaba enlazado. Ahora el estado sale de las
 * conexiones reales de la cuenta (channel_connections) y conectar lleva al
 * flujo real de canales.
 */

import Link from 'next/link'
import { CheckCircle, Circle, Loader2, ExternalLink } from 'lucide-react'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'
import { platformMeta } from '@/lib/platformMeta'

interface PlatformCard {
  id: string
  name: string
  description: string
  icon: string
  /** valores de ChannelPlatform (backend) que cuentan como esta plataforma */
  matches: string[]
}

const PLATFORMS: PlatformCard[] = [
  { id: 'mercadolibre', name: 'Mercado Libre', description: 'Preguntas y ventas de tus publicaciones', icon: '🏪', matches: ['mercadolibre'] },
  { id: 'amazon', name: 'Amazon', description: 'Mensajes de compradores de Amazon', icon: '📦', matches: ['amazon'] },
  { id: 'hotmart', name: 'Hotmart', description: 'Consultas de tus productos digitales', icon: '🎓', matches: ['hotmart'] },
  { id: 'whatsapp', name: 'WhatsApp', description: 'Atención por WhatsApp Business', icon: '💬', matches: ['whatsapp'] },
  { id: 'instagram', name: 'Instagram', description: 'DMs y comentarios de Instagram', icon: '📸', matches: ['instagram'] },
  { id: 'shopify', name: 'Shopify', description: 'Tu tienda Shopify', icon: '🛍️', matches: ['shopify'] },
]

export default function PlatformsPage() {
  const { snapshot, loading, unavailable } = useBusinessSnapshot()
  const channels = snapshot?.channels ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Plataformas</h1>
        <p className="text-slate-600 mt-2">
          Qué está realmente conectado a tu cuenta y qué actividad tuvo.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tus conexiones…
        </div>
      )}

      {!loading && unavailable && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <p className="font-semibold text-slate-900">No se pudo leer tu cuenta.</p>
          <p className="text-sm text-slate-600 mt-1">
            No se marca ninguna plataforma como conectada sin poder verificarlo.
          </p>
        </div>
      )}

      {!loading && !unavailable && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {PLATFORMS.map(p => {
              const conn = channels.find(ch => p.matches.includes(ch.platform))
              const meta = platformMeta(p.matches[0])
              return (
                <div key={p.id} className="bg-white rounded-lg border border-slate-200 p-6">
                  <div className="flex items-start justify-between mb-3">
                    <span className="text-3xl">{p.icon}</span>
                    {conn
                      ? <span className="inline-flex items-center gap-1 text-xs font-semibold text-green-700 bg-green-50 px-2 py-1 rounded-full">
                          <CheckCircle size={13} /> Conectado
                        </span>
                      : <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 bg-slate-50 px-2 py-1 rounded-full">
                          <Circle size={13} /> Sin conectar
                        </span>}
                  </div>
                  <h2 className="font-bold text-slate-900" style={{ color: conn ? meta.color : undefined }}>{p.name}</h2>
                  <p className="text-sm text-slate-600 mt-1">{p.description}</p>

                  {conn ? (
                    <div className="mt-4 text-sm text-slate-700 space-y-0.5">
                      <p>{conn.conversations} conversación(es) · {conn.ai_replies} respondidas por la IA</p>
                      <p className="text-xs text-slate-500">
                        Estado: {conn.status}
                        {conn.last_message_at
                          ? ` · último mensaje ${new Date(conn.last_message_at).toLocaleString('es-AR')}`
                          : ' · sin mensajes todavía'}
                      </p>
                    </div>
                  ) : (
                    <Link
                      href="/dashboard/canales"
                      className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700"
                    >
                      Conectar <ExternalLink size={14} />
                    </Link>
                  )}
                </div>
              )
            })}
          </div>

          {channels.some(ch => !PLATFORMS.some(p => p.matches.includes(ch.platform))) && (
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <h2 className="font-bold text-slate-900 mb-3">Otros canales conectados</h2>
              <ul className="text-sm text-slate-700 space-y-1">
                {channels
                  .filter(ch => !PLATFORMS.some(p => p.matches.includes(ch.platform)))
                  .map(ch => (
                    <li key={`${ch.platform}-${ch.name}`}>
                      {platformMeta(ch.platform).label} · {ch.name} — {ch.conversations} conversación(es)
                    </li>
                  ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
