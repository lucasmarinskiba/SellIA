'use client'

import { useAuth } from '@/hooks/useAuth'
import DealRiskDashboard from '@/components/Enterprise/DealRiskDashboard'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function IntelligencePage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login?from=/dashboard/enterprise/intelligence')
    }
  }, [user, loading, router])

  if (loading) return null
  if (!user) return null

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-brand-night mb-2">Deal Intelligence & Forecasting</h1>
          <p className="text-slate-600">AI-powered deal scoring, win probability & risk assessment</p>
        </div>

        <DealRiskDashboard userId={user.id} />
      </div>
    </div>
  )
}

