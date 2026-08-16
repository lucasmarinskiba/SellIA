'use client'

import { Plus, Eye, Edit2, Trash2 } from 'lucide-react'

export default function ListingsPage() {
  const listings = [
    { id: 'LST-001', product: 'iPhone 15 Pro', platform: 'Mercado Libre', price: '$999', stock: 12, views: 1234, rating: 4.8 },
    { id: 'LST-002', product: 'AirPods Pro', platform: 'Amazon', price: '$249', stock: 45, views: 856, rating: 4.6 },
    { id: 'LST-003', product: 'MacBook Air M3', platform: 'Hotmart', price: '$1,299', stock: 5, views: 432, rating: 4.9 },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-slate-900">Listings</h1>
          <p className="text-slate-600 mt-2">Gestiona tus productos en todas las plataformas</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">
          <Plus size={18} />
          Nuevo listing
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {listings.map((listing) => (
          <div key={listing.id} className="bg-white border border-slate-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-bold text-slate-900">{listing.product}</h3>
                <p className="text-xs text-slate-500 mt-1">{listing.platform}</p>
              </div>
              <div className="flex gap-2">
                <button className="p-2 hover:bg-slate-100 rounded"><Eye size={16} /></button>
                <button className="p-2 hover:bg-slate-100 rounded"><Edit2 size={16} /></button>
                <button className="p-2 hover:bg-slate-100 rounded"><Trash2 size={16} /></button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="bg-slate-50 p-2 rounded text-center">
                <p className="text-xs text-slate-600">Precio</p>
                <p className="font-bold">{listing.price}</p>
              </div>
              <div className="bg-slate-50 p-2 rounded text-center">
                <p className="text-xs text-slate-600">Stock</p>
                <p className="font-bold">{listing.stock}</p>
              </div>
              <div className="bg-slate-50 p-2 rounded text-center">
                <p className="text-xs text-slate-600">Rating</p>
                <p className="font-bold">⭐ {listing.rating}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
