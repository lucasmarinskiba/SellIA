/**
 * Supabase client · SellIA Brain
 *
 * Setup:
 *  1. Create a free project at https://supabase.com
 *  2. Run supabase/schema.sql in the SQL Editor
 *  3. Copy Project URL + anon key to .env.local:
 *       NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
 *       NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJh...
 */
import { createClient } from '@supabase/supabase-js'

const url  = process.env.NEXT_PUBLIC_SUPABASE_URL  ?? ''
const key  = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''

export const supabase = (url && key)
  ? createClient(url, key)
  : null

export const isConfigured = (): boolean => Boolean(url && key)
