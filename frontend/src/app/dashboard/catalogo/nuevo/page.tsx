import { Suspense } from 'react'
import { NuevoItemContent } from './NuevoItemContent'

export default function NuevoItemPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <NuevoItemContent />
    </Suspense>
  )
}

