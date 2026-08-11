import { create } from 'zustand'
import { apiClient } from '@/services/apiClient'
import { offlineSync } from '@/services/offlineSync'

interface Deal {
  id: string
  name: string
  value: number
  stage: string
  customer: string
  probability: number
  days_in_stage: number
  last_activity: string
}

interface PipelineState {
  deals: Deal[]
  isLoading: boolean
  error: string | null
  fetchDeals: (userId: string) => Promise<void>
  updateDealStage: (dealId: string, stage: string) => Promise<void>
  refreshDeals: (userId: string) => Promise<void>
}

export const usePipelineStore = create<PipelineState>((set, get) => ({
  deals: [],
  isLoading: false,
  error: null,

  fetchDeals: async (userId: string) => {
    set({ isLoading: true, error: null })
    try {
      // Try cache first
      const cached = await offlineSync.getCachedData('deals', userId)
      if (cached) {
        set({ deals: cached as Deal[], isLoading: false })
      }

      // Fetch fresh data
      const response = await apiClient.getDeals(userId, 100)
      const deals = response.data.deals || []

      // Cache for offline
      await offlineSync.cacheData('deals', userId, { deals }, 3600000) // 1 hour

      set({ deals, isLoading: false })
    } catch (error) {
      console.error('Fetch deals error:', error)
      set({
        error: 'Failed to load deals',
        isLoading: false,
      })
    }
  },

  updateDealStage: async (dealId: string, stage: string) => {
    const prevDeals = get().deals
    try {
      // Optimistic update
      set({
        deals: prevDeals.map((d) => (d.id === dealId ? { ...d, stage } : d)),
      })

      // Queue for sync
      await offlineSync.queueAction('update', 'deal_stage', dealId, { stage })

      // Try immediate sync
      await apiClient.updateDealStage(dealId, stage)
    } catch (error) {
      // Revert on failure
      set({ deals: prevDeals })
      console.error('Update deal stage error:', error)
    }
  },

  refreshDeals: async (userId: string) => {
    await get().fetchDeals(userId)
  },
}))

export const usePipeline = () => usePipelineStore()
