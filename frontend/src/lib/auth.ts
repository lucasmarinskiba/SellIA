import { api } from './api'

export interface LoginData {
  email: string
  password: string
  turnstileToken?: string
  tfaCode?: string
}

export interface RegisterData {
  email: string
  password: string
  full_name: string
  honeypot?: string
}

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  is_2fa_enabled: boolean
  created_at: string
  updated_at: string
}

export interface CloudflareInfo {
  is_cloudflare: boolean
  cf_ray: string | null
  cf_country: string | null
  cf_valid_origin: boolean
  cf_message: string
  is_high_risk_country: boolean
}

export interface SecurityStatus {
  secure_connection: boolean
  risk_score: number
  is_vpn: boolean
  is_tor: boolean
  mitm_detected: boolean
  mitm_headers: string[]
  malicious_ua: boolean
  recommendations: string[]
  device_fingerprint: string
  tips: string[]
  cloudflare: CloudflareInfo
}

export interface TwoFASetupResponse {
  secret: string
  qr_code: string
  provisioning_uri: string
  message: string
}

export interface TwoFAVerifyResponse {
  message: string
  backup_codes?: string[]
  warning?: string
}

export interface BackupCodesStatus {
  remaining: number
}

export const auth = {
  login: async (data: LoginData) => {
    const params = new URLSearchParams()
    params.append('username', data.email)
    params.append('password', data.password)
    const headers: Record<string, string> = {
      'Content-Type': 'application/x-www-form-urlencoded',
    }
    if (data.turnstileToken) {
      headers['X-Turnstile-Token'] = data.turnstileToken
    }
    if (data.tfaCode) {
      headers['X-2FA-Code'] = data.tfaCode
    }
    const res = await api.post('/auth/login', params, { headers })
    return res.data
  },
  register: async (data: RegisterData) => {
    const res = await api.post('/auth/register', data)
    return res.data
  },
  me: async (): Promise<User> => {
    const res = await api.get('/users/me')
    return res.data
  },
  logout: async () => {
    await api.post('/auth/logout')
    if (typeof window !== 'undefined') {
      localStorage.clear()
    }
  },
  securityStatus: async (): Promise<SecurityStatus> => {
    const res = await api.get('/auth/security-status')
    return res.data
  },
  resendVerification: async () => {
    const res = await api.post('/auth/resend-verification')
    return res.data
  },
  // 2FA
  setup2FA: async (): Promise<TwoFASetupResponse> => {
    const res = await api.post('/auth/2fa/setup')
    return res.data
  },
  verify2FA: async (code: string): Promise<TwoFAVerifyResponse> => {
    const res = await api.post('/auth/2fa/verify', null, { params: { code } })
    return res.data
  },
  disable2FA: async (code: string): Promise<{ message: string }> => {
    const res = await api.post('/auth/2fa/disable', null, { params: { code } })
    return res.data
  },
  getBackupCodesStatus: async (): Promise<BackupCodesStatus> => {
    const res = await api.get('/auth/2fa/backup-codes')
    return res.data
  },
  // Passkeys / WebAuthn
  registerPasskeyBegin: async () => {
    const res = await api.post('/auth/webauthn/register-begin')
    return res.data
  },
  registerPasskeyFinish: async (data: unknown) => {
    const res = await api.post('/auth/webauthn/register-finish', data)
    return res.data
  },
  loginPasskeyBegin: async () => {
    const res = await api.post('/auth/webauthn/login-begin')
    return res.data
  },
  loginPasskeyFinish: async (data: unknown) => {
    const res = await api.post('/auth/webauthn/login-finish', data)
    return res.data
  },
  getPasskeys: async (): Promise<{ passkeys: Array<{ id: string; device_name: string; created_at: string }> }> => {
    const res = await api.get('/auth/webauthn/credentials')
    return res.data
  },
  deletePasskey: async (id: string) => {
    const res = await api.delete(`/auth/webauthn/credentials/${id}`)
    return res.data
  },
  // Trusted Devices
  getTrustedDevices: async (): Promise<{ devices: Array<{ id: string; device_name: string | null; os: string | null; browser: string | null; ip_address: string | null; first_seen_at: string; last_seen_at: string; is_trusted: boolean; is_blocked: boolean }> }> => {
    const res = await api.get('/auth/trusted-devices')
    return res.data
  },
  trustDevice: async (id: string) => {
    const res = await api.post(`/auth/trusted-devices/${id}/trust`)
    return res.data
  },
  revokeDevice: async (id: string) => {
    const res = await api.post(`/auth/trusted-devices/${id}/revoke`)
    return res.data
  },
  blockDevice: async (id: string) => {
    const res = await api.post(`/auth/trusted-devices/${id}/block`)
    return res.data
  },
  // Email OTP
  setupEmailOTP: async () => {
    const res = await api.post('/auth/2fa/email/setup')
    return res.data
  },
  sendEmailOTP: async (purpose?: string) => {
    const res = await api.post('/auth/2fa/email/send', null, { params: { purpose } })
    return res.data
  },
  verifyEmailOTP: async (code: string, purpose?: string) => {
    const res = await api.post('/auth/2fa/email/verify', null, { params: { code, purpose } })
    return res.data
  },
  // Account deletion
  deleteAccount: async (password: string, reason?: string) => {
    const res = await api.post('/auth/delete-account', { password, reason })
    return res.data
  },
}
