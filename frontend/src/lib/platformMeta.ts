/**
 * Shared display metadata for ChannelPlatform values (real backend enum:
 * backend/app/domains/channels/models.py). Used anywhere a conversation,
 * message, or channel needs a human label + color badge -- keeps every
 * platform badge in the app consistent instead of each component inventing
 * its own label strings.
 */
export interface PlatformMeta {
  label: string
  color: string
}

export const PLATFORM_META: Record<string, PlatformMeta> = {
  whatsapp: { label: 'WhatsApp', color: '#25D366' },
  instagram: { label: 'Instagram', color: '#E1306C' },
  email: { label: 'Email', color: '#64748B' },
  mercadolibre: { label: 'MercadoLibre', color: '#FFE600' },
  amazon: { label: 'Amazon', color: '#FF9900' },
  beacons: { label: 'Beacons', color: '#8B5CF6' },
  linkedin: { label: 'LinkedIn', color: '#0A66C2' },
  telegram: { label: 'Telegram', color: '#26A5E4' },
  webchat: { label: 'Web', color: '#38BDF8' },
  messenger: { label: 'Messenger', color: '#00B2FF' },
  facebook_ads: { label: 'Facebook Ads', color: '#1877F2' },
  meta_ads: { label: 'Meta Ads', color: '#1877F2' },
  google_ads: { label: 'Google Ads', color: '#4285F4' },
  shopify: { label: 'Shopify', color: '#95BF47' },
  tiktok: { label: 'TikTok', color: '#EE1D52' },
  tiktok_ads: { label: 'TikTok Ads', color: '#EE1D52' },
  tiktok_shop: { label: 'TikTok Shop', color: '#EE1D52' },
  twitter: { label: 'Twitter/X', color: '#1DA1F2' },
  threads: { label: 'Threads', color: '#000000' },
  hotmart: { label: 'Hotmart', color: '#F04E23' },
}

export const platformMeta = (platform: string | null | undefined): PlatformMeta => {
  if (!platform) return { label: 'Sin canal', color: '#64748B' }
  return PLATFORM_META[platform] || { label: platform, color: '#64748B' }
}
