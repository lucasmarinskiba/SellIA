import { Suspense } from 'react'
import { AgentesContent } from './AgentesContent'

export default function AgentesPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <AgentesContent />
    </Suspense>
  )
}

