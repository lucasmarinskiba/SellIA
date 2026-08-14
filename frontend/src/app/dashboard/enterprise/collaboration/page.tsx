'use client'

import { useAuth } from '@/hooks/useAuth'
import DealCollaborationPanel from '@/components/Enterprise/DealCollaborationPanel'
import ApprovalQueue from '@/components/Enterprise/ApprovalQueue'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function CollaborationPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()
  const [selectedDealId, setSelectedDealId] = useState('deal_001')

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?from=/dashboard/enterprise/collaboration')
    }
  }, [user, isLoading, router])

  if (isLoading) return null
  if (!user) return null

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-brand-night mb-2">Team Collaboration</h1>
        <p className="text-slate-600 mb-8">Real-time deal discussions, approvals & team coordination</p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Collaboration Panel */}
          <div className="lg:col-span-2">
            <DealCollaborationPanel userId={user.id} dealId={selectedDealId} />
          </div>

          {/* Sidebar: Approval Queue + Deal List */}
          <div className="space-y-6">
            <ApprovalQueue userId={user.id} />

            {/* Deal List Selector */}
            <div className="bg-white p-4 rounded-lg border border-slate-200">
              <h3 className="font-semibold text-brand-night mb-3">Recent Deals</h3>
              <div className="space-y-2">
                {['deal_001', 'deal_002', 'deal_003'].map((deal) => (
                  <button
                    key={deal}
                    onClick={() => setSelectedDealId(deal)}
                    className={`w-full p-3 text-left rounded-lg transition-colors ${
                      selectedDealId === deal
                        ? 'bg-orange-100 border border-brand-orange'
                        : 'bg-slate-50 border border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    <p className="font-medium text-sm text-brand-night">{deal}</p>
                    <p className="text-xs text-slate-600 mt-1">Enterprise Deal</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

