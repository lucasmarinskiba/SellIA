'use client'

/**
 * Live KPI counters per funnel lobe.
 * Animated count-up + delta indicator. Values are seeded; production wires to TanStack queries.
 */

import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'


interface KPI {
  label: string
  value: number
  format: 'int' | 'currency' | 'pct'
  delta: number     // pct change vs prev period
  color: string
}


const formatValue = (n: number, fmt: KPI['format']): string => {
  if (fmt === 'currency') {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `$${(n / 1_000).toFixed(1)}k`
    return `$${Math.round(n)}`
  }
  if (fmt === 'pct') return `${n.toFixed(1)}%`
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return Math.round(n).toLocaleString('es-AR')
}


const useCountUp = (target: number, duration = 1400): number => {
  const [val, setVal] = useState<number>(0)
  useEffect(() => {
    let raf = 0
    const start = performance.now()
    const tick = (t: number): void => {
      const p = Math.min((t - start) / duration, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setVal(target * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])
  return val
}


export const KPICell = ({ kpi }: { kpi: KPI }): React.JSX.Element => {
  const v = useCountUp(kpi.value)
  const up = kpi.delta >= 0
  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex items-baseline gap-1.5">
        <span
          className="text-[20px] font-light tabular-nums leading-none"
          style={{ color: kpi.color, fontFamily: '"JetBrains Mono", ui-monospace, monospace' }}
        >
          {formatValue(v, kpi.format)}
        </span>
        <span
          className={`text-[9px] font-mono flex items-center gap-0.5 ${up ? 'text-emerald-300' : 'text-red-300'}`}
        >
          {up ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
          {Math.abs(kpi.delta).toFixed(1)}%
        </span>
      </div>
      <span className="text-[8.5px] font-mono tracking-[0.18em] uppercase text-white/35">
        {kpi.label}
      </span>
    </div>
  )
}


export const LOBE_KPIS: Record<'acquire' | 'convert' | 'retain' | 'core', KPI[]> = {
  acquire: [
    { label: 'leads/24h',       value: 1284,    format: 'int',      delta: 18.4, color: '#22d3ee' },
    { label: 'cpl medio',       value: 2.40,    format: 'currency', delta: -7.2, color: '#22d3ee' },
    { label: 'señales/min',     value: 47,      format: 'int',      delta: 12.0, color: '#22d3ee' },
  ],
  convert: [
    { label: 'deals abiertos',  value: 318,     format: 'int',      delta: 9.1,  color: '#ec4899' },
    { label: 'win-rate',        value: 42.6,    format: 'pct',      delta: 4.3,  color: '#ec4899' },
    { label: 'pipeline',        value: 184_000, format: 'currency', delta: 22.5, color: '#ec4899' },
  ],
  retain: [
    { label: 'mrr activo',      value: 47_300,  format: 'currency', delta: 6.8,  color: '#10b981' },
    { label: 'nps',             value: 71,      format: 'int',      delta: 3.0,  color: '#10b981' },
    { label: 'churn',           value: 1.8,     format: 'pct',      delta: -0.4, color: '#10b981' },
  ],
  core: [
    { label: 'agentes vivos',   value: 47,      format: 'int',      delta: 0.0,  color: '#a855f7' },
    { label: 'tokens/min',      value: 184_000, format: 'int',      delta: 11.0, color: '#a855f7' },
    { label: 'uptime',          value: 99.97,   format: 'pct',      delta: 0.0,  color: '#a855f7' },
  ],
}


export default KPICell
