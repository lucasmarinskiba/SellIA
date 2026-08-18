import { Suspense } from 'react'
import ProductsContent from './_components/products-content'

export default function ProductsDashboard() {
  return (
    <Suspense fallback={<div className="p-6 text-center">Cargando productos...</div>}>
      <ProductsContent />
    </Suspense>
  )
}
