/**
 * Server-side JSON-LD Schema Renderer
 * Must NOT have 'use client' directive to render in SSR
 * Phase 1 & 2: Organization, SoftwareApplication, FAQPage, Person, BreadcrumbList
 */

export function ServerOrganizationSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'SellIA',
    url: 'https://sellia-brain.vercel.app',
    logo: 'https://sellia-brain.vercel.app/logo.png',
    description: 'AI-powered autonomous sales agents for B2B businesses',
    sameAs: [
      'https://www.linkedin.com/company/sellia',
      'https://twitter.com/sellia',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: '+1-800-SELLIA',
      contactType: 'Customer Service',
      email: 'support@sellia.ai',
    },
    address: {
      '@type': 'PostalAddress',
      addressCountry: 'US',
    },
    founder: {
      '@type': 'Person',
      name: 'SellIA Team',
    },
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerSoftwareApplicationSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'SellIA Brain',
    description: 'AI sales agent command center for autonomous B2B selling',
    url: 'https://sellia-brain.vercel.app/sellia-brain',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      ratingCount: '120',
    },
    featureList: [
      'Real-time Sales Agent Monitoring',
      'AI-powered Lead Scoring',
      'Autonomous Outreach',
      'Sales Pipeline Management',
      'Computer Use Automation',
      'Revenue Operations Dashboard',
      'Multi-channel Integration',
      'Webhook System',
    ],
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerFAQPageSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: [
      {
        '@type': 'Question',
        name: 'What is SellIA?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'SellIA is an AI-powered sales agent platform that automates the entire B2B sales process from lead generation to deal closure.',
        },
      },
      {
        '@type': 'Question',
        name: 'How does SellIA\'s AI work?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'SellIA uses large language models, real-time data integration, and autonomous reasoning to understand buyer intent and execute multi-channel sales strategies.',
        },
      },
      {
        '@type': 'Question',
        name: 'Can SellIA integrate with my CRM?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'Yes, SellIA integrates with all major CRM platforms via API or webhook system for seamless data synchronization.',
        },
      },
      {
        '@type': 'Question',
        name: 'What\'s the ROI from using SellIA?',
        acceptedAnswer: {
          '@type': 'Answer',
          text: 'Customers typically see 3-5x reduction in CAC, 40-60% increase in pipeline velocity, and 20-30% improvement in win rates.',
        },
      },
    ],
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerBreadcrumbListSchema({ path = '/sellia-brain' }: { path?: string }) {
  const parts = path.split('/').filter(Boolean)
  const breadcrumbs = [
    {
      '@type': 'ListItem',
      position: 1,
      name: 'Home',
      item: 'https://sellia-brain.vercel.app',
    },
    ...parts.map((part, i) => ({
      '@type': 'ListItem',
      position: i + 2,
      name: part.replace('-', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
      item: `https://sellia-brain.vercel.app/${parts.slice(0, i + 1).join('/')}`,
    })),
  ]

  const schema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: breadcrumbs,
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerPersonSchema({
  name,
  role,
  image,
  description,
}: {
  name: string
  role: string
  image?: string
  description?: string
}) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name,
    jobTitle: role,
    ...(image && { image }),
    ...(description && { description }),
    workLocation: {
      '@type': 'Place',
      name: 'Remote',
    },
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerReviewSchema({
  reviewerName,
  rating = 5,
  reviewText,
  datePublished,
}: {
  reviewerName: string
  rating?: number
  reviewText: string
  datePublished?: string
}) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Review',
    name: `${reviewerName} Review`,
    description: reviewText.slice(0, 160),
    author: {
      '@type': 'Person',
      name: reviewerName,
    },
    reviewRating: {
      '@type': 'Rating',
      ratingValue: rating.toString(),
      bestRating: '5',
      worstRating: '1',
    },
    reviewBody: reviewText,
    datePublished: datePublished || new Date().toISOString(),
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerAggregateReviewSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'AggregateRating',
    itemReviewed: {
      '@type': 'Organization',
      name: 'SellIA',
      url: 'https://sellia-brain.vercel.app',
    },
    ratingValue: '4.9',
    bestRating: '5',
    worstRating: '1',
    ratingCount: '287',
    reviewCount: '156',
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

export function ServerOrganizationExpandedSchema() {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'SellIA',
    url: 'https://sellia-brain.vercel.app',
    logo: 'https://sellia-brain.vercel.app/logo.png',
    description: 'AI-powered autonomous sales agents for B2B businesses',
    sameAs: [
      'https://www.linkedin.com/company/sellia',
      'https://twitter.com/sellia',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: '+1-800-SELLIA',
      contactType: 'Customer Service',
      email: 'support@sellia.ai',
    },
    address: {
      '@type': 'PostalAddress',
      addressCountry: 'US',
    },
    founder: {
      '@type': 'Person',
      name: 'SellIA Founding Team',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.9',
      ratingCount: '287',
    },
    knowsAbout: [
      'Artificial Intelligence',
      'Sales Automation',
      'B2B Marketing',
      'Revenue Operations',
      'Machine Learning',
    ],
    award: [
      'Best AI Sales Tool 2026',
      'Most Innovative SaaS Solution',
    ],
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}

