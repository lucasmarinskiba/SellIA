'use client'

/**
 * Root provider · wraps app in QueryClientProvider with sensible defaults.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState, type ReactNode } from 'react'

export default function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            retry: (failureCount, error: any) => {
              // No retry on 4xx (auth/validation)
              const status = error?.response?.status
              if (status && status >= 400 && status < 500) return false
              return failureCount < 2
            },
            refetchOnWindowFocus: false,
          },
          mutations: { retry: 0 },
        },
      })
  )

  return (
    <QueryClientProvider client={client}>
      {children}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  )
}
