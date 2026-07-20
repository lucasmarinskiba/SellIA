'use client'

import { useState, useEffect, useCallback } from 'react'

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ''

function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray.buffer
}

export function usePushNotifications() {
  const [isSupported, setIsSupported] = useState(false)
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true)
      checkSubscription()
    }
  }, [])

  const checkSubscription = useCallback(async () => {
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      setIsSubscribed(!!subscription)
    } catch {
      setIsSubscribed(false)
    }
  }, [])

  const subscribe = useCallback(async () => {
    if (!VAPID_PUBLIC_KEY) {
      import('@/lib/logger').then(({ logger }) => logger.warn('VAPID_PUBLIC_KEY no configurada'))
      return
    }

    setLoading(true)
    try {
      // Registrar service worker si no está registrado
      let registration = await navigator.serviceWorker.ready
      try {
        registration = await navigator.serviceWorker.register('/sw.js')
        await navigator.serviceWorker.ready
      } catch {
        // Ya registrado
      }

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      })

      // Enviar suscripción al backend
      const subJson = subscription.toJSON()
      const token = localStorage.getItem('token')
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/security/push/subscribe`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: token ? `Bearer ${token}` : '',
          },
          body: JSON.stringify({
            endpoint: subJson.endpoint,
            p256dh: subJson.keys?.p256dh,
            auth: subJson.keys?.auth,
            user_agent: navigator.userAgent,
          }),
        }
      )

      if (res.ok) {
        setIsSubscribed(true)
      }
    } catch (err) {
      import('@/lib/logger').then(({ logger }) => logger.error('Error suscribiendo a push', err))
    } finally {
      setLoading(false)
    }
  }, [])

  const unsubscribe = useCallback(async () => {
    setLoading(true)
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      if (subscription) {
        await subscription.unsubscribe()
        const token = localStorage.getItem('token')
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/security/push/unsubscribe`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: token ? `Bearer ${token}` : '',
            },
            body: JSON.stringify({ endpoint: subscription.endpoint }),
          }
        )
        setIsSubscribed(false)
      }
    } catch (err) {
      import('@/lib/logger').then(({ logger }) => logger.error('Error desuscribiendo', err))
    } finally {
      setLoading(false)
    }
  }, [])

  const sendTest = useCallback(async () => {
    const token = localStorage.getItem('token')
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/security/push/test`,
        {
          method: 'POST',
          headers: {
            Authorization: token ? `Bearer ${token}` : '',
          },
        }
      )
      return res.ok
    } catch {
      return false
    }
  }, [])

  return { isSupported, isSubscribed, loading, subscribe, unsubscribe, sendTest }
}
