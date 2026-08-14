'use client'

/**
 * Semantic Recommendations Component
 * Phase 4: Embeddings-powered content discovery
 * Shows related content, personalized recommendations, topic clusters
 */

import React, { useEffect, useState } from 'react'
import Link from 'next/link'

export interface Recommendation {
  id: string
  title: string
  url: string
  reason?: string
  similarity?: number
}

export interface RelatedContent {
  id: string
  title: string
  similarity: number
}

export function RelatedContentSection({
  contentId,
  limit = 5,
}: {
  contentId: string
  limit?: number
}) {
  const [related, setRelated] = useState<RelatedContent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchRelated() {
      try {
        const response = await fetch(
          `/api/v1/embeddings/similar-content?content_id=${contentId}&limit=${limit}`,
        )
        const data = await response.json()
        setRelated(data.results || [])
      } catch (error) {
        console.error('Failed to fetch related content:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchRelated()
  }, [contentId, limit])

  if (loading) return <div style={{ padding: '20px', textAlign: 'center' }}>Loading related content...</div>

  if (!related.length) return null

  return (
    <section
      style={{
        padding: '40px',
        borderTop: '1px solid rgba(255,255,255,0.1)',
        marginTop: '60px',
      }}
    >
      <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '30px' }}>
        Related Content
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        {related.map((item) => (
          <article
            key={item.id}
            style={{
              padding: '20px',
              borderRadius: '8px',
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(13,18,30,0.5)',
            }}
          >
            <Link
              href={item.url}
              style={{
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px', color: '#00D4FF' }}>
                {item.title}
              </h3>
            </Link>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
              Similarity: {(item.similarity * 100).toFixed(0)}%
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

export function PersonalizedRecommendations({
  userContext = 'browsing',
  currentPage,
  limit = 3,
}: {
  userContext?: 'browsing' | 'signup' | 'converting'
  currentPage?: string
  limit?: number
}) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchRecommendations() {
      try {
        const params = new URLSearchParams({
          user_context: userContext,
          limit: limit.toString(),
        })
        if (currentPage) params.append('current_page', currentPage)

        const response = await fetch(`/api/v1/embeddings/recommendations?${params}`)
        const data = await response.json()
        setRecommendations(data.recommendations || [])
      } catch (error) {
        console.error('Failed to fetch recommendations:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendations()
  }, [userContext, currentPage, limit])

  if (loading) return null
  if (!recommendations.length) return null

  const contextLabels = {
    browsing: 'Explore',
    signup: 'Ready to Start?',
    converting: 'Next Steps',
  }

  return (
    <aside
      style={{
        padding: '32px',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, rgba(0,212,255,0.05), rgba(139,92,246,0.05))',
        border: '1px solid rgba(0,212,255,0.1)',
      }}
    >
      <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px', color: '#00D4FF' }}>
        {contextLabels[userContext]}
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {recommendations.map((rec) => (
          <Link
            key={rec.id}
            href={rec.url}
            style={{
              padding: '12px 16px',
              borderRadius: '8px',
              background: 'rgba(13,18,30,0.6)',
              border: '1px solid rgba(255,255,255,0.1)',
              textDecoration: 'none',
              color: 'inherit',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLElement
              el.style.borderColor = 'rgba(0,212,255,0.3)'
              el.style.background = 'rgba(13,18,30,0.8)'
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLElement
              el.style.borderColor = 'rgba(255,255,255,0.1)'
              el.style.background = 'rgba(13,18,30,0.6)'
            }}
          >
            <div style={{ fontWeight: '600', color: '#fff' }}>{rec.title}</div>
            {rec.reason && (
              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginTop: '4px' }}>
                {rec.reason}
              </div>
            )}
          </Link>
        ))}
      </div>
    </aside>
  )
}

export function ContentCluster({
  topic = 'sales-automation',
}: {
  topic?: 'sales-automation' | 'ai-features' | 'pricing'
}) {
  const [clusterData, setClusterData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchCluster() {
      try {
        const response = await fetch(`/api/v1/embeddings/content-cluster?cluster_topic=${topic}`)
        const data = await response.json()
        setClusterData(data)
      } catch (error) {
        console.error('Failed to fetch cluster:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchCluster()
  }, [topic])

  if (loading || !clusterData) return null

  return (
    <nav
      aria-label={`${topic} content cluster`}
      style={{
        padding: '24px',
        borderRadius: '8px',
        background: 'rgba(13,18,30,0.5)',
        border: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>
        {clusterData.name}
      </h3>
      <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', marginBottom: '16px' }}>
        {clusterData.description}
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
        {clusterData.hasPart?.map((item: any) => (
          <Link
            key={item.name}
            href={item.url}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              background: 'rgba(0,212,255,0.1)',
              color: '#00D4FF',
              textDecoration: 'none',
              fontSize: '12px',
              fontWeight: '500',
              textAlign: 'center',
              border: '1px solid rgba(0,212,255,0.2)',
            }}
          >
            {item.name}
          </Link>
        ))}
      </div>
    </nav>
  )
}

export function EmbeddingStatsWidget() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch('/api/v1/embeddings/embedding-stats')
        const data = await response.json()
        setStats(data)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  if (loading || !stats) return null

  return (
    <div
      style={{
        padding: '16px',
        borderRadius: '8px',
        background: 'rgba(13,18,30,0.5)',
        border: '1px solid rgba(255,255,255,0.1)',
        fontSize: '12px',
      }}
    >
      <div style={{ fontWeight: '600', marginBottom: '12px' }}>Semantic Search Status</div>
      <div style={{ display: 'grid', gap: '8px', color: 'rgba(255,255,255,0.7)' }}>
        <div>📊 {stats.statistics?.total_embeddings} content items indexed</div>
        <div>⚡ {stats.performance?.avg_similarity_search} per query</div>
        <div>🗄️ {stats.statistics?.vector_dimensions}D embeddings</div>
      </div>
    </div>
  )
}

