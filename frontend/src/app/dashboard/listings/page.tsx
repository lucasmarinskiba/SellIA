'use client'

/**
 * Listings — el catálogo real del negocio (agentes/servicios/productos).
 *
 * Antes mostraba tres productos inventados (iPhone 15 Pro con 12 de stock y
 * 1234 vistas, AirPods, MacBook) escritos a mano en el componente, luego se
 * cambió a leer GET /businesses/{id}/products -- pero ese modelo (storefront
 * de /dashboard/websites/products) no tiene clasificación de tipo. Ahora lee
 * GET /catalog/{id}/items, el catálogo real (CatalogItemType: service/good/
 * digital) que también alimenta el contexto de negocio del SellIA Assistant.
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Plus, Loader2, Package, ExternalLink, RefreshCw, Search, Flame } from 'lucide-react'
import { api } from '@/lib/api'
import { useBusinessSnapshot, formatMoney } from '@/lib/businessSnapshot'
import { commerceApi, type PlatformRow } from '@/lib/platformCommerce'
import { webPresenceApi, scoreColor } from '@/lib/webPresence'

type CatalogItemType = 'service' | 'good' | 'digital'

interface CatalogItemSeo {
  title: string
  meta_description: string
}

interface CatalogItemFomo {
  headline: string
  angle: 'scarcity' | 'value'
}

interface CatalogItemRow {
  id: string
  type: CatalogItemType
  name: string
  category: string | null
  source_platform: string | null
  listing_url: string | null
  price: number | string
  currency: string
  stock: number | null
  is_available: boolean
  extra_data: Record<string, unknown> & { seo?: CatalogItemSeo; fomo?: CatalogItemFomo }
}

interface SyncPullResult {
  platform: string
  success: boolean
  message: string
  items_synced: number
}

const TYPE_LABEL: Record<CatalogItemType, string> = { service: 'Servicio', good: 'Físico', digital: 'Digital' }
const TYPE_COLOR: Record<CatalogItemType, string> = {
  service: 'bg-purple-100 text-purple-700',
  good: 'bg-blue-100 text-blue-700',
  digital: 'bg-emerald-100 text-emerald-700',
}

export default function ListingsPage() {
  const { snapshot, loading: snapLoading } = useBusinessSnapshot()
  const [items, setItems] = useState<CatalogItemRow[]>([])
  const [loading, setLoading] = useState(true)
  const [platforms, setPlatforms] = useState<PlatformRow[]>([])
  const [syncing, setSyncing] = useState(false)
  const [syncResults, setSyncResults] = useState<SyncPullResult[] | null>(null)
  const [seoLoadingId, setSeoLoadingId] = useState<string | null>(null)
  const [fomoLoadingId, setFomoLoadingId] = useState<string | null>(null)
  const [auditLoadingId, setAuditLoadingId] = useState<string | null>(null)
  const [auditResults, setAuditResults] = useState<Record<string, { ok: boolean; score?: number; issues?: number; error?: string }>>({})

  const businessId = snapshot?.business.id ?? null

  const loadItems = (id: string): Promise<void> =>
    api.get<CatalogItemRow[]>(`/catalog/${id}/items`).then(res => setItems(res.data ?? []))

  useEffect(() => {
    if (snapLoading) return
    if (!businessId) { setLoading(false); return }
    let alive = true
    Promise.all([
      loadItems(businessId),
      commerceApi.overview().then(o => { if (alive) setPlatforms(o.platforms) }),
    ])
      .catch(() => { /* sin negocio / sin catálogo -> lista vacía real */ })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [businessId, snapLoading])

  // Only platforms actually connected -- capabilities.catalog_pull comes
  // straight from platform_commerce/capabilities.py's introspection of the
  // real connector classes, so this never promises an import for a platform
  // whose connector can't do it (mercadolibre, whatsapp, etc.).
  const connectedPlatforms = platforms.filter(p => p.connection?.connected)
  const pullable = connectedPlatforms.filter(p => p.capabilities.some(c => c.key === 'catalog_pull' && c.available))
  const notPullable = connectedPlatforms.filter(p => !p.capabilities.some(c => c.key === 'catalog_pull' && c.available))

  const handleAuditReal = async (itemId: string, listingUrl: string): Promise<void> => {
    setAuditLoadingId(itemId)
    try {
      const res = await webPresenceApi.analyzeUrl(listingUrl)
      setAuditResults(prev => ({
        ...prev,
        [itemId]: res.ok
          ? { ok: true, score: res.score, issues: res.audit?.issues.length ?? 0 }
          : { ok: false, error: res.error || `HTTP ${res.http_status}` },
      }))
    } catch {
      setAuditResults(prev => ({ ...prev, [itemId]: { ok: false, error: 'No se pudo auditar la publicación.' } }))
    } finally {
      setAuditLoadingId(null)
    }
  }

  const handleSync = async (): Promise<void> => {
    if (!businessId) return
    setSyncing(true)
    setSyncResults(null)
    try {
      const res = await api.post<{ results: SyncPullResult[] }>(`/catalog/${businessId}/catalog/sync-pull`)
      setSyncResults(res.data.results ?? [])
      await loadItems(businessId)
    } catch {
      setSyncResults([{ platform: '', success: false, message: 'No se pudo sincronizar. Probá de nuevo en un momento.', items_synced: 0 }])
    } finally {
      setSyncing(false)
    }
  }

  const handleSeoOptimize = async (itemId: string): Promise<void> => {
    if (!businessId) return
    setSeoLoadingId(itemId)
    try {
      const res = await api.post<CatalogItemRow>(`/catalog/${businessId}/items/${itemId}/seo-optimize`)
      setItems(prev => prev.map(it => it.id === itemId ? res.data : it))
    } catch {
      alert('No se pudo generar el SEO. Probá de nuevo en un momento.')
    } finally {
      setSeoLoadingId(null)
    }
  }

  const handleFomoGenerate = async (itemId: string): Promise<void> => {
    if (!businessId) return
    setFomoLoadingId(itemId)
    try {
      const res = await api.post<CatalogItemRow>(`/catalog/${businessId}/items/${itemId}/fomo-generate`)
      setItems(prev => prev.map(it => it.id === itemId ? res.data : it))
    } catch {
      alert('No se pudo generar el FOMO. Probá de nuevo en un momento.')
    } finally {
      setFomoLoadingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Listings</h1>
          <p className="text-slate-600 mt-2">
            {items.length > 0
              ? `${items.length} producto(s)/servicio(s) en tu catálogo`
              : 'Tu catálogo de productos y servicios'}
          </p>
        </div>
        {businessId && (
          <div className="flex items-center gap-2">
            {pullable.length > 0 && (
              <button
                onClick={handleSync}
                disabled={syncing}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg font-medium disabled:opacity-50"
              >
                <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
                {syncing ? 'Sincronizando…' : 'Sincronizar desde plataformas'}
              </button>
            )}
            <Link href="/dashboard/listings/create" className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">
              <Plus size={18} />
              Nuevo listing
            </Link>
          </div>
        )}
      </div>

      {syncResults && (
        <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-1">
          {syncResults.map((r, i) => (
            <p key={i} className={`text-sm ${r.success ? 'text-slate-700' : 'text-red-600'}`}>
              {r.platform && <span className="font-medium">{r.platform}: </span>}
              {r.message}
            </p>
          ))}
        </div>
      )}

      {!syncing && notPullable.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
          {notPullable.map(p => p.platform).join(', ')} {notPullable.length === 1 ? 'está conectada' : 'están conectadas'} pero
          todavía no {notPullable.length === 1 ? 'puede' : 'pueden'} traer tu catálogo automáticamente — cargalo a mano con &quot;Nuevo listing&quot;.
        </div>
      )}

      {(snapLoading || loading) && (
        <div className="flex items-center gap-3 text-slate-500 py-10">
          <Loader2 className="w-5 h-5 animate-spin" /> Leyendo tu catálogo…
        </div>
      )}

      {!snapLoading && !loading && !businessId && (
        <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
          <p className="font-semibold text-slate-900 mb-1">Todavía no tenés un negocio creado</p>
          <p className="text-slate-600 text-sm mb-5">Creá tu negocio para publicar productos y servicios.</p>
          <Link
            href="/sellia-onboarding"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700"
          >
            Configurar mi negocio <ExternalLink className="w-4 h-4" />
          </Link>
        </div>
      )}

      {!snapLoading && !loading && businessId && (
        <div className="bg-white rounded-lg border border-slate-200 p-6">
          {items.length === 0 ? (
            <div className="text-center py-6">
              <Package className="w-8 h-8 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-900 mb-1">Todavía no cargaste nada en tu catálogo</p>
              <p className="text-slate-600 text-sm">
                Cuando cargues un producto o servicio, aparece acá con su precio, tipo y plataforma reales.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Producto/Servicio</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Tipo</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Categoría</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Plataforma</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Precio</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Stock</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Estado</th>
                    <th className="text-left py-2 px-2 text-slate-600 font-medium">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(it => (
                    <tr key={it.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-2 text-slate-900 font-medium">
                        {it.name}
                        {it.extra_data?.seo?.title && (
                          <p className="text-xs text-blue-600 font-normal mt-0.5" title={it.extra_data.seo.meta_description}>
                            SEO: {it.extra_data.seo.title}
                          </p>
                        )}
                        {it.extra_data?.fomo?.headline && (
                          <p className={`text-xs font-normal mt-0.5 ${it.extra_data.fomo.angle === 'scarcity' ? 'text-orange-600' : 'text-slate-500'}`}>
                            {it.extra_data.fomo.angle === 'scarcity' ? '🔥 ' : '✨ '}{it.extra_data.fomo.headline}
                          </p>
                        )}
                        {it.listing_url && (
                          <p className="text-xs mt-0.5 flex items-center gap-2 flex-wrap">
                            <a href={it.listing_url} target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-slate-700 hover:underline inline-flex items-center gap-0.5">
                              Ver publicación <ExternalLink size={10} />
                            </a>
                            <button
                              type="button"
                              onClick={() => handleAuditReal(it.id, it.listing_url!)}
                              disabled={auditLoadingId === it.id}
                              className="text-blue-600 hover:underline disabled:opacity-50"
                            >
                              {auditLoadingId === it.id ? 'Auditando…' : 'Auditar SEO real'}
                            </button>
                            {auditResults[it.id] && (
                              auditResults[it.id].ok
                                ? <span className={`font-semibold ${scoreColor(auditResults[it.id].score ?? null)}`}>
                                    Score real: {auditResults[it.id].score} ({auditResults[it.id].issues} hallazgos)
                                  </span>
                                : <span className="text-red-600">{auditResults[it.id].error}</span>
                            )}
                          </p>
                        )}
                      </td>
                      <td className="py-3 px-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${TYPE_COLOR[it.type]}`}>
                          {TYPE_LABEL[it.type]}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-slate-600">{it.category || '—'}</td>
                      <td className="py-3 px-2 text-slate-600">
                        {it.source_platform
                          ? <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200" title="Importado automáticamente">
                              <RefreshCw size={11} /> {it.source_platform}
                            </span>
                          : (typeof it.extra_data?.source_platform === 'string' ? it.extra_data.source_platform : 'Sin especificar')}
                      </td>
                      <td className="py-3 px-2 font-semibold text-slate-900">
                        {formatMoney(Number(it.price), it.currency)}
                      </td>
                      <td className="py-3 px-2 text-slate-600">
                        {it.type === 'good' ? (it.stock ?? 0) : '—'}
                      </td>
                      <td className="py-3 px-2">
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                          {it.is_available ? 'Disponible' : 'Pausado'}
                        </span>
                      </td>
                      <td className="py-3 px-2">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleSeoOptimize(it.id)}
                            disabled={seoLoadingId === it.id}
                            title="Optimizar SEO"
                            className="p-1.5 rounded-lg hover:bg-blue-50 text-slate-400 hover:text-blue-600 disabled:opacity-50"
                          >
                            {seoLoadingId === it.id ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                          </button>
                          <button
                            onClick={() => handleFomoGenerate(it.id)}
                            disabled={fomoLoadingId === it.id}
                            title="Generar FOMO"
                            className="p-1.5 rounded-lg hover:bg-orange-50 text-slate-400 hover:text-orange-600 disabled:opacity-50"
                          >
                            {fomoLoadingId === it.id ? <Loader2 size={14} className="animate-spin" /> : <Flame size={14} />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
