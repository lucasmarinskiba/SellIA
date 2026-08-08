'use client'

/**
 * Monitoring Dashboard Components
 * Phase 5: Real-time metrics, conversion funnels, A/B tests, anomalies
 */

import React, { useEffect, useState } from 'react'

export interface ConversionStage {
  name: string
  value: number
  conversion: number
  drop_off?: number
}

export interface CoreWebVital {
  name: string
  value: string
  status: 'good' | 'needs-improvement' | 'poor'
  target: string
}

export interface ABTest {
  id: string
  name: string
  variants: Record<string, any>
  confidence: number
  statistical_significance: boolean
}

export interface Anomaly {
  type: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  description: string
  timestamp: string
}

export function ConversionFunnel({
  funnel,
}: {
  funnel: {
    name: string
    stages: ConversionStage[]
  }
}) {
  const maxValue = Math.max(...funnel.stages.map((s) => s.value))

  return (
    <section style={{ padding: '24px', borderRadius: '8px', background: 'rgba(13,18,30,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '24px' }}>{funnel.name}</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {funnel.stages.map((stage, idx) => {
          const width = (stage.value / maxValue) * 100
          return (
            <div key={idx}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '12px', fontWeight: '500' }}>{stage.name}</span>
                <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
                  {stage.value.toLocaleString()} ({stage.conversion}%)
                </span>
              </div>
              <div style={{ width: '100%', height: '24px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${width}%`,
                    height: '100%',
                    background: `linear-gradient(90deg, #00D4FF, #8B5CF6)`,
                    transition: 'width 0.3s ease',
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}

export function CoreWebVitalsCard({
  vitals,
}: {
  vitals: Record<string, CoreWebVital>
}) {
  const statusColors = {
    good: '#10B981',
    'needs-improvement': '#F59E0B',
    poor: '#EF4444',
  }

  return (
    <section style={{ padding: '24px', borderRadius: '8px', background: 'rgba(13,18,30,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px' }}>Core Web Vitals</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        {Object.entries(vitals).map(([key, vital]) => (
          <div key={key} style={{ padding: '16px', borderRadius: '6px', background: 'rgba(255,255,255,0.02)', border: `2px solid ${statusColors[vital.status]}` }}>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}>{key}</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: statusColors[vital.status], marginBottom: '8px' }}>
              {vital.value}
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>Target: {vital.target}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

export function ABTestsCard({
  tests,
}: {
  tests: ABTest[]
}) {
  return (
    <section style={{ padding: '24px', borderRadius: '8px', background: 'rgba(13,18,30,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px' }}>Active A/B Tests</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {tests.map((test) => (
          <div key={test.id} style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)' }}>
            <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{test.name}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              {Object.entries(test.variants).map(([key, variant]: any) => (
                <div key={key}>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginBottom: '4px' }}>{variant.name}</div>
                  <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '4px' }}>
                    {(variant.conversion_rate * 100).toFixed(2)}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)' }}>
                    {variant.conversions} conversions
                  </div>
                </div>
              ))}
            </div>
            <div style={{ fontSize: '11px', color: '#00D4FF' }}>
              Confidence: {test.confidence}% {test.statistical_significance ? '✅' : '⏳'}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AnomalyDetection({
  anomalies,
}: {
  anomalies: Anomaly[]
}) {
  const severityColors = {
    info: '#3B82F6',
    warning: '#F59E0B',
    critical: '#EF4444',
  }

  const severityIcons = {
    info: 'ℹ️',
    warning: '⚠️',
    critical: '🚨',
  }

  return (
    <section style={{ padding: '24px', borderRadius: '8px', background: 'rgba(13,18,30,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h2 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px' }}>Anomaly Detection</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {anomalies.map((anomaly, idx) => (
          <div
            key={idx}
            style={{
              padding: '12px',
              borderRadius: '6px',
              borderLeft: `4px solid ${severityColors[anomaly.severity]}`,
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'start', gap: '8px' }}>
              <span style={{ fontSize: '16px' }}>{severityIcons[anomaly.severity]}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '2px' }}>{anomaly.title}</div>
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)' }}>{anomaly.description}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export function MetricCard({
  title,
  value,
  change,
  unit = '',
}: {
  title: string
  value: number | string
  change: string
  unit?: string
}) {
  const isPositive = change.startsWith('+')
  const changeColor = isPositive ? '#10B981' : '#EF4444'

  return (
    <div style={{ padding: '20px', borderRadius: '8px', background: 'rgba(13,18,30,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>{title}</div>
      <div style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
        {value}
        <span style={{ fontSize: '16px', marginLeft: '4px' }}>{unit}</span>
      </div>
      <div style={{ fontSize: '12px', color: changeColor, fontWeight: '600' }}>{change}</div>
    </div>
  )
}

export function SEODashboard() {
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const response = await fetch('/api/v1/analytics/dashboard/seo-metrics')
        const data = await response.json()
        setMetrics(data)
      } catch (error) {
        console.error('Failed to fetch SEO metrics:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (loading || !metrics) return <div style={{ padding: '20px' }}>Loading SEO metrics...</div>

  const m = metrics.metrics

  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <MetricCard title="Organic Traffic" value={m.organic_traffic.value} change={m.organic_traffic.change} />
        <MetricCard title="Indexed Pages" value={m.indexed_pages.value} change={m.indexed_pages.change} />
        <MetricCard title="Avg Position" value={m.avg_ranking_position.value} change={m.avg_ranking_position.change} />
        <MetricCard title="CTR" value={m.click_through_rate.value} change={m.click_through_rate.change} unit="%" />
      </div>

      <section style={{ padding: '24px', borderRadius: '8px', background: 'rgba(13,18,30,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Top Pages</h3>
        <div style={{ overflow: 'auto' }}>
          <table style={{ width: '100%', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <th style={{ textAlign: 'left', padding: '8px', fontWeight: '600' }}>Page</th>
                <th style={{ textAlign: 'right', padding: '8px' }}>Views</th>
                <th style={{ textAlign: 'right', padding: '8px' }}>Avg Time</th>
                <th style={{ textAlign: 'right', padding: '8px' }}>Bounce</th>
              </tr>
            </thead>
            <tbody>
              {m.top_pages.map((page: any) => (
                <tr key={page.page} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '8px' }}>{page.page}</td>
                  <td style={{ textAlign: 'right', padding: '8px' }}>{page.views.toLocaleString()}</td>
                  <td style={{ textAlign: 'right', padding: '8px' }}>{page.avg_time}</td>
                  <td style={{ textAlign: 'right', padding: '8px' }}>{(page.bounce_rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
