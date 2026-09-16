'use client'

import React, { useEffect, useState, useRef } from 'react'
import { ShoppingCart, Loader2, Wifi, WifiOff } from 'lucide-react'
import { fomaPhase1Api, type ConversionEvent } from '@/lib/fomoPhase1'
import { fomaWebhookClient, type FOMAWebhookClient } from '@/lib/fomoWebhooks'

interface ConversionTickerProps {
  businessId: string
  refreshInterval?: number
}

export function ConversionTicker({
  businessId,
  refreshInterval = 10000,
}: ConversionTickerProps): React.JSX.Element {
  const [conversions, setConversions] = useState<ConversionEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [streamConnected, setStreamConnected] = useState(false)
  const webhookClientRef = useRef<FOMAWebhookClient | null>(null)

  const loadConversions = async () => {
    try {
      const data = await fomaPhase1Api.getRecentConversions(businessId, 10, 24)
      setConversions(data)
    } catch (error) {
      console.error('Error loading conversions:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadConversions()

    // Connect to real-time stream
    const client = fomaWebhookClient.create(businessId, {
      onConversion: (event) => {
        setConversions(prev => {
          const newConversion: ConversionEvent = {
            id: event.data.id,
            platform_name: event.data.platform,
            conversion_value: event.data.amount || 0,
            created_at: event.data.timestamp,
          }
          return [newConversion, ...prev.slice(0, 9)]
        })
      },
      onClose: () => setStreamConnected(false),
    })

    client.connect()
    webhookClientRef.current = client
    setStreamConnected(client.isConnected())

    const interval = setInterval(() => {
      void loadConversions()
    }, refreshInterval)

    return () => {
      clearInterval(interval)
      client.disconnect()
    }
  }, [businessId, refreshInterval])

  if (loading && conversions.length === 0) {
    return (
      <div className="flex items-center gap-2 text-slate-500 py-4">
        <Loader2 className="w-4 h-4 animate-spin" />
        Cargando conversiones…
      </div>
    )
  }

  if (conversions.length === 0) {
    return (
      <div className="text-sm text-slate-500 py-4">
        No hay conversiones en las últimas 24h
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
          Conversiones Recientes (últimas 24h)
        </div>
        <div className="flex items-center gap-1.5">
          {streamConnected ? (
            <>
              <Wifi className="w-3 h-3 text-green-600" />
              <span className="text-xs text-green-600 font-medium">En vivo</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3 text-amber-600" />
              <span className="text-xs text-amber-600 font-medium">Polling</span>
            </>
          )}
        </div>
      </div>
      {conversions.map((conversion, idx) => (
        <div
          key={conversion.id}
          className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-green-50 to-transparent border border-green-100 animate-fade-in"
          style={{
            animationDelay: `${idx * 50}ms`,
          }}
        >
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100">
              <ShoppingCart className="w-4 h-4 text-green-600" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">
              {conversion.platform_name === 'mercado-libre'
                ? 'Mercado Libre'
                : conversion.platform_name === 'amazon'
                  ? 'Amazon'
                  : conversion.platform_name}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              {new Date(conversion.created_at).toLocaleTimeString('es-AR')}
            </p>
          </div>
          {conversion.conversion_value > 0 && (
            <div className="text-sm font-semibold text-green-600">
              ${conversion.conversion_value.toFixed(2)}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
