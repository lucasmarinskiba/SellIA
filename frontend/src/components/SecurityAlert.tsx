'use client'

import { useEffect, useState } from 'react'
import { Shield, ShieldAlert, ShieldCheck, X } from 'lucide-react'
import { auth, SecurityStatus } from '@/lib/auth'

export default function SecurityAlert() {
  const [status, setStatus] = useState<SecurityStatus | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    auth
      .securityStatus()
      .then((data) => {
        if (mounted) setStatus(data)
      })
      .catch(() => {
        // Silencioso: no bloquear UI si falla
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [])

  if (loading || dismissed || !status) return null

  const hasIssues =
    status.risk_score > 0 ||
    status.mitm_detected ||
    status.is_tor ||
    status.recommendations.length > 0 ||
    (status.cloudflare?.is_high_risk_country ?? false)

  if (!hasIssues) {
    return (
      <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 px-4 py-2.5 text-xs text-emerald-400 backdrop-blur-md">
        <ShieldCheck className="w-4 h-4" />
        <span>
          {status.cloudflare?.is_cloudflare
            ? 'Conexión segura (Cloudflare) ✅'
            : 'Conexión segura verificada'}
        </span>
      </div>
    )
  }

  const severity = status.mitm_detected || status.is_tor || status.cloudflare?.is_high_risk_country ? 'critical' : 'warning'

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 max-w-sm rounded-xl border px-4 py-3 text-sm shadow-2xl backdrop-blur-md ${
        severity === 'critical'
          ? 'bg-red-500/10 border-red-500/20 text-red-300'
          : 'bg-amber-500/10 border-amber-500/20 text-amber-300'
      }`}
    >
      <div className="flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5" />
        <div className="flex-1 space-y-1">
          <p className="font-semibold">
            {severity === 'critical'
              ? 'Alerta de seguridad detectada'
              : 'Revisá tu conexión'}
          </p>
          <ul className="list-disc list-inside text-xs opacity-90 space-y-0.5">
            {status.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
            {status.is_vpn && (
              <li>
                VPN detectada. Asegurate de usar una VPN de confianza y mantené tu
                antivirus actualizado.
              </li>
            )}
            {status.cloudflare?.is_high_risk_country && (
              <li>
                Conexión desde país de alto riesgo. Verificá tu identidad adicionalmente.
              </li>
            )}
            {status.cloudflare?.is_cloudflare && !status.cloudflare?.cf_valid_origin && (
              <li className="text-red-400 font-semibold">
                ⚠️ Posible spoofing de headers de Cloudflare detectado.
              </li>
            )}
          </ul>
          <div className="pt-1 text-[11px] opacity-70">
            Consejo: {status.tips[Math.floor(Math.random() * status.tips.length)]}
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="shrink-0 opacity-60 hover:opacity-100 transition-opacity"
          aria-label="Cerrar alerta"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
