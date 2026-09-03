import { Suspense } from 'react'
import { TransformacionContent } from './TransformacionContent'

export default function TransformacionPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-b-2 border-primary" />
        </div>
      }
    >
      <TransformacionContent />
    </Suspense>
  )
}
