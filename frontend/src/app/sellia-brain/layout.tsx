import type { Metadata } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'
const BRAIN_URL = `${SITE_URL}/sellia-brain`

const BRAIN_TITLE = 'SellIA Brain - Command Center de Ventas IA'
const BRAIN_DESCRIPTION = 'Dashboard de control de SellIA: visualiza agentes de IA vendiendo en tiempo real. Supervisa escuadrones autónomos de ventas, pipeline, analytics y operaciones de IA. Motor de crecimiento inteligente para B2B.'

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: BRAIN_TITLE,
  description: BRAIN_DESCRIPTION,
  keywords: [
    'SellIA dashboard', 'agente de ventas IA', 'command center ventas',
    'CRM con inteligencia artificial', 'automatización ventas B2B',
    'sales automation', 'AI sales agent', 'sales pipeline dashboard',
    'autonomous sales agent', 'revenue operations',
  ],
  alternates: { canonical: BRAIN_URL },
  robots: { index: true, follow: true, nocache: false },
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    url: BRAIN_URL,
    siteName: 'SellIA',
    title: BRAIN_TITLE,
    description: BRAIN_DESCRIPTION,
    images: [
      {
        url: `${SITE_URL}/og-image-sellia-brain.svg`,
        width: 1200,
        height: 630,
        alt: 'SellIA Brain - AI Sales Command Center',
        type: 'image/svg+xml',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: BRAIN_TITLE,
    description: BRAIN_DESCRIPTION,
    images: [`${SITE_URL}/og-image-sellia-brain.svg`],
  },
  viewport: 'width=device-width, initial-scale=1.0, viewport-fit=cover',
  formatDetection: { telephone: false, email: false },
}

export default function SelliaBrainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'SoftwareApplication',
            name: 'SellIA Brain',
            description: BRAIN_DESCRIPTION,
            url: BRAIN_URL,
            applicationCategory: 'BusinessApplication',
            operatingSystem: 'Web',
            offers: {
              '@type': 'Offer',
              price: '0',
              priceCurrency: 'USD',
            },
            image: `${SITE_URL}/og-image-sellia-brain.svg`,
            author: {
              '@type': 'Organization',
              name: 'SellIA',
              url: SITE_URL,
            },
            featureList: [
              'Real-time Sales Agent Monitoring',
              'AI-powered Lead Scoring',
              'Autonomous Outreach',
              'Sales Pipeline Management',
              'Computer Use Automation',
              'Revenue Operations Dashboard',
            ],
          }),
        }}
      />
      {children}
    </>
  )
}

