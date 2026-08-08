/**
 * Performance optimization hints for Core Web Vitals.
 * - dns-prefetch: DNS lookup optimization
 * - preconnect: Establish connection to third-party origins
 * - preload: Load critical resources early
 */

export function PerformanceHints() {
  return (
    <>
      {/* DNS prefetch for common third-party services */}
      <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      <link rel="dns-prefetch" href="https://fonts.gstatic.com" />

      {/* Preconnect to critical origins */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />

      {/* Preload critical fonts (if any) */}
      {/* Note: Adjust based on actual fonts used in sellia-brain */}
    </>
  )
}
