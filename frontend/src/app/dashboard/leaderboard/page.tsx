'use client'

/**
 * Ranking de tu negocio — qué producto, qué cliente y qué plataforma te sostienen.
 *
 * Esta página era un leaderboard que comparaba la cuenta con otros usuarios de
 * SellIA: pedía /gamification/leaderboard, /gamification/leaderboard/me y
 * /gamification/leaderboard/nearby, y ninguna de las tres existe en este backend
 * (404). Aun funcionando, saber que sos el puesto 47 de 300 desconocidos no
 * vende un producto más.
 *
 * Lo que sí sirve es el ranking de lo propio, y eso sale de las órdenes reales:
 * qué se vende, quién compra, dónde. Los montos van separados por moneda y cada
 * fila lleva la cantidad de órdenes detrás, para que un primer puesto construido
 * sobre dos ventas se lea como lo que es.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { Info, Loader2, Package, Store, Trophy, Users } from 'lucide-react'
import { logger } from '@/lib/logger'
import { formatAmounts, nextStepsApi, type RankingResponse } from '@/lib/nextSteps'

const Section = ({ title, icon: Icon, subtitle, children }: {
  title: string
  icon: typeof Trophy
  subtitle: string
  children: React.ReactNode
}): React.JSX.Element => (
  <div className="bg-white rounded-lg border border-slate-200 p-5">
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4 text-slate-400" />
      <h2 className="font-bold text-slate-900">{title}</h2>
    </div>
    <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
    <div className="mt-4">{children}</div>
  </div>
)

const medal = (index: number): string => (index === 0 ? '1º' : index === 1 ? '2º' : index === 2 ? '3º' : `${index + 1}º`)

export default function RankingNegocioPage(): React.JSX.Element {
  const [data, setData] = useState<RankingResponse | null>(null)
  const [days, setDays] = useState(90)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  const load = useCallback(async (): Promise<void> => {
    setLoading(true)
    setFailed(false)
    try {
      setData(await nextStepsApi.ranking(days))
    } catch (e) {
      logger.error(String(e))
      setFailed(true)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => { void load() }, [load])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Ranking de tu negocio</h1>
          <p className="text-slate-600 mt-2">
            Qué producto, qué cliente y qué plataforma te sostienen. Sale de tus órdenes, no de una
            comparación con otros.
          </p>
        </div>
        <div className="flex gap-1">
          {[30, 90, 180, 365].map(option => (
            <button
              key={option}
              onClick={() => setDays(option)}
              className={`px-2.5 py-1 rounded-md text-xs border ${
                days === option
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
              }`}
            >
              {option === 365 ? '1 año' : `${option}d`}
            </button>
          ))}
        </div>
      </div>

      {loading && !data && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Ordenando tus ventas…
        </div>
      )}

      {failed && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <p className="font-semibold text-slate-900">No se pudo leer tu ranking.</p>
          <p className="text-sm text-slate-600 mt-1">No se muestran posiciones de ejemplo.</p>
        </div>
      )}

      {data && !data.has_data && (
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <Trophy className="w-7 h-7 text-slate-300 mb-2" />
          <p className="text-sm text-slate-700">{data.note}</p>
          <p className="text-xs text-slate-400 mt-1">
            Cuando entre la primera venta, acá aparece qué se vendió y a quién.
          </p>
        </div>
      )}

      {data?.note && data.has_data && (
        <div className="flex items-start gap-2 px-4 py-3 rounded-xl border border-amber-200 bg-amber-50 text-xs text-amber-900">
          <Info className="w-4 h-4 mt-0.5 shrink-0" />
          {data.note}
        </div>
      )}

      {data?.has_data && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Section
            title="Lo que más se vende"
            icon={Package}
            subtitle={`Sobre ${data.orders_counted} órdenes de los últimos ${data.period_days} días.`}
          >
            {data.products.length === 0 ? (
              <p className="text-xs text-slate-500">
                Ninguna orden tiene productos con nombre, así que no se puede armar este ranking.
              </p>
            ) : (
              <ol className="space-y-2">
                {data.products.map((product, index) => (
                  <li key={product.name} className="flex items-start justify-between gap-3 text-sm">
                    <span className="text-slate-800">
                      <span className="text-slate-400 mr-1.5">{medal(index)}</span>
                      {product.name}
                      <span className="block text-[11px] text-slate-500">
                        {product.units} unidad(es) en {product.orders} orden(es)
                      </span>
                    </span>
                    <span className="text-slate-900 font-medium tabular-nums whitespace-nowrap">
                      {formatAmounts(product.revenue)}
                    </span>
                  </li>
                ))}
              </ol>
            )}
            {(data.orders_without_named_items ?? 0) > 0 && (
              <p className="text-[11px] text-slate-400 mt-3">
                {data.orders_without_named_items} orden(es) no tienen productos con nombre y no entran
                en este ranking.
              </p>
            )}
          </Section>

          <Section
            title="Tus mejores clientes"
            icon={Users}
            subtitle="Identificados por email o teléfono; se muestran enmascarados."
          >
            {data.customers.length === 0 ? (
              <p className="text-xs text-slate-500">
                Ninguna orden tiene email ni teléfono, así que no se puede saber quién compra.
              </p>
            ) : (
              <ol className="space-y-2">
                {data.customers.map((customer, index) => (
                  <li key={`${customer.label}-${index}`} className="flex items-start justify-between gap-3 text-sm">
                    <span className="text-slate-800">
                      <span className="text-slate-400 mr-1.5">{medal(index)}</span>
                      {customer.label}
                      <span className="block text-[11px] text-slate-500">
                        {customer.orders} compra(s)
                        {customer.days_since !== null && ` · última hace ${customer.days_since} días`}
                      </span>
                    </span>
                    <span className="text-slate-900 font-medium tabular-nums whitespace-nowrap">
                      {formatAmounts(customer.revenue)}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </Section>

          <Section
            title="Dónde se vende"
            icon={Store}
            subtitle="Plataforma de origen de cada orden, con cuántas terminaron cobradas."
          >
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 text-xs">
                  <th className="text-left py-1.5">Plataforma</th>
                  <th className="text-right py-1.5">Órdenes</th>
                  <th className="text-right py-1.5">Cobradas</th>
                  <th className="text-right py-1.5">Facturado</th>
                </tr>
              </thead>
              <tbody>
                {data.platforms.map(platform => (
                  <tr key={platform.platform} className="border-b border-slate-100">
                    <td className="py-2 text-slate-800">{platform.platform}</td>
                    <td className="py-2 text-right text-slate-600 tabular-nums">{platform.orders}</td>
                    <td className="py-2 text-right text-slate-600 tabular-nums">{platform.paid}</td>
                    <td className="py-2 text-right text-slate-900 tabular-nums whitespace-nowrap">
                      {formatAmounts(platform.revenue)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>
        </div>
      )}

      {data?.has_data && (
        <p className="text-[11px] text-slate-400">
          Los montos van por moneda y no se suman entre sí. Calculado el{' '}
          {new Date(data.generated_at).toLocaleString('es-AR')}.
        </p>
      )}
    </div>
  )
}
