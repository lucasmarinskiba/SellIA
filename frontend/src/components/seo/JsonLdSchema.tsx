'use client'

/**
 * JSON-LD Schema Component
 * Renders structured data for SEO optimization
 * Supports: Organization, SoftwareApplication, LocalBusiness, FAQPage, BreadcrumbList, Product, Event
 */

import { useMemo } from 'react'

export interface JsonLdProps {
  type: 'organization' | 'software-application' | 'local-business' | 'faq' | 'breadcrumb' | 'product' | 'event'
  data: Record<string, unknown>
}

export function JsonLdSchema({ type, data }: JsonLdProps) {
  const schemaData = useMemo(() => ({
    '@context': 'https://schema.org',
    '@type': type.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(''),
    ...data,
  }), [type, data])

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaData) }}
    />
  )
}

/**
 * Organization Schema
 * Use on homepage and global layouts
 */
export function OrganizationSchema() {
  const data = {
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
  }
  return <JsonLdSchema type="organization" data={data} />
}

/**
 * SoftwareApplication Schema
 * Use on /sellia-brain and product pages
 */
export function SoftwareApplicationSchema() {
  const data = {
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
  return <JsonLdSchema type="software-application" data={data} />
}

/**
 * FAQPage Schema
 * Use on FAQ pages to capture featured snippets
 */
export function FAQPageSchema() {
  const data = {
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
  return <JsonLdSchema type="faq" data={data} />
}

/**
 * BreadcrumbList Schema
 * Use for navigation breadcrumbs on all pages
 */
export interface BreadcrumbItem {
  name: string
  url: string
  position: number
}

export function BreadcrumbListSchema({ items }: { items: BreadcrumbItem[] }) {
  const data = {
    itemListElement: items.map(item => ({
      '@type': 'ListItem',
      position: item.position,
      name: item.name,
      item: item.url,
    })),
  }
  return <JsonLdSchema type="breadcrumb" data={data} />
}

/**
 * Product Schema
 * Use on product/feature pages
 */
export interface ProductSchemaProps {
  name: string
  description: string
  url: string
  ratingValue?: number
  ratingCount?: number
  price?: string
}

export function ProductSchema({
  name,
  description,
  url,
  ratingValue = 4.8,
  ratingCount = 150,
  price = '0',
}: ProductSchemaProps) {
  const data = {
    name,
    description,
    url,
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: ratingValue.toString(),
      ratingCount: ratingCount.toString(),
    },
    offers: {
      '@type': 'Offer',
      price,
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
    },
  }
  return <JsonLdSchema type="product" data={data} />
}

/**
 * Event Schema
 * Use on webinar, demo, or event pages
 */
export interface EventSchemaProps {
  name: string
  description: string
  startDate: string
  endDate: string
  eventUrl?: string
}

export function EventSchema({
  name,
  description,
  startDate,
  endDate,
  eventUrl,
}: EventSchemaProps) {
  const data = {
    name,
    description,
    startDate,
    endDate,
    eventStatus: 'https://schema.org/EventScheduled',
    eventAttendanceMode: 'https://schema.org/OnlineEventAttendanceMode',
    location: {
      '@type': 'VirtualLocation',
      url: eventUrl || 'https://sellia-brain.vercel.app',
    },
    organizer: {
      '@type': 'Organization',
      name: 'SellIA',
      url: 'https://sellia-brain.vercel.app',
    },
  }
  return <JsonLdSchema type="event" data={data} />
}

