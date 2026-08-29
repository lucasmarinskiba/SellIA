'use client';

import React, { ReactNode } from 'react';

declare global {
  interface Window {
    // Optional: only present when the Sentry browser SDK has loaded itself
    // onto window. Guarded with `typeof window !== 'undefined' && window.__SENTRY__`
    // below, so this stays untyped/optional rather than pulling in @sentry/browser.
    __SENTRY__?: { captureException: (error: Error, context?: unknown) => void };
  }
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary component for graceful error handling.
 *
 * Catches unhandled errors + displays fallback UI.
 * Prevents entire app from crashing on component errors.
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught:', error, errorInfo);
    // Send to Sentry
    if (typeof window !== 'undefined' && window.__SENTRY__) {
      window.__SENTRY__.captureException(error, { extra: errorInfo });
    }
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        this.props.fallback?.(this.state.error) || (
          <div className="p-6 bg-red-50 border border-red-200 rounded">
            <h2 className="text-lg font-semibold text-red-900">Something went wrong</h2>
            <p className="mt-2 text-sm text-red-700">{this.state.error.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Try again
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

