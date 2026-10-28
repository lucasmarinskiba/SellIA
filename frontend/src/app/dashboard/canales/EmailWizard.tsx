'use client'

import { useEffect, useId, useState } from 'react'
import { ExternalLink, Eye, EyeOff, Info, Loader2, MailCheck } from 'lucide-react'
import { channelsApi } from '@/lib/channels'

const inputCls =
  'h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-orange focus:outline-none focus:ring-2 focus:ring-brand-orange/30'
const primaryCls =
  'inline-flex h-11 items-center gap-2 rounded-xl bg-brand-orange px-5 text-sm font-semibold text-white hover:bg-brand-orange-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange focus-visible:ring-offset-2 disabled:opacity-50'
const ghostCls =
  'h-11 rounded-xl px-4 text-sm font-medium text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange disabled:opacity-50'

const RESEND_SECONDS = 60

/** Where the person creates the password a mailbox needs for third-party apps, by the address's domain. */
const PASSWORD_HELP: { domains: string[]; name: string; text: string; url: string }[] = [
  {
    domains: ['gmail.com', 'googlemail.com'],
    name: 'Gmail',
    text: 'Gmail pide una contraseña de aplicación (no la normal). Necesitás la verificación en 2 pasos activada.',
    url: 'https://myaccount.google.com/apppasswords',
  },
  {
    domains: ['outlook.com', 'outlook.es', 'hotmail.com', 'hotmail.es', 'live.com', 'msn.com'],
    name: 'Outlook',
    text: 'Outlook pide una contraseña de aplicación. Necesitás la verificación en dos pasos activada.',
    url: 'https://account.live.com/proofs/AppPassword',
  },
  {
    domains: ['yahoo.com', 'yahoo.com.ar', 'yahoo.es', 'ymail.com'],
    name: 'Yahoo',
    text: 'Yahoo pide una contraseña de aplicación, que se crea en la seguridad de tu cuenta.',
    url: 'https://login.yahoo.com/account/security',
  },
  {
    domains: ['icloud.com', 'me.com', 'mac.com'],
    name: 'iCloud',
    text: 'iCloud pide una contraseña específica de app, que se crea en tu cuenta de Apple.',
    url: 'https://account.apple.com/account/manage',
  },
]

const helpFor = (email: string) => {
  const domain = email.split('@')[1]?.trim().toLowerCase() ?? ''
  return PASSWORD_HELP.find((h) => h.domains.includes(domain)) ?? null
}

const reason = (e: unknown, fallback: string): string => {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
}

interface Props {
  businessId: string
  onConnected: (email: string) => void
  onClose: () => void
}

/**
 * Two steps. 1) address + password: the servers are detected, the mailbox is tested, and a code is mailed to
 * itself. 2) the code from that email connects it. Nothing else to configure.
 */
export function EmailWizard({ businessId, onConnected, onClose }: Props) {
  const uid = useId()
  const [step, setStep] = useState<1 | 2>(1)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [shown, setShown] = useState(false)
  const [advanced, setAdvanced] = useState(false)
  const [other, setOther] = useState({ smtp_host: '', smtp_port: '587' })
  const [channelId, setChannelId] = useState('')
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (cooldown <= 0) return
    const t = window.setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => window.clearTimeout(t)
  }, [cooldown])

  const help = helpFor(email)

  const start = async () => {
    setBusy(true)
    setError(null)
    try {
      const custom = other.smtp_host.trim()
        ? {
            smtp_host: other.smtp_host.trim(),
            smtp_port: Number(other.smtp_port) || 587,
          }
        : {}
      const out = await channelsApi.startEmail(businessId, { email: email.trim(), password, ...custom })
      setChannelId(out.channel_id)
      setCode('')
      setCooldown(RESEND_SECONDS)
      setStep(2)
    } catch (e) {
      setError(reason(e, 'No pudimos probar la casilla. Revisá los datos e intentá de nuevo.'))
    } finally {
      setBusy(false)
    }
  }

  const confirm = async () => {
    setBusy(true)
    setError(null)
    try {
      const out = await channelsApi.confirmEmail(businessId, channelId, code.trim())
      onConnected(out.email)
    } catch (e) {
      setError(reason(e, 'No pudimos confirmar el código. Intentá de nuevo.'))
    } finally {
      setBusy(false)
    }
  }

  const resend = async () => {
    setBusy(true)
    setError(null)
    try {
      await channelsApi.resendEmail(businessId, channelId)
      setCooldown(RESEND_SECONDS)
    } catch (e) {
      setError(reason(e, 'No pudimos reenviar el código.'))
    } finally {
      setBusy(false)
    }
  }

  const errorBox = error && (
    <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">{error}</p>
  )

  if (step === 2) {
    return (
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (code.trim().length >= 4) void confirm()
        }}
        className="flex-1 space-y-5 overflow-y-auto px-5 py-5"
      >
        <div className="flex gap-3 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900">
          <MailCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <p>
            Te mandamos un código de 6 dígitos a <strong>{email.trim().toLowerCase()}</strong>. Abrí tu casilla (si no
            aparece, mirá spam), copiá el código y pegalo acá. Vence en 15 minutos.
          </p>
        </div>
        <div>
          <label htmlFor={`${uid}-code`} className="mb-1 block text-sm font-medium text-slate-700">Código</label>
          <input
            id={`${uid}-code`}
            inputMode="numeric"
            autoComplete="one-time-code"
            autoFocus
            maxLength={12}
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\s/g, ''))}
            placeholder="123456"
            className={`${inputCls} text-center text-lg tracking-[0.4em]`}
          />
        </div>
        {errorBox}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
          <div className="flex gap-1">
            <button type="button" onClick={() => { setStep(1); setError(null) }} className={ghostCls} disabled={busy}>
              Cambiar casilla
            </button>
            <button type="button" onClick={() => void resend()} className={ghostCls} disabled={busy || cooldown > 0}>
              {cooldown > 0 ? `Reenviar código (${cooldown}s)` : 'Reenviar código'}
            </button>
          </div>
          <button type="submit" disabled={busy || code.trim().length < 4} className={primaryCls}>
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            {busy ? 'Confirmando…' : 'Confirmar y conectar'}
          </button>
        </div>
      </form>
    )
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        void start()
      }}
      className="flex-1 space-y-5 overflow-y-auto px-5 py-5"
    >
      <p className="text-sm text-slate-600">
        Ponés tu email y su contraseña. Nosotros hacemos el resto y te mandamos un código para confirmar que es tuyo.
      </p>
      <div>
        <label htmlFor={`${uid}-email`} className="mb-1 block text-sm font-medium text-slate-700">Tu email</label>
        <input
          id={`${uid}-email`}
          type="email"
          autoFocus
          required
          autoComplete="off"
          spellCheck={false}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="ventas@tunegocio.com"
          className={inputCls}
        />
      </div>
      <div>
        <label htmlFor={`${uid}-pass`} className="mb-1 block text-sm font-medium text-slate-700">{help ? 'Contraseña de aplicación' : 'Contraseña'}</label>
        <div className="relative">
          <input
            id={`${uid}-pass`}
            type={shown ? 'text' : 'password'}
            required
            autoComplete="off"
            spellCheck={false}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={`${inputCls} pr-11`}
          />
          <button
            type="button"
            onClick={() => setShown((s) => !s)}
            aria-label={shown ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            className="absolute right-1 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
          >
            {shown ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {help && (
        <div className="flex gap-3 rounded-xl bg-blue-50 p-4 text-sm text-blue-900">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <div className="space-y-1">
            <p>{help.text}</p>
            <a href={help.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-medium underline">
              Crear contraseña de aplicación de {help.name} <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          </div>
        </div>
      )}

      {error && !help && !advanced && (
        <button type="button" onClick={() => setAdvanced(true)} className="text-sm font-medium text-slate-600 underline">
          Mi correo es de una empresa y no se conecta
        </button>
      )}

      {advanced && (
        <div className="space-y-3 rounded-xl border border-slate-200 p-4">
          <p className="text-sm text-slate-600">
            Pedile a quien administra tu correo estos datos (o buscá «configuración SMTP» en la ayuda de tu proveedor):
          </p>
          <input aria-label="Servidor de salida" placeholder="Servidor de salida (ej.: smtp.miempresa.com)" className={inputCls}
            value={other.smtp_host} onChange={(e) => setOther({ ...other, smtp_host: e.target.value })} />
          <input aria-label="Puerto" inputMode="numeric" placeholder="Puerto (casi siempre 587)" className={inputCls}
            value={other.smtp_port} onChange={(e) => setOther({ ...other, smtp_port: e.target.value })} />
        </div>
      )}

      {errorBox}
      <div className="flex items-center justify-end gap-3 border-t border-slate-200 pt-4">
        <button type="button" onClick={onClose} className={ghostCls}>Cancelar</button>
        <button type="submit" disabled={busy || !email.trim() || !password} className={primaryCls}>
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {busy ? 'Probando tu casilla…' : 'Enviar código'}
        </button>
      </div>
    </form>
  )
}
