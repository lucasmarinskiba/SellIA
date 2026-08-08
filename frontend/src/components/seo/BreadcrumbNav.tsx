'use client'

/**
 * Breadcrumb navigation for SEO + UX.
 * Structured data for search engines, semantic HTML for browsers.
 */

import Link from 'next/link'

export interface BreadcrumbItem {
  label: string
  url?: string
  current?: boolean
}

interface BreadcrumbNavProps {
  items: BreadcrumbItem[]
}

export function BreadcrumbNav({ items }: BreadcrumbNavProps) {
  return (
    <nav aria-label="breadcrumb" className="mb-6">
      <ol className="flex items-center space-x-2 text-sm text-slate-400">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-center">
            {item.url && !item.current ? (
              <>
                <Link
                  href={item.url}
                  className="hover:text-blue-400 transition-colors"
                >
                  {item.label}
                </Link>
                {idx < items.length - 1 && (
                  <span className="mx-2 text-slate-600">/</span>
                )}
              </>
            ) : (
              <>
                <span className={item.current ? 'text-slate-200' : ''}>
                  {item.label}
                </span>
                {idx < items.length - 1 && (
                  <span className="mx-2 text-slate-600">/</span>
                )}
              </>
            )}
          </li>
        ))}
      </ol>

      {/* Structured data for search engines */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            itemListElement: items.map((item, idx) => ({
              '@type': 'ListItem',
              position: idx + 1,
              name: item.label,
              item: item.url ? `${typeof window !== 'undefined' ? window.location.origin : ''}${item.url}` : undefined,
            })).filter(item => item.item !== undefined),
          }),
        }}
      />
    </nav>
  )
}
