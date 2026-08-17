import { Suspense } from 'react'
import { CatalogoContent } from './CatalogoContent'

export default function CatalogoPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <CatalogoContent />
    </Suspense>
  )
}

