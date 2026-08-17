import { Suspense } from 'react'
import { WorkflowBuilderContent } from './WorkflowBuilderContent'

export default function WorkflowBuilderPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <WorkflowBuilderContent />
    </Suspense>
  )
}

