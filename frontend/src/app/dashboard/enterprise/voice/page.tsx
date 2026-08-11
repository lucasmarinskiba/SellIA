'use client'

import { useAuth } from '@/hooks/useAuth'
import VoiceAgentDashboard from '@/components/Enterprise/VoiceAgentDashboard'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function VoiceAgentPage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login?from=/dashboard/enterprise/voice')
    }
  }, [user, isLoading, router])

  if (isLoading) return null
  if (!user) return null

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-brand-night mb-2">AI Voice Agent</h1>
          <p className="text-slate-600">Real-time call handling, transcription & sentiment analysis</p>
        </div>

        <VoiceAgentDashboard userId={user.id} />
      </div>
    </div>
  )
}
