'use client'

import { ExternalLink, CheckCircle, Circle, AlertCircle, Loader } from 'lucide-react'
import { useState } from 'react'

const PLATFORMS = [
  {
    id: 'mercado-libre',
    name: 'Mercado Libre',
    description: 'Vende en Mercado Libre con sincronización automática',
    icon: '🏪',
    color: 'from-yellow-400 to-yellow-600',
    connected: false,
    authUrl: 'https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://sellia-brain.vercel.app/api/v1/oauth/mercado-libre/callback',
  },
  {
    id: 'amazon',
    name: 'Amazon',
    description: 'Gestiona tu tienda en Amazon Seller Central',
    icon: '📦',
    color: 'from-orange-400 to-orange-600',
    connected: false,
    authUrl: 'https://sellercentral.amazon.com/ap/signin',
  },
  {
    id: 'hotmart',
    name: 'Hotmart',
    description: 'Vende productos digitales en Hotmart',
    icon: '🎓',
    color: 'from-purple-400 to-purple-600',
    connected: false,
    authUrl: 'https://app.hotmart.com/login',
  },
]

export default function PlatformsPage() {
  const [platforms, setPlatforms] = useState(PLATFORMS)
  const [connecting, setConnecting] = useState<string | null>(null)

  const handleConnect = (platformId: string) => {
    setConnecting(platformId)
    // Simulado: después de 1.5s marca como conectado
    setTimeout(() => {
      setPlatforms(
        platforms.map((p) =>
          p.id === platformId ? { ...p, connected: true } : p
        )
      )
      setConnecting(null)
    }, 1500)
  }

  const handleDisconnect = (platformId: string) => {
    setPlatforms(
      platforms.map((p) =>
        p.id === platformId ? { ...p, connected: false } : p
      )
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black text-slate-900">Conecta tus plataformas</h1>
        <p className="text-slate-600 mt-2">Sincroniza órdenes, inventario y listings automáticamente</p>
      </div>

      {/* Connection Status */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          {platforms.filter((p) => p.connected).length} de {platforms.length} plataformas conectadas
        </p>
        <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{
              width: `${(platforms.filter((p) => p.connected).length / platforms.length) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Platform Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {platforms.map((platform) => (
          <div
            key={platform.id}
            className="bg-white border-2 border-slate-200 rounded-lg p-6 transition-all hover:border-slate-300"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="text-3xl">{platform.icon}</div>
                <div>
                  <h3 className="font-bold text-slate-900">{platform.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">{platform.description}</p>
                </div>
              </div>
              {platform.connected ? (
                <CheckCircle size={20} className="text-green-600" />
              ) : (
                <Circle size={20} className="text-slate-300" />
              )}
            </div>

            {/* Status Info */}
            {platform.connected ? (
              <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="text-sm font-medium text-green-900">Conectado</p>
                <p className="text-xs text-green-700 mt-1">
                  Última sincronización: Hace 2 minutos
                </p>
              </div>
            ) : (
              <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm font-medium text-yellow-900">No conectado</p>
                <p className="text-xs text-yellow-700 mt-1">
                  Haz clic en conectar para comenzar
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              {platform.connected ? (
                <>
                  <button className="flex-1 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-900 rounded-lg font-medium text-sm transition-colors">
                    Configurar
                  </button>
                  <button
                    onClick={() => handleDisconnect(platform.id)}
                    className="flex-1 px-4 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg font-medium text-sm transition-colors"
                  >
                    Desconectar
                  </button>
                </>
              ) : (
                <button
                  onClick={() => handleConnect(platform.id)}
                  disabled={connecting === platform.id}
                  className="w-full px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-slate-300 disabled:to-slate-400 text-white rounded-lg font-medium text-sm transition-all flex items-center justify-center gap-2"
                >
                  {connecting === platform.id ? (
                    <>
                      <Loader size={16} className="animate-spin" />
                      Conectando...
                    </>
                  ) : (
                    <>
                      <ExternalLink size={16} />
                      Conectar
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Info Section */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-6">
        <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
          <AlertCircle size={18} />
          ¿Cómo funciona?
        </h3>
        <ol className="space-y-2 text-sm text-slate-700 list-decimal list-inside">
          <li>Haz clic en "Conectar" para autenticar tu cuenta en la plataforma</li>
          <li>Se abrirá una nueva ventana con el login de la plataforma</li>
          <li>Autoriza a SellIA para acceder a tus datos</li>
          <li>Serás redirigido de vuelta a tu dashboard</li>
          <li>¡Listo! Tu inventario se sincronizará automáticamente</li>
        </ol>
      </div>
    </div>
  )
}
