'use client'

import { useState } from 'react'
import Button from '@/components/ui/Button'
import { harvey, type HarveyStatus } from '@/lib/api/harvey'
import { card, input, label, Notice, useAction } from './ui'

const PROVIDERS = [
  {
    id: 'brave' as const,
    name: 'Brave Search',
    field: 'brave_api_key' as const,
    has: 'has_brave_key' as const,
    help: 'Tiene un plan gratuito. Creás una clave en brave.com/search/api.',
  },
  {
    id: 'google' as const,
    name: 'Google Places',
    field: 'google_places_api_key' as const,
    has: 'has_google_key' as const,
    help: 'Requiere un proyecto de Google Cloud con facturación activa y "Places API (New)" habilitada.',
  },
]

/**
 * Where this business looks for prospects. Nothing here is paid by SellIA: each business brings its own search
 * key (or none, and pastes sites by hand). Keys are write-only: once saved they are never shown again.
 */
export function DiscoverySources({
  bid, status, onChange,
}: { bid: string; status: HarveyStatus; onChange: () => Promise<void> }) {
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const { busy, notice, run } = useAction()

  const save = (field: (typeof PROVIDERS)[number]['field'], value: string, provider?: 'brave' | 'google') =>
    run(
      field,
      () => harvey.setDiscoveryKeys(bid, { [field]: value, ...(provider ? { search_provider: provider } : {}) }),
      () => (value ? 'Clave guardada' : 'Clave quitada'),
    ).then(async (r) => {
      if (r) {
        setDrafts((d) => ({ ...d, [field]: '' }))
        await onChange()
      }
    })

  return (
    <section className={`${card} space-y-4`}>
      <div>
        <h2 className="font-semibold text-slate-900">Fuentes de prospectos</h2>
        <p className="mt-1 text-sm text-slate-600">
          Elegís cómo encontrar clientes. Siempre podés pegar sitios o cargar tu lista a mano, sin costo. Para que Harvey
          busque solo según tu cliente ideal, cargá tu propia clave de un buscador: es tuya y la pagás vos; SellIA no
          gasta nada por vos.
        </p>
      </div>

      {PROVIDERS.map((p) => (
        <div key={p.id} className="space-y-2 rounded-lg border border-slate-200 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-900">{p.name}</p>
            <span className={`text-xs font-semibold ${status[p.has] ? 'text-emerald-700' : 'text-slate-500'}`}>
              {status[p.has] ? 'Clave cargada' : 'Sin clave'}
              {status[p.has] && status.search_provider === p.id ? ' · en uso' : ''}
            </span>
          </div>
          <p className="text-xs text-slate-500">{p.help}</p>
          <label className={label} htmlFor={`key-${p.id}`}>{status[p.has] ? 'Reemplazar clave' : 'Tu clave'}</label>
          <input
            id={`key-${p.id}`}
            type="password"
            autoComplete="off"
            className={input}
            placeholder={status[p.has] ? '••••••••••••' : 'Pegá tu clave'}
            value={drafts[p.field] ?? ''}
            onChange={(e) => setDrafts((d) => ({ ...d, [p.field]: e.target.value }))}
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" isLoading={busy === p.field} disabled={!(drafts[p.field] ?? '').trim()}
              onClick={() => save(p.field, (drafts[p.field] ?? '').trim(), p.id)}>
              Guardar
            </Button>
            {status[p.has] && (
              <>
                {status.search_provider !== p.id && (
                  <Button size="sm" variant="secondary"
                    onClick={() => run('use', () => harvey.setDiscoveryKeys(bid, { search_provider: p.id }), () => `Se usa ${p.name}`).then(onChange)}>
                    Usar esta
                  </Button>
                )}
                <Button size="sm" variant="ghost" onClick={() => save(p.field, '')}>Quitar clave</Button>
              </>
            )}
          </div>
        </div>
      ))}
      <Notice notice={notice} />
    </section>
  )
}
