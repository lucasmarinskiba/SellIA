'use client'

/**
 * Related internal links for SEO + User journey optimization.
 * Improves internal link structure, navigation patterns, and crawlability.
 */

import Link from 'next/link'

export interface RelatedLink {
  href: string
  title: string
  description: string
}

interface RelatedLinksProps {
  title?: string
  links: RelatedLink[]
}

export function RelatedLinks({ title = 'Related Resources', links }: RelatedLinksProps) {
  return (
    <aside className="mt-12 pt-8 border-t border-slate-800">
      <h2 className="text-lg font-semibold text-slate-200 mb-6">{title}</h2>
      <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="block p-4 rounded-lg border border-slate-700 hover:border-blue-500 hover:bg-blue-500/5 transition-colors group"
            >
              <h3 className="font-medium text-blue-400 group-hover:text-blue-300 mb-2">
                {link.title}
                <span className="ml-2">→</span>
              </h3>
              <p className="text-sm text-slate-400">{link.description}</p>
            </Link>
          </li>
        ))}
      </ul>
    </aside>
  )
}

