import type { Metadata } from 'next'
import { ServerBreadcrumbListSchema } from '@/components/seo/ServerJsonLd'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'

export const metadata: Metadata = {
  title: 'Customer Testimonials | SellIA',
  description: 'Real reviews from SellIA customers. See how AI sales agents are transforming B2B sales.',
  alternates: { canonical: `${SITE_URL}/testimonials` },
  robots: { index: true, follow: true },
  openGraph: {
    type: 'website',
    url: `${SITE_URL}/testimonials`,
    title: 'Customer Testimonials | SellIA',
    description: 'Real reviews from SellIA customers',
  },
}

export default function TestimonialsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <ServerBreadcrumbListSchema path="/testimonials" />
      {children}
    </>
  )
}
