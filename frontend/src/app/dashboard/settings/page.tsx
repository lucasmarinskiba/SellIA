'use client'

import { Save, Shield, Bell, Users } from 'lucide-react'
import { useState } from 'react'

export default function SettingsPage() {
  const [seller, setSeller] = useState('Juan Pérez')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900">Configuración</h1>
        <p className="text-slate-600 mt-2">Personaliza tu cuenta y preferencias</p>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Users size={20} />
          Perfil
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
            <input
              type="text"
              value={seller}
              onChange={(e) => setSeller(e.target.value)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold">
        <Save size={18} />
        Guardar cambios
      </button>
    </div>
  )
}
