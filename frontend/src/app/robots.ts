import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'

  return {
    rules: [
      {
        userAgent: '*',
        allow: [
          '/',
          '/sellia-brain',
          '/sellia-dashboard',
          '/sellia-landing',
          '/privacy',
          '/data-deletion',
          '/soporte',
        ],
        disallow: [
          '/api/',
          '/admin/',
          '/_next/',
          '/node_modules/',
        ],
        crawlDelay: 1,
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
