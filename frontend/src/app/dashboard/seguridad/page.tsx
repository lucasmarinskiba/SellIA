'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { auth } from '@/lib/auth'
import { api } from '@/lib/api'
import {
  Shield,
  Smartphone,
  Key,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Copy,
  MapPin,
  Bell,
  Fingerprint,
  Mail,
  Monitor,
  Check,
  X,
  Lock,
  Trash2,
  Clock,
  Globe,
  AlertOctagon,
} from 'lucide-react'

interface SecurityConfig {
  max_distance_km: number | null
  alert_on_geofence: boolean
  alert_on_breach: boolean
}

interface Passkey {
  id: string
  device_name: string
  created_at: string
}

interface TrustedDevice {
  id: string
  device_name: string | null
  os: string | null
  browser: string | null
  ip_address: string | null
  first_seen_at: string
  last_seen_at: string
  is_trusted: boolean
  is_blocked: boolean
}

interface Session {
  id: string
  ip_address: string
  user_agent: string
  location: string | null
  created_at: string
  last_used_at: string
  is_current: boolean
}

export default function SeguridadPage() {
  const router = useRouter()
  const { user, loading: authLoading, refetch } = useAuth()
  const [loading, setLoading] = useState(true)
  const [setupData, setSetupData] = useState<{
    secret: string
    qr_code: string
  } | null>(null)
  const [verifyCode, setVerifyCode] = useState('')
  const [disableCode, setDisableCode] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)
  const [backupRemaining, setBackupRemaining] = useState(0)
  const [config, setConfig] = useState<SecurityConfig | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [processing, setProcessing] = useState(false)
  const [showCodes, setShowCodes] = useState(false)

  // Passkeys
  const [passkeys, setPasskeys] = useState<Passkey[]>([])
  const [passkeyName, setPasskeyName] = useState('')
  const [showPasskeyForm, setShowPasskeyForm] = useState(false)

  // Email OTP
  const [emailOtpEnabled, setEmailOtpEnabled] = useState(false)
  const [emailOtpCode, setEmailOtpCode] = useState('')
  const [showEmailOtpSetup, setShowEmailOtpSetup] = useState(false)

  // Trusted Devices
  const [devices, setDevices] = useState<TrustedDevice[]>([])

  // Sessions
  const [sessions, setSessions] = useState<Session[]>([])

  // Account deletion
  const [deletePassword, setDeletePassword] = useState('')
  const [deleteReason, setDeleteReason] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [authLoading, user, router])

  useEffect(() => {
    if (user) {
      fetchBackupStatus()
      fetchConfig()
      fetchPasskeys()
      fetchDevices()
      fetchSessions()
      fetchEmailOtpStatus()
    }
  }, [user])

  const fetchBackupStatus = async () => {
    try {
      const data = await auth.getBackupCodesStatus()
      setBackupRemaining(data.remaining)
    } catch {
      // silencioso
    } finally {
      setLoading(false)
    }
  }

  const fetchConfig = async () => {
    try {
      const res = await api.get('/security/config')
      setConfig(res.data)
    } catch {
      // silencioso
    }
  }

  const fetchPasskeys = async () => {
    try {
      const data = await auth.getPasskeys()
      setPasskeys(data.passkeys || [])
    } catch {
      // silencioso
    }
  }

  const fetchDevices = async () => {
    try {
      const data = await auth.getTrustedDevices()
      setDevices(data.devices || [])
    } catch {
      // silencioso
    }
  }

  const fetchSessions = async () => {
    try {
      const res = await api.get('/auth/sessions')
      setSessions(res.data.sessions || [])
    } catch {
      // silencioso
    }
  }

  const fetchEmailOtpStatus = async () => {
    try {
      const res = await api.get('/auth/2fa/email/status')
      setEmailOtpEnabled(res.data.enabled)
    } catch {
      // silencioso
    }
  }

  const handleSetup2FA = async () => {
    setProcessing(true)
    setError('')
    try {
      const data = await auth.setup2FA()
      setSetupData({ secret: data.secret, qr_code: data.qr_code })
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al configurar 2FA')
    } finally {
      setProcessing(false)
    }
  }

  const handleVerify2FA = async () => {
    if (!verifyCode) return
    setProcessing(true)
    setError('')
    try {
      const data = await auth.verify2FA(verifyCode)
      setMessage(data.message)
      if (data.backup_codes) {
        setBackupCodes(data.backup_codes)
        setShowCodes(true)
      }
      setSetupData(null)
      setVerifyCode('')
      refetch()
      fetchBackupStatus()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Código incorrecto')
    } finally {
      setProcessing(false)
    }
  }

  const handleDisable2FA = async () => {
    if (!disableCode) return
    setProcessing(true)
    setError('')
    try {
      const data = await auth.disable2FA(disableCode)
      setMessage(data.message)
      setDisableCode('')
      refetch()
      fetchBackupStatus()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Código incorrecto')
    } finally {
      setProcessing(false)
    }
  }

  // Passkey handlers
  const handleRegisterPasskey = async () => {
    if (!passkeyName) return
    setProcessing(true)
    setError('')
    try {
      const beginRes = await auth.registerPasskeyBegin()
      const options = beginRes.options

      // Convert challenge from base64url
      options.challenge = base64urlToBuffer(options.challenge)
      options.user.id = base64urlToBuffer(options.user.id)
      if (options.excludeCredentials) {
        options.excludeCredentials = options.excludeCredentials.map((cred: any) => ({
          ...cred,
          id: base64urlToBuffer(cred.id),
        }))
      }

      const credential = await navigator.credentials.create({ publicKey: options })
      if (!credential) throw new Error('No se pudo crear la credencial')

      const credentialData = {
        id: credential.id,
        rawId: bufferToBase64url((credential as any).rawId),
        type: credential.type,
        response: {
          clientDataJSON: bufferToBase64url((credential as any).response.clientDataJSON),
          attestationObject: bufferToBase64url((credential as any).response.attestationObject),
        },
        device_name: passkeyName,
      }

      await auth.registerPasskeyFinish(credentialData)
      setMessage('Passkey registrado correctamente')
      setPasskeyName('')
      setShowPasskeyForm(false)
      fetchPasskeys()
    } catch (e: any) {
      setError(e.message || 'Error al registrar passkey')
    } finally {
      setProcessing(false)
    }
  }

  const handleDeletePasskey = async (id: string) => {
    setProcessing(true)
    try {
      await auth.deletePasskey(id)
      setMessage('Passkey eliminado')
      fetchPasskeys()
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al eliminar passkey')
    } finally {
      setProcessing(false)
    }
  }

  // Email OTP handlers
  const handleSetupEmailOTP = async () => {
    setProcessing(true)
    setError('')
    try {
      await auth.setupEmailOTP()
      setShowEmailOtpSetup(true)
      setMessage('Código enviado a tu email')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al configurar OTP por email')
    } finally {
      setProcessing(false)
    }
  }

  const handleVerifyEmailOTP = async () => {
    if (!emailOtpCode) return
    setProcessing(true)
    setError('')
    try {
      await auth.verifyEmailOTP(emailOtpCode, 'verify')
      setMessage('Verificación por email activada')
      setEmailOtpCode('')
      setShowEmailOtpSetup(false)
      setEmailOtpEnabled(true)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Código incorrecto')
    } finally {
      setProcessing(false)
    }
  }

  const handleDisableEmailOTP = async () => {
    setProcessing(true)
    setError('')
    try {
      await api.post('/auth/2fa/email/disable')
      setMessage('Verificación por email desactivada')
      setEmailOtpEnabled(false)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al desactivar')
    } finally {
      setProcessing(false)
    }
  }

  // Device handlers
  const handleTrustDevice = async (id: string) => {
    try {
      await auth.trustDevice(id)
      fetchDevices()
      setMessage('Dispositivo confiable')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  const handleRevokeDevice = async (id: string) => {
    try {
      await auth.revokeDevice(id)
      fetchDevices()
      setMessage('Dispositivo revocado')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  const handleBlockDevice = async (id: string) => {
    try {
      await auth.blockDevice(id)
      fetchDevices()
      setMessage('Dispositivo bloqueado')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  // Session handlers
  const handleKillSession = async (id: string) => {
    try {
      await api.post(`/auth/sessions/${id}/revoke`)
      fetchSessions()
      setMessage('Sesión cerrada')
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error')
    }
  }

  // Account deletion
  const handleDeleteAccount = async () => {
    if (!deletePassword) return
    setProcessing(true)
    setError('')
    try {
      await auth.deleteAccount(deletePassword, deleteReason)
      localStorage.removeItem('token')
      window.location.href = '/'
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error al eliminar cuenta')
      setProcessing(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setMessage('Copiado al portapapeles')
    setTimeout(() => setMessage(''), 2000)
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#060812]">
        <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-brand-orange" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Seguridad</h1>
          <p className="text-sm text-white/40">
            Configurá 2FA, passkeys, dispositivos y monitoreo
          </p>
        </div>
      </div>

      {message && (
        <div className="mb-6 flex items-center gap-2 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
          <CheckCircle2 className="w-4 h-4" />
          {message}
        </div>
      )}

      {error && (
        <div className="mb-6 flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* 2FA TOTP Section */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <Smartphone className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Autenticación TOTP (App)</h2>
        </div>

        {user?.is_2fa_enabled ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-emerald-400 text-sm">
              <CheckCircle2 className="w-4 h-4" />
              TOTP activado
            </div>
            <p className="text-sm text-white/40">
              Tu cuenta está protegida con TOTP. Se requiere un código de tu app de autenticación en cada login.
            </p>
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-2 mb-2">
                <Key className="w-4 h-4 text-brand-orange" />
                <span className="text-sm font-medium text-white/80">Códigos de backup</span>
              </div>
              <p className="text-sm text-white/40 mb-2">
                Te quedan <b className="text-white/60">{backupRemaining}</b> códigos de backup disponibles.
              </p>
              {backupRemaining === 0 && (
                <p className="text-xs text-red-400">
                  ⚠️ Sin códigos de backup. Si perdés tu dispositivo, no podrás acceder a tu cuenta.
                </p>
              )}
            </div>
            <div className="pt-4 border-t border-white/10">
              <p className="text-sm text-white/40 mb-3">Para desactivar TOTP, ingresá un código válido:</p>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value)}
                  placeholder="Código TOTP"
                  className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-brand-orange/50"
                />
                <button
                  onClick={handleDisable2FA}
                  disabled={processing || !disableCode}
                  className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm hover:bg-red-500/20 transition-all disabled:opacity-50"
                >
                  {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Desactivar'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-white/40">
              Activá TOTP para agregar una capa extra de seguridad con apps como Google Authenticator o Authy.
            </p>
            {!setupData ? (
              <button
                onClick={handleSetup2FA}
                disabled={processing}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-sm hover:bg-brand-orange/20 transition-all disabled:opacity-50"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Smartphone className="w-4 h-4" />}
                Configurar TOTP
              </button>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={setupData.qr_code} alt="QR 2FA" className="w-48 h-48 rounded-xl" />
                </div>
                <div className="text-center">
                  <p className="text-xs text-white/40 mb-1">Clave secreta (por si no podés escanear el QR):</p>
                  <code className="inline-block px-3 py-1 rounded bg-white/5 text-white/60 text-xs font-mono">
                    {setupData.secret}
                  </code>
                  <button
                    onClick={() => copyToClipboard(setupData.secret)}
                    className="ml-2 text-brand-orange text-xs hover:underline"
                  >
                    Copiar
                  </button>
                </div>
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={verifyCode}
                    onChange={(e) => setVerifyCode(e.target.value)}
                    placeholder="Código de 6 dígitos"
                    className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-brand-orange/50"
                  />
                  <button
                    onClick={handleVerify2FA}
                    disabled={processing || verifyCode.length < 6}
                    className="px-4 py-2 rounded-lg bg-brand-orange text-white text-sm hover:bg-brand-orange/90 transition-all disabled:opacity-50"
                  >
                    {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verificar'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Backup codes modal */}
      {showCodes && backupCodes && (
        <div className="mb-8 p-6 rounded-2xl bg-emerald-500/5 border border-emerald-500/20">
          <div className="flex items-center gap-2 mb-3">
            <Key className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-semibold text-emerald-400">Códigos de backup generados</h3>
          </div>
          <p className="text-xs text-white/40 mb-3">
            Guardá estos códigos en un lugar seguro. Solo se muestran una vez y te permiten acceder si perdés tu dispositivo.
          </p>
          <div className="grid grid-cols-2 gap-2 mb-4">
            {backupCodes.map((code, i) => (
              <div
                key={i}
                className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/5 border border-white/10"
              >
                <code className="text-white/60 text-xs font-mono">{code}</code>
                <button onClick={() => copyToClipboard(code)} className="text-white/30 hover:text-white/60">
                  <Copy className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
          <button
            onClick={() => setShowCodes(false)}
            className="text-xs text-emerald-400 hover:underline"
          >
            Entendido, guardé los códigos
          </button>
        </div>
      )}

      {/* Email OTP */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <Mail className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Verificación por email</h2>
        </div>
        {emailOtpEnabled ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-emerald-400 text-sm">
              <CheckCircle2 className="w-4 h-4" />
              Verificación por email activada
            </div>
            <p className="text-sm text-white/40">
              Recibirás un código de 6 dígitos en tu email para logins desde dispositivos nuevos.
            </p>
            <button
              onClick={handleDisableEmailOTP}
              disabled={processing}
              className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm hover:bg-red-500/20 transition-all disabled:opacity-50"
            >
              {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Desactivar'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-white/40">
              Activá la verificación por email para recibir códigos OTP cuando inicies sesión desde dispositivos desconocidos.
            </p>
            {!showEmailOtpSetup ? (
              <button
                onClick={handleSetupEmailOTP}
                disabled={processing}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-sm hover:bg-brand-orange/20 transition-all disabled:opacity-50"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                Activar verificación por email
              </button>
            ) : (
              <div className="flex gap-3">
                <input
                  type="text"
                  value={emailOtpCode}
                  onChange={(e) => setEmailOtpCode(e.target.value)}
                  placeholder="Código de 6 dígitos"
                  className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-brand-orange/50"
                />
                <button
                  onClick={handleVerifyEmailOTP}
                  disabled={processing || emailOtpCode.length < 6}
                  className="px-4 py-2 rounded-lg bg-brand-orange text-white text-sm hover:bg-brand-orange/90 transition-all disabled:opacity-50"
                >
                  {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verificar'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Passkeys */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <Fingerprint className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Passkeys (WebAuthn)</h2>
        </div>
        <p className="text-sm text-white/40 mb-4">
          Usá tu huella digital, Face ID o PIN del dispositivo para iniciar sesión de forma segura sin contraseñas.
        </p>
        {passkeys.length > 0 && (
          <div className="space-y-2 mb-4">
            {passkeys.map((pk) => (
              <div
                key={pk.id}
                className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center gap-3">
                  <Fingerprint className="w-4 h-4 text-white/40" />
                  <div>
                    <p className="text-sm text-white/80">{pk.device_name}</p>
                    <p className="text-xs text-white/30">
                      Registrado {new Date(pk.created_at).toLocaleDateString('es-ES')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDeletePasskey(pk.id)}
                  disabled={processing}
                  className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
        {!showPasskeyForm ? (
          <button
            onClick={() => setShowPasskeyForm(true)}
            disabled={processing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-orange/10 border border-brand-orange/20 text-brand-orange text-sm hover:bg-brand-orange/20 transition-all disabled:opacity-50"
          >
            <Fingerprint className="w-4 h-4" />
            Agregar passkey
          </button>
        ) : (
          <div className="flex gap-3">
            <input
              type="text"
              value={passkeyName}
              onChange={(e) => setPasskeyName(e.target.value)}
              placeholder="Nombre del dispositivo (ej: iPhone de Juan)"
              className="flex-1 px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-brand-orange/50"
            />
            <button
              onClick={handleRegisterPasskey}
              disabled={processing || !passkeyName}
              className="px-4 py-2 rounded-lg bg-brand-orange text-white text-sm hover:bg-brand-orange/90 transition-all disabled:opacity-50"
            >
              {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Registrar'}
            </button>
            <button
              onClick={() => setShowPasskeyForm(false)}
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 text-sm hover:bg-white/10 transition-all"
            >
              Cancelar
            </button>
          </div>
        )}
      </div>

      {/* Trusted Devices */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <Monitor className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Dispositivos confiables</h2>
        </div>
        {devices.length === 0 ? (
          <p className="text-sm text-white/40">No hay dispositivos registrados.</p>
        ) : (
          <div className="space-y-2">
            {devices.map((device) => (
              <div
                key={device.id}
                className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center gap-3">
                  <Monitor className="w-4 h-4 text-white/40" />
                  <div>
                    <p className="text-sm text-white/80">
                      {device.device_name || 'Dispositivo desconocido'}
                    </p>
                    <p className="text-xs text-white/30">
                      {device.os} · {device.browser} · {device.ip_address}
                    </p>
                    <p className="text-xs text-white/20">
                      Último uso: {new Date(device.last_seen_at).toLocaleDateString('es-ES')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {device.is_trusted ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : device.is_blocked ? (
                    <AlertOctagon className="w-4 h-4 text-red-400" />
                  ) : (
                    <X className="w-4 h-4 text-white/30" />
                  )}
                  {!device.is_trusted && !device.is_blocked && (
                    <button
                      onClick={() => handleTrustDevice(device.id)}
                      className="p-1.5 rounded-lg text-emerald-400 hover:bg-emerald-500/10 transition-all"
                      title="Marcar como confiable"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {device.is_trusted && (
                    <button
                      onClick={() => handleRevokeDevice(device.id)}
                      className="p-1.5 rounded-lg text-white/40 hover:bg-white/10 transition-all"
                      title="Revocar confianza"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {!device.is_blocked && (
                    <button
                      onClick={() => handleBlockDevice(device.id)}
                      className="p-1.5 rounded-lg text-red-400 hover:bg-red-500/10 transition-all"
                      title="Bloquear dispositivo"
                    >
                      <Lock className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Active Sessions */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Sesiones activas</h2>
        </div>
        {sessions.length === 0 ? (
          <p className="text-sm text-white/40">No hay sesiones activas.</p>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center gap-3">
                  <Globe className="w-4 h-4 text-white/40" />
                  <div>
                    <p className="text-sm text-white/80">
                      {session.location || session.ip_address}
                      {session.is_current && (
                        <span className="ml-2 text-xs text-emerald-400">(actual)</span>
                      )}
                    </p>
                    <p className="text-xs text-white/30">{session.user_agent}</p>
                    <p className="text-xs text-white/20">
                      Último uso: {new Date(session.last_used_at).toLocaleDateString('es-ES')}
                    </p>
                  </div>
                </div>
                {!session.is_current && (
                  <button
                    onClick={() => handleKillSession(session.id)}
                    className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs hover:bg-red-500/20 transition-all"
                  >
                    Cerrar
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Geofencing Info */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <MapPin className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Geofencing</h2>
        </div>
        <p className="text-sm text-white/40 mb-3">
          El sistema detecta automáticamente logins desde ubicaciones inesperadas.
        </p>
        {config?.max_distance_km ? (
          <div className="text-sm text-white/60">
            Distancia máxima permitida: <b className="text-white">{config.max_distance_km} km</b> desde tu último login.
            {config.alert_on_geofence && (
              <span className="text-emerald-400 ml-2">● Alertas activadas</span>
            )}
          </div>
        ) : (
          <p className="text-sm text-white/30">Geofencing desactivado por el administrador.</p>
        )}
      </div>

      {/* Breach Monitoring */}
      <div className="mb-8 p-6 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-5 h-5 text-brand-orange" />
          <h2 className="text-lg font-semibold text-white">Monitoreo de breaches</h2>
        </div>
        <p className="text-sm text-white/40">
          Verificamos automáticamente si tu email aparece en filtraciones de datos conocidas (Have I Been Pwned).
          {config?.alert_on_breach ? (
            <span className="text-emerald-400 ml-2">● Activado</span>
          ) : (
            <span className="text-white/30 ml-2">● Desactivado</span>
          )}
        </p>
      </div>

      {/* Account Deletion */}
      <div className="p-6 rounded-2xl bg-red-500/[0.03] border border-red-500/[0.1]">
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <h2 className="text-lg font-semibold text-white">Eliminar cuenta</h2>
        </div>
        <p className="text-sm text-white/40 mb-4">
          Esta acción es irreversible. Todos tus datos serán eliminados permanentemente de nuestros sistemas.
        </p>
        {!showDeleteConfirm ? (
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm hover:bg-red-500/20 transition-all"
          >
            Eliminar mi cuenta
          </button>
        ) : (
          <div className="space-y-3">
            <input
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              placeholder="Ingresá tu contraseña para confirmar"
              className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-red-500/50"
            />
            <textarea
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              placeholder="Motivo de la eliminación (opcional)"
              rows={2}
              className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm placeholder-white/20 focus:outline-none focus:border-red-500/50 resize-none"
            />
            <div className="flex gap-3">
              <button
                onClick={handleDeleteAccount}
                disabled={processing || !deletePassword}
                className="px-4 py-2 rounded-lg bg-red-500 text-white text-sm hover:bg-red-600 transition-all disabled:opacity-50"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Confirmar eliminación'}
              </button>
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setDeletePassword('')
                  setDeleteReason('')
                }}
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white/60 text-sm hover:bg-white/10 transition-all"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Base64url helpers for WebAuthn
function base64urlToBuffer(base64url: string): ArrayBuffer {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/')
  const pad = base64.length % 4
  const padded = pad ? base64 + '='.repeat(4 - pad) : base64
  const binary = atob(padded)
  const buffer = new ArrayBuffer(binary.length)
  const view = new Uint8Array(buffer)
  for (let i = 0; i < binary.length; i++) {
    view[i] = binary.charCodeAt(i)
  }
  return buffer
}

function bufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}
