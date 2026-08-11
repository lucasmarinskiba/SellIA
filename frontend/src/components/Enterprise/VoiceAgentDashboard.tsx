'use client'

import { useEffect, useState } from 'react'
import { Phone, Mic, Volume2, Clock, Send } from 'lucide-react'
import { Card } from '@/components/ui/Card'

interface CallRecord {
  id: string
  contact_number: string
  call_type: string
  status: string
  duration_seconds: number
  sentiment?: string
  created_at: string
}

interface CallAnalytics {
  total_calls: number
  avg_duration_seconds: number
  completed_calls: number
  completion_rate: number
  avg_sentiment_score: number
}

export default function VoiceAgentDashboard({ userId }: { userId: string }) {
  const [calls, setCalls] = useState<CallRecord[]>([])
  const [analytics, setAnalytics] = useState<CallAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [isCallActive, setIsCallActive] = useState(false)
  const [callTranscript, setCallTranscript] = useState<string>('')

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchCalls()
    fetchAnalytics()
  }, [userId])

  const fetchCalls = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/voice/calls/user/${userId}?limit=20`)
      if (res.ok) {
        const data = await res.json()
        setCalls(data.calls || [])
      }
    } catch (error) {
      console.error('Fetch calls error:', error)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/voice/analytics/${userId}`)
      if (res.ok) {
        const data = await res.json()
        setAnalytics(data.analytics)
      }
    } catch (error) {
      console.error('Fetch analytics error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStartCall = async () => {
    setIsCallActive(true)
    setCallTranscript('')
  }

  const handleEndCall = async () => {
    setIsCallActive(false)
    fetchCalls()
  }

  const handleTranscriptAdd = (text: string) => {
    setCallTranscript((prev) => prev + '\n' + text)
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600'
      case 'negative':
        return 'text-red-600'
      case 'neutral':
        return 'text-slate-600'
      default:
        return 'text-slate-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Active Call Widget */}
      {isCallActive && (
        <Card className="p-6 bg-gradient-to-r from-red-50 to-orange-50 border-red-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 bg-red-600 rounded-full animate-pulse" />
              <h3 className="text-lg font-bold text-brand-night">Call in Progress</h3>
            </div>
            <button
              onClick={handleEndCall}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center gap-2"
            >
              <Phone className="w-4 h-4" />
              End Call
            </button>
          </div>

          <div className="bg-slate-100 p-4 rounded-lg mb-4 max-h-64 overflow-y-auto">
            <p className="text-sm text-slate-600 whitespace-pre-wrap">{callTranscript || 'Waiting for transcript...'}</p>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Add note..."
              onKeyPress={(e) => {
                if (e.key === 'Enter' && e.currentTarget.value) {
                  handleTranscriptAdd(e.currentTarget.value)
                  e.currentTarget.value = ''
                }
              }}
              className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
            />
            <button className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Total Calls</p>
          <p className="text-3xl font-bold text-brand-night">{analytics?.total_calls || 0}</p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Avg Duration</p>
          <p className="text-3xl font-bold text-brand-night">
            {analytics ? formatDuration(analytics.avg_duration_seconds) : '0s'}
          </p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Completed</p>
          <p className="text-3xl font-bold text-green-600">{analytics?.completed_calls || 0}</p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Completion Rate</p>
          <p className="text-3xl font-bold text-brand-night">
            {analytics ? Math.round(analytics.completion_rate * 100) : 0}%
          </p>
        </Card>

        <Card className="p-4">
          <p className="text-slate-600 text-sm mb-2">Avg Sentiment</p>
          <p className="text-3xl font-bold text-blue-600">
            {analytics ? (analytics.avg_sentiment_score * 100).toFixed(0) : 0}%
          </p>
        </Card>
      </div>

      {/* Start Call Button */}
      {!isCallActive && (
        <Card className="p-6">
          <button
            onClick={handleStartCall}
            className="w-full px-6 py-4 bg-brand-orange text-white rounded-lg hover:bg-orange-600 text-lg font-bold flex items-center justify-center gap-3"
          >
            <Phone className="w-6 h-6" />
            Start Outbound Call
          </button>
        </Card>
      )}

      {/* Recent Calls */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-brand-night mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Recent Calls
        </h3>

        {loading ? (
          <div className="text-center py-8 text-slate-500">Loading calls...</div>
        ) : calls.length === 0 ? (
          <div className="text-center py-8 text-slate-500">No calls yet</div>
        ) : (
          <div className="space-y-3">
            {calls.map((call) => (
              <div key={call.id} className="p-4 border border-slate-200 rounded-lg hover:bg-slate-50">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="font-semibold text-slate-900">{call.contact_number}</p>
                    <p className="text-sm text-slate-600 mt-1">
                      {call.call_type.charAt(0).toUpperCase() + call.call_type.slice(1)} •{' '}
                      {formatDuration(call.duration_seconds)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-sm font-semibold ${
                        call.status === 'completed' ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {call.status.charAt(0).toUpperCase() + call.status.slice(1)}
                    </p>
                    {call.sentiment && (
                      <p className={`text-xs mt-1 ${getSentimentColor(call.sentiment)}`}>
                        {call.sentiment.charAt(0).toUpperCase() + call.sentiment.slice(1)}
                      </p>
                    )}
                  </div>
                </div>
                <p className="text-xs text-slate-500">{new Date(call.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
