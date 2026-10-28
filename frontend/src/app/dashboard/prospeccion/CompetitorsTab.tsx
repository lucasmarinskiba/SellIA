'use client'

import { useCallback, useEffect, useState } from 'react'
import { Loader2, Sparkles, Trash2 } from 'lucide-react'
import Button from '@/components/ui/Button'
import { harvey, type Competitor, type CompetitorKind, type CompetitiveBrief } from '@/lib/api/harvey'
import { card, fmtDate, input, label, Notice, useAction } from './ui'

const KINDS: { value: CompetitorKind; label: string; hint: string }[] = [
  { value: 'direct', label: 'Compite conmigo', hint: 'Vende lo mismo a los mismos clientes' },
  { value: 'indirect', label: 'Lo resuelve distinto', hint: 'Otra forma de cubrir la misma necesidad' },
  { value: 'own', label: 'Mi propio sitio', hint: 'Para compararme con ellos en igualdad' },
]
const KIND_LABEL: Record<CompetitorKind, string> = { direct: 'Compite conmigo', indirect: 'Lo resuelve distinto', own: 'Mi sitio' }

const BriefList = ({ title, items }: { title: string; items?: string[] }) =>
  items && items.length > 0 ? (
    <div>
      <h3 className="mb-1 text-sm font-semibold text-slate-900">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
        {items.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
    </div>
  ) : null

/**
 * The business's market map: the sites it studies (competitors and its own), what they publish, and a comparison.
 * Everything shown was read from public pages; the "angles" are what Harvey may use when drafting emails.
 */
export function CompetitorsTab({ bid }: { bid: string }) {
  const [list, setList] = useState<Competitor[]>([])
  const [brief, setBrief] = useState<CompetitiveBrief | null>(null)
  const [loading, setLoading] = useState(true)
  const [url, setUrl] = useState('')
  const [kind, setKind] = useState<CompetitorKind>('direct')
  const { busy, notice, run } = useAction()

  const load = useCallback(async () => {
    try {
      const [l, b] = await Promise.all([harvey.competitors(bid), harvey.competitiveBrief(bid)])
      setList(l)
      setBrief(b)
    } catch {
      /* the action notices report failures; an empty map is a valid state */
    } finally {
      setLoading(false)
    }
  }, [bid])

  useEffect(() => {
    void load()
  }, [load])

  const add = () =>
    run('add', () => harvey.addCompetitor(bid, { url: url.trim(), kind }), (c) => `Agregado: ${c.url.replace(/^https?:\/\//, '')}`).then(
      async (r) => {
        if (r) {
          setUrl('')
          await load()
        }
      },
    )

  const analyze = () =>
    run('analyze', () => harvey.analyzeCompetitors(bid), () => 'Listo: leímos los sitios y actualizamos la comparación.').then(load)

  const hasBrief = !!brief && Object.keys(brief.brief).length > 0
  const b = brief?.brief

  return (
    <div className="space-y-5">
      <section className={`${card} space-y-3`}>
        <div>
          <h2 className="font-semibold text-slate-900">Tu mercado</h2>
          <p className="mt-1 text-sm text-slate-600">
            Pegá la web de quienes te compiten (y la tuya). Leemos solo lo que publican abierto —precios, ofertas y
            titulares— y lo comparamos con lo que ofrecés. Harvey usa esas diferencias para escribir mejor, sin nombrar
            nunca a nadie.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
          <div>
            <label className={label} htmlFor="comp-url">Web</label>
            <input
              id="comp-url"
              className={input}
              placeholder="www.otrapanaderia.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && url.trim() && void add()}
            />
          </div>
          <div className="flex items-end">
            <Button isLoading={busy === 'add'} disabled={!url.trim()} onClick={() => void add()}>
              Agregar
            </Button>
          </div>
        </div>
        <fieldset className="flex flex-wrap gap-2">
          <legend className="sr-only">Tipo de sitio</legend>
          {KINDS.map((k) => (
            <label
              key={k.value}
              title={k.hint}
              className={`cursor-pointer rounded-full px-3 py-1.5 text-sm ring-1 ring-inset ${
                kind === k.value ? 'bg-primary text-primary-foreground ring-primary' : 'bg-white text-slate-700 ring-slate-300'
              }`}
            >
              <input type="radio" className="sr-only" name="comp-kind" checked={kind === k.value} onChange={() => setKind(k.value)} />
              {k.label}
            </label>
          ))}
        </fieldset>
        <Notice notice={notice} />
      </section>

      {loading ? (
        <div className="flex h-24 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : list.length === 0 ? (
        <p className={`${card} text-sm text-slate-600`}>
          Todavía no cargaste ningún sitio. Empezá con tu competidor más cercano: con uno ya podemos compararte.
        </p>
      ) : (
        <>
          <section className="space-y-3">
            {list.map((c) => (
              <article key={c.id} className={`${card} space-y-2`}>
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-slate-900">{c.name || c.url}</p>
                    <p className="truncate text-xs text-slate-500">
                      {KIND_LABEL[c.kind]} · {c.url.replace(/^https?:\/\//, '')} · leído: {fmtDate(c.last_scanned_at)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" isLoading={busy === `scan-${c.id}`}
                      onClick={() => run(`scan-${c.id}`, () => harvey.scanCompetitor(bid, c.id), () => 'Sitio leído').then(load)}>
                      Leer de nuevo
                    </Button>
                    <button
                      type="button"
                      aria-label={`Quitar ${c.name || c.url}`}
                      className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
                      onClick={() => run(`del-${c.id}`, () => harvey.deleteCompetitor(bid, c.id), () => 'Quitado').then(load)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                {c.last_error && <p className="text-sm text-amber-700">No pudimos leerlo: {c.last_error}</p>}
                {c.snapshot.prices && c.snapshot.prices.length > 0 && (
                  <details className="text-sm text-slate-700">
                    <summary className="cursor-pointer font-medium">
                      Qué publica ({c.snapshot.prices.length} precios, {c.snapshot.offers?.length ?? 0} ofertas)
                    </summary>
                    <ul className="mt-2 list-disc space-y-1 pl-5">
                      {[...(c.snapshot.prices ?? []), ...(c.snapshot.offers ?? [])].slice(0, 12).map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </article>
            ))}
          </section>

          <section className={`${card} space-y-4`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-semibold text-slate-900">Comparación</h2>
              <Button isLoading={busy === 'analyze'} onClick={() => void analyze()}>
                <Sparkles className="mr-1 h-4 w-4" /> {hasBrief ? 'Actualizar análisis' : 'Analizar mi mercado'}
              </Button>
            </div>
            {hasBrief && b ? (
              <>
                {b.summary && <p className="text-sm text-slate-700">{b.summary}</p>}
                <BriefList title="Dónde estás atrás" items={b.gaps} />
                <BriefList title="Oportunidades" items={b.opportunities} />
                <BriefList title="Lo que Harvey va a destacar en sus emails" items={b.angles} />
                <BriefList title="A qué clientes conviene apuntar" items={b.icp_hints} />
                <p className="text-xs text-slate-500">Actualizado: {fmtDate(brief?.generated_at ?? null)}</p>
              </>
            ) : (
              <p className="text-sm text-slate-600">
                Cuando analices, vas a ver acá en qué se diferencian y qué podés aprovechar.
              </p>
            )}
          </section>
        </>
      )}
    </div>
  )
}

