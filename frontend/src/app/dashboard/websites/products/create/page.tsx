import { Suspense } from 'react'
import ProductForm from '../form'

export default function CreateProductPage() {
  return (
    <Suspense fallback={<div className="p-6 text-center">Cargando formulario...</div>}>
      <ProductForm mode="create" />
    </Suspense>
  )
}
