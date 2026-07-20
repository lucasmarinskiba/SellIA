'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { businessApi, Business } from '@/lib/business'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import { Store, Plus, Pencil, Trash2, Package, Briefcase, FileText, Layers, ArrowRight } from 'lucide-react'

const typeLabels = {
  services: { label: 'Servicios', icon: Briefcase, color: 'bg-blue-50 text-blue-600', badge: 'info' as const },
  goods: { label: 'Bienes', icon: Package, color: 'bg-emerald-50 text-emerald-600', badge: 'teal' as const },
  digital: { label: 'Digital', icon: FileText, color: 'bg-violet-50 text-violet-600', badge: 'violet' as const },
  mixed: { label: 'Mixto', icon: Layers, color: 'bg-orange-50 text-orange-600', badge: 'orange' as const },
}

export default function NegociosPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadBusinesses()
  }, [])

  const loadBusinesses = async () => {
    try {
      const data = await businessApi.list()
      setBusinesses(data)
    } catch {
      // error handled by api interceptor
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('¿Estás seguro de que quieres eliminar este negocio?')) return
    try {
      await businessApi.delete(id)
      setBusinesses((prev) => prev.filter((b) => b.id !== id))
    } catch {
      // error handled by api interceptor
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-brand-orange/20 border-t-brand-orange rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-brand-night">Mis Negocios</h1>
          <p className="text-slate-500 mt-1">Configura tus negocios y canales de venta</p>
        </div>
        <Link href="/dashboard/negocios/nuevo">
          <Button leftIcon={<Plus className="w-4 h-4" />}>
            Nuevo negocio
          </Button>
        </Link>
      </div>

      {businesses.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={<Store className="w-8 h-8" />}
            title="No tienes negocios aún"
            description="Crea tu primer negocio para empezar a vender con agentes IA."
            action={{
              label: 'Crear negocio',
              onClick: () => window.location.href = '/dashboard/negocios/nuevo',
              icon: <Plus className="w-4 h-4" />,
            }}
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {businesses.map((business) => {
            const typeInfo = typeLabels[business.type] || typeLabels.mixed
            const TypeIcon = typeInfo.icon
            return (
              <div key={business.id} className="card p-6 group hover:shadow-card-hover transition-all duration-300">
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${typeInfo.color}`}>
                    <TypeIcon className="w-5 h-5" />
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Link
                      href={`/dashboard/negocios/${business.id}`}
                      className="p-1.5 text-slate-400 hover:text-brand-orange hover:bg-brand-orange/10 rounded-lg transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                    </Link>
                    <button
                      onClick={() => handleDelete(business.id)}
                      className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <h3 className="font-semibold text-brand-night text-lg">{business.name}</h3>
                <Badge variant={typeInfo.badge} className="mt-2">{typeInfo.label}</Badge>
                {business.description && (
                  <p className="text-sm text-slate-500 mt-3 line-clamp-2">{business.description}</p>
                )}
                <div className="mt-5 pt-4 border-t border-slate-100">
                  <Link
                    href={`/dashboard/catalogo?business=${business.id}`}
                    className="inline-flex items-center gap-1 text-sm font-medium text-brand-orange hover:text-brand-orange-dark transition-colors"
                  >
                    Ver catálogo <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
