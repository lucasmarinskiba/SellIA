'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/Card'

interface Pipeline {
  total_opportunities: number
  total_pipeline_value: string
  weighted_forecast: string
  average_deal_size: string
  by_stage: Record<
    string,
    {
      count: number
      value: string
      weighted_value: string
      avg_probability: string
    }
  >
}

interface Projection {
  period: string
  projected_revenue: string
  confidence: string
  scenarios: {
    best_case: string
    most_likely: string
    worst_case: string
  }
  key_drivers: {
    avg_deal_size: string
    pipeline_velocity: string
  }
}

interface Scenario {
  name: string
  projected_revenue: string
  probability: string
  assumptions: Record<string, string>
}

interface Risk {
  summary: {
    at_risk_count: number
    stalled_count: number
    risk_value: string
  }
  at_risk_opportunities: Array<{
    id: string
    title: string
    amount: number
    stage: string
  }>
}

export default function ForecastChart({ userId }: { userId: string }) {
  const [pipeline, setPipeline] = useState<Pipeline | null>(null)
  const [projection, setProjection] = useState<Projection | null>(null)
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [risks, setRisks] = useState<Risk | null>(null)
  const [daysAhead, setDaysAhead] = useState(30)
  const [loading, setLoading] = useState(true)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchForecastData()
  }, [userId, daysAhead])

  const fetchForecastData = async () => {
    try {
      setLoading(true)

      const [pipelineRes, projectionRes, scenariosRes, risksRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/forecast/pipeline/${userId}?model=standard`),
        fetch(`${apiUrl}/api/v1/forecast/revenue/${userId}?days_ahead=${daysAhead}`),
        fetch(`${apiUrl}/api/v1/forecast/scenarios/${userId}?days_ahead=${daysAhead}`),
        fetch(`${apiUrl}/api/v1/forecast/risks/${userId}`),
      ])

      if (pipelineRes.ok) {
        const data = await pipelineRes.json()
        setPipeline(data)
      }

      if (projectionRes.ok) {
        const data = await projectionRes.json()
        setProjection(data)
      }

      if (scenariosRes.ok) {
        const data = await scenariosRes.json()
        setScenarios(data.scenarios || [])
      }

      if (risksRes.ok) {
        const data = await risksRes.json()
        setRisks(data)
      }
    } catch (error) {
      console.error('Forecast fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  const parseAmount = (str: string): number => {
    return parseFloat(str.replace(/[$,]/g, ''))
  }

  return (
    <div className="space-y-6">
      {/* Header with period selector */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-brand-night flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            Revenue Forecasting
          </h2>
          <p className="text-sm text-slate-600 mt-1">AI-powered pipeline projection</p>
        </div>
        <div className="flex gap-2">
          {[7, 14, 30, 60, 90].map((days) => (
            <button
              key={days}
              onClick={() => setDaysAhead(days)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                daysAhead === days
                  ? 'bg-brand-orange text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-4" />
              <div className="h-8 bg-slate-200 rounded w-1/2 mb-2" />
              <div className="h-3 bg-slate-100 rounded w-2/3" />
            </Card>
          ))}
        </div>
      ) : projection ? (
        <>
          {/* Projection Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="p-6">
              <p className="text-sm text-slate-600 mb-2">Projected Revenue</p>
              <p className="text-3xl font-bold text-green-600">{projection.projected_revenue}</p>
              <p className="text-xs text-slate-500 mt-2">Confidence: {projection.confidence}</p>
            </Card>

            <Card className="p-6">
              <p className="text-sm text-slate-600 mb-2">Most Likely</p>
              <p className="text-3xl font-bold text-brand-orange">{projection.scenarios.most_likely}</p>
              <p className="text-xs text-slate-500 mt-2">Expected value</p>
            </Card>

            <Card className="p-6">
              <p className="text-sm text-slate-600 mb-2">Avg Deal Size</p>
              <p className="text-3xl font-bold text-blue-600">{projection.key_drivers.avg_deal_size}</p>
              <p className="text-xs text-slate-500 mt-2">Pipeline velocity: {projection.key_drivers.pipeline_velocity}</p>
            </Card>
          </div>

          {/* Scenarios */}
          <Card className="p-6">
            <h3 className="font-semibold text-brand-night mb-4">Forecast Scenarios</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {scenarios.map((scenario) => (
                <div
                  key={scenario.name}
                  className={`p-4 rounded-lg border-2 ${
                    scenario.name === 'Base Case' ? 'border-brand-orange bg-orange-50' : 'border-slate-200 bg-white'
                  }`}
                >
                  <p className="font-semibold text-brand-night">{scenario.name}</p>
                  <p className="text-2xl font-bold text-slate-700 mt-2">{scenario.projected_revenue}</p>
                  <p className="text-xs text-slate-600 mt-2">{scenario.probability} probability</p>

                  <div className="mt-3 pt-3 border-t text-xs space-y-1">
                    {Object.entries(scenario.assumptions).map(([key, value]) => (
                      <p key={key} className="text-slate-600">
                        <span className="font-medium">{key}:</span> {value}
                      </p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Scenario Range Chart */}
          <Card className="p-6">
            <h3 className="font-semibold text-brand-night mb-4">Scenario Range</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-slate-600">Best Case</span>
                  <span className="font-semibold text-brand-night">{projection.scenarios.best_case}</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div
                    className="bg-green-500 h-3 rounded-full"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-slate-600">Most Likely</span>
                  <span className="font-semibold text-brand-night">{projection.scenarios.most_likely}</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div
                    className="bg-brand-orange h-3 rounded-full"
                    style={{
                      width: `${
                        (parseAmount(projection.scenarios.most_likely) /
                          parseAmount(projection.scenarios.best_case)) *
                        100
                      }%`,
                    }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-slate-600">Worst Case</span>
                  <span className="font-semibold text-brand-night">{projection.scenarios.worst_case}</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div
                    className="bg-red-500 h-3 rounded-full"
                    style={{
                      width: `${
                        (parseAmount(projection.scenarios.worst_case) /
                          parseAmount(projection.scenarios.best_case)) *
                        100
                      }%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </Card>
        </>
      ) : null}

      {/* Pipeline by Stage */}
      {pipeline && (
        <Card className="p-6">
          <h3 className="font-semibold text-brand-night mb-4">Pipeline by Stage</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
            {Object.entries(pipeline.by_stage).map(([stage, data]) => (
              <div key={stage} className="p-4 bg-gradient-to-br from-blue-50 to-slate-50 rounded-lg border border-slate-200">
                <p className="text-xs font-semibold text-slate-600 uppercase">{stage}</p>
                <p className="text-2xl font-bold text-brand-night mt-2">{data.count}</p>
                <p className="text-sm text-slate-600 mt-1">{data.value}</p>
                <p className="text-xs text-orange-600 font-semibold mt-2">
                  Forecast: {data.weighted_value}
                </p>
                <p className="text-xs text-slate-500 mt-1">{data.avg_probability} prob</p>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-slate-600">Total Opportunities</p>
              <p className="text-2xl font-bold text-brand-night">{pipeline.total_opportunities}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Pipeline Value</p>
              <p className="text-2xl font-bold text-green-600">{pipeline.total_pipeline_value}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Weighted Forecast</p>
              <p className="text-2xl font-bold text-blue-600">{pipeline.weighted_forecast}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Risks & Alerts */}
      {risks && (
        <Card
          className={`p-6 border-l-4 ${
            risks.summary.at_risk_count > 0
              ? 'border-l-red-500 bg-red-50'
              : 'border-l-green-500 bg-green-50'
          }`}
        >
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0">
              {risks.summary.at_risk_count > 0 ? (
                <AlertTriangle className="w-6 h-6 text-red-600" />
              ) : (
                <CheckCircle className="w-6 h-6 text-green-600" />
              )}
            </div>

            <div className="flex-1">
              <h3 className="font-semibold text-brand-night">
                {risks.summary.at_risk_count > 0 ? 'At-Risk Opportunities' : 'Pipeline Healthy'}
              </h3>

              <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-slate-600">At Risk</p>
                  <p className="text-2xl font-bold text-red-600">{risks.summary.at_risk_count}</p>
                </div>
                <div>
                  <p className="text-slate-600">Stalled</p>
                  <p className="text-2xl font-bold text-orange-600">{risks.summary.stalled_count}</p>
                </div>
                <div>
                  <p className="text-slate-600">Risk Value</p>
                  <p className="text-2xl font-bold text-red-600">{risks.summary.risk_value}</p>
                </div>
              </div>

              {risks.at_risk_opportunities.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className="font-semibold text-sm text-brand-night mb-2">Needs Attention:</p>
                  <div className="space-y-2">
                    {risks.at_risk_opportunities.slice(0, 3).map((opp) => (
                      <div key={opp.id} className="text-sm">
                        <p className="font-medium text-slate-700">{opp.title}</p>
                        <p className="text-xs text-slate-600">
                          {opp.stage} • ${opp.amount.toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
