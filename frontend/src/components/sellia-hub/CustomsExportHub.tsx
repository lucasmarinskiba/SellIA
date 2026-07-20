'use client'

/**
 * CUSTOMS EXPORT HUB — RETAIN lobe — style migration.
 * DGA · ARCA · COVE, Certificado de Origen, DJVE, PE, Manifiesto, INCOTERMS, NCM.
 */

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Ship, Plane, Globe2, FileBadge, BookOpen, Container, Award, AlertTriangle,
  CheckCircle2, Hash, MapPin, DollarSign,
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

type TramiteId = 'cove' | 'origen' | 'djve' | 'pe' | 'manifiesto' | 'incoterms' | 'ncm'

interface TramiteCard {
  id: TramiteId
  title: string
  subtitle: string
  icon: React.ComponentType<{ style?: React.CSSProperties }>
  cluster: 'documental' | 'fiscal' | 'logistico' | 'referencia'
  endpoint: string
}

const TRAMITES: TramiteCard[] = [
  { id: 'cove',       title: 'COVE',                    subtitle: 'Comprobante Venta Exterior · pre-oficialización', icon: FileBadge,  cluster: 'documental', endpoint: 'POST /arca/aduana/cove' },
  { id: 'origen',     title: 'Certificado de Origen',   subtitle: 'MERCOSUR · ALADI · SGP · CAN',                    icon: Award,      cluster: 'documental', endpoint: 'POST /arca/aduana/origen' },
  { id: 'djve',       title: 'DJVE',                    subtitle: 'DJ Venta Exterior · agro · retenciones DE',       icon: BookOpen,   cluster: 'fiscal',     endpoint: 'POST /arca/aduana/djve' },
  { id: 'pe',         title: 'Permiso de Embarque',     subtitle: 'SIM MALVINA · derechos + reintegros + canal',     icon: Ship,       cluster: 'logistico',  endpoint: 'POST /arca/aduana/permiso-embarque' },
  { id: 'manifiesto', title: 'Manifiesto WSCOEM',       subtitle: 'Manifiesto electrónico de carga · ATA',           icon: Container,  cluster: 'logistico',  endpoint: 'POST /arca/aduana/manifiesto' },
  { id: 'incoterms',  title: 'INCOTERMS 2020',          subtitle: '11 reglas · transferencia riesgo + costos',       icon: Globe2,     cluster: 'referencia', endpoint: 'GET /arca/aduana/incoterms' },
  { id: 'ncm',        title: 'NCM / HS Code',           subtitle: 'Validador 8 dígitos + descripción',               icon: Hash,       cluster: 'referencia', endpoint: 'GET /arca/aduana/ncm/{code}' },
]

const CLUSTER_TONES: Record<TramiteCard['cluster'], { label: string; color: string }> = {
  documental: { label: 'DOCUMENTAL', color: T.amber   },
  fiscal:     { label: 'FISCAL',     color: T.cyan    },
  logistico:  { label: 'LOGÍSTICO',  color: T.violet  },
  referencia: { label: 'REFERENCIA', color: T.emerald },
}

interface IncotermRow {
  code: string
  name: string
  grupo: string
  modo: string
  paga_flete: string
  paga_seguro: string
  transferencia_riesgo: string
}

export const CustomsExportHub = (): React.JSX.Element => {
  const [active, setActive] = useState<TramiteId>('cove')
  const [loading, setLoading] = useState<boolean>(false)
  const [result, setResult] = useState<unknown>(null)
  const [error, setError] = useState<string | null>(null)
  const [incoterms, setIncoterms] = useState<IncotermRow[]>([])
  const [ncmCode, setNcmCode] = useState<string>('')

  const activeCard = useMemo<TramiteCard>(
    () => TRAMITES.find((t) => t.id === active) ?? TRAMITES[0],
    [active],
  )

  useEffect(() => {
    if (active !== 'incoterms') return
    const load = async (): Promise<void> => {
      setLoading(true); setError(null)
      try {
        const r = await api.get<IncotermRow[]>('/arca/aduana/incoterms')
        setIncoterms(r.data)
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Error cargando INCOTERMS')
      } finally { setLoading(false) }
    }
    void load()
  }, [active])

  const lookupNcm = useCallback(async (): Promise<void> => {
    if (ncmCode.replace(/\D/g, '').length !== 8) { setError('NCM debe tener 8 dígitos'); return }
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await api.get(`/arca/aduana/ncm/${encodeURIComponent(ncmCode)}`)
      setResult(r.data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'NCM inválido')
    } finally { setLoading(false) }
  }, [ncmCode])

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #10B98180, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Ship style={{ width: 18, height: 18, color: T.violet }} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Customs Export Hub
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· DGA · ARCA · exportación</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>Exportá a cualquier país sin pisar la aduana</div>
          </div>
        </div>
        <div style={{ padding: '4px 12px', borderRadius: 6, fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', background: T.violet + '18', border: '1px solid ' + T.violet + '40', color: T.violet }}>
          {TRAMITES.length} TRÁMITES · MERCOSUR + ALADI + SGP + CAN
        </div>
      </div>

      {/* Tramite grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '16px 20px' }}>
        {TRAMITES.map((t) => {
          const Icon = t.icon
          const cluster = CLUSTER_TONES[t.cluster]
          const isActive = t.id === active
          return (
            <button key={t.id} type="button"
              onClick={() => { setActive(t.id); setResult(null); setError(null) }}
              style={{ textAlign: 'left', borderRadius: 10, border: '1px solid ' + (isActive ? cluster.color + '80' : T.border), background: isActive ? cluster.color + '12' : T.bgApp, padding: 12, cursor: 'pointer', transition: 'all .15s' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <Icon style={{ width: 16, height: 16, color: cluster.color }} />
                <span style={{ fontSize: 8, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: cluster.color }}>{cluster.label}</span>
              </div>
              <div style={{ fontSize: 11, fontWeight: 700, color: T.textPrim, lineHeight: 1.3, marginBottom: 2 }}>{t.title}</div>
              <div style={{ fontSize: 9, color: T.textSub, lineHeight: 1.4 }}>{t.subtitle}</div>
            </button>
          )
        })}
      </div>

      {/* Active panel */}
      <div style={{ margin: '0 20px 16px', background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim }}>{activeCard.title}</div>
          <code style={{ fontSize: 9, color: T.violet + 'aa', fontFamily: 'JetBrains Mono,monospace' }}>{activeCard.endpoint}</code>
        </div>

        {active === 'ncm' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 10, color: T.textSub }}>Código NCM (8 dígitos · con o sin puntos)</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input type="text" value={ncmCode} onChange={e => setNcmCode(e.target.value.toUpperCase())} placeholder="8471.30.12"
                style={{ flex: 1, background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 8, padding: '8px 12px', fontSize: 12, fontFamily: 'JetBrains Mono,monospace', color: T.textPrim, outline: 'none' }} />
              <button type="button" onClick={lookupNcm} disabled={loading}
                style={{ padding: '8px 18px', borderRadius: 8, background: T.violet + '22', border: '1px solid ' + T.violet + '55', color: T.violet, fontSize: 11, fontWeight: 700, cursor: 'pointer', opacity: loading ? 0.5 : 1 }}>
                {loading ? 'Buscando…' : 'Validar'}
              </button>
            </div>
          </div>
        )}

        {active === 'incoterms' && (
          <div style={{ maxHeight: 260, overflow: 'auto', borderRadius: 8, border: '1px solid ' + T.border }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
              <thead style={{ position: 'sticky', top: 0, background: T.bgApp }}>
                <tr>
                  {['Code', 'Nombre', 'Modo', 'Flete', 'Seguro', 'Riesgo'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '8px 10px', fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, borderBottom: '1px solid ' + T.border }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {incoterms.map((row) => (
                  <tr key={row.code} style={{ borderTop: '1px solid ' + T.border + '44' }}>
                    <td style={{ padding: '7px 10px', fontFamily: 'JetBrains Mono,monospace', fontWeight: 700, color: T.violet }}>{row.code}</td>
                    <td style={{ padding: '7px 10px', color: T.textPrim }}>{row.name}</td>
                    <td style={{ padding: '7px 10px', color: T.textSub }}>{row.modo}</td>
                    <td style={{ padding: '7px 10px', color: T.textSub }}>{row.paga_flete}</td>
                    <td style={{ padding: '7px 10px', color: T.textSub }}>{row.paga_seguro}</td>
                    <td style={{ padding: '7px 10px', color: T.textSub, fontSize: 9 }}>{row.transferencia_riesgo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {(active === 'cove' || active === 'origen' || active === 'djve' || active === 'pe' || active === 'manifiesto') && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: T.cyan }}>
              <CheckCircle2 style={{ width: 14, height: 14 }} />
              SellIA pre-llena este trámite usando los datos del deal cerrado + Factura E asociada. Solo confirmás.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              {[
                { icon: MapPin,     label: 'País destino',     value: 'BR · Brasil' },
                { icon: DollarSign, label: 'Valor FOB',        value: 'USD 18.400' },
                { icon: Globe2,     label: 'INCOTERM',         value: 'FOB · Bs. As.' },
                { icon: Hash,       label: 'NCM principal',    value: '8471.30.12' },
                { icon: Plane,      label: 'Medio transporte', value: 'Aéreo · EZE→GRU' },
                { icon: Award,      label: 'Régimen origen',   value: 'MERCOSUR ACE-18' },
              ].map(({ icon: Icon, label, value }) => (
                <div key={label} style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 8, padding: '8px 10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 4 }}>
                    <Icon style={{ width: 10, height: 10 }} /> {label}
                  </div>
                  <div style={{ fontSize: 11, fontFamily: 'JetBrains Mono,monospace', color: T.textPrim, fontWeight: 600 }}>{value}</div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button style={{ padding: '7px 14px', borderRadius: 8, fontSize: 11, cursor: 'pointer', background: 'transparent', border: '1px solid ' + T.border, color: T.textSub }}>Vista previa JSON</button>
              <button style={{ padding: '7px 18px', borderRadius: 8, fontSize: 11, fontWeight: 700, cursor: 'pointer', background: T.violet + '22', border: '1px solid ' + T.violet + '55', color: T.violet }}>Emitir + Oficializar (CUA)</button>
            </div>
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: T.rose, fontSize: 11, padding: '8px 12px', borderRadius: 8, background: T.rose + '12', border: '1px solid ' + T.rose + '28', marginTop: 8 }}>
            <AlertTriangle style={{ width: 14, height: 14 }} /> {error}
          </div>
        )}

        {result !== null && active === 'ncm' && (
          <div style={{ marginTop: 12, borderRadius: 8, border: '1px solid ' + T.emerald + '44', background: T.emerald + '08', padding: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: T.emerald, fontFamily: 'monospace', marginBottom: 8 }}>
              <CheckCircle2 style={{ width: 12, height: 12 }} /> NCM VÁLIDO
            </div>
            <pre style={{ fontSize: 10, color: T.textPrim, fontFamily: 'JetBrains Mono,monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0 }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '0 20px 16px' }}>
        {[
          { label: 'Países cubiertos',     value: '184',      color: T.emerald },
          { label: 'Regímenes activos',    value: '5',        color: T.cyan    },
          { label: 'Embarques este mes',   value: '12',       color: T.violet  },
          { label: 'Reintegros liquidados',value: 'USD 9.4k', color: T.amber   },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: '10px 14px' }}>
            <div style={{ fontSize: 18, fontWeight: 800, color, textShadow: '0 0 20px ' + color + '88' }}>{value}</div>
            <div style={{ fontSize: 9, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginTop: 2 }}>{label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

export default CustomsExportHub
