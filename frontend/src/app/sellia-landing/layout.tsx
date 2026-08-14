import type { Metadata } from 'next'
import { ServerOrganizationSchema, ServerBreadcrumbListSchema, ServerAggregateReviewSchema, ServerOrganizationExpandedSchema } from '@/components/seo/ServerJsonLd'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'
const LANDING_URL = `${SITE_URL}/sellia-landing`

const LANDING_TITLE = 'SellIA - AI Sales Agent | Automatiza B2B Vendiendo 24/7'
const LANDING_DESCRIPTION = 'Agente de ventas IA que vende automáticamente. Integración con WhatsApp, email, LinkedIn. 14 días gratis. Sin tarjeta de crédito. Multiplica tu equipo de ventas.'

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: LANDING_TITLE,
  description: LANDING_DESCRIPTION,
  keywords: [
    'agente de ventas IA', 'sales automation', 'sales bot', 'AI sales representative',
    'vendedor automático', 'automatizar ventas B2B', 'chatbot ventas',
    'WhatsApp sales bot', 'AI sales agent platform',
  ],
  alternates: { canonical: LANDING_URL },
  robots: { index: true, follow: true, nocache: false },
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    url: LANDING_URL,
    siteName: 'SellIA',
    title: LANDING_TITLE,
    description: LANDING_DESCRIPTION,
    images: [
      {
        url: `${SITE_URL}/og-image-sellia-brain.svg`,
        width: 1200,
        height: 630,
        alt: 'SellIA - AI Sales Agent',
        type: 'image/svg+xml',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: LANDING_TITLE,
    description: LANDING_DESCRIPTION,
    images: [`${SITE_URL}/og-image-sellia-brain.svg`],
  },
  viewport: 'width=device-width, initial-scale=1.0, viewport-fit=cover',
  formatDetection: { telephone: false, email: false },
}

export default function SelliaNandingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <ServerOrganizationSchema />
      <ServerOrganizationExpandedSchema />
      <ServerBreadcrumbListSchema path="/sellia-landing" />
      <ServerAggregateReviewSchema />
      {children}
    </>
  )
}

