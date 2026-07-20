'use client'

/**
 * TAX SYNC — RETAIN lobe — FULL RICH REWRITE
 *
 * Country selector tabs, per-country tax rates, compliance status, last sync, sync button.
 */

import { useState, useMemo } from 'react'
import { Globe, RefreshCw, CheckCircle2, AlertTriangle, Clock, Bot } from 'lucide-react'

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

type CountryCode = 'AR' | 'MX' | 'CO' | 'PE' | 'BR' | 'USA' | 'EU'
type ComplianceStatus = 'activo' | 'pendiente' | 'no_configurado' | 'error'

interface TaxRate { name: string; rate: string; desc: string }

interface CountryConfig {
  code: CountryCode
  flag: string
  name: string
  authority: string
  color: string
  status: ComplianceStatus
  lastSync: string
  invoicesMonth: number
  taxCollectedUSD: number
  rates: TaxRate[]
  nextDeadline?: string
  aiNote?: string
}

const COUNTRIES: CountryConfig[] = [
  {
    code: 'AR', flag: '🇦🇷', name: 'Argentina', authority: 'ARCA / AFIP', color: '#75AADB',
    status: 'activo', lastSync: 'hace 12s', invoicesMonth: 184, taxCollectedUSD: 12800,
    rates: [
      { name: 'IVA General',    rate: '21%',  desc: 'Alícuota estándar bienes y servicios' },
      { name: 'IVA Reducido',   rate: '10.5%',desc: 'Alimentos, construcción, turismo' },
      { name: 'IIBB CABA',      rate: '3%',   desc: 'Ingresos brutos Ciudad de Buenos Aires' },
      { name: 'IIBB GBA',       rate: '3.5%', desc: 'Provincia de Buenos Aires' },
      { name: 'Monotributo H',  rate: 'ARS 19.000/mes', desc: 'Cuota categoría H servicios' },
    ],
    nextDeadline: 'IIBB 22 jun · IVA 20 jun',
    aiNote: 'Auto-emite CAE post-pago · IIBB CABA + GBA despachados',
  },
  {
    code: 'MX', flag: '🇲🇽', name: 'México', authority: 'SAT · CFDI 4.0', color: '#006847',
    status: 'activo', lastSync: 'hace 47s', invoicesMonth: 47, taxCollectedUSD: 6200,
    rates: [
      { name: 'IVA',     rate: '16%',  desc: 'Impuesto al valor agregado general' },
      { name: 'IVA 0%',  rate: '0%',   desc: 'Alimentos, medicamentos, exportaciones' },
      { name: 'ISR',     rate: '30%',  desc: 'Impuesto sobre la renta personas morales' },
      { name: 'ISR retención', rate: '10%', desc: 'Honorarios profesionales' },
    ],
    nextDeadline: 'DIOT 17 jun',
    aiNote: 'PAC integrado · timbrado auto · folios disponibles: 9.847',
  },
  {
    code: 'CO', flag: '🇨🇴', name: 'Colombia', authority: 'DIAN', color: '#FCD116',
    status: 'pendiente', lastSync: 'syncing…', invoicesMonth: 23, taxCollectedUSD: 2400,
    rates: [
      { name: 'IVA General', rate: '19%', desc: 'Tarifa general bienes y servicios' },
      { name: 'IVA 5%',      rate: '5%',  desc: 'Bienes de primera necesidad' },
      { name: 'IVA 0%',      rate: '0%',  desc: 'Alimentos básicos, educación, salud' },
      { name: 'Retención IVA', rate: '15%', desc: 'Retención en la fuente sobre IVA' },
    ],
    aiNote: 'Resolución activa · CUFE generándose · configuración 80% completa',
  },
  {
    code: 'PE', flag: '🇵🇪', name: 'Perú', authority: 'SUNAT', color: '#D91023',
    status: 'pendiente', lastSync: 'hace 4h', invoicesMonth: 8, taxCollectedUSD: 460,
    rates: [
      { name: 'IGV',      rate: '18%',  desc: 'Impuesto general a las ventas' },
      { name: 'IPM',      rate: '2%',   desc: 'Impuesto de Promoción Municipal' },
      { name: 'IR 3ra',   rate: '29.5%',desc: 'Renta de tercera categoría empresas' },
      { name: 'Retención IGV', rate: '3%', desc: 'Retención para agentes de retención' },
    ],
    nextDeadline: 'PDT mensual 15 jun',
  },
  {
    code: 'BR', flag: '🇧🇷', name: 'Brasil', authority: 'NFE/NFSe', color: '#009C3B',
    status: 'no_configurado', lastSync: 'sin config', invoicesMonth: 0, taxCollectedUSD: 0,
    rates: [
      { name: 'ICMS',  rate: '12–25%', desc: 'Varía por estado · SP 18% · RJ 20%' },
      { name: 'PIS',   rate: '0.65%',  desc: 'Programa de Integração Social' },
      { name: 'COFINS',rate: '3%',     desc: 'Contribuição para o Financiamento da Seguridade Social' },
      { name: 'ISS',   rate: '2–5%',   desc: 'Imposto Sobre Serviços · municipal' },
    ],
    aiNote: 'Activar SP + RJ + MG primero · requiere certificado A1 por CNPJ',
  },
  {
    code: 'USA', flag: '🇺🇸', name: 'USA', authority: 'Stripe Tax · Sales Tax', color: '#3C3B6E',
    status: 'activo', lastSync: 'hace 2min', invoicesMonth: 89, taxCollectedUSD: 3400,
    rates: [
      { name: 'Sales Tax CA', rate: '8.25%', desc: 'California · combinado estado + local' },
      { name: 'Sales Tax NY', rate: '8.875%',desc: 'Nueva York · ciudad incluida' },
      { name: 'Sales Tax TX', rate: '8.25%', desc: 'Texas estándar' },
      { name: 'No sales tax', rate: '0%',    desc: 'OR, MT, NH, DE, AK sin impuesto' },
    ],
    aiNote: 'Nexus tracking activo · 4 estados cerca del threshold económico',
  },
  {
    code: 'EU', flag: '🇪🇺', name: 'Unión Europea', authority: 'OSS · VAT One-Stop-Shop', color: '#003399',
    status: 'activo', lastSync: 'hace 1min', invoicesMonth: 124, taxCollectedUSD: 8400,
    rates: [
      { name: 'VAT DE',  rate: '19%',  desc: 'Alemania · tipo estándar' },
      { name: 'VAT FR',  rate: '20%',  desc: 'Francia · tipo estándar' },
      { name: 'VAT ES',  rate: '21%',  desc: 'España · tipo general' },
      { name: 'VAT IT',  rate: '22%',  desc: 'Italia · tipo ordinario' },
    ],
    nextDeadline: 'OSS Q2 declaración 31 jul',
    aiNote: 'B2C VAT por país comprador · auto-rate lookup activo',
  },
]

const STATUS_CONFIG: Record<ComplianceStatus, { color: string; label: string }> = {
  activo:           { color: '#10B981', label: '● ACTIVO'         },
  pendiente:        { color: '#F59E0B', label: '◐ PENDIENTE'      },
  no_configurado:   { color: '#9CA3AF', label: '○ NO CONFIG'      },
  error:            { color: '#ef4444', label: '⚠ ERROR'          },
}

export default function TaxSync() {
  const [activeCode, setActiveCode] = useState<CountryCode>('AR')
  const [syncing, setSyncing] = useState(false)

  const country = useMemo(() => COUNTRIES.find(c => c.code === activeCode)!, [activeCode])

  const stats = useMemo(() => ({
    active: COUNTRIES.filter(c => c.status === 'activo').length,
    total: COUNTRIES.length,
    invoices: COUNTRIES.reduce((s, c) => s + c.invoicesMonth, 0),
    taxUSD: COUNTRIES.reduce((s, c) => s + c.taxCollectedUSD, 0),
  }), [])

  const handleSync = () => {
    setSyncing(true)
    setTimeout(() => setSyncing(false), 2000)
  }

  return (
    <section style={{ background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #10B98180, transparent)' }} />

      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 10, background: T.emerald + '22', border: '1px solid ' + T.emerald + '44', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Globe style={{ width: 20, height: 20, color: T.emerald, filter: 'drop-shadow(0 0 6px ' + T.emerald + '88)' }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, letterSpacing: '.06em', textTransform: 'uppercase' }}>
              Tax Sync · Multi-país
              <span style={{ fontSize: 11, color: T.textSub, fontWeight: 400, textTransform: 'none', marginLeft: 8, letterSpacing: 0 }}>· {stats.active}/{stats.total} jurisdicciones</span>
            </div>
            <div style={{ fontSize: 11, color: T.textSub, marginTop: 2 }}>{stats.invoices} facturas/mes · ${stats.taxUSD.toLocaleString()} USD collected</div>
          </div>
        </div>
        <button onClick={handleSync}
          style={{ padding: '7px 16px', borderRadius: 8, fontSize: 11, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.04em', textTransform: 'uppercase', cursor: 'pointer', background: T.emerald + '22', border: '1px solid ' + T.emerald + '44', color: T.emerald, display: 'flex', alignItems: 'center', gap: 6 }}>
          <RefreshCw style={{ width: 12, height: 12 }} className={syncing ? 'animate-spin' : ''} />
          {syncing ? 'Sincronizando…' : 'Sync ahora'}
        </button>
      </div>

      {/* Country tabs */}
      <div style={{ padding: '12px 20px', borderBottom: '1px solid ' + T.border, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {COUNTRIES.map(c => {
          const st = STATUS_CONFIG[c.status]
          const isActive = c.code === activeCode
          return (
            <button key={c.code} onClick={() => setActiveCode(c.code)}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 12px', borderRadius: 8, cursor: 'pointer', transition: 'all .15s', background: isActive ? c.color + '22' : T.bgApp, border: '1px solid ' + (isActive ? c.color + '66' : T.border) }}>
              <span style={{ fontSize: 16 }}>{c.flag}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: isActive ? T.textPrim : T.textSub }}>{c.code}</span>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: st.color, boxShadow: '0 0 4px ' + st.color }} />
            </button>
          )
        })}
      </div>

      {/* Country detail */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, padding: '16px 20px' }}>

        {/* Left: rates */}
        <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 12, padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <span style={{ fontSize: 24 }}>{country.flag}</span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: T.textPrim }}>{country.name}</div>
              <div style={{ fontSize: 11, color: T.textSub, fontFamily: 'JetBrains Mono,monospace' }}>{country.authority}</div>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 10, fontFamily: 'monospace', background: STATUS_CONFIG[country.status].color + '18', border: '1px solid ' + STATUS_CONFIG[country.status].color + '28', color: STATUS_CONFIG[country.status].color }}>
                {STATUS_CONFIG[country.status].label}
              </span>
            </div>
          </div>

          <div style={{ fontSize: 10, fontFamily: 'JetBrains Mono,monospace', letterSpacing: '.06em', textTransform: 'uppercase', color: T.textSub, marginBottom: 8 }}>Tasas impositivas</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {country.rates.map((r, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 10px', background: T.bgCard, border: '1px solid ' + T.border, borderRadius: 8 }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: T.textPrim }}>{r.name}</div>
                  <div style={{ fontSize: 10, color: T.textSub }}>{r.desc}</div>
                </div>
                <div style={{ fontSize: 16, fontWeight: 800, color: country.color, textShadow: '0 0 20px ' + country.color + '88', fontFamily: 'JetBrains Mono,monospace', flexShrink: 0, marginLeft: 12 }}>{r.rate}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: status & info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { label: 'Facturas / mes', value: country.invoicesMonth.toString(), color: T.emerald },
              { label: 'Tax collected (USD)', value: '$' + country.taxCollectedUSD.toLocaleString(), color: T.cyan },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: 12 }}>
                <div style={{ fontSize: 10, color: T.textSub, marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 20, fontWeight: 800, color, textShadow: '0 0 20px ' + color + '88' }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Last sync */}
          <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock style={{ width: 13, height: 13, color: T.textSub, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 10, color: T.textSub }}>Último sync</div>
              <div style={{ fontSize: 12, fontWeight: 600, color: T.textPrim, fontFamily: 'JetBrains Mono,monospace' }}>{country.lastSync}</div>
            </div>
          </div>

          {/* Next deadline */}
          {country.nextDeadline && (
            <div style={{ background: T.amber + '0A', border: '1px solid ' + T.amber + '30', borderRadius: 10, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertTriangle style={{ width: 13, height: 13, color: T.amber, flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 10, color: T.textSub }}>Próximo deadline</div>
                <div style={{ fontSize: 12, fontWeight: 700, color: T.amber }}>{country.nextDeadline}</div>
              </div>
            </div>
          )}

          {/* AI note */}
          {country.aiNote ? (
            <div style={{ background: T.violet + '0A', border: '1px solid ' + T.violet + '30', borderRadius: 10, padding: '10px 14px', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <Bot style={{ width: 13, height: 13, color: T.violet, flexShrink: 0, marginTop: 2 }} />
              <div style={{ fontSize: 11, color: T.textSub, lineHeight: 1.5 }}>{country.aiNote}</div>
            </div>
          ) : (
            country.status === 'no_configurado' && (
              <div style={{ background: T.bgApp, border: '1px solid ' + T.border, borderRadius: 10, padding: '10px 14px' }}>
                <div style={{ fontSize: 11, color: T.textSub, marginBottom: 8 }}>País no configurado. Activar para habilitar facturación electrónica.</div>
                <button style={{ padding: '6px 14px', borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: 'pointer', background: T.emerald + '22', border: '1px solid ' + T.emerald + '44', color: T.emerald }}>Configurar ahora</button>
              </div>
            )
          )}
        </div>
      </div>

      {/* Footer */}
      <div style={{ borderTop: '1px solid ' + T.border, padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
        <CheckCircle2 style={{ width: 12, height: 12, color: T.emerald }} />
        <span style={{ fontSize: 11, color: T.textSub }}>
          IA arma declaraciones mensuales auto · firma con cert digital · avisa 7 días antes de cada deadline · cero multas por olvido.
        </span>
      </div>
    </section>
  )
}
