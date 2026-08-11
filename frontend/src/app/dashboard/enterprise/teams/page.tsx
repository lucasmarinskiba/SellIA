'use client'

import { useAuth } from '@/hooks/useAuth'
import TeamManager from '@/components/Enterprise/TeamManager'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function TeamsPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?from=/dashboard/enterprise/teams')
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4" />
          <p className="text-slate-600">Cargando equipo...</p>
        </div>
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <TeamManager userId={user.id} />
    </div>
  )
}
