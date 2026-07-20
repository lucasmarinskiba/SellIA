'use client'

/**
 * BUSINESS PROFILE WIZARD
 *
 * Cuestionario obligatorio + carga de links reales (plataformas de venta,
 * de anuncios, redes sociales). Persiste en localStorage y, si hay sesión,
 * en el backend (Business.config JSONB). Alimenta el cerebro/mapa/Computer Use.
 */

import { useState } from 'react'
import { X, ArrowRight, ArrowLeft, Check, ExternalLink, Sparkles } from 'lucide-react'
import { SELLIA } from '@/lib/sellia-theme'
import {
  type BusinessProfile, type LinkEntry, type CustomLink, type CustomLinkType,
  GOALS, CHANNELS, emptyProfile, loadProfile, saveProfile, validateLink, isComplete,
  detectLinkType, labelFromUrl,
} from '@/lib/business-profile'

interface Props { open: boolean; onClose: () => void; onSaved: (p: BusinessProfile) => void }

const T = SELLIA
const STEP_TITLES = [
  'Qué vendés', 'Qué ofrecés', 'Plataformas de venta', 'Dónde te anunciás',
  'Contenido / redes', 'Otros links', 'Atención', 'Resumen',
]
const LAST = STEP_TITLES.length - 1

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '9px 11px', borderRadius: 8, background: T.bg,
  border: `1px solid ${T.border}`, color: T.text, fontSize: 13, outline: 'none',
  fontFamily: T.sans, boxSizing: 'border-box',
}
const labelStyle: React.CSSProperties = { fontSize: 12, color: T.text2, marginBottom: 5, display: 'block', fontWeight: 600 }

const Chip = ({ on, label, onClick }: { on: boolean; label: string; onClick: () => void }): React.JSX.Element => (
  <button type="button" onClick={onClick} style={{
    padding: '6px 12px', borderRadius: 100, fontSize: 12, fontWeight: 600, cursor: 'pointer',
    fontFamily: T.sans, border: `1px solid ${on ? T.cobalt : T.border}`,
    background: on ? `${T.cobalt}1F` : 'transparent', color: on ? T.cobalt : T.text2,
  }}>{on ? '✓ ' : ''}{label}</button>
)

const LinkRow = ({ item, onToggle, onUrl, host }: {
  item: LinkEntry; onToggle: () => void; onUrl: (v: string) => void; host?: string
}): React.JSX.Element => {
  const chk = item.enabled ? validateLink(item.url, host) : { ok: true, reason: '' }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
      <button type="button" onClick={onToggle} style={{
        width: 130, flexShrink: 0, textAlign: 'left', padding: '7px 10px', borderRadius: 8, cursor: 'pointer',
        fontSize: 12, fontWeight: 600, fontFamily: T.sans,
        border: `1px solid ${item.enabled ? T.cobalt : T.border}`,
        background: item.enabled ? `${T.cobalt}1F` : 'transparent', color: item.enabled ? T.cobalt : T.text2,
      }}>{item.enabled ? '✓ ' : ''}{item.label}</button>
      <input
        disabled={!item.enabled}
        value={item.url}
        onChange={e => onUrl(e.target.value)}
        placeholder={item.enabled ? `Link / cuenta de ${item.label}…` : '—'}
        style={{ ...inputStyle, opacity: item.enabled ? 1 : 0.4 }}
      />
      {item.enabled && item.url && (
        <span style={{ fontSize: 11, color: chk.ok ? T.emerald : T.amber, width: 56, flexShrink: 0 }}>
          {chk.ok ? 'OK' : chk.reason}
        </span>
      )}
    </div>
  )
}

export default function BusinessProfileWizard({ open, onClose, onSaved }: Props): React.JSX.Element | null {
  const [step, setStep] = useState(0)
  const [p, setP] = useState<BusinessProfile>(() => loadProfile() ?? emptyProfile())
  const [saving, setSaving] = useState(false)

  if (!open) return null
  const set = (patch: Partial<BusinessProfile>): void => setP(prev => ({ ...prev, ...patch }))
  const setLink = (key: 'salesPlatforms' | 'adPlatforms' | 'socialLinks', id: string, patch: Partial<LinkEntry>): void =>
    set({ [key]: p[key].map(l => l.id === id ? { ...l, ...patch } : l) } as Partial<BusinessProfile>)
  const toggleArr = (key: 'goals' | 'channels', id: string): void =>
    set({ [key]: p[key].includes(id) ? p[key].filter(x => x !== id) : [...p[key], id] } as Partial<BusinessProfile>)
  const customs = p.customLinks ?? []
  const addCustom = (): void => set({ customLinks: [...customs, { id: `c${Date.now()}`, label: '', url: '', type: 'web', enabled: true }] })
  const updateCustom = (id: string, patch: Partial<CustomLink>): void => set({ customLinks: customs.map(c => c.id === id ? { ...c, ...patch } : c) })
  const removeCustom = (id: string): void => set({ customLinks: customs.filter(c => c.id !== id) })
  const onCustomUrl = (id: string, url: string): void => {
    const cur = customs.find(c => c.id === id)
    const patch: Partial<CustomLink> = { url, type: detectLinkType(url) }
    if (cur && !cur.label) patch.label = labelFromUrl(url)
    updateCustom(id, patch)
  }

  const finish = async (): Promise<void> => {
    setSaving(true)
    saveProfile(p)
    // best-effort backend (Business.config); ignora si no hay sesión/backend
    try {
      await fetch('/api/v1/businesses', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: p.industry || 'Mi negocio',
          type: p.bizType === 'servicio' ? 'services' : p.bizType === 'producto' ? 'products' : 'hybrid',
          description: p.productDesc, config: p,
        }),
      })
    } catch { /* localStorage ya guardó */ }
    setSaving(false)
    onSaved(p)
    onClose()
  }

  const SOCIAL_HOST: Record<string, string> = {
    tiktok: 'tiktok.com', instagram: 'instagram.com', facebook: 'facebook.com',
    twitter: 'x.com', youtube: 'youtube.com', linkedin: 'linkedin.com',
    pinterest: 'pinterest.com', threads: 'threads.net',
  }

  return (
    <div className="fixed inset-0 z-[125] flex items-center justify-center px-4" onClick={onClose}
      style={{ background: 'rgba(5,8,16,0.78)', backdropFilter: 'blur(10px)' }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: '100%', maxWidth: 640, maxHeight: '88vh', display: 'flex', flexDirection: 'column',
        background: T.panel, border: `1px solid ${T.borderStrong}`, borderRadius: 16, overflow: 'hidden',
        fontFamily: T.sans, color: T.text,
      }}>
        {/* header + progreso */}
        <div style={{ padding: '16px 20px', borderBottom: `1px solid ${T.border}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 30, height: 30, borderRadius: 8, display: 'grid', placeItems: 'center', background: `${T.cobalt}1F`, border: `1px solid ${T.cobalt}44`, color: T.cobalt }}>
              <Sparkles size={15} />
            </span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Tu negocio · paso {step + 1}/{STEP_TITLES.length} — {STEP_TITLES[step]}</div>
              <div style={{ fontSize: 11, color: T.text2, fontFamily: T.mono }}>Para que SellIA venda por vos en tus plataformas reales</div>
            </div>
            <button type="button" onClick={onClose} style={{ width: 30, height: 30, borderRadius: '50%', border: `1px solid ${T.border}`, background: 'transparent', color: T.text2, cursor: 'pointer' }}><X size={15} /></button>
          </div>
          <div style={{ display: 'flex', gap: 4, marginTop: 12 }}>
            {STEP_TITLES.map((_, i) => (
              <div key={i} style={{ flex: 1, height: 4, borderRadius: 4, background: i <= step ? T.cobalt : T.border }} />
            ))}
          </div>
        </div>

        {/* body */}
        <div style={{ padding: 20, overflowY: 'auto', flex: 1 }}>
          {step === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={labelStyle}>¿Vendés producto, servicio o ambos?</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  {(['producto', 'servicio', 'ambos'] as const).map(t => (
                    <Chip key={t} on={p.bizType === t} label={t} onClick={() => set({ bizType: t })} />
                  ))}
                </div>
              </div>
              <div><label style={labelStyle}>¿Qué vendés? (descripción)</label>
                <textarea value={p.productDesc} onChange={e => set({ productDesc: e.target.value })} rows={2} placeholder="Ej: zapatillas urbanas, consultoría de marketing…" style={{ ...inputStyle, resize: 'vertical' }} /></div>
              <div style={{ display: 'flex', gap: 12 }}>
                <div style={{ flex: 1 }}><label style={labelStyle}>Industria/rubro</label><input value={p.industry} onChange={e => set({ industry: e.target.value })} placeholder="Indumentaria, Software…" style={inputStyle} /></div>
                <div style={{ flex: 1 }}><label style={labelStyle}>Ticket promedio</label><input value={p.ticket} onChange={e => set({ ticket: e.target.value })} placeholder="$ / rango" style={inputStyle} /></div>
              </div>
              <div><label style={labelStyle}>Público objetivo</label><input value={p.audience} onChange={e => set({ audience: e.target.value })} placeholder="A quién le vendés" style={inputStyle} /></div>
            </div>
          )}

          {step === 1 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div><label style={labelStyle}>Oferta principal</label><textarea value={p.offer} onChange={e => set({ offer: e.target.value })} rows={2} placeholder="Tu oferta estrella / promo" style={{ ...inputStyle, resize: 'vertical' }} /></div>
              <div><label style={labelStyle}>Propuesta de valor / diferenciador</label><textarea value={p.valueProp} onChange={e => set({ valueProp: e.target.value })} rows={2} placeholder="Por qué te eligen a vos" style={{ ...inputStyle, resize: 'vertical' }} /></div>
              <div><label style={labelStyle}>Objetivos (elegí los que apliquen)</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {GOALS.map(g => <Chip key={g.id} on={p.goals.includes(g.id)} label={g.label} onClick={() => toggleArr('goals', g.id)} />)}
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <p style={{ fontSize: 12, color: T.text2, marginBottom: 12 }}>Marcá dónde vendés y pegá el link de cada una.</p>
              {p.salesPlatforms.map(it => (
                <LinkRow key={it.id} item={it}
                  onToggle={() => setLink('salesPlatforms', it.id, { enabled: !it.enabled })}
                  onUrl={v => setLink('salesPlatforms', it.id, { url: v })} />
              ))}
            </div>
          )}

          {step === 3 && (
            <div>
              <p style={{ fontSize: 12, color: T.text2, marginBottom: 12 }}>Dónde te anunciás (cuenta o link del administrador de anuncios).</p>
              {p.adPlatforms.map(it => (
                <LinkRow key={it.id} item={it}
                  onToggle={() => setLink('adPlatforms', it.id, { enabled: !it.enabled })}
                  onUrl={v => setLink('adPlatforms', it.id, { url: v })} />
              ))}
            </div>
          )}

          {step === 4 && (
            <div>
              <p style={{ fontSize: 12, color: T.text2, marginBottom: 12 }}>Dónde subís contenido — pegá los links de tus perfiles (TikTok, IG, FB, X, YouTube…).</p>
              {p.socialLinks.map(it => (
                <LinkRow key={it.id} item={it} host={SOCIAL_HOST[it.id]}
                  onToggle={() => setLink('socialLinks', it.id, { enabled: !it.enabled })}
                  onUrl={v => setLink('socialLinks', it.id, { url: v })} />
              ))}
            </div>
          )}

          {step === 5 && (
            <div>
              <p style={{ fontSize: 12, color: T.text2, marginBottom: 12 }}>
                Pegá CUALQUIER link donde tengas presencia: tienda (ML/Amazon/Hotmart/Shopify…), perfil de redes, o web (Beacons, Linktree, sitios Lovable/Vercel…). Se autodetecta el tipo; corregilo si hace falta.
              </p>
              {customs.map(c => {
                const chk = c.url ? validateLink(c.url) : { ok: true, reason: '' }
                return (
                  <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <input value={c.url} onChange={e => onCustomUrl(c.id, e.target.value)} placeholder="https://…" style={{ ...inputStyle, flex: 2 }} />
                    <input value={c.label} onChange={e => updateCustom(c.id, { label: e.target.value })} placeholder="nombre" style={{ ...inputStyle, flex: 1 }} />
                    <select value={c.type} onChange={e => updateCustom(c.id, { type: e.target.value as CustomLinkType })}
                      style={{ ...inputStyle, width: 90, flex: 'none' }}>
                      <option value="venta">venta</option>
                      <option value="perfil">perfil</option>
                      <option value="web">web</option>
                    </select>
                    {c.url && <span style={{ fontSize: 11, color: chk.ok ? T.emerald : T.amber, width: 40 }}>{chk.ok ? 'OK' : '✕'}</span>}
                    <button type="button" onClick={() => removeCustom(c.id)} style={{ background: 'none', border: 'none', color: T.text3, cursor: 'pointer', fontSize: 16 }}>×</button>
                  </div>
                )
              })}
              <button type="button" onClick={addCustom} style={{ marginTop: 4, padding: '8px 14px', borderRadius: 8, border: `1px dashed ${T.border}`, background: 'transparent', color: T.cobalt, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
                + Agregar link
              </button>
            </div>
          )}

          {step === 6 && (
            <div>
              <label style={labelStyle}>¿Por dónde atendés a tus clientes?</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {CHANNELS.map(c => <Chip key={c.id} on={p.channels.includes(c.id)} label={c.label} onClick={() => toggleArr('channels', c.id)} />)}
              </div>
            </div>
          )}

          {step === 7 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <SummaryRow k="Vende" v={`${p.bizType || '—'} · ${p.productDesc || '—'}`} />
              <SummaryRow k="Objetivos" v={p.goals.join(', ') || '—'} />
              <SummaryRow k="Plataformas de venta" v={p.salesPlatforms.filter(l => l.enabled).map(l => l.label).join(', ') || '—'} />
              <SummaryRow k="Anuncios" v={p.adPlatforms.filter(l => l.enabled).map(l => l.label).join(', ') || '—'} />
              <SummaryRow k="Redes/contenido" v={p.socialLinks.filter(l => l.enabled).map(l => l.label).join(', ') || '—'} />
              <SummaryRow k="Otros links" v={customs.filter(l => l.enabled && l.url).map(l => `${l.label || labelFromUrl(l.url)} (${l.type})`).join(', ') || '—'} />
              <SummaryRow k="Atención" v={p.channels.join(', ') || '—'} />
              {/* validador de links cargados */}
              <div style={{ marginTop: 6 }}>
                <div style={{ fontSize: 11, color: T.text3, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Validación de links</div>
                {[...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks].filter(l => l.enabled && l.url).map(l => {
                  const c = validateLink(l.url, SOCIAL_HOST[l.id])
                  return (
                    <div key={l.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, marginBottom: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: c.ok ? T.emerald : T.amber }} />
                      <span style={{ color: T.text2, width: 120 }}>{l.label}</span>
                      <a href={l.url.startsWith('http') ? l.url : `https://${l.url}`} target="_blank" rel="noreferrer" style={{ color: T.cobalt, fontSize: 11, display: 'inline-flex', alignItems: 'center', gap: 3 }}>abrir <ExternalLink size={11} /></a>
                      <span style={{ color: c.ok ? T.emerald : T.amber, fontSize: 11 }}>{c.ok ? 'OK' : c.reason}</span>
                    </div>
                  )
                })}
                {![...p.salesPlatforms, ...p.adPlatforms, ...p.socialLinks].some(l => l.enabled && l.url) && (
                  <span style={{ fontSize: 12, color: T.amber }}>Cargá al menos un link en pasos anteriores.</span>
                )}
              </div>
              {!isComplete(p) && <span style={{ fontSize: 12, color: T.amber }}>Falta: qué vendés + 1 objetivo + 1 link válido.</span>}
            </div>
          )}
        </div>

        {/* footer nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 20px', borderTop: `1px solid ${T.border}` }}>
          <button type="button" onClick={() => setStep(s => Math.max(0, s - 1))} disabled={step === 0}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '8px 14px', borderRadius: 9, border: `1px solid ${T.border}`, background: 'transparent', color: T.text2, cursor: step === 0 ? 'not-allowed' : 'pointer', opacity: step === 0 ? 0.4 : 1, fontSize: 13 }}>
            <ArrowLeft size={14} /> Atrás
          </button>
          <span style={{ flex: 1 }} />
          {step < LAST ? (
            <button type="button" onClick={() => setStep(s => Math.min(LAST, s + 1))}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '9px 18px', borderRadius: 9, border: 'none', background: T.cobalt, color: '#fff', cursor: 'pointer', fontSize: 13, fontWeight: 700 }}>
              Siguiente <ArrowRight size={14} />
            </button>
          ) : (
            <button type="button" onClick={() => { void finish() }} disabled={saving || !isComplete(p)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '9px 20px', borderRadius: 9, border: 'none', background: T.emerald, color: '#04110b', cursor: saving || !isComplete(p) ? 'not-allowed' : 'pointer', fontSize: 13, fontWeight: 800, opacity: saving || !isComplete(p) ? 0.5 : 1 }}>
              <Check size={15} /> {saving ? 'Guardando…' : 'Activar SellIA'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

const SummaryRow = ({ k, v }: { k: string; v: string }): React.JSX.Element => (
  <div style={{ display: 'flex', gap: 10, fontSize: 13 }}>
    <span style={{ width: 150, flexShrink: 0, color: T.text3 }}>{k}</span>
    <span style={{ color: T.text }}>{v}</span>
  </div>
)
