'use client'

/**
 * The configuration screen: who this seller is, where they sell, in what
 * languages, and how the AI should sound for them.
 *
 * Every option list comes from the backend, so a value the API would reject can
 * never appear in a dropdown. The platform suggestions carry reasons instead of
 * a score, because nothing here has been measured — they are matches between
 * what the seller declared and where each platform operates.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Check, Globe, Languages, Loader2, Plus, Save, Sparkles, Store, Target, X,
} from 'lucide-react'
import { logger } from '@/lib/logger'
import {
  preferencesApi,
  type PreferencesCatalog,
  type PlatformSuggestion,
  type SellerProfile,
} from '@/lib/preferences'

const Chips = ({
  items, onRemove, onAdd, placeholder,
}: {
  items: string[]
  onRemove: (item: string) => void
  onAdd: (item: string) => void
  placeholder: string
}): React.JSX.Element => {
  const [draft, setDraft] = useState('')
  const submit = (): void => {
    const value = draft.trim()
    if (value) { onAdd(value); setDraft('') }
  }
  return (
    <div>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {items.length === 0 && <span className="text-xs text-white/25">Todavía no agregaste ninguno</span>}
        {items.map(item => (
          <span key={item} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.07] text-xs text-white/80">
            {item}
            <button onClick={() => onRemove(item)} aria-label={`Quitar ${item}`} className="hover:text-white">
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); submit() } }}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 rounded-lg bg-white/[0.05] border border-white/[0.08] text-sm text-white placeholder:text-white/25 focus:outline-none focus:ring-1 focus:ring-brand-orange"
        />
        <button onClick={submit} className="px-3 py-2 rounded-lg bg-white/[0.08] hover:bg-white/[0.14] text-white/70" aria-label="Agregar">
          <Plus className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

const Field = ({ label, hint, children }: {
  label: string
  hint?: string
  children: React.ReactNode
}): React.JSX.Element => (
  <div>
    <label className="block text-xs text-white/50 mb-1.5">{label}</label>
    {children}
    {hint && <p className="text-[10px] text-white/25 mt-1">{hint}</p>}
  </div>
)

const inputClass =
  'w-full px-3 py-2 rounded-lg bg-white/[0.05] border border-white/[0.08] text-sm text-white placeholder:text-white/25 focus:outline-none focus:ring-1 focus:ring-brand-orange'

const SellerPreferences = (): React.JSX.Element => {
  const [profile, setProfile] = useState<SellerProfile | null>(null)
  const [catalog, setCatalog] = useState<PreferencesCatalog | null>(null)
  const [businessId, setBusinessId] = useState<string | null>(null)
  const [hasBusiness, setHasBusiness] = useState(true)
  const [suggestions, setSuggestions] = useState<PlatformSuggestion[]>([])
  const [connected, setConnected] = useState<string[]>([])
  const [unknowns, setUnknowns] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [dirty, setDirty] = useState(false)

  const load = useCallback(async (): Promise<void> => {
    setLoading(true)
    try {
      const data = await preferencesApi.get()
      setProfile(data.profile)
      setCatalog(data.catalog)
      setBusinessId(data.business_id)
      setHasBusiness(data.has_business)
      if (data.has_business) {
        const sug = await preferencesApi.suggestions()
        setSuggestions(sug.suggestions)
        setConnected(sug.connected)
        setUnknowns(sug.unknowns)
      }
    } catch (e) {
      logger.error(String(e))
      setMessage('No se pudo cargar tu configuración')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { void load() }, [load])

  const patch = (changes: Partial<SellerProfile>): void => {
    setProfile(prev => (prev ? { ...prev, ...changes } : prev))
    setDirty(true)
  }

  const toggleInList = (key: 'target_platforms' | 'languages' | 'markets', value: string): void => {
    if (!profile) return
    const current = profile[key]
    patch({ [key]: current.includes(value) ? current.filter(v => v !== value) : [...current, value] } as Partial<SellerProfile>)
  }

  const save = async (): Promise<void> => {
    if (!profile) return
    setSaving(true)
    setMessage('')
    try {
      const { completeness, ...rest } = profile
      void completeness
      const result = await preferencesApi.update(rest, businessId || undefined)
      setProfile(result.profile)
      setDirty(false)
      setMessage('Configuración guardada')
      const sug = await preferencesApi.suggestions(businessId || undefined)
      setSuggestions(sug.suggestions)
      setConnected(sug.connected)
      setUnknowns(sug.unknowns)
      setTimeout(() => setMessage(''), 3000)
    } catch (e) {
      logger.error(String(e))
      setMessage('No se pudo guardar')
    } finally {
      setSaving(false)
    }
  }

  const platformsByKind = useMemo(() => {
    const groups: Record<string, PreferencesCatalog['platforms']> = {}
    ;(catalog?.platforms ?? []).forEach(p => {
      groups[p.kind] = [...(groups[p.kind] || []), p]
    })
    return groups
  }, [catalog])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-white/30 text-sm">
        <Loader2 className="w-4 h-4 animate-spin mr-2" /> Cargando tu configuración…
      </div>
    )
  }

  if (!profile || !catalog) {
    return <p className="text-sm text-white/40">{message || 'No se pudo cargar tu configuración'}</p>
  }

  if (!hasBusiness) {
    return (
      <div className="p-6 rounded-2xl border border-white/[0.08] text-center">
        <Store className="w-8 h-8 text-white/15 mx-auto mb-3" />
        <p className="text-sm text-white/50">Creá tu negocio para poder configurarlo.</p>
      </div>
    )
  }

  const KIND_LABELS: Record<string, string> = {
    marketplace: 'Marketplaces',
    own_store: 'Tienda propia',
    social: 'Redes sociales',
    messaging: 'Mensajería',
  }

  return (
    <div className="space-y-6">
      {/* Completeness — counts only the fields that change what the AI does */}
      <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-white">
            Perfil {profile.completeness.percent}% completo
            <span className="text-white/30 text-xs ml-2">
              {profile.completeness.filled} de {profile.completeness.total} datos que cambian cómo vende la IA
            </span>
          </p>
          <button
            onClick={() => void save()}
            disabled={saving || !dirty}
            className="px-4 py-2 rounded-lg bg-brand-orange/15 border border-brand-orange/30 text-brand-orange text-sm flex items-center gap-2 disabled:opacity-40"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            {dirty ? 'Guardar cambios' : 'Guardado'}
          </button>
        </div>
        <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
          <div className="h-full bg-brand-orange/70 transition-all" style={{ width: `${profile.completeness.percent}%` }} />
        </div>
        {profile.completeness.missing.length > 0 && (
          <p className="text-[11px] text-white/35 mt-2">
            Falta: {profile.completeness.missing.map(m => m.label).join(' · ')}
          </p>
        )}
        {message && <p className="text-xs text-brand-orange mt-2">{message}</p>}
      </div>

      {/* Negocio */}
      <section className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-4">
        <h3 className="text-sm font-medium text-white flex items-center gap-2">
          <Store className="w-4 h-4 text-brand-orange" /> Tu negocio
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Tipo de negocio">
            <select value={profile.business_type || ''} onChange={e => patch({ business_type: e.target.value || null })} className={inputClass}>
              <option value="" className="bg-[#0A0E1A]">Sin especificar</option>
              {catalog.business_types.map(t => (
                <option key={t.value} value={t.value} className="bg-[#0A0E1A]">{t.label}</option>
              ))}
            </select>
          </Field>
          <Field label="Modelo de venta">
            <select value={profile.sales_model || ''} onChange={e => patch({ sales_model: e.target.value || null })} className={inputClass}>
              <option value="" className="bg-[#0A0E1A]">Sin especificar</option>
              {catalog.sales_models.map(m => (
                <option key={m.value} value={m.value} className="bg-[#0A0E1A]">{m.label}</option>
              ))}
            </select>
          </Field>
          <Field label="Nicho" hint="Lo más específico posible: “indumentaria femenina de autor”, no “ropa”.">
            <input value={profile.niche || ''} onChange={e => patch({ niche: e.target.value })} placeholder="Tu nicho" className={inputClass} />
          </Field>
          <Field label="A quién le vendés">
            <input value={profile.target_audience || ''} onChange={e => patch({ target_audience: e.target.value })} placeholder="Mujeres 25-40, clase media-alta…" className={inputClass} />
          </Field>
          <Field label="Por qué te compran a vos" hint="La IA lo usa para responder “¿por qué vos y no otro?”.">
            <input value={profile.value_proposition || ''} onChange={e => patch({ value_proposition: e.target.value })} placeholder="Tu propuesta de valor" className={inputClass} />
          </Field>
          <Field label="Rango de precio">
            <select value={profile.price_range || ''} onChange={e => patch({ price_range: e.target.value || null })} className={inputClass}>
              <option value="" className="bg-[#0A0E1A]">Sin especificar</option>
              {catalog.price_ranges.map(p => (
                <option key={p.value} value={p.value} className="bg-[#0A0E1A]">{p.label}</option>
              ))}
            </select>
          </Field>
          <Field label="Qué querés lograr">
            <select value={profile.primary_goal || ''} onChange={e => patch({ primary_goal: e.target.value || null })} className={inputClass}>
              <option value="" className="bg-[#0A0E1A]">Sin especificar</option>
              {catalog.goals.map(g => (
                <option key={g.value} value={g.value} className="bg-[#0A0E1A]">{g.label}</option>
              ))}
            </select>
          </Field>
          <Field label="Ciudad">
            <input value={profile.city || ''} onChange={e => patch({ city: e.target.value })} placeholder="Dónde estás" className={inputClass} />
          </Field>
        </div>
      </section>

      {/* Idiomas y mercados */}
      <section className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-4">
        <h3 className="text-sm font-medium text-white flex items-center gap-2">
          <Languages className="w-4 h-4 text-brand-orange" /> Idiomas y mercados
        </h3>
        <Field label="Idiomas en los que vendés" hint="El bot responde en el idioma del comprador cuando es uno de estos.">
          <div className="flex flex-wrap gap-1.5">
            {catalog.languages.map(lang => {
              const active = profile.languages.includes(lang.code)
              return (
                <button
                  key={lang.code}
                  onClick={() => toggleInList('languages', lang.code)}
                  className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                    active ? 'bg-brand-orange/15 border-brand-orange/40 text-brand-orange' : 'bg-white/5 border-white/10 text-white/50 hover:text-white/80'
                  }`}
                >
                  {active && <Check className="w-3 h-3 inline mr-1" />}{lang.label}
                </button>
              )
            })}
          </div>
        </Field>
        <Field label="Idioma principal">
          <select value={profile.primary_language} onChange={e => patch({ primary_language: e.target.value })} className={`${inputClass} md:w-64`}>
            {catalog.languages.map(l => (
              <option key={l.code} value={l.code} className="bg-[#0A0E1A]">{l.label}</option>
            ))}
          </select>
        </Field>
        <Field label="Países donde vendés" hint="Define qué marketplaces tienen sentido y cómo se calculan los envíos.">
          <div className="flex flex-wrap gap-1.5">
            {catalog.markets.map(market => {
              const active = profile.markets.includes(market.code)
              return (
                <button
                  key={market.code}
                  onClick={() => toggleInList('markets', market.code)}
                  className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                    active ? 'bg-brand-orange/15 border-brand-orange/40 text-brand-orange' : 'bg-white/5 border-white/10 text-white/50 hover:text-white/80'
                  }`}
                >
                  {active && <Check className="w-3 h-3 inline mr-1" />}{market.label}
                </button>
              )
            })}
          </div>
        </Field>
        <Field label="Moneda que querés ver primero" hint="Solo elige qué total encabeza los tableros. Nunca convierte entre monedas.">
          <input
            value={profile.display_currency || ''}
            onChange={e => patch({ display_currency: e.target.value.toUpperCase().slice(0, 3) })}
            placeholder="ARS"
            className={`${inputClass} md:w-32 uppercase`}
          />
        </Field>
      </section>

      {/* Plataformas */}
      <section className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-4">
        <h3 className="text-sm font-medium text-white flex items-center gap-2">
          <Globe className="w-4 h-4 text-brand-orange" /> Dónde querés vender
        </h3>
        {Object.entries(platformsByKind).map(([kind, platforms]) => (
          <div key={kind}>
            <p className="text-[10px] uppercase tracking-wide text-white/30 mb-1.5">{KIND_LABELS[kind] || kind}</p>
            <div className="flex flex-wrap gap-1.5">
              {platforms.map(platform => {
                const active = profile.target_platforms.includes(platform.value)
                const isConnected = connected.includes(platform.value)
                return (
                  <button
                    key={platform.value}
                    onClick={() => toggleInList('target_platforms', platform.value)}
                    title={`${platform.note}${platform.capabilities.length ? ` · Automatiza: ${platform.capabilities.join(', ')}` : ' · Sin integración todavía'}`}
                    className={`px-2.5 py-1 rounded-lg text-xs border transition-colors ${
                      active ? 'bg-brand-orange/15 border-brand-orange/40 text-brand-orange' : 'bg-white/5 border-white/10 text-white/50 hover:text-white/80'
                    }`}
                  >
                    {active && <Check className="w-3 h-3 inline mr-1" />}
                    {platform.label}
                    {isConnected && <span className="ml-1 text-emerald-400" title="Ya conectada">•</span>}
                  </button>
                )
              })}
            </div>
          </div>
        ))}

        <div className="pt-2 border-t border-white/[0.06]">
          <p className="text-xs text-white/50 flex items-center gap-1.5 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-brand-orange" /> Plataformas afines a lo que configuraste
          </p>
          {suggestions.length === 0 ? (
            <p className="text-xs text-white/30">
              {unknowns.length
                ? 'Completá rubro y países para que esto tenga con qué comparar.'
                : 'Ya estás en todas las que encajan con tu perfil.'}
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {suggestions.map(s => (
                <div key={s.platform} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-white">{s.label}</p>
                    <button
                      onClick={() => toggleInList('target_platforms', s.platform)}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-white/10 text-white/60 hover:text-white"
                    >
                      {profile.target_platforms.includes(s.platform) ? 'En tu lista' : 'Agregar'}
                    </button>
                  </div>
                  <p className="text-[11px] text-white/40 mt-0.5">{s.note}</p>
                  <ul className="mt-1.5 space-y-0.5">
                    {s.reasons.map(reason => (
                      <li key={reason} className="text-[11px] text-white/55">· {reason}</li>
                    ))}
                  </ul>
                  <p className="text-[10px] text-white/30 mt-1.5">
                    {s.capabilities.length
                      ? `SellIA automatiza acá: ${s.capabilities.join(', ')}`
                      : 'Todavía sin integración: tendrías que operarla por fuera.'}
                  </p>
                </div>
              ))}
            </div>
          )}
          {unknowns.map(note => (
            <p key={note} className="text-[11px] text-amber-200/70 mt-2">{note}</p>
          ))}
        </div>
      </section>

      {/* Gustos y voz */}
      <section className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-4">
        <h3 className="text-sm font-medium text-white flex items-center gap-2">
          <Target className="w-4 h-4 text-brand-orange" /> Tus gustos y tu voz
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Field label="Cómo querés sonar">
            <select value={profile.tone} onChange={e => patch({ tone: e.target.value })} className={inputClass}>
              {catalog.tones.map(t => (
                <option key={t.value} value={t.value} className="bg-[#0A0E1A]">{t.label}</option>
              ))}
            </select>
            <p className="text-[10px] text-white/25 mt-1">
              {catalog.tones.find(t => t.value === profile.tone)?.detail}
            </p>
          </Field>
          <Field label="La IA responde sola">
            <button
              onClick={() => patch({ autonomous_replies: !profile.autonomous_replies })}
              className={`px-3 py-2 rounded-lg text-sm border w-full text-left ${
                profile.autonomous_replies
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-white/5 border-white/10 text-white/50'
              }`}
            >
              {profile.autonomous_replies ? 'Sí, contesta sin esperarte' : 'No, primero lo leés vos'}
            </button>
          </Field>
        </div>
        <Field label="Gustos y referencias" hint="Estilo que te gusta, marcas que admirás, cómo te gusta que te vendan a vos.">
          <Chips
            items={profile.tastes}
            onAdd={item => patch({ tastes: [...profile.tastes, item] })}
            onRemove={item => patch({ tastes: profile.tastes.filter(t => t !== item) })}
            placeholder="Diseño minimalista, trato directo…"
          />
        </Field>
        <Field label="Temas que te interesan">
          <Chips
            items={profile.interests}
            onAdd={item => patch({ interests: [...profile.interests, item] })}
            onRemove={item => patch({ interests: profile.interests.filter(t => t !== item) })}
            placeholder="SEO, automatización, packaging…"
          />
        </Field>
        <Field label="Lo que la IA nunca debe decir" hint="Promesas, comparaciones o temas que no querés que aparezcan en tu nombre.">
          <Chips
            items={profile.banned_topics}
            onAdd={item => patch({ banned_topics: [...profile.banned_topics, item] })}
            onRemove={item => patch({ banned_topics: profile.banned_topics.filter(t => t !== item) })}
            placeholder="Descuentos sin autorizar, política…"
          />
        </Field>
        <Field label="Instrucciones de voz">
          <textarea
            value={profile.voice_notes || ''}
            onChange={e => patch({ voice_notes: e.target.value })}
            rows={3}
            placeholder="Tuteo siempre. Nunca prometas plazos de envío. Firmá como el equipo, no como una persona."
            className={inputClass}
          />
        </Field>
      </section>

      <div className="flex justify-end">
        <button
          onClick={() => void save()}
          disabled={saving || !dirty}
          className="px-5 py-2.5 rounded-xl bg-brand-orange/15 border border-brand-orange/30 text-brand-orange text-sm flex items-center gap-2 disabled:opacity-40"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Guardar configuración
        </button>
      </div>
    </div>
  )
}

export default SellerPreferences
