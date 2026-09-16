import { api } from './api'

export interface ConversionEvent {
  id: string
  link_id: string
  platform_name: string
  conversion_type: string
  conversion_value: number
  created_at: string
}

export interface UrgencyMetric {
  trigger: string
  conversions: number
  avg_ctr: number
}

export interface FOMAPreview {
  link: {
    id: string
    title: string
    url: string
    platform: string
  }
  original: {
    title: string
    description: string
  }
  with_fomo: {
    title: string
    urgency_trigger: string | null
    scarcity_message: string | null
    call_to_action: string
    full_copy: string
    fomo_score: number
  }
}

export const fomaPhase1Api = {
  async trackConversion(
    businessId: string,
    linkId: string,
    platformName: string,
    conversionType: string = 'purchase',
    conversionValue: number = 0,
  ) {
    const res = await api.post(
      `/businesses/${businessId}/seo-config/conversions/track`,
      null,
      {
        params: {
          link_id: linkId,
          platform_name: platformName,
          conversion_type: conversionType,
          conversion_value: conversionValue,
        },
      },
    )
    return res.data
  },

  async getRecentConversions(
    businessId: string,
    limit: number = 10,
    hoursBack: number = 24,
  ): Promise<ConversionEvent[]> {
    const res = await api.get(
      `/businesses/${businessId}/seo-config/conversions/recent`,
      {
        params: { limit, hours_back: hoursBack },
      },
    )
    return res.data
  },

  async getUrgencyMetrics(businessId: string) {
    const res = await api.get(
      `/businesses/${businessId}/seo-config/analytics/urgency-metrics`,
    )
    return res.data as { triggers: UrgencyMetric[] }
  },

  async getFOMAPreview(businessId: string, linkId: string): Promise<FOMAPreview> {
    const res = await api.get(
      `/businesses/${businessId}/seo-config/publication-links/${linkId}/preview`,
    )
    return res.data
  },
}
