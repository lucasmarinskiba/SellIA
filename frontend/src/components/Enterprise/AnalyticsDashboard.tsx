'use client'

import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Target, Users, DollarSign, Zap } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface KPICard {
  label: string
  value: number
  unit: string
  target?: number
  trend: number
  direction: 'up' | 'down' | 'neutral'
}

interface AgentMetric {
  id: string
  name: string
  status: string
  success_rate: number
  efficiency_score: number
  conversions: number
  revenue_attributed: number
}

interface PipelineData {
  total_value: number
  stages: Record<string, number>
  forecast_confidence: number
  projected_revenue_30d: number
}

interface SegmentBenchmark {
  segment: string
  avg_leads_per_user: number
  avg_revenue_per_user: number
  churn_rate: number
  expansion_rate: number
}

export default function AnalyticsDashboard({ userId, segment = 'active' }: { userId: string; segment?: string }) {
  const [kpis, setKpis] = useState<KPICard[]>([])
  const [agents, setAgents] = useState<AgentMetric[]>([])
  const [pipeline, setPipeline] = useState<PipelineData | null>(null)
  const [benchmarks, setBenchmarks] = useState<SegmentBenchmark | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('month')

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true)

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const res = await fetch(`${apiUrl}/api/v1/analytics/dashboard/${userId}?segment=${segment}&time_range=${timeRange}`)
        if (!res.ok) throw new Error('Failed to fetch dashboard')

        const data = await res.json()

        setKpis(
          data.kpi_cards.map((kpi: any) => ({
            label: kpi.label,
            value: kpi.current_value,
            unit: kpi.unit,
            target: kpi.target,
            trend: kpi.trend,
            direction: kpi.trend_direction,
          }))
        )

        setAgents(
          data.agent_performance.map((agent: any) => ({
            id: agent.agent_id,
            name: agent.agent_name,
            status: agent.status,
            success_rate: agent.success_rate,
            efficiency_score: agent.efficiency_score,
            conversions: agent.conversions,
            revenue_attributed: agent.revenue_attributed,
          }))
        )

        setPipeline(data.pipeline)
        setBenchmarks(data.segment_benchmarks)
      } catch (error) {
        console.error('Dashboard fetch error:', error)
        // Mock data fallback
        setKpis([
          { label: 'Total Leads', value: 145, unit: 'leads', target: 200, trend: 12.5, direction: 'up' },
          { label: 'Conversion Rate', value: 4.2, unit: '%', target: 5, trend: 2.1, direction: 'up' },
          { label: 'Revenue', value: 8500, unit: 'USD', target: 10000, trend: 18.3, direction: 'up' },
          { label: 'Pipeline Value', value: 45000, unit: 'USD', target: 50000, trend: 5.2, direction: 'neutral' },
        ])
        setAgents([
          { id: 'lead_scout', name: 'Lead Scout', status: 'active', success_rate: 87.5, efficiency_score: 89, conversions: 12, revenue_attributed: 2400 },
          { id: 'closer_bot', name: 'Closer Bot', status: 'active', success_rate: 92.1, efficiency_score: 94, conversions: 35, revenue_attributed: 8500 },
        ])
        setPipeline({
          total_value: 45000,
          stages: { prospecting: 35, qualification: 18, proposal: 8, negotiation: 2 },
          forecast_confidence: 82,
          projected_revenue_30d: 12000,
        })
        setBenchmarks({
          segment: 'active',
          avg_leads_per_user: 80,
          avg_revenue_per_user: 5000,
          churn_rate: 0.08,
          expansion_rate: 0.42,
        })
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [userId, segment, timeRange])

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />
      default:
        return <Zap className="w-4 h-4 text-slate-400" />
    }
  }

  const getTrendColor = (direction: string): string => {
    switch (direction) {
      case 'up':
        return 'text-green-600'
      case 'down':
        return 'text-red-600'
      default:
        return 'text-slate-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with time range selector */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-brand-night">Performance Analytics</h2>
          <p className="text-sm text-slate-600 mt-1">Real-time insights powered by your AI agents</p>
        </div>
        <div className="flex gap-2">
          {['today', 'week', 'month', 'quarter'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-brand-orange text-white'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-4" />
              <div className="h-8 bg-slate-200 rounded w-1/2 mb-2" />
              <div className="h-3 bg-slate-100 rounded w-2/3" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpis.map((kpi, idx) => (
            <Card key={idx} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <p className="text-sm font-medium text-slate-600">{kpi.label}</p>
                {getTrendIcon(kpi.direction)}
              </div>

              <div className="mb-3">
                <p className="text-3xl font-bold text-brand-night">
                  {kpi.value.toLocaleString()}
                  <span className="text-lg text-slate-500 ml-2">{kpi.unit}</span>
                </p>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className={`font-semibold ${getTrendColor(kpi.direction)}`}>
                  {kpi.trend > 0 ? '+' : ''}
                  {kpi.trend.toFixed(1)}%
                </span>
                {kpi.target && (
                  <span className="text-slate-500">
                    Target: {kpi.target.toLocaleString()}
                  </span>
                )}
              </div>

              {kpi.target && (
                <div className="mt-4 w-full bg-slate-100 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-brand-orange to-orange-500 h-2 rounded-full"
                    style={{
                      width: `${Math.min(100, (kpi.value / kpi.target) * 100)}%`,
                    }}
                  />
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Agent Performance & Pipeline Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Performance */}
        <Card className="lg:col-span-2 p-6">
          <h3 className="text-lg font-bold text-brand-night mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-orange-500" />
            Agent Performance
          </h3>

          <div className="space-y-3">
            {agents.map((agent) => (
              <div key={agent.id} className="p-4 border border-slate-200 rounded-lg">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-brand-night">{agent.name}</p>
                    <p className="text-xs text-slate-600">
                      <span
                        className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                          agent.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {agent.status}
                      </span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-brand-orange">${agent.revenue_attributed.toLocaleString()}</p>
                    <p className="text-xs text-slate-600">Revenue</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <p className="text-slate-600">Success Rate</p>
                    <p className="font-bold text-brand-night">{agent.success_rate.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-slate-600">Efficiency</p>
                    <p className="font-bold text-brand-night">{agent.efficiency_score.toFixed(0)}/100</p>
                  </div>
                  <div>
                    <p className="text-slate-600">Conversions</p>
                    <p className="font-bold text-brand-night">{agent.conversions}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Pipeline Forecast */}
        {pipeline && (
          <Card className="p-6">
            <h3 className="text-lg font-bold text-brand-night mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-500" />
              Pipeline
            </h3>

            <div className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-slate-600">Total Value</p>
                <p className="text-2xl font-bold text-brand-night">${(pipeline.total_value / 1000).toFixed(1)}k</p>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-700 mb-2">Stages</p>
                <div className="space-y-1">
                  {Object.entries(pipeline.stages).map(([stage, count]) => (
                    <div key={stage} className="flex justify-between text-xs">
                      <span className="text-slate-600 capitalize">{stage}</span>
                      <span className="font-bold text-brand-night">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-green-50 rounded-lg border-l-4 border-l-green-500">
                <p className="text-xs text-slate-600">Projected Revenue (30d)</p>
                <p className="text-xl font-bold text-green-700">${pipeline.projected_revenue_30d.toLocaleString()}</p>
                <p className="text-xs text-slate-600 mt-1">
                  {pipeline.forecast_confidence}% confidence
                </p>
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Segment Benchmarks */}
      {benchmarks && (
        <Card className="p-6">
          <h3 className="text-lg font-bold text-brand-night mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-500" />
            Segment Benchmarks ({benchmarks.segment})
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg">
              <p className="text-xs text-slate-600 mb-2">Avg Leads/User</p>
              <p className="text-2xl font-bold text-brand-night">{benchmarks.avg_leads_per_user.toFixed(0)}</p>
            </div>

            <div className="p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg">
              <p className="text-xs text-slate-600 mb-2">Avg Revenue/User</p>
              <p className="text-2xl font-bold text-brand-night">${(benchmarks.avg_revenue_per_user / 1000).toFixed(1)}k</p>
            </div>

            <div className="p-4 bg-gradient-to-br from-red-50 to-pink-50 rounded-lg">
              <p className="text-xs text-slate-600 mb-2">Churn Rate</p>
              <p className="text-2xl font-bold text-red-600">{(benchmarks.churn_rate * 100).toFixed(1)}%</p>
            </div>

            <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
              <p className="text-xs text-slate-600 mb-2">Expansion Rate</p>
              <p className="text-2xl font-bold text-green-600">{(benchmarks.expansion_rate * 100).toFixed(1)}%</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

