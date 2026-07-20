/**
 * TanStack Query hooks · type-safe wrappers around API client.
 */
import { useMutation, useQuery, useQueryClient, type UseQueryOptions } from '@tanstack/react-query'

import { authApi, billingApi, dealsApi, type Deal, type MeResponse, setToken } from './client'

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const useMe = (options?: Partial<UseQueryOptions<MeResponse>>) =>
  useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    retry: false,
    staleTime: 5 * 60_000,
    ...options,
  })

export const useLogin = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setToken(data.access_token)
      qc.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export const useSignup = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: authApi.signup,
    onSuccess: (data) => {
      setToken(data.access_token)
      qc.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export const useLogout = () => {
  const qc = useQueryClient()
  return () => {
    setToken(null)
    qc.clear()
    if (typeof window !== 'undefined') window.location.href = '/login'
  }
}

// ─── Deals ────────────────────────────────────────────────────────────────────

export const useDeals = () =>
  useQuery({ queryKey: ['deals'], queryFn: dealsApi.list, staleTime: 30_000 })

export const useCreateDeal = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: dealsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  })
}

export const useUpdateDeal = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...patch }: { id: string } & Partial<Deal>) => dealsApi.update(id, patch),
    onMutate: async ({ id, ...patch }) => {
      // Optimistic update
      await qc.cancelQueries({ queryKey: ['deals'] })
      const prev = qc.getQueryData<Deal[]>(['deals'])
      if (prev) {
        qc.setQueryData<Deal[]>(['deals'], prev.map((d) => (d.id === id ? { ...d, ...patch } : d)))
      }
      return { prev }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(['deals'], ctx.prev)
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  })
}

export const useDeleteDeal = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: dealsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['deals'] }),
  })
}

// ─── Billing ──────────────────────────────────────────────────────────────────

export const useCheckout = () =>
  useMutation({
    mutationFn: ({ plan, successUrl, cancelUrl }: { plan: 'starter' | 'pro' | 'scale'; successUrl: string; cancelUrl: string }) =>
      billingApi.checkout(plan, successUrl, cancelUrl),
    onSuccess: (data) => {
      window.location.href = data.checkout_url
    },
  })
