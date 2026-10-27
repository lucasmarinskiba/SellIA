'use client'

import { useState } from 'react'
import Button from '@/components/ui/Button'
import { harvey, type HarveyProfile, type HarveyStatus } from '@/lib/api/harvey'
import { DiscoverySources } from './DiscoverySources'
import { card, fmtDate, input, label, lines, Notice, useAction } from './ui'

const Toggle = ({ checked, onChange, children }: { checked: boolean; onChange: (v: boolean) => void; children: React.ReactNode }) => (
  <label className="flex items-start gap-2 text-sm text-slate-700">
    <input type="checkbox" className="mt-1" checked={checked} onChange={(e) => onChange(e.target.checked)} />
    <span>{children}</span>
  </label>
)

export function SettingsTab({
  bid, profile, status, onChange, onSaved,
}: {
  bid: string; profile: HarveyProfile; status: HarveyStatus; onChange: () => Promise<void>
  onSaved: (p: HarveyProfile) => Promise<void>
}) {
  const [f, setF] = useState({
    persona_name: profile.persona_name,
    persona_role: profile.persona_role,
    tone: profile.tone,
    offer: profile.offer,
    benefits: profile.benefits.join('\n'),
    keywords: (profile.icp.keywords ?? []).join('\n'),
    locations: (profile.icp.locations ?? []).join('\n'),
    postal_address: profile.postal_address,
    opt_out_line: profile.opt_out_line,
    do_not_contact: profile.do_not_contact.join('\n'),
    max_daily_drafts: profile.max_daily_drafts,
    max_daily_sends: profile.max_daily_sends,
    max_daily_discoveries: profile.max_daily_discoveries,
    send_window_start: profile.send_window_start,
    send_window_end: profile.send_window_end,
    send_timezone: profile.send_timezone,
    send_weekdays_only: profile.send_weekdays_only,
    auto_draft: profile.auto_draft,
    auto_discover: profile.auto_discover,
  })
  const { busy, notice, run } = useAction()
  const set = <K extends keyof typeof f>(key: K, value: (typeof f)[K]) => setF((prev) => ({ ...prev, [key]: value }))
  const num = (key: 'max_daily_drafts' | 'max_daily_sends' | 'max_daily_discoveries' | 'send_window_start' | 'send_window_end') =>
    (e: React.ChangeEvent<HTMLInputElement>) => set(key, Number(e.target.value))

  const save = () =>
    run(
      'save',
      () =>
        harvey.updateProfile(bid, {
          persona_name: f.persona_name,
          persona_role: f.persona_role,
          tone: f.tone,
          offer: f.offer,
          benefits: lines(f.benefits),
          icp: { ...profile.icp, keywords: lines(f.keywords), locations: lines(f.locations) },
          postal_address: f.postal_address,
          opt_out_line: f.opt_out_line,
          do_not_contact: lines(f.do_not_contact),
          max_daily_drafts: f.max_daily_drafts,
          max_daily_sends: f.max_daily_sends,
          max_daily_discoveries: f.max_daily_discoveries,
          send_window_start: f.send_window_start,
          send_window_end: f.send_window_end,
          send_timezone: f.send_timezone,
          send_weekdays_only: f.send_weekdays_only,
          auto_draft: f.auto_draft,
          auto_discover: f.auto_discover,
        }),
      () => 'Configuración guardada',
    ).then((p) => (p ? onSaved(p) : undefined))

  return (
    <div className="space-y-5">
      <section className={`${card} space-y-3`}>
        <h2 className="font-semibold text-slate-900">Quién escribe y qué ofrece</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div><label className={label} htmlFor="p-name">Nombre de quien firma</label>
            <input id="p-name" className={input} value={f.persona_name} onChange={(e) => set('persona_name', e.target.value)} /></div>
          <div><label className={label} htmlFor="p-role">Cargo</label>
            <input id="p-role" className={input} value={f.persona_role} onChange={(e) => set('persona_role', e.target.value)} /></div>
        </div>
        <div><label className={label} htmlFor="p-tone">Tono</label>
          <input id="p-tone" className={input} value={f.tone} onChange={(e) => set('tone', e.target.value)} /></div>
        <div><label className={label} htmlFor="p-offer">Qué ofrece tu negocio</label>
          <textarea id="p-offer" className={`${input} min-h-[80px]`} value={f.offer} onChange={(e) => set('offer', e.target.value)} /></div>
        <div><label className={label} htmlFor="p-ben">Beneficios (uno por línea, solo los que son ciertos)</label>
          <textarea id="p-ben" className={`${input} min-h-[80px]`} value={f.benefits} onChange={(e) => set('benefits', e.target.value)} /></div>
      </section>

      <section className={`${card} space-y-3`}>
        <h2 className="font-semibold text-slate-900">Cliente ideal (para buscar prospectos)</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div><label className={label} htmlFor="p-kw">Palabras clave (una por línea)</label>
            <textarea id="p-kw" className={`${input} min-h-[80px]`} placeholder="panadería&#10;rotisería" value={f.keywords} onChange={(e) => set('keywords', e.target.value)} /></div>
          <div><label className={label} htmlFor="p-loc">Zonas (una por línea)</label>
            <textarea id="p-loc" className={`${input} min-h-[80px]`} placeholder="Córdoba&#10;Rosario" value={f.locations} onChange={(e) => set('locations', e.target.value)} /></div>
        </div>
      </section>

      <section className={`${card} space-y-3`}>
        <h2 className="font-semibold text-slate-900">Pie legal de cada email</h2>
        <div><label className={label} htmlFor="p-addr">Dirección postal del negocio (obligatoria)</label>
          <input id="p-addr" className={input} value={f.postal_address} onChange={(e) => set('postal_address', e.target.value)} /></div>
        <div><label className={label} htmlFor="p-opt">Línea para darse de baja</label>
          <input id="p-opt" className={input} value={f.opt_out_line} onChange={(e) => set('opt_out_line', e.target.value)} /></div>
        <div><label className={label} htmlFor="p-dnc">No contactar (emails o dominios, uno por línea)</label>
          <textarea id="p-dnc" className={`${input} min-h-[70px]`} value={f.do_not_contact} onChange={(e) => set('do_not_contact', e.target.value)} /></div>
      </section>

      <DiscoverySources bid={bid} status={status} onChange={onChange} />

      <section className={`${card} space-y-3`}>
        <h2 className="font-semibold text-slate-900">Ritmo y automatización</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <div><label className={label} htmlFor="p-sends">Envíos por día</label>
            <input id="p-sends" type="number" min={1} max={500} className={input} value={f.max_daily_sends} onChange={num('max_daily_sends')} /></div>
          <div><label className={label} htmlFor="p-drafts">Borradores por día</label>
            <input id="p-drafts" type="number" min={1} max={200} className={input} value={f.max_daily_drafts} onChange={num('max_daily_drafts')} /></div>
          <div><label className={label} htmlFor="p-disc">Descubiertos por día</label>
            <input id="p-disc" type="number" min={1} max={100} className={input} value={f.max_daily_discoveries} onChange={num('max_daily_discoveries')} /></div>
          <div><label className={label} htmlFor="p-ws">Enviar desde (hora)</label>
            <input id="p-ws" type="number" min={0} max={23} className={input} value={f.send_window_start} onChange={num('send_window_start')} /></div>
          <div><label className={label} htmlFor="p-we">Hasta (hora)</label>
            <input id="p-we" type="number" min={1} max={24} className={input} value={f.send_window_end} onChange={num('send_window_end')} /></div>
          <div><label className={label} htmlFor="p-tz">Zona horaria</label>
            <input id="p-tz" className={input} value={f.send_timezone} onChange={(e) => set('send_timezone', e.target.value)} /></div>
        </div>
        <Toggle checked={f.send_weekdays_only} onChange={(v) => set('send_weekdays_only', v)}>Enviar solo de lunes a viernes</Toggle>
        <Toggle checked={f.auto_draft} onChange={(v) => set('auto_draft', v)}>
          Redactar solo los borradores (primer email, seguimientos y respuestas). Usa créditos del modelo; igual vos aprobás cada uno.
        </Toggle>
        <Toggle checked={f.auto_discover} onChange={(v) => set('auto_discover', v)}>
          Buscar prospectos nuevos una vez por día según tu cliente ideal (necesita tu propia clave en Fuentes de prospectos).
        </Toggle>
        <p className="text-xs text-slate-500">
          Una casilla nueva arranca con pocos envíos por día y sube sola. Última pasada automática: {fmtDate(profile.last_cycle_at)}.
        </p>
      </section>

      <div className="flex items-center gap-3">
        <Button isLoading={busy === 'save'} onClick={save}>Guardar</Button>
        <Notice notice={notice} />
      </div>
    </div>
  )
}
