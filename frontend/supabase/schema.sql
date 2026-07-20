-- ═══════════════════════════════════════════════
-- SellIA Brain · Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor
-- ═══════════════════════════════════════════════

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── User keys (no auth required - keyed by localStorage UUID) ────────────────
CREATE TABLE IF NOT EXISTS public.brain_users (
  user_key   TEXT PRIMARY KEY,               -- UUID from localStorage
  biz_name   TEXT,
  biz_type   TEXT,
  volume     TEXT,
  channels   TEXT[],
  goals      TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Metrics (one row per metric per user) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.brain_metrics (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_key   TEXT REFERENCES public.brain_users(user_key) ON DELETE CASCADE,
  key        TEXT NOT NULL,       -- e.g. 'win_rate', 'mrr_growth', 'lead_velocity'
  value      NUMERIC  NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_key, key)
);

-- ─── Activity events (log terminal) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.brain_events (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_key   TEXT REFERENCES public.brain_users(user_key) ON DELETE CASCADE,
  tag        TEXT NOT NULL,       -- 'CLOSE', 'CUA', 'RCVR', 'OK', 'WARN'
  color      TEXT NOT NULL,       -- hex color for the tag
  message    TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS brain_events_user_ts ON public.brain_events (user_key, created_at DESC);

-- ─── Agents ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.brain_agents (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_key   TEXT REFERENCES public.brain_users(user_key) ON DELETE CASCADE,
  code       TEXT NOT NULL,       -- 'HRMZ', 'BELF', etc.
  name       TEXT NOT NULL,
  busy_pct   INTEGER NOT NULL DEFAULT 0,
  color      TEXT NOT NULL DEFAULT '#22d3ee',
  status     TEXT NOT NULL DEFAULT 'active',
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_key, code)
);

-- ─── Pipeline (ADQ / CON / RET counts) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.brain_pipeline (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_key   TEXT REFERENCES public.brain_users(user_key) ON DELETE CASCADE,
  lobe       TEXT NOT NULL,       -- 'acquire', 'convert', 'retain'
  count      INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_key, lobe)
);

-- ─── Automatizaciones (automation jobs) ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.brain_automations (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_key   TEXT REFERENCES public.brain_users(user_key) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'running',  -- 'running', 'paused', 'completed'
  progress   INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Row Level Security (open for now, user_key acts as password) ─────────────
ALTER TABLE public.brain_users       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brain_metrics     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brain_events      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brain_agents      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brain_pipeline    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brain_automations ENABLE ROW LEVEL SECURITY;

-- Policies: allow anon to read/write their own rows via user_key header
CREATE POLICY "own_rows" ON public.brain_users       FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "own_rows" ON public.brain_metrics     FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "own_rows" ON public.brain_events      FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "own_rows" ON public.brain_agents      FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "own_rows" ON public.brain_pipeline    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "own_rows" ON public.brain_automations FOR ALL USING (true) WITH CHECK (true);
