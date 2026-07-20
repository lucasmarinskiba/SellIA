'use client'

import { useEffect } from 'react'

interface GlobalErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error('Global error:', error)
  }, [error])

  return (
    <html lang="es">
      <body style={{ background: '#060812', color: '#fff', fontFamily: 'sans-serif', margin: 0 }}>
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div style={{ textAlign: 'center', maxWidth: 420 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Error crítico</h2>
            <p style={{ fontSize: 14, opacity: 0.6, marginBottom: 16 }}>
              Algo inesperado ocurrió. Estamos investigando.
            </p>
            {error.digest && (
              <p style={{ fontSize: 11, opacity: 0.4, fontFamily: 'monospace', marginBottom: 20 }}>
                ref: {error.digest}
              </p>
            )}
            <button
              onClick={reset}
              style={{
                padding: '10px 20px',
                borderRadius: 12,
                background: 'rgba(255, 107, 53, 0.2)',
                border: '1px solid rgba(255, 107, 53, 0.3)',
                color: '#ff6b35',
                fontWeight: 500,
                cursor: 'pointer',
                fontSize: 14,
              }}
            >
              Reintentar
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
