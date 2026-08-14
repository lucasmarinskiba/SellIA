'use client'

import { useEffect, useState } from 'react'
import { AlertCircle, TrendingUp, CheckCircle, Clock } from 'lucide-react'
import { Card } from '@/components/ui/card'

interface AtRiskDeal {
  deal_id: string
  deal_name: string
  win_probability: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  risk_reason: string
  suggested_action: string
}

interface IntelligenceDashboard {
  at_risk: { total_at_risk: number; critical_count: number; deals: AtRiskDeal[] }
  accuracy: { accuracy: number; total_outcomes: number; won_count: number }
  win_loss_patterns: { top_loss_reasons: Array<{ reason: string; count: number }> }
}

export default function DealRiskDashboard({ userId }: { userId: string }) {
  const [dashboard, setDashboard] = useState<IntelligenceDashboard | null>(null)
  const [loading, setLoading] = useState(true)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchDashboard()
  }, [userId])

  const fetchDashboard = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/intelligence/dashboard/${userId}`)
      if (res.ok) {
        const data = await res.json()
        setDashboard(data.dashboard)
      }
    } catch (error) {
      console.error('Fetch dashboard error:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 border-red-300'
      case 'high':
        return 'bg-orange-100 border-orange-300'
      case 'medium':
        return 'bg-yellow-100 border-yellow-300'
      default:
        return 'bg-green-100 border-green-300'
    }
  }

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-600 text-white'
      case 'high':
        return 'bg-orange-600 text-white'
      case 'medium':
        return 'bg-yellow-600 text-white'
      default:
        return 'bg-green-600 text-white'
    }
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">At-Risk Deals</p>
          <p className="text-3xl font-bold text-brand-night">
            {dashboard?.at_risk.total_at_risk || 0}
          </p>
          <p className="text-xs text-red-600 mt-2">
            {dashboard?.at_risk.critical_count || 0} critical
          </p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Forecast Accuracy</p>
          <p className="text-3xl font-bold text-brand-night">
            {dashboard ? Math.round(dashboard.accuracy.accuracy * 100) : 0}%
          </p>
          <p className="text-xs text-slate-500 mt-2">
            {dashboard?.accuracy.total_outcomes || 0} outcomes
          </p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Deals Won</p>
          <p className="text-3xl font-bold text-green-600">
            {dashboard?.accuracy.won_count || 0}
          </p>
          <p className="text-xs text-slate-500 mt-2">Recent outcomes</p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Revenue at Risk</p>
          <p className="text-3xl font-bold text-brand-night">
            ${(dashboard?.at_risk.deals.reduce((sum, d) => sum + (d.win_probability || 0), 0) / 1000).toFixed(1)}k
          </p>
          <p className="text-xs text-orange-600 mt-2">Requires action</p>
        </Card>
      </div>

      {/* At-Risk Deals Section */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-brand-night flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-orange-600" />
            At-Risk Deals
          </h3>
          <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-semibold">
            {dashboard?.at_risk.total_at_risk || 0}
          </span>
        </div>

        {!dashboard?.at_risk.deals || dashboard.at_risk.deals.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No at-risk deals. Great job!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {dashboard.at_risk.deals.map((deal) => (
              <div key={deal.deal_id} className={`p-4 border rounded-lg ${getRiskColor(deal.risk_level)}`}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-slate-900">{deal.deal_name}</p>
                    <p className="text-sm text-slate-600 mt-1">{deal.risk_reason}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${getRiskBadgeColor(deal.risk_level)}`}>
                    {deal.risk_level.toUpperCase()}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-slate-600" />
                    <span className="text-sm text-slate-600">
                      {(deal.win_probability * 100).toFixed(0)}% win probability
                    </span>
                  </div>
                  <button className="px-3 py-1 bg-slate-700 text-white text-xs rounded hover:bg-slate-800">
                    {deal.suggested_action}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Loss Patterns */}
      {dashboard?.win_loss_patterns.top_loss_reasons && dashboard.win_loss_patterns.top_loss_reasons.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-bold text-brand-night mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-600" />
            Top Loss Reasons
          </h3>

          <div className="space-y-2">
            {dashboard.win_loss_patterns.top_loss_reasons.map((reason, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded">
                <span className="text-sm text-slate-700">{reason.reason}</span>
                <span className="text-sm font-semibold text-slate-900">{reason.count} deals</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

