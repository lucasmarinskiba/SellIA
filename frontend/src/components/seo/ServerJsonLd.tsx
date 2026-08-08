/**
 * Server-side JSON-LD Schema Renderer
 * Must NOT have 'use client' directive to render in SSR
 */

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
