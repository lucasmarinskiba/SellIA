'use client'

/**
 * Authority Building Components
 * Phase 3: E-E-A-T signals (Expertise, Experience, Authority, Trustworthiness)
 * Testimonials, reviews, team bios, social proof
 */

import React from 'react'

export interface Testimonial {
  id: string
  name: string
  role?: string
  company?: string
  rating: number
  text: string
  image?: string
  date?: string
}

export interface TeamMember {
  id: string
  name: string
  role: string
  bio?: string
  image?: string
  expertise: string[]
  social?: {
    linkedin?: string
    twitter?: string
  }
}

export function TestimonialCard({
  testimonial,
  variant = 'default',
}: {
  testimonial: Testimonial
  variant?: 'default' | 'minimal' | 'featured'
}) {
  return (
    <article
      itemScope
      itemType="https://schema.org/Review"
      style={{
        padding: variant === 'featured' ? '32px' : '24px',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(13,18,30,0.5)',
      }}
    >
      {/* Hidden for SEO but parsed by crawlers */}
      <meta itemProp="name" content={`Review by ${testimonial.name}`} />
      <meta itemProp="description" content={testimonial.text} />
      <meta itemProp="author" content={testimonial.name} />
      {testimonial.date && <meta itemProp="datePublished" content={testimonial.date} />}

      {/* Rating */}
      <div
        itemScope
        itemType="https://schema.org/Rating"
        style={{ marginBottom: '12px', display: 'flex', gap: '4px' }}
      >
        <meta itemProp="ratingValue" content={testimonial.rating.toString()} />
        <meta itemProp="bestRating" content="5" />
        {Array.from({ length: 5 }).map((_, i) => (
          <span key={i} style={{ fontSize: '18px', color: i < testimonial.rating ? '#d3ff3a' : 'rgba(255,255,255,0.2)' }}>
            ★
          </span>
        ))}
      </div>

      {/* Text */}
      <p itemProp="reviewBody" style={{ fontSize: '15px', lineHeight: '1.6', marginBottom: '16px', color: 'rgba(255,255,255,0.8)' }}>
        {testimonial.text}
      </p>

      {/* Author */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '16px' }}>
        {testimonial.image && (
          <img
            src={testimonial.image}
            alt={testimonial.name}
            style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }}
          />
        )}
        <div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: '#fff' }}>
            <span itemProp="author">{testimonial.name}</span>
          </div>
          {testimonial.role && (
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
              {testimonial.role} {testimonial.company && `at ${testimonial.company}`}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}

export function TeamMemberCard({
  member,
  variant = 'default',
}: {
  member: TeamMember
  variant?: 'default' | 'featured'
}) {
  return (
    <article
      itemScope
      itemType="https://schema.org/Person"
      style={{
        padding: variant === 'featured' ? '32px' : '24px',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.1)',
        background: 'rgba(13,18,30,0.5)',
        textAlign: 'center' as const,
      }}
    >
      {/* SEO metadata */}
      <meta itemProp="name" content={member.name} />
      <meta itemProp="jobTitle" content={member.role} />
      {member.bio && <meta itemProp="description" content={member.bio} />}
      {member.image && <meta itemProp="image" content={member.image} />}

      {/* Image */}
      {member.image && (
        <img
          itemProp="image"
          src={member.image}
          alt={member.name}
          style={{ width: '120px', height: '120px', borderRadius: '50%', objectFit: 'cover', marginBottom: '16px' }}
        />
      )}

      {/* Name & Role */}
      <h3 itemProp="name" style={{ fontSize: '18px', fontWeight: '700', marginBottom: '4px', color: '#fff' }}>
        {member.name}
      </h3>
      <p itemProp="jobTitle" style={{ fontSize: '14px', color: '#00D4FF', marginBottom: '12px' }}>
        {member.role}
      </p>

      {/* Bio */}
      {member.bio && (
        <p itemProp="description" style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)', marginBottom: '12px', lineHeight: '1.5' }}>
          {member.bio}
        </p>
      )}

      {/* Expertise */}
      {member.expertise.length > 0 && (
        <div style={{ marginBottom: '12px' }}>
          {member.expertise.map((exp, i) => (
            <meta key={i} itemProp="knowsAbout" content={exp} />
          ))}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            {member.expertise.map((exp) => (
              <span key={exp} style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '4px', background: 'rgba(0,212,255,0.1)', color: '#00D4FF' }}>
                {exp}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Social */}
      {member.social && (
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '12px' }}>
          {member.social.linkedin && (
            <a href={member.social.linkedin} rel="noopener noreferrer" style={{ color: '#0A66C2', fontSize: '12px' }}>
              LinkedIn
            </a>
          )}
          {member.social.twitter && (
            <a href={member.social.twitter} rel="noopener noreferrer" style={{ color: '#1DA1F2', fontSize: '12px' }}>
              Twitter
            </a>
          )}
        </div>
      )}
    </article>
  )
}

export function SocialProofSection({
  rating,
  reviewCount,
  customers,
}: {
  rating: number
  reviewCount: number
  customers: number
}) {
  return (
    <div
      itemScope
      itemType="https://schema.org/AggregateRating"
      style={{
        padding: '24px',
        borderRadius: '12px',
        background: 'rgba(0,212,255,0.05)',
        border: '1px solid rgba(0,212,255,0.2)',
        textAlign: 'center' as const,
      }}
    >
      <meta itemProp="ratingValue" content={rating.toFixed(1)} />
      <meta itemProp="bestRating" content="5" />
      <meta itemProp="ratingCount" content={reviewCount.toString()} />

      <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '12px' }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <span key={i} style={{ fontSize: '20px', color: i < Math.floor(rating) ? '#d3ff3a' : 'rgba(255,255,255,0.2)' }}>
            ★
          </span>
        ))}
      </div>

      <p style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
        {rating.toFixed(1)} out of 5 stars
      </p>

      <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>
        Based on {reviewCount} verified reviews from {customers.toLocaleString()} customers
      </p>
    </div>
  )
}

export function CredentialsBadge({
  title,
  issuer,
  year,
}: {
  title: string
  issuer: string
  year: number
}) {
  return (
    <div
      itemScope
      itemType="https://schema.org/Award"
      style={{
        padding: '12px 16px',
        borderRadius: '8px',
        background: 'rgba(139,92,246,0.1)',
        border: '1px solid rgba(139,92,246,0.3)',
        fontSize: '13px',
      }}
    >
      <meta itemProp="name" content={title} />
      <meta itemProp="awardedBy" content={issuer} />
      <meta itemProp="datePublished" content={year.toString()} />

      <div style={{ fontWeight: '600', color: '#8B5CF6' }}>{title}</div>
      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>
        {issuer} • {year}
      </div>
    </div>
  )
}
