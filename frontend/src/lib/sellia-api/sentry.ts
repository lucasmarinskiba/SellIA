/**
 * Sentry init for frontend · lazy-loaded · runs on app startup.
 * Wire in app/layout.tsx or in QueryProvider.
 */
let initialized = false

export async function initSentryClient(): Promise<void> {
  if (initialized || typeof window === 'undefined') return

  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN
  if (!dsn) return

  try {
    // @ts-expect-error · optional dep · only loaded if installed by user
    const Sentry = await import('@sentry/nextjs').catch(() => null) as any
    if (!Sentry) return

    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV,
      tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
      replaysSessionSampleRate: 0.01,
      replaysOnErrorSampleRate: 1.0,
      integrations: [Sentry.replayIntegration()],
      sendDefaultPii: false,
    })

    initialized = true
  } catch {
    // swallow · sentry missing or runtime error
  }
}
