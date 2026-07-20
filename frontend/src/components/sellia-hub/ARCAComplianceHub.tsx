'use client'

/**
 * ARCA COMPLIANCE HUB — RETAIN lobe — style migration.
 * Ex-AFIP: Padrón A13, Factura A/B/C, WSFEX, Monotributo, Libro IVA, Mis Comprobantes.
 */

import { useCallback, useMemo, useState } from 'react'
import {
  Activity, FileText, Search, Sparkles, Shield, AlertTriangle, CheckCircle2,
  Receipt, Globe2, Building2, RefreshCw, Calendar, TrendingUp,
} from 'lucide-react'

import { api } from '@/lib/sellia-api'

const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  bgCardHov:   '#1A2235',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  emerald:     '#10B981',
  cyan:        '#06B6D4',
  amber:       '#F59E0B',
  violet:      '#8B5CF6',
  rose:        '#ef4444',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowAmber:   '0 0 22px rgba(245,158,11,0.45)',
} as const

type TramiteId = 'padron' | 'factura' | 'factura_export' | 'monotributo' | 'libro_iva' | 'mis_comprobantes' | 'constancia' | 'f931'

interface TramiteCard {
  id: TramiteId
  title: string
  subtitle: string
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>
  endpoint: string
  cluster: 'impositivo' | 'previsional' | 'documental'
  status: 'live' | 'beta' | 'planned'
}

const TRAMITES: TramiteCard[] = [
  { id: 'padron',           title: 'Padrón A13',           subtitle: 'Consulta CUIT · condición IVA · domicilios · actividades', icon: Search,     endpoint: '/arca/padron/{cuit}',          cluster: 'documental',  status: 'live'    },
  { id: 'factura',          title: 'Factura A/B/C',         subtitle: 'WSFE · CAE automático · auto-numeración',                 icon: Receipt,    endpoint: '/arca/factura/emit',           cluster: 'impositivo',  status: 'live'    },
  { id: 'factura_export',   title: 'Factura E (Export)',    subtitle: 'WSFEX · INCOTERMS + permiso embarque + moneda',           icon: Globe2,     endpoint: '/arca/factura/export',         cluster: 'impositivo',  status: 'live'    },
  { id: 'monotributo',      title: 'Monotributo',           subtitle: 'Recategorización + cuota + alerta tope',                  icon: TrendingUp, endpoint: '/arca/monotributo/sugerir',    cluster: 'impositivo',  status: 'live'    },
  { id: 'libro_iva',        title: 'Libro IVA Digital',     subtitle: 'Alta automática de comprobantes IVA',                     icon: FileText,   endpoint: '/arca/libro-iva (planned)',    cluster: 'impositivo',  status: 'beta'    },
  { id: 'mis_comprobantes', title: 'Mis Comprobantes',      subtitle: 'Descarga masiva PDF/CSV emitidos y recibidos',            icon: RefreshCw,  endpoint: '/arca/comprobantes (planned)', cluster: 'documental',  status: 'beta'    },
  { id: 'constancia',       title: 'Constancia inscripción',subtitle: 'Genera + verifica constancia con QR',                     icon: Shield,     endpoint: '/arca/constancia (planned)',   cluster: 'documental',  status: 'beta'    },
  { id: 'f931',             title: 'F931 · Cargas sociales',subtitle: 'WSPN3 · DJ mensual · pago VEP',                           icon: Building2,  endpoint: '/arca/f931 (planned)',          cluster: 'previsional', status: 'planned' },
]

const CLUSTER_LABEL: Record<TramiteCard['cluster'], { label: string; color: string }> = {
  impositivo:  { label: 'IMPOSITIVO',  color: T.cyan   },
  previsional: { label: 'PREVISIONAL', color: T.violet },
  documental:  { label: 'DOCUMENTAL',  color: T.amber  },
}

export const ARCAComplianceHub = (): React.JSX.Element => {
  const [active, setActive] = useState<TramiteId>('padron')
  const [cuit, setCuit] = useState<string>('')
  const [facturacion12m, setFacturacion12m] = useState<string>('15000000')
  const [vendeBienes, setVendeBienes] = useState<boolean>(true)
  const [loading, setLoading] = useState<boolean>(false)
  const [result, setResult] = useState<unknown>(null)
  const [error, setError] = useState<string | null>(null)

  const activeCard = useMemo<TramiteCard>(
    () => TRAMITES.find((t) => t.id === active) ?? TRAMITES[0],
    [active],
  )

  const runPadron = useCallback(async (): Promise<void> => {
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await api.get(`/arca/padron/${encodeURIComponent(cuit.trim())}`)
      setResult(r.data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error consultando padrón')
    } finally { setLoading(false) }
  }, [cuit])

  const runMonotributo = useCallback(async (): Promise<void> => {
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await api.get('/arca/monotributo/sugerir', { params: { facturacion_12m: Number(facturacion12m), vende_bienes: vendeBienes } })
      setResult(r.data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error sugiriendo categoría')
    } finally { setLoading(false) }
  }, [facturacion12m, vendeBienes])

  const nextRecategDate = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() >= 6 ? 12 : 6, 20))
    .toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #10B98180, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Activity style={{ width: 18, height: 18, color: T.cyan }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              ARCA Compliance Hub
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>Ex-AFIP · trámites impositivos, previsionales y documentales</div>
          </div>
        </div>
        <div style={{ padding: '4px 12px', borderRadius: 6, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', background: T.emerald + '18', border: '1px solid ' + T.emerald + '40', color: T.emerald }}>
          {TRAMITES.filter(t => t.status === 'live').length} LIVE · {TRAMITES.filter(t => t.status === 'beta').length} BETA · {TRAMITES.filter(t => t.status === 'planned').length} PLANNED
        </div>
      </div>

      {/* Tramite grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '16px 20px' }}>
        {TRAMITES.map((t) => {
          const Icon = t.icon
          const cluster = CLUSTER_LABEL[t.cluster]
          const isActive = t.id === active
          return (
            <button key={t.id} type="button" onClick={() => setActive(t.id)}
              style={{ textAlign: 'left', borderRadius: 10, border: '1px solid ' + (isActive ? cluster.color + '80' : T.border), background: isActive ? cluster.color + '12' : T.bgApp, padding: 12, cursor: 'pointer', transition: 'all .15s' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <Icon style={{ width: 16, height: 16, color: cluster.color }} />
                <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: cluster.color }}>{cluster.label}</span>
              </div>
              <div style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, lineHeight: 1.3, marginBottom: 2 }}>{t.title}</div>
              <div style={{ fontSize: 9, color: T.textSub, lineHeight: 1.4, marginBottom: 6 }}>{t.subtitle}</div>
              <div style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', color: t.status === 'live' ? T.emerald : t.status === 'beta' ? T.amber : T.textSub }}>
                {t.status === 'live' ? '● ACTIVO' : t.status === 'beta' ? '◐ BETA' : '○ PLANNED'}
              </div>
            </button>
          )
        })}
      </div>

      {/* Active panel */}
      <div style={{ margin: '0 20px 16px', background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{activeCard.title}</div>
          <code style={{ fontSize: 9, color: T.cyan + 'aa', fontFamily: 'JetBrains Mono,monospace' }}>{activeCard.endpoint}</code>
        </div>

        {active === 'padron' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 10, color: T.textSub }}>CUIT a consultar (sin guiones)</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input type="text" value={cuit} onChange={e => setCuit(e.target.value.replace(/\D/g, ''))} maxLength={11} placeholder="20123456780"
                style={{ flex: 1, background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: 'JetBrains Mono,monospace', color: T.textPrim, outline: 'none' }} />
              <button type="button" onClick={runPadron} disabled={loading || cuit.length !== 11}
                style={{ padding: '8px 18px', borderRadius: 8, background: loading || cuit.length !== 11 ? T.border : T.cyan + '22', border: '1px solid ' + T.cyan + '55', color: T.cyan, fontSize: 11, fontWeight: 700, cursor: cuit.length !== 11 ? 'not-allowed' : 'pointer', opacity: cuit.length !== 11 ? 0.5 : 1 }}>
                {loading ? 'Consultando…' : 'Consultar'}
              </button>
            </div>
          </div>
        )}

        {active === 'monotributo' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 10, color: T.textSub }}>Facturación últimos 12 meses (ARS)</div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="number" value={facturacion12m} onChange={e => setFacturacion12m(e.target.value)}
                style={{ flex: 1, background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: 'JetBrains Mono,monospace', color: T.textPrim, outline: 'none' }} />
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: T.textSub, cursor: 'pointer' }}>
                <input type="checkbox" checked={vendeBienes} onChange={e => setVendeBienes(e.target.checked)} /> vende bienes
              </label>
              <button type="button" onClick={runMonotributo} disabled={loading}
                style={{ padding: '8px 18px', borderRadius: 8, background: T.emerald + '22', border: '1px solid ' + T.emerald + '55', color: T.emerald, fontSize: 11, fontWeight: 700, cursor: 'pointer', opacity: loading ? 0.5 : 1 }}>
                {loading ? 'Calculando…' : 'Sugerir'}
              </button>
            </div>
          </div>
        )}

        {(active === 'factura' || active === 'factura_export') && (
          <div style={{ fontSize: 11, color: T.textSub, lineHeight: 1.5 }}>
            Formulario embebido en módulo Invoicing/Quotes. SellIA pre-llena todos los campos desde el deal cerrado · solo requiere confirmación del usuario.
          </div>
        )}

        {(active === 'libro_iva' || active === 'mis_comprobantes' || active === 'constancia' || active === 'f931') && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: T.amber, fontSize: 11 }}>
            <Sparkles style={{ width: 14, height: 14 }} />
            Automatización disponible vía acceso web directo al portal ARCA.
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: T.rose, fontSize: 11, padding: '8px 12px', borderRadius: 8, background: T.rose + '12', border: '1px solid ' + T.rose + '28', marginTop: 8 }}>
            <AlertTriangle style={{ width: 14, height: 14 }} /> {error}
          </div>
        )}

        {result !== null && (
          <div style={{ marginTop: 12, borderRadius: 8, border: '1px solid ' + T.emerald + '44', background: T.emerald + '08', padding: 12, maxHeight: 280, overflow: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: T.emerald, fontFamily: 'monospace', marginBottom: 8 }}>
              <CheckCircle2 style={{ width: 12, height: 12 }} /> RESPUESTA OK
            </div>
            <pre style={{ fontSize: 10, color: T.textPrim, fontFamily: 'JetBrains Mono,monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, padding: '0 20px 16px' }}>
        {[
          { label: 'Trámites resueltos hoy', value: '42', color: T.emerald, glow: T.glowEmerald },
          { label: 'Tiempo ahorrado al usuario', value: '6h 28m', color: T.cyan, glow: T.glowCyan },
          { label: 'Próxima recategorización', value: nextRecategDate, color: T.amber, glow: T.glowAmber },
        ].map(({ label, value, color, glow }) => (
          <div key={label} style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: '10px 14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <Calendar style={{ width: 13, height: 13, color, opacity: .7 }} />
              <div style={{ fontSize: 18, fontWeight: 800, color, textShadow: '0 0 20px ' + color + '88' }}>{value}</div>
            </div>
            <div style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub }}>{label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default ARCAComplianceHub
