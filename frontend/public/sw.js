// Service Worker para notificaciones push Web Push
self.addEventListener('push', (event) => {
  if (!event.data) return

  let payload
  try {
    payload = event.data.json()
  } catch {
    payload = { title: 'Notificación', body: event.data.text() }
  }

  const options = {
    body: payload.body || '',
    icon: payload.icon || '/icon-192x192.png',
    badge: payload.badge || '/badge-72x72.png',
    tag: payload.tag || 'default',
    requireInteraction: payload.requireInteraction ?? true,
    data: {
      url: payload.url || '/dashboard',
      timestamp: payload.timestamp,
    },
    actions: [
      {
        action: 'open',
        title: 'Abrir',
      },
      {
        action: 'dismiss',
        title: 'Cerrar',
      },
    ],
  }

  event.waitUntil(
    self.registration.showNotification(payload.title || 'SellIA', options)
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()

  const url = event.notification.data?.url || '/dashboard'

  if (event.action === 'dismiss') {
    return
  }

  event.waitUntil(
    clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Si ya hay una ventana abierta, enfocarla
        for (const client of windowClients) {
          if (client.url.includes(url) && 'focus' in client) {
            return client.focus()
          }
        }
        // Si no, abrir nueva ventana
        if (clients.openWindow) {
          return clients.openWindow(url)
        }
      })
  )
})

// Instalación y activación
self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})
