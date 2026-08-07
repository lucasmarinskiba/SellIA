import type { Metadata } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'

export const metadata: Metadata = {
  title: 'Soporte',
  description: 'Centro de soporte de SellIA: creá un ticket y te ayudamos.',
  alternates: { canonical: `${SITE_URL}/soporte` },
}

export default function SoporteLayout({ children }: { children: React.ReactNode }) {
  return children
}
