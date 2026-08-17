import { Suspense } from 'react'
import { ConversacionesContent } from './ConversacionesContent'

export default function ConversacionesPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <ConversacionesContent />
    </Suspense>
  )
}

