/**
 * Real-time FOMO webhook client.
 * Connects to SSE stream for live conversion updates.
 */

interface FOMOWebhookEvent {
  type: string
  data: {
    id: string
    platform: string
    amount?: number
    email?: string
    timestamp: string
  }
  timestamp: string
}

interface WebhookOptions {
  onConversion?: (data: FOMOWebhookEvent) => void
  onError?: (error: Error) => void
  onClose?: () => void
}

export class FOMAWebhookClient {
  private eventSource: EventSource | null = null
  private businessId: string
  private baseUrl: string
  private options: WebhookOptions

  constructor(businessId: string, baseUrl = '/api', options: WebhookOptions = {}) {
    this.businessId = businessId
    this.baseUrl = baseUrl
    this.options = options
  }

  connect(): void {
    const url = `${this.baseUrl}/businesses/${this.businessId}/seo-config/webhooks/events/stream`

    this.eventSource = new EventSource(url)

    this.eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data: FOMOWebhookEvent = JSON.parse(event.data)
        if (data.type === 'conversion' && this.options.onConversion) {
          this.options.onConversion(data)
        }
      } catch (error) {
        this.options.onError?.(new Error(`Failed to parse webhook: ${event.data}`))
      }
    }

    this.eventSource.onerror = () => {
      this.options.onError?.(new Error('Webhook stream connection failed'))
      this.disconnect()
    }
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
      this.options.onClose?.()
    }
  }

  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN
  }
}

export const fomaWebhookClient = {
  /**
   * Create a webhook client instance.
   */
  create(businessId: string, options?: WebhookOptions): FOMAWebhookClient {
    return new FOMAWebhookClient(businessId, '/api', options)
  },

  /**
   * Send conversion event to backend (for testing/manual tracking).
   */
  async sendConversion(businessId: string, payload: {
    platform: string
    link_id?: string
    amount?: number
    email?: string
  }): Promise<{ received: boolean; message: string; event_id: string }> {
    const res = await fetch(`/api/businesses/${businessId}/seo-config/webhooks/conversion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        timestamp: new Date().toISOString(),
      }),
    })
    if (!res.ok) throw new Error(`Webhook failed: ${res.statusText}`)
    return res.json()
  },
}
