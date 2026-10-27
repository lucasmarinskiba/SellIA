'use client'

import { useEffect, useId, useRef, useState } from 'react'
import { ChevronDown, ExternalLink, Eye, EyeOff, Info, Loader2, X } from 'lucide-react'
import type { ChannelPlatform } from '@/types/channels'
import {
  CATEGORIES, CREDENTIAL_FORMS, EMAIL_PRESETS, ONE_CLICK_PLATFORMS, PLATFORMS, platformMeta, type FieldDef,
} from './catalog'

export interface ConnectDraft {
  platform: ChannelPlatform
  name: string
  credentials: Record<string, string>
}

interface Props {
  draft: ConnectDraft
  onChange: (draft: ConnectDraft) => void
  onClose: () => void
  onSubmit: () => void
  onOAuth: (platform: ChannelPlatform) => void
  onWhatsApp: () => void
  saving: boolean
  connecting: boolean
  error: string | null
}

const inputCls =
  'h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-orange focus:outline-none focus:ring-2 focus:ring-brand-orange/30'

function Field({ def, value, onChange }: { def: FieldDef; value: string; onChange: (v: string) => void }) {
  const id = useId()
  const [shown, setShown] = useState(false)
  const secret = def.type === 'password'
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium text-slate-700">
        {def.label}
        {def.required && <span className="ml-0.5 text-red-600" aria-hidden="true">*</span>}
      </label>
      <div className="relative">
        <input
          id={id}
          type={secret && !shown ? 'password' : def.type === 'number' ? 'number' : 'text'}
          inputMode={def.type === 'number' ? 'numeric' : undefined}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={def.placeholder}
          required={def.required}
          autoComplete="off"
          spellCheck={false}
          aria-describedby={def.help ? `${id}-help` : undefined}
          className={`${inputCls} ${secret ? 'pr-11' : ''}`}
        />
        {secret && (
          <button
            type="button"
            onClick={() => setShown((s) => !s)}
            aria-label={shown ? `Ocultar ${def.label}` : `Mostrar ${def.label}`}
            className="absolute right-1 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
          >
            {shown ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
      {def.help && (
        <p id={`${id}-help`} className="mt-1 text-xs text-slate-500">
          {def.help}
        </p>
      )}
    </div>
  )
}

export function ConnectModal({ draft, onChange, onClose, onSubmit, onOAuth, onWhatsApp, saving, connecting, error }: Props) {
  const titleId = useId()
  const firstRef = useRef<HTMLSelectElement>(null)
  const meta = platformMeta(draft.platform)
  const form = CREDENTIAL_FORMS[draft.platform]
  const oneClick = ONE_CLICK_PLATFORMS.includes(draft.platform)
  const isWhatsApp = draft.platform === 'whatsapp'
  const isEmail = draft.platform === 'email'
  const Icon = meta.icon

  useEffect(() => {
    firstRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const setCred = (key: string, value: string) =>
    onChange({ ...draft, credentials: { ...draft.credentials, [key]: value } })

  const pickPlatform = (platform: ChannelPlatform) =>
    onChange({
      platform,
      credentials: platform === 'email' ? { smtp_host: 'smtp.gmail.com', smtp_port: '587' } : {},
      name: platformMeta(platform).label,
    })

  const basic = (form?.fields ?? []).filter((f) => !f.advanced)
  const advanced = (form?.fields ?? []).filter((f) => f.advanced)

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-0 backdrop-blur-sm sm:items-center sm:p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex max-h-[92vh] w-full max-w-xl flex-col overflow-hidden rounded-t-3xl bg-white shadow-2xl sm:rounded-2xl"
      >
        <header className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${meta.tile}`} aria-hidden="true">
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h2 id={titleId} className="text-lg font-bold text-slate-900">Conectar {meta.label}</h2>
            <p className="truncate text-sm text-slate-500">{meta.description}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="flex h-10 w-10 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit()
          }}
          className="flex-1 space-y-5 overflow-y-auto px-5 py-5"
        >
          <div>
            <label htmlFor={`${titleId}-platform`} className="mb-1 block text-sm font-medium text-slate-700">Plataforma</label>
            <select
              id={`${titleId}-platform`}
              ref={firstRef}
              value={draft.platform}
              onChange={(e) => pickPlatform(e.target.value as ChannelPlatform)}
              className={inputCls}
            >
              {CATEGORIES.map((c) => (
                <optgroup key={c.key} label={c.label}>
                  {Object.entries(PLATFORMS)
                    .filter(([, p]) => p.category === c.key)
                    .map(([key, p]) => (
                      <option key={key} value={key}>{p.label}</option>
                    ))}
                </optgroup>
              ))}
            </select>
          </div>

          {isWhatsApp ? (
            <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
              Sin claves ni configuración manual: hacé clic y elegí (o creá) tu WhatsApp Business en el popup de Meta. No cierres el popup hasta el final.
            </p>
          ) : oneClick ? (
            <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
              Sin claves ni configuración manual: hacé clic y autorizá tu cuenta de {meta.label}.
            </p>
          ) : (
            <>
              {isEmail && (
                <div className="space-y-3">
                  <div>
                    <p className="mb-2 text-sm font-medium text-slate-700">Proveedor</p>
                    <div className="flex flex-wrap gap-2" role="group" aria-label="Proveedor de email">
                      {EMAIL_PRESETS.map((p) => {
                        const active = draft.credentials.smtp_host === p.smtp_host
                        return (
                          <button
                            key={p.label}
                            type="button"
                            aria-pressed={active}
                            onClick={() =>
                              onChange({
                                ...draft,
                                credentials: {
                                  ...draft.credentials,
                                  smtp_host: p.smtp_host,
                                  smtp_port: p.smtp_port,
                                  imap_host: p.imap_host,
                                },
                              })
                            }
                            className={`h-10 rounded-full px-4 text-sm font-medium ring-1 ring-inset focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange ${
                              active ? 'bg-brand-orange text-white ring-brand-orange' : 'bg-white text-slate-700 ring-slate-300 hover:bg-slate-50'
                            }`}
                          >
                            {p.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                  <div className="flex gap-3 rounded-xl bg-blue-50 p-4 text-sm text-blue-900">
                    <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                    <div className="space-y-1">
                      <p>
                        Gmail y Outlook piden una <strong>contraseña de aplicación</strong>, no tu contraseña normal. En Google:
                        Cuenta → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones.
                      </p>
                      <a
                        href="https://myaccount.google.com/apppasswords"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 font-medium underline"
                      >
                        Crear contraseña de aplicación <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {basic.length > 0 ? (
                <fieldset className="space-y-4">
                  <legend className="mb-1 text-sm font-semibold text-slate-900">{isEmail ? 'Datos de tu casilla' : 'Credenciales'}</legend>
                  {basic.map((def) => (
                    <Field key={def.key} def={def} value={draft.credentials[def.key] ?? ''} onChange={(v) => setCred(def.key, v)} />
                  ))}
                </fieldset>
              ) : (
                <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                  Configuración manual disponible próximamente para este canal.
                </p>
              )}

              {advanced.length > 0 && (
                <details className="group rounded-xl border border-slate-200">
                  <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-sm font-medium text-slate-800">
                    Lectura de respuestas (IMAP) — opcional
                    <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" aria-hidden="true" />
                  </summary>
                  <div className="space-y-4 border-t border-slate-200 p-4">
                    {advanced.map((def) => (
                      <Field key={def.key} def={def} value={draft.credentials[def.key] ?? ''} onChange={(v) => setCred(def.key, v)} />
                    ))}
                  </div>
                </details>
              )}

              {form?.note && <p className="text-xs text-slate-500">{form.note}</p>}
            </>
          )}

          {error && (
            <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">
              {error}
            </p>
          )}

          <div className="sticky bottom-0 -mx-5 -mb-5 flex items-center justify-end gap-3 border-t border-slate-200 bg-white px-5 py-4">
            <button
              type="button"
              onClick={onClose}
              className="h-11 rounded-xl px-4 text-sm font-medium text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
            >
              Cancelar
            </button>
            {isWhatsApp || oneClick ? (
              <button
                type="button"
                disabled={connecting}
                onClick={() => (isWhatsApp ? onWhatsApp() : onOAuth(draft.platform))}
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2 disabled:opacity-50"
              >
                {connecting && <Loader2 className="h-4 w-4 animate-spin" />}
                {connecting ? 'Conectando…' : `Conectar con ${meta.label}`}
              </button>
            ) : (
              <button
                type="submit"
                disabled={saving || basic.length === 0}
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2 disabled:opacity-50"
              >
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                {saving ? 'Guardando…' : 'Guardar y conectar'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
