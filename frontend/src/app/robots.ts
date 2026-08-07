import type { MetadataRoute } from 'next'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: ['/landing', '/privacy', '/data-deletion', '/soporte'],
        disallow: [
          '/api/',
          '/dashboard',
          '/sellia-brain',
          '/sellia-dashboard',
          '/sellia-ext-auth',
          '/sellia-onboarding',
          '/sellia-login',
          '/sellia-signup',
          '/sellia-landing',
          '/onboarding',
          '/login',
          '/signup',
          '/register',
          '/pitch',
          '/preview-hub',
          '/preview-ui',
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  }
}
