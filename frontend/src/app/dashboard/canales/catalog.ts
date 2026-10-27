import {
  Bot, Briefcase, Camera, Gem, GraduationCap, Globe, Link2, Mail, Megaphone, MessageSquare, Music,
  Phone, Search, ShoppingBag, ShoppingCart, Store,
  type LucideIcon,
} from 'lucide-react'
import type { ChannelStatus } from '@/types/channels'

export type CategoryKey = 'messaging' | 'marketplaces' | 'store' | 'ads' | 'social'

export interface PlatformMeta {
  label: string
  icon: LucideIcon
  /** Tinted tile behind the icon; light backgrounds with a darker glyph keep 4.5:1 contrast. */
  tile: string
  description: string
  category: CategoryKey
}

export const CATEGORIES: { key: CategoryKey; label: string; hint: string }[] = [
  { key: 'messaging', label: 'Mensajería', hint: 'Donde te escriben tus clientes' },
  { key: 'marketplaces', label: 'Marketplaces', hint: 'Donde publicás y vendés' },
  { key: 'store', label: 'Tienda propia', hint: 'Tu sitio de ventas' },
  { key: 'ads', label: 'Publicidad', hint: 'Anuncios y catálogos' },
  { key: 'social', label: 'Redes y contenido', hint: 'Presencia y tráfico' },
]

export const PLATFORMS: Record<string, PlatformMeta> = {
  whatsapp: { label: 'WhatsApp', icon: Phone, tile: 'bg-green-50 text-green-700', description: 'WhatsApp Business: conversaciones con clientes', category: 'messaging' },
  email: { label: 'Email', icon: Mail, tile: 'bg-blue-50 text-blue-700', description: 'Tu casilla: envía y lee respuestas (prospección)', category: 'messaging' },
  instagram: { label: 'Instagram', icon: Camera, tile: 'bg-pink-50 text-pink-700', description: 'Mensajes directos de Instagram', category: 'messaging' },
  messenger: { label: 'Messenger', icon: MessageSquare, tile: 'bg-blue-50 text-blue-700', description: 'Facebook Messenger', category: 'messaging' },
  telegram: { label: 'Telegram', icon: MessageSquare, tile: 'bg-cyan-50 text-cyan-700', description: 'Bot de Telegram', category: 'messaging' },
  linkedin: { label: 'LinkedIn', icon: Briefcase, tile: 'bg-sky-50 text-sky-700', description: 'Mensajes de LinkedIn', category: 'messaging' },
  webchat: { label: 'WebChat', icon: MessageSquare, tile: 'bg-slate-100 text-slate-700', description: 'Chat en tu sitio web', category: 'messaging' },
  manychat: { label: 'ManyChat', icon: Bot, tile: 'bg-teal-50 text-teal-700', description: 'Automatizaciones de ManyChat', category: 'messaging' },
  mercadolibre: { label: 'Mercado Libre', icon: ShoppingCart, tile: 'bg-yellow-50 text-yellow-800', description: 'Preguntas y ventas', category: 'marketplaces' },
  amazon: { label: 'Amazon', icon: ShoppingCart, tile: 'bg-orange-50 text-orange-700', description: 'Amazon Seller Central', category: 'marketplaces' },
  etsy: { label: 'Etsy', icon: Gem, tile: 'bg-orange-50 text-orange-700', description: 'Productos artesanales y de diseño', category: 'marketplaces' },
  facebook_marketplace: { label: 'Facebook Marketplace', icon: Store, tile: 'bg-blue-50 text-blue-700', description: 'Ventas en Marketplace', category: 'marketplaces' },
  tiktok_shop: { label: 'TikTok Shop', icon: Music, tile: 'bg-slate-100 text-slate-800', description: 'Catálogo y pedidos de TikTok Shop', category: 'marketplaces' },
  hotmart: { label: 'Hotmart', icon: GraduationCap, tile: 'bg-red-50 text-red-700', description: 'Cursos y productos digitales', category: 'marketplaces' },
  shopify: { label: 'Shopify', icon: ShoppingBag, tile: 'bg-green-50 text-green-700', description: 'Tu tienda Shopify', category: 'store' },
  woocommerce: { label: 'WooCommerce', icon: Store, tile: 'bg-purple-50 text-purple-700', description: 'Tienda en WordPress', category: 'store' },
  facebook_ads: { label: 'Facebook Ads', icon: Megaphone, tile: 'bg-blue-50 text-blue-700', description: 'Campañas de Facebook', category: 'ads' },
  meta_ads: { label: 'Meta Ads', icon: Globe, tile: 'bg-indigo-50 text-indigo-700', description: 'Catálogo y anuncios de Meta', category: 'ads' },
  google_ads: { label: 'Google Ads', icon: Search, tile: 'bg-red-50 text-red-700', description: 'Campañas de Google', category: 'ads' },
  tiktok_ads: { label: 'TikTok Ads', icon: Music, tile: 'bg-slate-100 text-slate-800', description: 'Campañas de TikTok', category: 'ads' },
  tiktok: { label: 'TikTok', icon: Music, tile: 'bg-slate-100 text-slate-800', description: 'Tu cuenta de TikTok', category: 'social' },
  beacons: { label: 'Beacons', icon: Link2, tile: 'bg-purple-50 text-purple-700', description: 'Beacons / Linktree', category: 'social' },
}

export const platformMeta = (platform: string): PlatformMeta =>
  PLATFORMS[platform] ?? {
    label: platform, icon: Link2, tile: 'bg-slate-100 text-slate-700', description: platform, category: 'social',
  }

export const STATUS_STYLE: Record<ChannelStatus, { label: string; pill: string; dot: string }> = {
  connected: { label: 'Conectado', pill: 'bg-emerald-50 text-emerald-800 ring-emerald-200', dot: 'bg-emerald-500' },
  pending: { label: 'Pendiente de verificar', pill: 'bg-amber-50 text-amber-800 ring-amber-200', dot: 'bg-amber-500' },
  error: { label: 'Con error', pill: 'bg-red-50 text-red-800 ring-red-200', dot: 'bg-red-500' },
  disabled: { label: 'Deshabilitado', pill: 'bg-slate-100 text-slate-700 ring-slate-200', dot: 'bg-slate-400' },
}

/** Platforms with their own SellIA app: the user only authorizes, never pastes credentials. */
export const ONE_CLICK_PLATFORMS = ['mercadolibre', 'instagram', 'messenger', 'facebook_ads', 'facebook_marketplace']

export interface FieldDef {
  key: string
  label: string
  type?: 'text' | 'password' | 'number'
  placeholder?: string
  required?: boolean
  help?: string
  advanced?: boolean
}

export interface CredentialForm {
  fields: FieldDef[]
  note?: string
}

const f = (key: string, label: string, extra: Partial<FieldDef> = {}): FieldDef => ({ key, label, ...extra })
const secret = (key: string, label: string, extra: Partial<FieldDef> = {}): FieldDef => f(key, label, { type: 'password', ...extra })

export const CREDENTIAL_FORMS: Record<string, CredentialForm> = {
  whatsapp: {
    fields: [
      secret('api_token', 'API Token', { placeholder: 'EAAB...' }),
      f('phone_number_id', 'Phone Number ID'),
      f('business_account_id', 'Business Account ID'),
    ],
  },
  email: {
    fields: [
      f('smtp_host', 'Servidor de envío (SMTP)', { placeholder: 'smtp.gmail.com', required: true }),
      f('smtp_port', 'Puerto', { type: 'number', placeholder: '587', required: true, help: '587 para casi todos los proveedores (465 si usa SSL).' }),
      f('smtp_user', 'Usuario (tu email)', { placeholder: 'tunombre@gmail.com', required: true }),
      secret('smtp_password', 'Contraseña de aplicación', { required: true, help: 'No es tu contraseña normal. Se guarda cifrada y nunca se muestra de nuevo.' }),
      f('from_address', 'Remitente (opcional)', { placeholder: 'Si lo dejás vacío usamos tu usuario', help: 'La dirección que ve quien recibe el mail.' }),
      f('imap_host', 'Servidor de lectura (IMAP)', { advanced: true, placeholder: 'imap.gmail.com', help: 'Para leer las respuestas. Si lo dejás vacío lo deducimos del servidor de envío.' }),
      f('imap_port', 'Puerto IMAP', { advanced: true, type: 'number', placeholder: '993' }),
      f('imap_user', 'Usuario IMAP', { advanced: true, help: 'Vacío = el mismo usuario de envío.' }),
      secret('imap_password', 'Contraseña IMAP', { advanced: true, help: 'Vacía = la misma contraseña de envío.' }),
    ],
  },
  instagram: {
    fields: [secret('api_token', 'API Token'), f('instagram_account_id', 'Instagram Account ID'), f('page_id', 'Page ID')],
  },
  mercadolibre: { fields: [] },
  telegram: { fields: [secret('bot_token', 'Bot Token', { placeholder: '123456:ABC-DEF...' })] },
  webchat: { fields: [f('site_domain', 'Dominio del sitio', { placeholder: 'tudominio.com' })] },
  hotmart: {
    fields: [
      secret('hottok', 'Hottok', { placeholder: 'Token de verificación del webhook' }),
      f('client_id', 'Client ID'),
      secret('client_secret', 'Client Secret'),
    ],
    note: 'Configurá este mismo Hottok en Hotmart → Herramientas → Webhook.',
  },
  woocommerce: {
    fields: [
      f('site_url', 'URL del sitio', { placeholder: 'https://tutienda.com' }),
      f('consumer_key', 'Consumer Key', { placeholder: 'ck_...' }),
      secret('consumer_secret', 'Consumer Secret', { placeholder: 'cs_...' }),
      secret('webhook_secret', 'Webhook Secret'),
    ],
  },
  etsy: {
    fields: [
      f('shop_id', 'Shop ID'),
      f('api_keystring', 'API Keystring'),
      secret('shared_secret', 'Shared Secret'),
      secret('access_token', 'Access Token'),
    ],
  },
  amazon: {
    fields: [
      f('lwa_app_id', 'LWA App ID'),
      secret('lwa_client_secret', 'LWA Client Secret'),
      secret('refresh_token', 'Refresh Token'),
      f('marketplace_id', 'Marketplace ID'),
      f('seller_id', 'Seller ID (opcional)'),
    ],
    note: 'Necesitás una app en Amazon Selling Partner API (SP-API) aprobada para tu cuenta de vendedor.',
  },
  shopify: {
    fields: [
      f('shop_domain', 'Dominio de la tienda', { placeholder: 'mitienda.myshopify.com' }),
      secret('admin_api_token', 'Admin API access token'),
      f('api_key', 'API Key (opcional)'),
      secret('api_secret', 'API Secret (opcional)'),
      secret('webhook_secret', 'Webhook Secret (opcional)'),
    ],
    note: 'Admin de Shopify → Configuración → Apps y canales de venta → Desarrollar apps.',
  },
  messenger: { fields: [secret('api_token', 'Page Access Token'), f('page_id', 'Page ID')] },
  linkedin: {
    fields: [secret('access_token', 'Access Token'), f('sender_urn', 'URN del remitente')],
    note: 'Requiere una app aprobada en LinkedIn Developers con permisos de mensajería.',
  },
  manychat: { fields: [secret('api_token', 'API Token')] },
  tiktok_shop: {
    fields: [
      f('client_id', 'App Key (Client ID)'),
      secret('client_secret', 'App Secret (Client Secret)'),
      secret('access_token', 'Access Token'),
      f('shop_id', 'Shop ID'),
      f('shop_cipher', 'Shop Cipher (opcional)'),
      secret('refresh_token', 'Refresh Token (opcional)'),
    ],
    note: 'Se generan en TikTok Shop Partner Center al crear tu app.',
  },
  meta_ads: {
    fields: [
      secret('access_token', 'Access Token', { placeholder: 'Token del System User con permiso catalog_management' }),
      f('catalog_id', 'Catalog ID'),
      f('app_id', 'App ID'),
      secret('app_secret', 'App Secret'),
      f('page_id', 'Page ID (opcional)'),
      f('ad_account_id', 'Ad Account ID (opcional)'),
    ],
    note: 'Sacá el Access Token y Catalog ID desde Meta Business Settings → Usuarios del sistema → Commerce Manager.',
  },
  facebook_marketplace: {
    fields: [f('page_id', 'Page ID'), secret('page_access_token', 'Page Access Token'), f('catalog_id', 'Catalog ID')],
  },
}

/** One-tap presets for the email form. */
export const EMAIL_PRESETS: { label: string; smtp_host: string; smtp_port: string; imap_host: string }[] = [
  { label: 'Gmail', smtp_host: 'smtp.gmail.com', smtp_port: '587', imap_host: 'imap.gmail.com' },
  { label: 'Outlook / Microsoft 365', smtp_host: 'smtp.office365.com', smtp_port: '587', imap_host: 'outlook.office365.com' },
  { label: 'Yahoo', smtp_host: 'smtp.mail.yahoo.com', smtp_port: '587', imap_host: 'imap.mail.yahoo.com' },
]
