'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import {
  Shield,
  Smartphone,
  Monitor,
  Globe,
  Clock,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  MapPin,
} from 'lucide-react'

interface Session {
  id: string
  device_name: string | null
  ip_address: string
  country: string | null
  last_active_at: string
  expires_at: string
  created_at: string
  is_current?: boolean
}

export default function SessionsPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [revoking, setRevoking] = useState<string | null>(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [authLoading, user, router])

  useEffect(() => {
    if (user) fetchSessions()
  }, [user])

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token')
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/security/sessions`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
      }
    } catch {
      // silencioso
    } finally {
      setLoading(false)
    }
  }

  const revokeSession = async (sessionId: string) => {
    setRevoking(sessionId)
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token')
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/security/sessions/${sessionId}/revoke`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (res.ok) {
        setMessage('Sesión cerrada correctamente')
        fetchSessions()
      }
    } catch {
      setMessage('Error al cerrar sesión')
    } finally {
      setRevoking(null)
      setTimeout(() => setMessage(''), 3000)
    }
  }

  const revokeAll = async () => {
    if (!confirm('¿Cerrar todas las sesiones excepto la actual?')) return
    setLoading(true)
    try {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token')
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/security/sessions/revoke-all`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (res.ok) {
        setMessage('Todas las sesiones cerradas')
        fetchSessions()
      }
    } catch {
      setMessage('Error al cerrar sesiones')
    } finally {
      setLoading(false)
      setTimeout(() => setMessage(''), 3000)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-brand-orange" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Sesiones activas</h1>
          <p className="text-sm text-white/40">Gestioná tus dispositivos conectados</p>
        </div>
      </div>

      {message && (
        <div className="mb-6 flex items-center gap-2 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
          <CheckCircle2 className="w-4 h-4" />
          {message}
        </div>
      )}

      <div className="flex justify-end mb-4">
        <button
          onClick={revokeAll}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm hover:bg-red-500/20 transition-all"
        >
          <AlertTriangle className="w-4 h-4" />
          Cerrar todas las demás sesiones
        </button>
      </div>

      <div className="space-y-3">
        {sessions.length === 0 && (
          <div className="text-center py-12 text-white/30 text-sm">
            No hay sesiones activas
          </div>
        )}

        {sessions.map((session) => (
          <div
            key={session.id}
            className="flex items-center justify-between p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.1] transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/50">
                {session.device_name?.toLowerCase().includes('mobile') ? (
                  <Smartphone className="w-5 h-5" />
                ) : (
                  <Monitor className="w-5 h-5" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-white/90">
                    {session.device_name || 'Dispositivo desconocido'}
                  </p>
                  {session.is_current && (
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-orange/10 text-brand-orange border border-brand-orange/20">
                      Actual
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-white/30">
                  <span className="flex items-center gap-1">
                    <Globe className="w-3 h-3" />
                    {session.ip_address}
                  </span>
                  {session.country && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {session.country}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Última actividad: {new Date(session.last_active_at).toLocaleString('es-AR')}
                  </span>
                </div>
              </div>
            </div>

            {!session.is_current && (
              <button
                onClick={() => revokeSession(session.id)}
                disabled={revoking === session.id}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-500/5 border border-red-500/10 text-red-400 text-xs hover:bg-red-500/10 transition-all disabled:opacity-50"
              >
                {revoking === session.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
                Cerrar sesión
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
