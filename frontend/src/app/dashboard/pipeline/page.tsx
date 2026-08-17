import { Suspense } from 'react'
import { PipelineContent } from './PipelineContent'

export default function PipelinePage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <PipelineContent />
    </Suspense>
  )
}

