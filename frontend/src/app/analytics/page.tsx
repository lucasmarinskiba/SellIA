'use client'

/**
 * Analytics Dashboard - Phase 5
 * Real-time monitoring: SEO, marketing, A/B tests, anomalies, personalization
 */

import React, { useEffect, useState } from 'react'
import { ConversionFunnel, CoreWebVitalsCard, ABTestsCard, AnomalyDetection, SEODashboard } from '@/components/analytics/MonitoringDashboard'

export default function AnalyticsDashboard() {
  const [funnel, setFunnel] = useState<any>(null)
  const [vitals, setVitals] = useState<any>(null)
  const [tests, setTests] = useState<any>(null)
  const [anomalies, setAnomalies] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const [funnelRes, vitalsRes, testsRes, anomaliesRes] = await Promise.all([
          fetch('/api/v1/analytics/funnel/conversion'),
          fetch('/api/v1/analytics/performance/core-web-vitals'),
          fetch('/api/v1/analytics/ab-test/active'),
          fetch('/api/v1/analytics/anomalies/seo'),
        ])

        setFunnel((await funnelRes.json()).stages ? (await funnelRes.json()) : null)
        setVitals((await vitalsRes.json()).metrics)
        setTests((await testsRes.json()).tests)
        setAnomalies((await anomaliesRes.json()).anomalies)
      } catch (error) {
        console.error('Failed to fetch analytics:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '40px 20px' }}>
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '18px', color: 'rgba(255,255,255,0.6)' }}>Loading analytics dashboard...</div>
        </div>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '40px 20px' }}>
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: 'clamp(28px, 5vw, 48px)', fontWeight: '700', marginBottom: '12px' }}>
          Analytics Dashboard
        </h1>
        <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.6)' }}>
          Real-time monitoring: SEO, marketing, conversions, anomalies
        </p>
      </div>

      {/* SEO Metrics */}
      <div style={{ marginBottom: '60px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '20px' }}>SEO Metrics</h2>
        <SEODashboard />
      </div>

      {/* Conversion Funnel */}
      {funnel && (
        <div style={{ marginBottom: '60px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '20px' }}>Conversion Funnel</h2>
          <ConversionFunnel funnel={funnel} />
        </div>
      )}

      {/* Core Web Vitals */}
      {vitals && (
        <div style={{ marginBottom: '60px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '20px' }}>Performance</h2>
          <CoreWebVitalsCard vitals={vitals} />
        </div>
      )}

      {/* A/B Tests */}
      {tests && (
        <div style={{ marginBottom: '60px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '20px' }}>Active A/B Tests</h2>
          <ABTestsCard tests={tests} />
        </div>
      )}

      {/* Anomalies */}
      {anomalies && (
        <div style={{ marginBottom: '60px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '20px' }}>Anomaly Detection</h2>
          <AnomalyDetection anomalies={anomalies} />
        </div>
      )}

      {/* Footer */}
      <div style={{ padding: '40px', textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '60px' }}>
        <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
          Dashboard updates every 5 minutes. Last updated: {new Date().toLocaleTimeString()}
        </p>
      </div>
    </main>
  )
}

