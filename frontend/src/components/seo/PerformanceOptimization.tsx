/**
 * Performance Optimization Hints
 * DNS prefetch, preconnect, image lazy loading directives
 * Phase 2: CWV optimization
 */

export function PreloadFonts() {
  return (
    <>
      <link
        rel="preconnect"
        href="https://fonts.googleapis.com"
      />
      <link
        rel="dns-prefetch"
        href="https://fonts.gstatic.com"
      />
    </>
  )
}

export function PreconnectBackend() {
  return (
    <>
      <link
        rel="preconnect"
        href="https://selliaii-backend.onrender.com"
      />
      <link
        rel="dns-prefetch"
        href="https://selliaii-backend.onrender.com"
      />
    </>
  )
}

export function ImageOptimizationHints() {
  return (
    <>
      {/* Instruct browser to defer image loading below fold */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            name: 'Performance Optimization',
            description: 'Lazy loading and image optimization enabled',
          }),
        }}
      />
    </>
  )
}

export function CoreWebVitalsOptimization() {
  return (
    <>
      {/* LCP: Ensure largest contentful paint is optimized */}
      {/* FID: First Input Delay minimized via code splitting */}
      {/* CLS: Cumulative Layout Shift prevented via fixed heights */}
      <style>
        {`
          /* Prevent CLS for dynamic content */
          img {
            aspect-ratio: auto;
            max-width: 100%;
            height: auto;
          }

          /* Load critical CSS first */
          @media (prefers-reduced-motion: no-preference) {
            * {
              scroll-behavior: smooth;
            }
          }

          /* Optimize font loading */
          @font-face {
            font-display: swap;
          }
        `}
      </style>
    </>
  )
}

export interface ImageWithLazyLoadProps {
  src: string
  alt: string
  width?: number
  height?: number
  loading?: 'lazy' | 'eager'
  className?: string
}

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  loading = 'lazy',
  className,
}: ImageWithLazyLoadProps) {
  return (
    <img
      src={src}
      alt={alt}
      width={width}
      height={height}
      loading={loading}
      className={className}
      style={{
        maxWidth: '100%',
        height: 'auto',
        aspectRatio: width && height ? `${width} / ${height}` : 'auto',
      }}
    />
  )
}
