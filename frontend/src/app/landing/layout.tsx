import type { Metadata } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'
const TITLE = 'SellIA - Vende mientras duermes | Agentes de IA para ventas'
const DESCRIPTION = 'SellIA automatiza tu proceso de ventas de punta a punta con IA: capta leads, negocia y cierra por vos. Para cualquier negocio que venda o alquile bienes o servicios.'

export const metadata: Metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: `${SITE_URL}/landing` },
  openGraph: {
    type: 'website',
    url: `${SITE_URL}/landing`,
    title: TITLE,
    description: DESCRIPTION,
  },
}

const jsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'SellIA',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web',
  description: DESCRIPTION,
  url: `${SITE_URL}/landing`,
  offers: {
    '@type': 'Offer',
    priceCurrency: 'ARS',
    price: '0',
    description: 'Plan gratuito disponible',
  },
}

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      {children}
    </>
  )
}
