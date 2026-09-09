'use client'

/**
 * "Dónde vendés" — the account's real links, and the real state of each one.
 *
 * This is the input every other tool depends on: the SEO audit, the authority
 * cross-link report and the multi-platform seller all work on these exact URLs.
 * Status shown per link is never inferred — it is the last real HTTP response
 * (or the reason the page could not be read, e.g. a marketplace that blocks
 * server-side fetches).
 */

import React, { useCallback, useEffect, useState } from 'react'
import {
  AlertCircle, CheckCircle2, Globe, Loader2, Plus, RefreshCw, ShoppingBag, Store, Trash2,
} from 'lucide-react'
import {
  webPresenceApi, scoreColor,
  type BusinessLink, type LinkKind, type PlatformOption,
} from '@/lib/webPresence'

const KIND_ICON: Record<LinkKind, React.ReactNode> = {
  website: <Globe className="w-4 h-4" />,
  social: <Store className="w-4 h-4" />,
  marketplace: <ShoppingBag className="w-4 h-4" />,
  other: <Globe className="w-4 h-4" />,
}

const KIND_LABEL: Record<LinkKind, string> = {
  website: 'Web propia',
  social: 'Red social',
  marketplace: 'Marketplace',
  other: 'Otro',
}

interface Props {
  /** Called whenever the set of links changes, so the parent page can refresh
   *  whatever report it derives from them. */
  onChanged?: () => void
  compact?: boolean
}

export default function LinksManager({ onChanged, compact = false }: Props): React.JSX.Element {
  const [links, setLinks] = useState<BusinessLink[]>([])
  const [platforms, setPlatforms] = useState<PlatformOption[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [platform, setPlatform] = useState('own_site')
  const [url, setUrl] = useState('')
  const [adding, setAdding] = useState(false)

  const reload = useCallback(async (): Promise<void> => {
    try {
      setLinks(await webPresenceApi.listLinks())
      setError(null)
    } catch {
      setError('No se pudieron leer tus links. Iniciá sesión de nuevo si el problema sigue.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
    webPresenceApi.platforms().then(setPlatforms).catch(() => setPlatforms([]))
  }, [reload])

  const add = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!url.trim()) return
    setAdding(true)
    setError(null)
    try {
      const created = await webPresenceApi.addLink({
        platform,
        url: url.trim(),
        is_primary: links.length === 0,
      })
      setUrl('')
      await reload()
      onChanged?.()
      // Audit it right away: a link nobody fetched shows no real state at all.
      setBusy(created.id)
      await webPresenceApi.auditLink(created.id).catch(() => undefined)
      await reload()
      onChanged?.()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail || 'No se pudo guardar el link.')
    } finally {
      setAdding(false)
      setBusy(null)
    }
  }

  const auditOne = async (id: string): Promise<void> => {
    setBusy(id)
    try {
      await webPresenceApi.auditLink(id)
      await reload()
      onChanged?.()
    } finally {
      setBusy(null)
    }
  }

  const auditAll = async (): Promise<void> => {
    setBusy('all')
    try {
      setLinks(await webPresenceApi.auditAll())
      onChanged?.()
    } finally {
      setBusy(null)
    }
  }

  const remove = async (id: string): Promise<void> => {
    setBusy(id)
    try {
      await webPresenceApi.deleteLink(id)
      await reload()
      onChanged?.()
    } finally {
      setBusy(null)
    }
  }

  const statusLine = (link: BusinessLink): { text: string; tone: string } => {
    if (!link.last_checked_at) return { text: 'Sin analizar todavía', tone: 'text-slate-500' }
    if (link.fetch_error) return { text: link.fetch_error, tone: 'text-red-600' }
    if (link.http_status && link.http_status >= 400) {
      return { text: `Respondió HTTP ${link.http_status}`, tone: 'text-red-600' }
    }
    return {
      text: `HTTP ${link.http_status} · ${link.response_ms} ms${
        link.audit ? ` · ${link.audit.issues.length} hallazgos` : ''
      }`,
      tone: 'text-slate-600',
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      <div className="p-5 flex items-center justify-between flex-wrap gap-3 border-b border-slate-100">
        <div>
          <h2 className="font-semibold text-slate-900">Dónde vendés</h2>
          <p className="text-sm text-slate-600 mt-0.5">
            Tu web, tus redes y tus tiendas. Todo lo que analizamos sale de estas URLs reales.
          </p>
        </div>
        {links.length > 0 && (
          <button
            type="button"
            onClick={auditAll}
            disabled={busy !== null}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            {busy === 'all'
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <RefreshCw className="w-4 h-4" />}
            Analizar todo
          </button>
        )}
      </div>

      <form onSubmit={add} className="p-5 flex gap-2 flex-wrap items-start border-b border-slate-100">
        <select
          value={platform}
          onChange={e => setPlatform(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white text-slate-900"
        >
          {platforms.map(p => (
            <option key={p.platform} value={p.platform}>{p.label}</option>
          ))}
        </select>
        <input
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://mitienda.com o link de tu publicación"
          className="flex-1 min-w-[240px] px-3 py-2 rounded-lg border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400"
        />
        <button
          type="submit"
          disabled={adding || !url.trim()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50"
        >
          {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Agregar y analizar
        </button>
      </form>

      {error && (
        <div className="mx-5 mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 flex gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" /> {error}
        </div>
      )}

      {loading && (
        <div className="p-8 flex items-center justify-center gap-2 text-slate-500 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Leyendo tus links…
        </div>
      )}

      {!loading && links.length === 0 && (
        <div className="p-8 text-center">
          <p className="font-semibold text-slate-900">Todavía no cargaste ningún link</p>
          <p className="text-sm text-slate-600 mt-1 max-w-md mx-auto">
            Sin tus URLs reales no se puede auditar ni posicionar nada. Empezá por tu web (o tu
            tienda principal) y sumá tus redes y publicaciones.
          </p>
        </div>
      )}

      {!loading && links.length > 0 && (
        <ul className="divide-y divide-slate-100">
          {links.map(link => {
            const status = statusLine(link)
            return (
              <li key={link.id} className="p-5 flex items-start gap-3 flex-wrap">
                <span className="mt-0.5 w-8 h-8 rounded-lg bg-slate-100 text-slate-600 grid place-items-center shrink-0">
                  {KIND_ICON[link.kind]}
                </span>
                <div className="flex-1 min-w-[200px]">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-slate-900">{link.label || link.platform}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                      {KIND_LABEL[link.kind]}
                    </span>
                    {link.is_primary && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                        Principal
                      </span>
                    )}
                  </div>
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline break-all"
                  >
                    {link.url}
                  </a>
                  <p className={`text-xs mt-1 ${status.tone}`}>{status.text}</p>
                </div>

                {link.seo_score !== null && (
                  <div className="text-right shrink-0">
                    <p className={`text-2xl font-bold ${scoreColor(link.seo_score)}`}>
                      {link.seo_score}
                    </p>
                    <p className="text-[11px] text-slate-500">score SEO</p>
                  </div>
                )}
                {link.seo_score === null && link.last_checked_at && (
                  <span className="shrink-0 text-xs text-slate-500 max-w-[180px] text-right">
                    No se pudo leer la página
                  </span>
                )}

                {!compact && (
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={() => auditOne(link.id)}
                      disabled={busy !== null}
                      title="Volver a analizar"
                      className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 disabled:opacity-40"
                    >
                      {busy === link.id
                        ? <Loader2 className="w-4 h-4 animate-spin" />
                        : <RefreshCw className="w-4 h-4" />}
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(link.id)}
                      disabled={busy !== null}
                      title="Eliminar"
                      className="p-2 rounded-lg text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-40"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}

      {!loading && links.length > 0 && (
        <p className="px-5 py-3 text-xs text-slate-500 border-t border-slate-100 flex items-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          Cada score sale de descargar la página y leerla. Nada acá es una estimación.
        </p>
      )}
    </div>
  )
}
