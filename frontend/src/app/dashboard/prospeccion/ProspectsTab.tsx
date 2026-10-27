'use client'

import { useCallback, useEffect, useState } from 'react'
import { Globe, PenLine, Plus, Search, ShieldCheck } from 'lucide-react'
import Button from '@/components/ui/Button'
import {
  errMsg, harvey, type DiscoverResult, type HarveyProspect, type HarveyStatus, type ProspectIn,
} from '@/lib/api/harvey'
import { Badge, card, input, label, lines, Notice, useAction } from './ui'

/** "email, nombre, empresa" per line. */
const parseList = (text: string): ProspectIn[] =>
  lines(text).map((line) => {
    const [email, first_name = '', company = ''] = line.split(',').map((p) => p.trim())
    return { email, first_name, company }
  })

const OUTCOME: Record<string, string> = {
  added: 'agregado',
  skipped: 'omitido',
  exists: 'ya estaba',
  no_email: 'sin email público',
  error: 'no se pudo leer',
}

export function ProspectsTab({
  bid, status, onChange,
}: { bid: string; status: HarveyStatus; onChange: () => Promise<void> }) {
  const [prospects, setProspects] = useState<HarveyProspect[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [manual, setManual] = useState('')
  const [urls, setUrls] = useState('')
  const [found, setFound] = useState<DiscoverResult | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const { busy, notice, run } = useAction()

  const load = useCallback(async () => {
    try {
      setProspects(await harvey.prospects(bid))
      setLoadError(null)
    } catch (e) {
      setLoadError(errMsg(e))
    }
  }, [bid])

  useEffect(() => {
    void load()
  }, [load])

  const refreshAll = async () => {
    await load()
    await onChange()
  }

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const verify = (verified: boolean) =>
    run('verify', () => harvey.verify(bid, [...selected], verified), (r) => `${r.counts.updated} actualizados`).then(
      async () => {
        setSelected(new Set())
        await refreshAll()
      },
    )

  const unverified = prospects.filter((p) => p.email_status === 'scraped')

  return (
    <div className="space-y-5">
      <section className={`${card} space-y-3`}>
        <h2 className="flex items-center gap-2 font-semibold text-slate-900">
          <Globe className="h-4 w-4" /> Descubrir prospectos
        </h2>
        <p className="text-sm text-slate-500">
          Pegá sitios web de negocios (uno por línea). Leemos solo lo público, respetamos robots.txt y guardamos el email
          de contacto que publican. Antes de escribirles tenés que verificarlo.
        </p>
        <textarea
          className={`${input} min-h-[90px]`}
          placeholder={'panaderiasol.com\nlodemarta.com.ar'}
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
          aria-label="Sitios web"
        />
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" leftIcon={<Search className="h-4 w-4" />} isLoading={busy === 'discover'} disabled={!lines(urls).length}
            onClick={() =>
              run('discover', () => harvey.discover(bid, { urls: lines(urls), queries: [] }), (r) => `Nuevos: ${r.counts.created ?? 0}`)
                .then((r) => { if (r) setFound(r) })
                .then(refreshAll)
            }>
            Leer estos sitios
          </Button>
          <Button size="sm" variant="secondary" isLoading={busy === 'search'} disabled={!status.search_available}
            title={status.search_available ? undefined : 'Cargá tu propia clave de búsqueda en Configuración → Fuentes de prospectos'}
            onClick={() =>
              run('search', () => harvey.discover(bid, { urls: [], queries: [] }), (r) => `Nuevos: ${r.counts.created ?? 0}`)
                .then((r) => { if (r) setFound(r) })
                .then(refreshAll)
            }>
            Buscar según mi cliente ideal
          </Button>
          <span className="text-xs text-slate-500">Hoy: {status.discovered_today} descubiertos</span>
        </div>
        {found && (
          <ul className="space-y-1 text-sm">
            {found.sites.map((s) => (
              <li key={s.url} className="flex flex-wrap gap-2 text-slate-600">
                <span className="font-medium text-slate-900">{s.url}</span>
                <span className="text-slate-500">{OUTCOME[s.outcome] ?? s.outcome}</span>
                {s.detail && <span className="text-slate-500">{s.detail}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className={`${card} space-y-3`}>
        <h2 className="flex items-center gap-2 font-semibold text-slate-900">
          <Plus className="h-4 w-4" /> Cargar mi lista
        </h2>
        <label className={label} htmlFor="manual-list">email, nombre, empresa (uno por línea)</label>
        <textarea id="manual-list" className={`${input} min-h-[90px]`} placeholder="ana@cliente.com, Ana, Cliente SA"
          value={manual} onChange={(e) => setManual(e.target.value)} />
        <Button size="sm" isLoading={busy === 'add'} disabled={!lines(manual).length}
          onClick={() =>
            run('add', () => harvey.addProspects(bid, parseList(manual)),
              (r) => `${r.created.length} agregados${r.skipped.length ? `, ${r.skipped.length} omitidos` : ''}`)
              .then((r) => { if (r) setManual('') })
              .then(refreshAll)
          }>
          Agregar
        </Button>
        <div className="border-t border-slate-200 pt-3">
          <p className="mb-2 text-sm text-slate-600">
            ¿La tenés en una planilla? Importá un <strong>CSV</strong> con una columna <code>email</code> (y, si querés,
            <code> name, company, website, title</code>). Hasta 1000 filas.
          </p>
          <input
            type="file"
            accept=".csv,text/csv"
            aria-label="Importar CSV de contactos"
            disabled={busy === 'csv'}
            className="block text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
            onChange={(e) => {
              const file = e.target.files?.[0]
              e.target.value = ''
              if (!file) return
              void run('csv', () => harvey.importCsv(bid, file), (r) =>
                `${r.created} importados${r.skipped.length ? `, ${r.skipped.length} omitidos` : ''}${r.rejected.length ? `, ${r.rejected.length} filas con problemas (ej.: fila ${r.rejected[0].row}: ${r.rejected[0].reason})` : ''}`,
              ).then(refreshAll)
            }}
          />
        </div>
      </section>

      <Notice notice={notice} />
      {loadError && <p className="text-sm text-red-700">{loadError}</p>}

      {unverified.length > 0 && (
        <p className="text-sm text-amber-700">
          {unverified.length} email(s) encontrados sin verificar: confirmalos antes de redactar.
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" leftIcon={<ShieldCheck className="h-4 w-4" />} disabled={!selected.size}
          isLoading={busy === 'verify'} onClick={() => verify(true)}>
          Verificar seleccionados
        </Button>
        <Button size="sm" variant="ghost" disabled={!selected.size} onClick={() => verify(false)}>
          Descartar seleccionados
        </Button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-white text-xs uppercase text-slate-500">
            <tr>
              <th className="p-3" />
              <th className="p-3">Email</th>
              <th className="p-3">Empresa</th>
              <th className="p-3">Email</th>
              <th className="p-3">Estado</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {prospects.map((p) => (
              <tr key={p.id} className="border-t border-slate-200 text-slate-700">
                <td className="p-3">
                  {(p.email_status === 'scraped' || p.email_status === 'verified') && (
                    <input type="checkbox" checked={selected.has(p.id)} onChange={() => toggle(p.id)} aria-label={`Elegir ${p.email}`} />
                  )}
                </td>
                <td className="p-3">
                  {p.email}
                  {p.source === 'discovery' && p.source_url && (
                    <a href={p.source_url} target="_blank" rel="noopener noreferrer" className="ml-2 text-xs text-slate-500 underline">
                      origen
                    </a>
                  )}
                </td>
                <td className="p-3">{p.company || '—'}</td>
                <td className="p-3"><Badge value={p.email_status} /></td>
                <td className="p-3"><Badge value={p.status} /></td>
                <td className="p-3 text-right">
                  {p.status === 'new' && ['provided', 'verified'].includes(p.email_status) && (
                    <Button size="sm" variant="secondary" leftIcon={<PenLine className="h-4 w-4" />} isLoading={busy === p.id}
                      onClick={() => run(p.id, () => harvey.draft(bid, p.id, 1), () => 'Borrador listo en Aprobación').then(refreshAll)}>
                      Redactar
                    </Button>
                  )}
                </td>
              </tr>
            ))}
            {prospects.length === 0 && (
              <tr>
                <td colSpan={6} className="p-6 text-center text-slate-500">Todavía no hay prospectos.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
