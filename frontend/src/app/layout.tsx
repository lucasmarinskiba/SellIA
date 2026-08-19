import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { NotificationProvider } from "@/app/providers"
import type { Metadata } from "next"
import { PreconnectBackend, CoreWebVitalsOptimization } from "@/components/seo/PerformanceOptimization"

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'
const TITLE = 'SellIA - Vende mientras duermes'
const DESCRIPTION = 'Agentes de IA que automatizan todo tu proceso de ventas: captan clientes, negocian y cierran, para cualquier negocio que venda o alquile bienes o servicios.'

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: '%s | SellIA' },
  description: DESCRIPTION,
  keywords: [
    'IA para ventas', 'agente de ventas IA', 'automatización de ventas',
    'chatbot de ventas', 'CRM con inteligencia artificial', 'vender por WhatsApp con IA',
    'SellIA',
  ],
  robots: { index: true, follow: true },
  // TODO: no brand assets exist anywhere in the repo (no logo, favicon, or
  // OG image) — add og-image.png (1200x630) and set openGraph.images /
  // twitter.images once one exists. A missing image is invisible; a
  // broken link shows as a broken image card when shared on social.
  openGraph: {
    type: 'website',
    locale: 'es_AR',
    url: SITE_URL,
    siteName: 'SellIA',
    title: TITLE,
    description: DESCRIPTION,
  },
  twitter: {
    card: 'summary',
    title: TITLE,
    description: DESCRIPTION,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <PreconnectBackend />
        <CoreWebVitalsOptimization />
      </head>
      <body className="font-sans antialiased bg-background text-foreground">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <NotificationProvider>
            {children}
          </NotificationProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

