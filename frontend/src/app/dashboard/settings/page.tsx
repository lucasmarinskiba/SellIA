'use client'

/**
 * Configuración — perfil real, guardado real.
 *
 * Antes el campo "Nombre" venía pre-cargado con "Juan Pérez" (una constante,
 * no tu nombre) y el botón "Guardar cambios" no estaba conectado a nada: se
 * podía escribir cualquier cosa y se perdía al recargar. Ahora carga tu
 * nombre real desde /auth/me y guarda con PATCH /users/me.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Save, Users, Loader2, CheckCircle2, Store, Shield } from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot } from '@/lib/businessSnapshot'

export default function SettingsPage() {
  const { snapshot } = useBusinessSnapshot()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    api.get<{ full_name?: string; email?: string }>('/auth/me')
      .then(res => {
        if (!alive) return
        setName(res.data.full_name ?? '')
        setEmail(res.data.email ?? '')
      })
      .catch(() => { if (alive) setError('No se pudo leer tu perfil.') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [])

  const save = async (): Promise<void> => {
    setSaving(true); setMessage(null); setError(null)
    try {
      const res = await api.patch<{ full_name: string }>('/users/me', { full_name: name.trim() })
      setName(res.data.full_name)
      setMessage('Nombre guardado.')
    } catch {
      setError('No se pudo guardar. Revisá el nombre e intentá de nuevo.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Configuración</h1>
        <p className="text-slate-600 mt-2">Tu cuenta real y tu negocio.</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Users size={20} /> Perfil
        </h2>

        {loading ? (
          <p className="text-sm text-slate-500 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Leyendo tu perfil…
          </p>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full px-4 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-500"
              />
              <p className="text-xs text-slate-500 mt-1">
                El email es tu identidad de acceso: cambiarlo requiere verificación y todavía no está disponible.
              </p>
            </div>
          </div>
        )}
      </div>

      {snapshot && (
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
            <Store size={20} /> Negocio
          </h2>
          {snapshot.verification.has_business ? (
            <div className="text-sm text-slate-700 space-y-1">
              <p><span className="text-slate-500">Nombre:</span> {snapshot.business.name}</p>
              <p><span className="text-slate-500">Subdominio:</span> {snapshot.verification.subdomain ?? 'sin reclamar'}</p>
              <p><span className="text-slate-500">Sitio:</span> {snapshot.verification.website_published ? 'publicado' : 'sin publicar'}</p>
            </div>
          ) : (
            <p className="text-sm text-slate-600">
              Todavía no configuraste tu negocio.{' '}
              <Link href="/sellia-onboarding" className="text-blue-600 font-semibold">Configurarlo ahora</Link>.
            </p>
          )}
        </div>
      )}

      {snapshot && (
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
            <Shield size={20} /> Seguridad
          </h2>
          <div className="text-sm text-slate-700 space-y-1">
            <p><span className="text-slate-500">Email verificado:</span> {snapshot.verification.email_verified ? 'sí' : 'no'}</p>
            <p><span className="text-slate-500">Verificación en dos pasos:</span> {snapshot.verification.two_factor_enabled ? 'activada' : 'desactivada'}</p>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={() => { void save() }}
          disabled={saving || loading || name.trim().length < 2}
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-semibold"
        >
          {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
          Guardar cambios
        </button>
        {message && (
          <span className="text-sm text-green-700 flex items-center gap-1">
            <CheckCircle2 size={16} /> {message}
          </span>
        )}
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>
    </div>
  )
}
