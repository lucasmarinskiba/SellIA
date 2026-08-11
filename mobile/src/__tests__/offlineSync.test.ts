import { offlineSync } from '@/services/offlineSync'

describe('OfflineSync', () => {
  beforeEach(async () => {
    await offlineSync.init()
  })

  describe('Queue Actions', () => {
    it('should queue a create action', async () => {
      await offlineSync.queueAction('create', 'comment', 'deal_001', {
        content: 'Test comment',
        mentions: [],
      })

      // Verify action was queued by attempting to cache
      const cached = await offlineSync.getCachedData('comment', 'deal_001')
      expect(cached).toBeDefined()
    })

    it('should queue an update action', async () => {
      await offlineSync.queueAction('update', 'deal_stage', 'deal_001', {
        stage: 'proposal',
      })

      const cached = await offlineSync.getCachedData('deal_stage', 'deal_001')
      expect(cached).toMatchObject({ stage: 'proposal' })
    })

    it('should handle multiple queued actions', async () => {
      await offlineSync.queueAction('create', 'comment', 'deal_001', {
        content: 'Comment 1',
      })
      await offlineSync.queueAction('create', 'comment', 'deal_002', {
        content: 'Comment 2',
      })
      await offlineSync.queueAction('update', 'deal_stage', 'deal_001', {
        stage: 'negotiation',
      })

      const cached1 = await offlineSync.getCachedData('comment', 'deal_001')
      const cached2 = await offlineSync.getCachedData('comment', 'deal_002')
      const cached3 = await offlineSync.getCachedData('deal_stage', 'deal_001')

      expect(cached1).toBeDefined()
      expect(cached2).toBeDefined()
      expect(cached3).toMatchObject({ stage: 'negotiation' })
    })
  })

  describe('Caching', () => {
    it('should cache data with expiration', async () => {
      await offlineSync.cacheData(
        'deals',
        'user_001',
        { deals: [{ id: 'deal_1', name: 'Test Deal' }] },
        3600000
      )

      const cached = await offlineSync.getCachedData('deals', 'user_001')
      expect(cached).toMatchObject({
        deals: [{ id: 'deal_1', name: 'Test Deal' }],
      })
    })

    it('should return null for non-existent cache', async () => {
      const cached = await offlineSync.getCachedData('deals', 'user_999')
      expect(cached).toBeNull()
    })

    it('should handle cache data types', async () => {
      const testData = {
        string: 'value',
        number: 42,
        boolean: true,
        array: [1, 2, 3],
        nested: { key: 'value' },
      }

      await offlineSync.cacheData('test', 'entity_1', testData)
      const cached = await offlineSync.getCachedData('test', 'entity_1')

      expect(cached).toEqual(testData)
    })
  })

  describe('Sync Queue', () => {
    it('should return sync stats', async () => {
      const result = await offlineSync.syncQueue()

      expect(result).toHaveProperty('success')
      expect(result).toHaveProperty('failed')
      expect(typeof result.success).toBe('number')
      expect(typeof result.failed).toBe('number')
    })

    it('should handle empty sync queue', async () => {
      const result = await offlineSync.syncQueue()

      expect(result.success).toBeGreaterThanOrEqual(0)
      expect(result.failed).toBeGreaterThanOrEqual(0)
    })
  })

  describe('Expiration', () => {
    it('should clear expired cache entries', async () => {
      await offlineSync.cacheData('expires', 'entity_1', { data: 'value' }, 100) // 100ms

      // Wait for expiration
      await new Promise((resolve) => setTimeout(resolve, 150))

      await offlineSync.clearExpired()
      const cached = await offlineSync.getCachedData('expires', 'entity_1')

      expect(cached).toBeNull()
    })
  })
})
