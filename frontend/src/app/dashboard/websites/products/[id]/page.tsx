import { Suspense } from 'react'
import ProductForm from '../form'

export default function EditProductPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ProductForm productId={params.id} mode="edit" />
    </Suspense>
  )
}
