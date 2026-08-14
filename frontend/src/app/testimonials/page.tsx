import type { Metadata } from 'next'
import { ServerAggregateReviewSchema, ServerReviewSchema, ServerOrganizationExpandedSchema } from '@/components/seo/ServerJsonLd'
import { TestimonialCard, SocialProofSection, CredentialsBadge } from '@/components/seo/AuthorityBuilder'
import { RelatedContentSection, PersonalizedRecommendations, ContentCluster } from '@/components/seo/SemanticRecommendations'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://sellia-brain.vercel.app'

export const metadata: Metadata = {
  title: 'Customer Testimonials - SellIA',
  description: 'Real reviews from SellIA customers. See how AI sales agents are transforming B2B sales for businesses worldwide.',
  alternates: { canonical: `${SITE_URL}/testimonials` },
}

const testimonials = [
  {
    id: '1',
    name: 'María García',
    role: 'Sales Director',
    company: 'TechStart Argentina',
    rating: 5,
    text: 'SellIA aumentó nuestro pipeline en 40% en el primer mes. El cerebro IA entiende nuestros clientes mejor que nosotros mismos. Definitivamente el mejor investment en ventas que hicimos.',
    date: '2026-07-15',
  },
  {
    id: '2',
    name: 'Carlos López',
    role: 'CEO',
    company: 'Digital Solutions LLC',
    rating: 5,
    text: 'Automated 80% of our outreach while maintaining personalization. Our conversion rate jumped 35%. SellIA does the math so we focus on closing.',
    date: '2026-07-10',
  },
  {
    id: '3',
    name: 'Sofia Chen',
    role: 'Revenue Operations Manager',
    company: 'GrowthCo',
    rating: 5,
    text: 'What took us 3 SDRs now takes SellIA and 1 person. Cost per acquisition dropped 60%. Our board was shocked at the margins.',
    date: '2026-06-28',
  },
]

export default function TestimonialsPage() {
  return (
    <>
      <ServerOrganizationExpandedSchema />
      <ServerAggregateReviewSchema />
      {testimonials.map((t) => (
        <ServerReviewSchema key={t.id} reviewerName={t.name} rating={t.rating} reviewText={t.text} datePublished={t.date} />
      ))}

      <main role="main" style={{ maxWidth: '1200px', margin: '0 auto', padding: '80px 40px' }}>
        <h1 style={{ textAlign: 'center', fontSize: 'clamp(32px, 5vw, 56px)', fontWeight: '700', marginBottom: '16px' }}>
          What our customers say
        </h1>
        <p style={{ textAlign: 'center', fontSize: '18px', color: 'rgba(255,255,255,0.6)', marginBottom: '60px', maxWidth: '600px', margin: '0 auto 60px' }}>
          Real results from real businesses using SellIA to transform their sales
        </p>

        {/* Social Proof */}
        <div style={{ marginBottom: '80px', maxWidth: '600px', margin: '0 auto 80px' }}>
          <SocialProofSection rating={4.9} reviewCount={156} customers={287} />
        </div>

        {/* Credentials */}
        <div style={{ marginBottom: '80px' }}>
          <h2 style={{ textAlign: 'center', fontSize: '28px', fontWeight: '700', marginBottom: '40px' }}>Recognition & Awards</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', maxWidth: '900px', margin: '0 auto' }}>
            <CredentialsBadge title="Best AI Sales Tool" issuer="SaaS Awards 2026" year={2026} />
            <CredentialsBadge title="Most Innovative Solution" issuer="TechCrunch Disrupt" year={2026} />
            <CredentialsBadge title="Top 10 Revenue Tools" issuer="G2 Reviews" year={2026} />
          </div>
        </div>

        {/* Testimonials */}
        <div style={{ marginBottom: '80px' }}>
          <h2 style={{ textAlign: 'center', fontSize: '28px', fontWeight: '700', marginBottom: '40px' }}>Customer Stories</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
            {testimonials.map((testimonial) => (
              <TestimonialCard key={testimonial.id} testimonial={testimonial} />
            ))}
          </div>
        </div>

        {/* CTA */}
        <div style={{ textAlign: 'center', padding: '60px 40px', background: 'rgba(0,212,255,0.05)', borderRadius: '12px', border: '1px solid rgba(0,212,255,0.2)' }}>
          <h2 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '16px' }}>Ready to transform your sales?</h2>
          <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.7)', marginBottom: '24px' }}>
            Join 287+ companies generating more revenue with AI
          </p>
          <a href="/sellia-landing" style={{ display: 'inline-block', padding: '14px 32px', background: '#00D4FF', color: '#000', borderRadius: '8px', fontWeight: '600', textDecoration: 'none' }}>
            Start Free Trial
          </a>
        </div>

        {/* Phase 4: Semantic Recommendations */}
        <div style={{ marginTop: '80px', paddingTop: '60px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '40px' }}>Discover More</h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '40px', alignItems: 'start' }}>
            <div>
              <RelatedContentSection contentId="testimonials" limit={4} />
            </div>
            <div>
              <PersonalizedRecommendations userContext="converting" currentPage="testimonials" limit={3} />
            </div>
          </div>

          <div style={{ marginTop: '60px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '20px' }}>Sales Automation Hub</h3>
            <ContentCluster topic="sales-automation" />
          </div>
        </div>
      </main>
    </>
  )
}

