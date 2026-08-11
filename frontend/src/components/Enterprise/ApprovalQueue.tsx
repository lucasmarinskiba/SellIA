'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/Card'

interface Approval {
  id: string
  action_id: string
  action_type: string
  requested_by: string
  created_at: string
}

export default function ApprovalQueue({ userId }: { userId: string }) {
  const [pending, setPending] = useState<Approval[]>([])
  const [loading, setLoading] = useState(true)

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchPending()
    const interval = setInterval(fetchPending, 30000)
    return () => clearInterval(interval)
  }, [userId])

  const fetchPending = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/collaboration/pending/${userId}`)
      if (res.ok) {
        const data = await res.json()
        setPending(data.approvals || [])
      }
    } catch (error) {
      console.error('Fetch pending error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (actionId: string) => {
    try {
      await fetch(`${apiUrl}/api/v1/collaboration/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          action_id: actionId,
          decision: 'approved',
        }),
      })
      fetchPending()
    } catch (error) {
      console.error('Approve error:', error)
    }
  }

  const handleReject = async (actionId: string) => {
    try {
      await fetch(`${apiUrl}/api/v1/collaboration/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          action_id: actionId,
          decision: 'rejected',
        }),
      })
      fetchPending()
    } catch (error) {
      console.error('Reject error:', error)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-brand-night flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-orange-600" />
          Approval Queue
        </h3>
        {pending.length > 0 && (
          <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full font-bold text-sm">
            {pending.length}
          </span>
        )}
      </div>

      {loading ? (
        <div className="text-center py-8 text-slate-500">Loading approvals...</div>
      ) : pending.length === 0 ? (
        <div className="text-center py-8 text-slate-500 text-sm">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>All caught up! No pending approvals.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {pending.map((approval) => (
            <div key={approval.id} className="p-4 border border-orange-200 bg-orange-50 rounded-lg">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-semibold text-brand-night capitalize">{approval.action_type}</p>
                  <p className="text-xs text-slate-600 mt-1">Requested by: {approval.requested_by}</p>
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(approval.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(approval.action_id)}
                  className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </button>
                <button
                  onClick={() => handleReject(approval.action_id)}
                  className="flex-1 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium flex items-center justify-center gap-2"
                >
                  <XCircle className="w-4 h-4" />
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
