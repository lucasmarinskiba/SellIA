'use client'

import { useAuth } from '@/hooks/useAuth'
import AgentDashboard from '@/components/AgentDashboard'
import { redirect } from 'next/navigation'

export default function AgentsCentralPage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand-orange mb-4" />
          <p className="text-slate-600">Cargando centro de agentes...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="space-y-8 max-w-7xl">
      <AgentDashboard />
    </div>
  )
}
