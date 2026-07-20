'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import { ShoppingBag, Search, Star, Clock, Package, Loader2, Zap, TrendingUp, Tag } from 'lucide-react'

interface MarketplaceItem {
  id: string
  name: string
  slug: string
  short_description: string
  category: string
  price_usd: number
  compare_price_usd?: number
  thumbnail_url?: string
  rating_avg: number
  rating_count: number
  purchase_count: number
  is_limited: boolean
  stock_remaining?: number
  offer_ends_at?: string
  is_featured: boolean
}

export default function MarketplacePage() {
  const { user, loading: authLoading } = useAuth()
  const [items, setItems] = useState<MarketplaceItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')

  useEffect(() => {
    fetchItems()
  }, [category])

  const fetchItems = async () => {
    setLoading(true)
    try {
      const res = await api.get('/marketplace/items', {
        params: { category: category || undefined, search: search || undefined },
      })
      setItems(res.data)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => fetchItems()

  const categories = [
    { id: '', label: 'Todos', icon: <Package className="w-4 h-4" /> },
    { id: 'template', label: 'Templates', icon: <Tag className="w-4 h-4" /> },
    { id: 'app', label: 'Apps', icon: <Zap className="w-4 h-4" /> },
    { id: 'service', label: 'Servicios', icon: <Star className="w-4 h-4" /> },
    { id: 'digital_product', label: 'Digitales', icon: <TrendingUp className="w-4 h-4" /> },
  ]

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#060812]">
      <div className="max-w-6xl mx-auto px-6 py-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-brand-orange/10">
              <ShoppingBag className="w-6 h-6 text-brand-orange" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Marketplace</h1>
              <p className="text-sm text-white/50">Descubrí herramientas para potenciar tu negocio</p>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="flex gap-3 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              placeholder="Buscar templates, apps, servicios..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-white placeholder:text-white/30 text-sm focus:outline-none focus:border-brand-orange/50"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-6 py-3 rounded-xl bg-brand-orange text-white text-sm font-medium hover:bg-brand-orange/90 transition-colors"
          >
            Buscar
          </button>
        </div>

        {/* Categories */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setCategory(c.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                category === c.id
                  ? 'bg-brand-orange text-white'
                  : 'bg-white/[0.03] text-white/60 hover:bg-white/[0.06] hover:text-white/80'
              }`}
            >
              {c.icon}
              {c.label}
            </button>
          ))}
        </div>

        {/* Items Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20 text-white/40">
            <Package className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg">No se encontraron productos</p>
            <p className="text-sm">Probá con otra búsqueda o categoría</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map((item) => (
              <div
                key={item.id}
                className="group rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-hidden hover:border-white/[0.12] transition-colors"
              >
                <div className="aspect-video bg-white/[0.02] flex items-center justify-center relative">
                  {item.thumbnail_url ? (
                    <img src={item.thumbnail_url} alt={item.name} className="w-full h-full object-cover" />
                  ) : (
                    <Package className="w-10 h-10 text-white/10" />
                  )}
                  {item.is_featured && (
                    <span className="absolute top-3 left-3 px-2 py-1 rounded-md bg-brand-orange text-white text-[10px] font-bold uppercase tracking-wider">
                      Destacado
                    </span>
                  )}
                  {item.is_limited && (
                    <span className="absolute top-3 right-3 px-2 py-1 rounded-md bg-red-500/80 text-white text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {item.stock_remaining} restantes
                    </span>
                  )}
                </div>
                <div className="p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] uppercase tracking-wider text-white/40 font-medium">{item.category}</span>
                    {item.rating_count > 0 && (
                      <span className="flex items-center gap-1 text-[10px] text-yellow-400">
                        <Star className="w-3 h-3 fill-yellow-400" />
                        {item.rating_avg} ({item.rating_count})
                      </span>
                    )}
                  </div>
                  <h3 className="text-white font-semibold mb-1 group-hover:text-brand-orange transition-colors">{item.name}</h3>
                  <p className="text-sm text-white/50 mb-4 line-clamp-2">{item.short_description || 'Sin descripción'}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-baseline gap-2">
                      <span className="text-lg font-bold text-white">${item.price_usd}</span>
                      {item.compare_price_usd && (
                        <span className="text-sm text-white/30 line-through">${item.compare_price_usd}</span>
                      )}
                    </div>
                    <span className="text-xs text-white/30">{item.purchase_count} vendidos</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
