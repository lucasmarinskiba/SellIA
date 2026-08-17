import { Suspense } from 'react'
import { CajaDeCristalContent } from './CajaDeCristalContent'

export default function CajaDeCristalPage() {
  return (
    <Suspense fallback={<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>}>
      <CajaDeCristalContent />
    </Suspense>
  )
}

