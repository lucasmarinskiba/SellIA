'use client'

import { useAuth } from '@/hooks/useAuth'
import TestingDashboard from '@/components/Enterprise/TestingDashboard'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function TestingPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?from=/dashboard/enterprise/testing')
    }
  }, [user, isLoading, router])

  if (isLoading) return null
  if (!user) return null

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <TestingDashboard userId={user.id} />
    </div>
  )
}
