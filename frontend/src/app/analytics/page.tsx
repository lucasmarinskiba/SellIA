'use client'

/**
 * Analytics Dashboard - Phase 5
 * Shows only sections whose data source is connected (the API answers 501 for the rest).
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
    // A section without a connected data source answers 501: it stays hidden instead of showing invented numbers.
    const getJson = async (url: string) => {
      const res = await fetch(url)
      return res.ok ? res.json() : null
    }

    async function fetchData() {
      try {
        const [funnelData, vitalsData, testsData, anomaliesData] = await Promise.all([
          getJson('/api/v1/analytics/funnel/conversion'),
          getJson('/api/v1/analytics/performance/core-web-vitals'),
          getJson('/api/v1/analytics/ab-test/active'),
          getJson('/api/v1/analytics/anomalies/seo'),
        ])

        setFunnel(funnelData?.stages ? funnelData : null)
        setVitals(vitalsData?.metrics ?? null)
        setTests(testsData?.tests ?? null)
        setAnomalies(anomaliesData?.anomalies ?? null)
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
          Las secciones aparecen cuando tienen una fuente de datos conectada
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

