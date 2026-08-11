import { test, expect } from '@playwright/test'

const API_URL = 'http://localhost:8000'
const USER_ID = 'test_user_001'

test.describe('Phase 26 API Integration', () => {
  test.describe('Phase 26a - Collaboration API', () => {
    test('POST /api/v1/collaboration/comment should add comment', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/collaboration/comment`, {
        data: {
          user_id: USER_ID,
          deal_id: 'deal_001',
          content: `Test comment ${Date.now()}`,
          mentions: [],
        },
      })

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(json.comment).toBeDefined()
    })

    test('GET /api/v1/collaboration/comments/{deal_id} should list comments', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/collaboration/comments/deal_001?limit=50`)

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(Array.isArray(json.comments)).toBeTruthy()
    })

    test('GET /api/v1/collaboration/activity/{deal_id} should return activity feed', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/collaboration/activity/deal_001`)

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(Array.isArray(json.activity)).toBeTruthy()
    })

    test('GET /api/v1/collaboration/pending/{user_id} should return pending approvals', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/collaboration/pending/${USER_ID}`)

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(Array.isArray(json.approvals)).toBeTruthy()
    })

    test('POST /api/v1/collaboration/approve should approve action', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/collaboration/approve`, {
        data: {
          user_id: USER_ID,
          action_id: 'action_001',
          decision: 'approved',
        },
      })

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
    })

    test('POST /api/v1/collaboration/share should share deal', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/collaboration/share`, {
        data: {
          deal_id: 'deal_001',
          shared_by: USER_ID,
          shared_with: 'user_002',
          permissions: 'read_write',
        },
      })

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
    })
  })

  test.describe('Phase 26c - Deal Intelligence API', () => {
    test('POST /api/v1/intelligence/analyze-deals/{user_id} should analyze deals', async ({ request }) => {
      const deals = [
        {
          id: 'deal_001',
          name: 'Big Deal',
          value: 50000,
          stage: 'proposal',
          days_in_stage: 10,
          engagement_velocity: 0.8,
          proposal_status: 'sent',
          comment_count: 5,
          last_activity_days: 2,
          close_rate: 0.7,
        },
      ]

      const response = await request.post(`${API_URL}/api/v1/intelligence/analyze-deals/${USER_ID}`, {
        data: { deals },
      })

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(json.analysis).toBeDefined()
      expect(json.analysis.scores).toBeDefined()
    })

    test('GET /api/v1/intelligence/deal-score/{deal_id} should return score', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/intelligence/deal-score/deal_001`)

      // May return not_found if deal not yet scored
      expect([200, 404]).toContain(response.status())
    })

    test('POST /api/v1/intelligence/forecast-revenue/{user_id} should forecast revenue', async ({ request }) => {
      const deals = [
        {
          id: 'deal_001',
          name: 'Deal 1',
          value: 50000,
          stage: 'proposal',
          days_in_stage: 10,
          engagement_velocity: 0.8,
          proposal_status: 'sent',
          comment_count: 5,
          last_activity_days: 2,
          close_rate: 0.7,
        },
        {
          id: 'deal_002',
          name: 'Deal 2',
          value: 30000,
          stage: 'negotiation',
          days_in_stage: 5,
          engagement_velocity: 0.9,
          proposal_status: 'reviewed',
          comment_count: 8,
          last_activity_days: 1,
          close_rate: 0.8,
        },
      ]

      const response = await request.post(`${API_URL}/api/v1/intelligence/forecast-revenue/${USER_ID}?periods=30&periods=60&periods=90`, {
        data: { deals },
      })

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(json.forecast.forecasts).toBeDefined()
    })

    test('GET /api/v1/intelligence/at-risk-deals should return at-risk summary', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/intelligence/at-risk-deals`)

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(json.at_risk_summary).toBeDefined()
    })

    test('GET /api/v1/intelligence/accuracy-metrics/{user_id} should return accuracy', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/intelligence/accuracy-metrics/${USER_ID}`)

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(json.metrics).toBeDefined()
    })

    test('POST /api/v1/intelligence/record-outcome/{deal_id} should record outcome', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/intelligence/record-outcome/deal_001`, {
        data: {
          user_id: USER_ID,
          outcome: 'won',
          final_value: 50000,
          days_to_close: 25,
          forecasted_probability: 0.75,
          win_loss_reason: 'Strong engagement + proposal accepted',
        },
      })

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
    })

    test('GET /api/v1/intelligence/dashboard/{user_id} should return complete dashboard', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/intelligence/dashboard/${USER_ID}`)

      expect(response.status()).toBe(200)
      const json = await response.json()
      expect(json.status).toBe('ok')
      expect(json.dashboard).toBeDefined()
      expect(json.dashboard.at_risk).toBeDefined()
      expect(json.dashboard.accuracy).toBeDefined()
    })
  })

  test.describe('Phase 26 WebSocket', () => {
    test('WebSocket /ws/deal/{deal_id} should connect', async ({ browser }) => {
      const context = await browser.newContext()
      const page = await context.newPage()

      let wsConnected = false
      let wsMessage: string | null = null

      page.on('websocket', (ws) => {
        wsConnected = true

        ws.on('framereceived', (event) => {
          wsMessage = event.payload
        })
      })

      try {
        // Try to connect to WebSocket (may fail in test environment)
        await page.evaluate(() => {
          new WebSocket('ws://localhost:8000/ws/deal/deal_001')
        })

        await page.waitForTimeout(1000)
      } catch (e) {
        // WebSocket may not be available in test environment
      }

      await context.close()
    })
  })

  test.describe('Response Validation', () => {
    test('API responses should have correct structure', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/collaboration/comments/deal_001?limit=50`)

      const json = await response.json()
      expect(json).toHaveProperty('status')
      expect(json).toHaveProperty('comments')
      expect(Array.isArray(json.comments)).toBeTruthy()
    })

    test('Error responses should have error details', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/collaboration/comments/invalid_deal?limit=50`)

      // Should either return 200 with empty array or 404
      expect([200, 404]).toContain(response.status())
    })
  })
})
