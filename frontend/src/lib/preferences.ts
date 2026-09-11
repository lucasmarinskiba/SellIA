/**
 * Seller configuration.
 *
 * Mirrors backend/app/domains/preferences/. The fields live in three different
 * tables on the server (business context, user memory, seller preferences) and
 * are presented here as one profile, which is exactly how the seller thinks
 * about them.
 */

import { api } from './api'

export interface Option {
  value: string
  label: string
  detail?: string
}

export interface PlatformOption {
  value: string
  label: string
  kind: string
  note: string
  markets: string[]
  suits: string[]
  /** What the connector really implements — read off the code, not declared. */
  capabilities: string[]
}

export interface PreferencesCatalog {
  languages: { code: string; label: string }[]
  markets: { code: string; label: string }[]
  platforms: PlatformOption[]
  tones: Option[]
  goals: Option[]
  price_ranges: Option[]
  business_types: Option[]
  sales_models: Option[]
}

export interface Completeness {
  filled: number
  total: number
  percent: number
  missing: { field: string; label: string }[]
}

export interface SellerProfile {
  business_type: string | null
  sales_model: string | null
  niche: string | null
  target_audience: string | null
  value_proposition: string | null
  price_range: string | null
  primary_goal: string | null
  country: string | null
  city: string | null
  primary_language: string
  tone: string
  interests: string[]
  challenges: string[]
  target_platforms: string[]
  languages: string[]
  markets: string[]
  tastes: string[]
  banned_topics: string[]
  display_currency: string | null
  voice_notes: string | null
  autonomous_replies: boolean
  completeness: Completeness
  /**
   * Which parts of the profile could not be read at all (a table down, say).
   * Empty normally. A field blank because nothing was saved and a field blank
   * because its source failed look identical without this.
   */
  unavailable?: string[]
}

export interface PreferencesResponse {
  business_id: string | null
  has_business: boolean
  profile: SellerProfile
  catalog: PreferencesCatalog
}

export interface PlatformSuggestion {
  platform: string
  label: string
  kind: string
  note: string
  /** Why this platform is on the list. No score: nothing was measured. */
  reasons: string[]
  capabilities: string[]
  can_import_orders: boolean
  can_answer_messages: boolean
}

export interface SuggestionsResponse {
  connected: string[]
  suggestions: PlatformSuggestion[]
  /** What could not be evaluated, and why. */
  unknowns: string[]
}

export const preferencesApi = {
  get: (businessId?: string): Promise<PreferencesResponse> =>
    api.get<PreferencesResponse>('/preferences', {
      params: businessId ? { business_id: businessId } : {},
    }).then(r => r.data),

  update: (patch: Partial<SellerProfile>, businessId?: string): Promise<{ profile: SellerProfile }> =>
    api.put<{ profile: SellerProfile }>('/preferences', patch, {
      params: businessId ? { business_id: businessId } : {},
    }).then(r => r.data),

  suggestions: (businessId?: string): Promise<SuggestionsResponse> =>
    api.get<SuggestionsResponse>('/preferences/platform-suggestions', {
      params: businessId ? { business_id: businessId } : {},
    }).then(r => r.data),
}
