'use client';

import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

/**
 * Optimistic update hook for better UX.
 *
 * Updates UI immediately while request is in flight.
 * Rolls back if request fails.
 *
 * Usage:
 * ```
 * const { optimisticUpdate, isPending } = useOptimisticUpdate();
 *
 * const handleApprove = async (dealId) => {
 *   await optimisticUpdate({
 *     key: ['deal', dealId],
 *     update: (old) => ({ ...old, status: 'approved' }),
 *     request: () => api.post(`/deals/${dealId}/approve`),
 *   });
 * };
 * ```
 */
export const useOptimisticUpdate = () => {
  const queryClient = useQueryClient();
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const optimisticUpdate = useCallback(
    async <T,>({
      key,
      update,
      request,
      onSuccess,
      onError,
    }: {
      key: string[];
      update: (oldData: T) => T;
      request: () => Promise<T>;
      onSuccess?: (data: T) => void;
      onError?: (error: Error) => void;
    }) => {
      setIsPending(true);
      setError(null);

      // Get current data
      const oldData = queryClient.getQueryData<T>(key);

      try {
        // Optimistic update (immediate UI update)
        if (oldData) {
          const optimisticData = update(oldData);
          queryClient.setQueryData(key, optimisticData);
        }

        // Execute actual request
        const newData = await request();

        // Update with real data
        queryClient.setQueryData(key, newData);
        onSuccess?.(newData);
      } catch (err) {
        // Rollback on failure
        if (oldData) {
          queryClient.setQueryData(key, oldData);
        }

        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        onError?.(error);

        throw error;
      } finally {
        setIsPending(false);
      }
    },
    [queryClient]
  );

  return { optimisticUpdate, isPending, error };
};
