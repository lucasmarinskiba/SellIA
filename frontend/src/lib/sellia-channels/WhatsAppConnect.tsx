'use client'

/**
 * WhatsApp Cloud API · Embedded Signup component.
 *
 * Loads Meta FB SDK · opens FB.login w/ config_id · returns auth code.
 * POSTs code+waba_id+phone_number_id to backend /v1/channels/whatsapp/exchange.
 *
 * Prereq:
 *   - Meta App created · WhatsApp Business Embedded Signup configured
 *   - NEXT_PUBLIC_META_APP_ID + NEXT_PUBLIC_META_CONFIG_ID env vars
 */
import { useCallback, useEffect, useState } from 'react'

import { api } from '@/lib/sellia-api'


declare global {
  interface Window {
    FB?: any
    fbAsyncInit?: () => void
  }
}


interface SDKConfig {
  appId: string
  configId: string
}


function loadMetaSDK(appId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.FB) return resolve()
    const id = 'meta-jssdk'
    if (document.getElementById(id)) return resolve()

    window.fbAsyncInit = () => {
      window.FB.init({
        appId,
        autoLogAppEvents: true,
        xfbml: false,
        version: 'v21.0',
      })
      resolve()
    }

    const script = document.createElement('script')
    script.id = id
    script.src = 'https://connect.facebook.net/en_US/sdk.js'
    script.async = true
    script.defer = true
    script.crossOrigin = 'anonymous'
    script.onerror = () => reject(new Error('Failed to load Meta SDK'))
    document.body.appendChild(script)
  })
}


export interface WAConnectResult {
  channel_id: string
  phone_number_id: string
  display_phone: string | null
}


export function WhatsAppConnect({
  onConnected,
  onError,
  config,
}: {
  onConnected?: (r: WAConnectResult) => void
  onError?: (msg: string) => void
  config?: SDKConfig
}) {
  const appId = config?.appId || process.env.NEXT_PUBLIC_META_APP_ID
  const configId = config?.configId || process.env.NEXT_PUBLIC_META_CONFIG_ID

  const [loading, setLoading] = useState(false)
  const [sdkReady, setSdkReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!appId) return
    loadMetaSDK(appId).then(() => setSdkReady(true)).catch((e) => setError(String(e)))
  }, [appId])

  const sessionInfoListener = useCallback((evt: MessageEvent) => {
    if (typeof evt.data !== 'string') return
    if (!evt.origin.includes('facebook.com')) return
    try {
      const data = JSON.parse(evt.data)
      if (data?.type === 'WA_EMBEDDED_SIGNUP' && data?.event === 'FINISH') {
        // We get phone_number_id + waba_id here · paired with code from FB.login below
        ;(window as any).__sellia_wa_signup = data.data
      }
    } catch {
      /* ignore */
    }
  }, [])

  useEffect(() => {
    window.addEventListener('message', sessionInfoListener)
    return () => window.removeEventListener('message', sessionInfoListener)
  }, [sessionInfoListener])

  const launchSignup = useCallback(() => {
    if (!window.FB || !configId) {
      const msg = 'Meta SDK not ready or config missing'
      setError(msg)
      onError?.(msg)
      return
    }

    setLoading(true)
    setError(null)

    window.FB.login(
      async (response: any) => {
        try {
          const code = response?.authResponse?.code
          if (!code) {
            const msg = 'User canceled or no code returned'
            setError(msg)
            onError?.(msg)
            return
          }

          // Wait briefly for postMessage data
          await new Promise((r) => setTimeout(r, 800))
          const signup = (window as any).__sellia_wa_signup
          const waba_id = signup?.waba_id
          const phone_number_id = signup?.phone_number_id

          if (!waba_id || !phone_number_id) {
            const msg = 'Missing WABA or phone_number_id from Meta'
            setError(msg)
            onError?.(msg)
            return
          }

          const r = await api.post<WAConnectResult>('/channels/whatsapp/exchange', {
            code,
            waba_id,
            phone_number_id,
          })
          onConnected?.(r.data)
        } catch (e: any) {
          const msg = e?.response?.data?.detail || e?.message || 'Connect failed'
          setError(msg)
          onError?.(msg)
        } finally {
          setLoading(false)
          delete (window as any).__sellia_wa_signup
        }
      },
      {
        config_id: configId,
        response_type: 'code',
        override_default_response_type: true,
        extras: { setup: {}, featureType: '', sessionInfoVersion: '3' },
      }
    )
  }, [configId, onConnected, onError])

  if (!appId || !configId) {
    return (
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-[11px] text-amber-300">
        Meta App config missing · set <code>NEXT_PUBLIC_META_APP_ID</code> + <code>NEXT_PUBLIC_META_CONFIG_ID</code>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={launchSignup}
        disabled={!sdkReady || loading}
        className="w-full py-2.5 rounded-lg bg-[#25d366] text-white font-bold text-sm disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <span className="text-lg">💚</span>
        {loading ? 'Conectando…' : 'Conectar WhatsApp Business'}
      </button>
      {error && (
        <p className="text-[10px] text-red-300 px-2 py-1.5 rounded-md bg-red-500/10 border border-red-500/25">{error}</p>
      )}
    </div>
  )
}
