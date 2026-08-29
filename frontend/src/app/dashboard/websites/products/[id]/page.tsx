import { Suspense } from 'react'
import ProductForm from '../form'

export default async function EditProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ProductForm productId={id} mode="edit" />
    </Suspense>
  )
}
