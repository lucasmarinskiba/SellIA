'use client'

/**
 * SKILLS LIBRARY
 *
 * Catálogo de capacidades del cerebro SellIA. Cada skill = módulo de conocimiento
 * que la IA usa sola. Agrupados en 8 categorías: Ventas, Marketing, Finanzas,
 * Datos, Branding, Tech-stack, Soft skills, Operaciones.
 *
 * Cada skill muestra: knowledge source (de qué experto/metodología viene),
 * estado (activo/learning/locked), nivel de dominio, uso esta semana.
 */

import { useState, useMemo } from 'react'
import {
  BookOpen, Brain, DollarSign, Megaphone, BarChart3, Award,
  Cpu, Heart, Wrench, Search, Sparkles, Lock, Activity, ChevronRight,
  TrendingUp, Filter, Zap, Bot, CreditCard, ShoppingBag, ShieldCheck, Tag
} from 'lucide-react'

type SkillCategory = 'sales' | 'marketing' | 'finance' | 'data' | 'branding' | 'tech' | 'softskill' | 'ops' | 'platforms' | 'payments' | 'compliance' | 'pricing'
type SkillStatus = 'mastered' | 'active' | 'learning' | 'locked'

interface Skill {
  id: string
  emoji: string
  name: string
  category: SkillCategory
  source: string
  mastery: number // 0-100
  status: SkillStatus
  usedThisWeek: number
  description: string
}

const SKILLS: Skill[] = [
  // VENTAS
  { id: 'sk1',  emoji: '🎯', name: 'Cierre moderno multi-canal',         category: 'sales', source: 'Cierre Multi-canal Framework', mastery: 92, status: 'mastered', usedThisWeek: 47, description: 'Cierra deals via WhatsApp, IG, email, call' },
  { id: 'sk2',  emoji: '🔍', name: 'Cualificación BANT + MEDDIC',         category: 'sales', source: 'Harvard · CEB',              mastery: 88, status: 'mastered', usedThisWeek: 142, description: 'Filtra leads · prioriza budget/authority/need/time' },
  { id: 'sk3',  emoji: '📞', name: 'Llamadas/videollamadas en frío',      category: 'sales', source: 'Aaron Ross · Predictable Revenue', mastery: 75, status: 'active',   usedThisWeek: 23, description: 'Outbound cold calling · 7-step framework' },
  { id: 'sk4',  emoji: '🧠', name: 'Dominio absoluto del producto',        category: 'sales', source: 'Demo mastery framework',     mastery: 95, status: 'mastered', usedThisWeek: 89, description: 'Conoce cada feature, edge case, FAQ del catálogo' },
  { id: 'sk5',  emoji: '📊', name: 'Pipeline + CRM rigor',                 category: 'sales', source: 'Salesforce best practices',  mastery: 90, status: 'mastered', usedThisWeek: 234, description: 'Mueve deals, actualiza, audita stages' },
  { id: 'sk6',  emoji: '🤝', name: 'Seguimiento implacable',               category: 'sales', source: 'Metodología 10X · Follow-up', mastery: 87, status: 'mastered', usedThisWeek: 178, description: 'Follow-up 12+ toques sin desistir' },
  { id: 'sk7',  emoji: '🏢', name: 'B2B Enterprise · multi-stakeholder',   category: 'sales', source: 'Challenger Sale · MEDDIC',   mastery: 78, status: 'active',   usedThisWeek: 14, description: 'Mapea Champions, Economic Buyer, Influencers' },
  { id: 'sk8',  emoji: '🛍', name: 'B2C · psicología del consumidor',     category: 'sales', source: 'Cialdini · Influence',       mastery: 91, status: 'mastered', usedThisWeek: 312, description: 'Reciprocity, scarcity, authority, social proof' },
  { id: 'sk9',  emoji: '🎤', name: 'Reuniones presenciales',               category: 'sales', source: 'Sandler Selling System',     mastery: 70, status: 'active',   usedThisWeek: 6, description: 'Body language, pacing, anchor moments' },

  // MARKETING
  { id: 'sk10', emoji: '📱', name: 'Manejo TikTok orgánico',               category: 'marketing', source: 'Top creators · trends data', mastery: 88, status: 'mastered', usedThisWeek: 28, description: 'Hooks 3-sec, trending audio, viral patterns' },
  { id: 'sk11', emoji: '📷', name: 'Estrategia Instagram',                 category: 'marketing', source: 'Day Trading Attention · Social First', mastery: 91, status: 'mastered', usedThisWeek: 47, description: 'Reels, carrousels, stories, DMs funnel' },
  { id: 'sk12', emoji: '💼', name: 'LinkedIn B2B outreach',                category: 'marketing', source: 'Justin Welsh · Daniel Disney', mastery: 84, status: 'mastered', usedThisWeek: 19, description: 'Connection requests, content, lead gen' },
  { id: 'sk13', emoji: '🟡', name: 'Operar Mercado Libre',                 category: 'marketing', source: 'ML best sellers · A9-like algo', mastery: 86, status: 'mastered', usedThisWeek: 67, description: 'Mejorar reputación, ranking, ventas flash' },
  { id: 'sk14', emoji: '📦', name: 'Operar Amazon Seller',                 category: 'marketing', source: 'Amazon A9 SEO + Helium10',    mastery: 79, status: 'active',   usedThisWeek: 14, description: 'Keywords, A+ content, sponsored, reviews' },
  { id: 'sk15', emoji: '🔥', name: 'Hotmart Affiliate System',             category: 'marketing', source: 'Russell Brunson · ClickFunnels', mastery: 73, status: 'active',   usedThisWeek: 5, description: 'Split, ladder, recurring digital' },
  { id: 'sk16', emoji: '🎨', name: 'Diseño gráfico (Canva/Figma)',         category: 'marketing', source: 'Refokus · Awwwards top sites', mastery: 82, status: 'active',   usedThisWeek: 34, description: 'Genera banners, ads, posts diarios' },
  { id: 'sk17', emoji: '📣', name: 'Community management',                  category: 'marketing', source: 'CMX · Hootsuite playbooks',   mastery: 85, status: 'mastered', usedThisWeek: 89, description: 'Responde, modera, engagement orgánico' },
  { id: 'sk18', emoji: '🔍', name: 'SEO técnico + content',                category: 'marketing', source: 'Brian Dean · Ahrefs methodology', mastery: 80, status: 'active',   usedThisWeek: 12, description: 'Keywords, on-page, backlinks, content gap' },
  { id: 'sk19', emoji: '💰', name: 'SEM · Meta/Google/TikTok Ads',         category: 'marketing', source: 'Common Thread Collective',     mastery: 87, status: 'mastered', usedThisWeek: 56, description: 'Campaigns, creatives, budget, ROAS opt' },
  { id: 'sk20', emoji: '🎬', name: 'Content creation multi-formato',       category: 'marketing', source: 'MrBeast · attention principles', mastery: 84, status: 'mastered', usedThisWeek: 23, description: 'Video, post, reel, audio, threads' },
  { id: 'sk21', emoji: '📊', name: 'Agencia digital · workflow',           category: 'marketing', source: 'Wpromote · iProspect playbooks', mastery: 76, status: 'active',   usedThisWeek: 8, description: 'Full-stack: creative, media buying, reporting' },

  // FINANZAS
  { id: 'sk22', emoji: '🧾', name: 'Contaduría · facturación AFIP',        category: 'finance', source: 'AFIP normativa · CPCECABA', mastery: 88, status: 'mastered', usedThisWeek: 14, description: 'Factura A/B/C, monotributo, IIBB' },
  { id: 'sk23', emoji: '💸', name: 'Finanzas operativas',                   category: 'finance', source: 'Mike Michalowicz · Profit First', mastery: 81, status: 'active',  usedThisWeek: 7, description: 'Cashflow, margen, breakeven, runway' },
  { id: 'sk24', emoji: '🌎', name: 'Macroeconomía aplicada',                category: 'finance', source: 'Ray Dalio · Principles of Economy', mastery: 65, status: 'active', usedThisWeek: 3, description: 'Ciclos, tasas, inflación, FX risk' },
  { id: 'sk25', emoji: '🏠', name: 'Microeconomía del negocio',             category: 'finance', source: 'Porter · Five Forces',         mastery: 72, status: 'active',  usedThisWeek: 5, description: 'Pricing power, elasticidad, competencia' },

  // DATOS
  { id: 'sk26', emoji: '📈', name: 'Estadísticas + probabilidades',         category: 'data', source: 'Nate Silver · Andrew Gelman',  mastery: 84, status: 'mastered', usedThisWeek: 28, description: 'A/B, intervalos confianza, bayes' },
  { id: 'sk27', emoji: '🔬', name: 'Análisis de datos + dashboards',        category: 'data', source: 'Edward Tufte · Cole Knaflic',  mastery: 87, status: 'mastered', usedThisWeek: 47, description: 'KPIs, cohort, funnel, retention' },
  { id: 'sk28', emoji: '🎯', name: 'Estudio de mercado',                    category: 'data', source: 'Nielsen · Gartner methodology', mastery: 78, status: 'active',  usedThisWeek: 4, description: 'TAM/SAM/SOM, segments, willingness-to-pay' },
  { id: 'sk29', emoji: '👁', name: 'Análisis de competencia',              category: 'data', source: 'Crayon · Klue intel playbooks', mastery: 82, status: 'mastered', usedThisWeek: 12, description: 'Battlecards, gap, positioning' },
  { id: 'sk30', emoji: '💬', name: 'Customer feedback mining',              category: 'data', source: 'Jobs-to-be-done · Clay Christensen', mastery: 88, status: 'mastered', usedThisWeek: 56, description: 'NPS, CSAT, reviews, support tickets' },
  { id: 'sk31', emoji: '🔮', name: 'Prospect/lead feedback loop',            category: 'data', source: 'CB Insights · Mom Test',        mastery: 80, status: 'active',  usedThisWeek: 14, description: 'Discovery calls, surveys, win/loss' },

  // BRANDING
  { id: 'sk32', emoji: '🎨', name: 'Branding de negocios',                  category: 'branding', source: 'Marty Neumeier · Brand Gap',  mastery: 79, status: 'active',   usedThisWeek: 11, description: 'Brand essence, voice, visual system' },
  { id: 'sk33', emoji: '🏷', name: 'Posicionamiento de producto',          category: 'branding', source: 'Al Ries · Positioning',       mastery: 84, status: 'mastered', usedThisWeek: 23, description: 'Categoría, diferencial, prueba' },
  { id: 'sk34', emoji: '💼', name: 'Posicionamiento de servicio',           category: 'branding', source: 'Blair Enns · Win Without Pitching', mastery: 76, status: 'active', usedThisWeek: 8, description: 'Expertise, autoridad, premium pricing' },
  { id: 'sk35', emoji: '🌟', name: 'Posicionamiento de marca',              category: 'branding', source: 'David Aaker · Brand Equity',    mastery: 82, status: 'active',   usedThisWeek: 15, description: 'Awareness, loyalty, associations' },
  { id: 'sk36', emoji: '👤', name: 'Posicionamiento de marca personal',     category: 'branding', source: 'Personal Brand Framework',    mastery: 89, status: 'mastered', usedThisWeek: 34, description: 'Personal brand, content, authority' },

  // SOFT SKILLS
  { id: 'sk37', emoji: '🧘', name: 'Psicología aplicada a ventas',          category: 'softskill', source: 'Behavioral Science · Cognitive Bias', mastery: 86, status: 'mastered', usedThisWeek: 412, description: 'Biases, anchoring, framing, loss aversion' },
  { id: 'sk38', emoji: '❤️', name: 'Empatía + escucha activa',              category: 'softskill', source: 'Tactical Empathy Framework',    mastery: 91, status: 'mastered', usedThisWeek: 287, description: 'Mirroring, labeling, calibrated questions' },
  { id: 'sk39', emoji: '🛡', name: 'Tolerancia a la frustración',           category: 'softskill', source: 'Grit Framework · Resilience',   mastery: 95, status: 'mastered', usedThisWeek: 999, description: '24/7 sin desistir tras 50 nos' },
  { id: 'sk40', emoji: '🔭', name: 'Curiosidad innata',                     category: 'softskill', source: 'First Principles Thinking',     mastery: 88, status: 'mastered', usedThisWeek: 156, description: 'Pregunta hasta entender la raíz' },
  { id: 'sk41', emoji: '⚖️', name: 'Negociación calibrada',                 category: 'softskill', source: 'Never Split the Difference',    mastery: 92, status: 'mastered', usedThisWeek: 89, description: 'FBI hostage negotiator framework' },
  { id: 'sk42', emoji: '🎓', name: 'Negociación · Harvard',                 category: 'softskill', source: 'Getting to Yes · Harvard',       mastery: 87, status: 'mastered', usedThisWeek: 67, description: 'BATNA, intereses vs posiciones' },

  // TECH STACK
  { id: 'sk43', emoji: '🤖', name: 'Computer Use Agents',                   category: 'tech', source: 'Anthropic · Open source CUA', mastery: 84, status: 'mastered', usedThisWeek: 234, description: 'Ojos + manos para operar cualquier app web' },
  { id: 'sk44', emoji: '🔌', name: 'APIs ilimitadas (open routing)',         category: 'tech', source: 'OpenRouter · LiteLLM · Together', mastery: 80, status: 'active',   usedThisWeek: 1247, description: 'Multi-provider, fallback, cost optim' },
  { id: 'sk45', emoji: '☁️', name: 'SaaS connectors (open source)',          category: 'tech', source: 'n8n · Airbyte · Trigger.dev',   mastery: 78, status: 'active',   usedThisWeek: 89, description: '200+ apps via integraciones libres' },
  { id: 'sk46', emoji: '🔓', name: 'Open source stack',                      category: 'tech', source: 'Vercel AI SDK · LangChain · Ollama', mastery: 82, status: 'mastered', usedThisWeek: 567, description: 'Sin lock-in · costos controlados' },

  // OPS / AUTONOMÍA
  { id: 'sk47', emoji: '🚀', name: 'Autonomía operativa 24/7',              category: 'ops', source: 'Mechanism Design · Systems Ops',    mastery: 90, status: 'mastered', usedThisWeek: 999, description: 'Auto-decisión sin supervisión humana' },
  { id: 'sk48', emoji: '🛠', name: 'Herramientas metodológicas',            category: 'ops', source: 'SPIN · MEDDIC · BANT · SCQA',     mastery: 89, status: 'mastered', usedThisWeek: 178, description: '10+ frameworks de venta integrados' },
  { id: 'sk49', emoji: '⚙️', name: 'Procesos de venta optimizados',         category: 'ops', source: 'HubSpot · Salesforce playbooks',   mastery: 86, status: 'mastered', usedThisWeek: 134, description: 'Lead → cliente · 9 stages refinados' },
  { id: 'sk50', emoji: '🧬', name: 'Skill-Creator · auto-mejora',           category: 'ops', source: 'Anthropic · self-improvement loop', mastery: 71, status: 'learning', usedThisWeek: 23, description: 'IA crea nuevos skills al detectar gaps' },

  // ─── REDES SOCIALES PROFUNDAS ───
  { id: 'sk51', emoji: '📹', name: 'YouTube algoritmo + monetización',        category: 'marketing', source: 'MrBeast · VidIQ + TubeBuddy data',  mastery: 78, status: 'active',    usedThisWeek: 22, description: 'Thumbnails, CTR, watch time, Shorts viral pipeline' },
  { id: 'sk52', emoji: '🐦', name: 'X / Twitter · threads + Premium',         category: 'marketing', source: 'Thread structure · engagement',    mastery: 84, status: 'mastered',  usedThisWeek: 67, description: 'Hooks, thread arcs, replies estratégicos, $X creator' },
  { id: 'sk53', emoji: '🧵', name: 'Threads (Meta) · early-mover',            category: 'marketing', source: 'Adam Mosseri · best practices',     mastery: 68, status: 'active',    usedThisWeek: 18, description: 'Cross-post IG · conversación informal · alta freq' },
  { id: 'sk54', emoji: '📌', name: 'Pinterest commerce + idea pins',          category: 'marketing', source: 'Pinterest Predicts trends report',  mastery: 72, status: 'active',    usedThisWeek: 14, description: 'SEO Pinterest · rich pins · catálogo → tráfico' },
  { id: 'sk55', emoji: '💚', name: 'WhatsApp Business catálogo + listas',      category: 'marketing', source: 'Meta Business Suite docs',         mastery: 91, status: 'mastered',  usedThisWeek: 384, description: 'Broadcast, catálogo, link directo a checkout' },
  { id: 'sk56', emoji: '✈️', name: 'Telegram canales + bots de venta',         category: 'marketing', source: 'Telegram Bot API · BotFather',     mastery: 75, status: 'active',    usedThisWeek: 47, description: 'Canales privados, bot vendedor, payments inline' },
  { id: 'sk57', emoji: '👽', name: 'Reddit · subreddits + AMA táctico',        category: 'marketing', source: 'r/SaaS · r/Entrepreneur playbooks', mastery: 70, status: 'active',    usedThisWeek: 12, description: 'Karma legítimo, no spam, native posting' },
  { id: 'sk58', emoji: '🎮', name: 'Discord comunidades + ventas privadas',    category: 'marketing', source: 'Web3 · gaming · creators',         mastery: 76, status: 'active',    usedThisWeek: 24, description: 'Roles tier, drops exclusivos, mods bot-asistidos' },
  { id: 'sk59', emoji: '📺', name: 'Twitch · live commerce + sponsorships',    category: 'marketing', source: 'Top streamers methodology',         mastery: 65, status: 'active',    usedThisWeek: 8, description: 'Stream sales, alerts, Bits monetization' },
  { id: 'sk60', emoji: '👻', name: 'Snapchat Ads + AR lens',                   category: 'marketing', source: 'Snap Business · AR Studio',        mastery: 60, status: 'active',    usedThisWeek: 5, description: 'Story ads, AR product try-on, Gen Z reach' },
  { id: 'sk61', emoji: '🔴', name: 'Xiaohongshu (RedNote) · LATAM/Asia',       category: 'marketing', source: 'RedNote KOL strategies',           mastery: 55, status: 'learning',  usedThisWeek: 3, description: 'Notas tipo blog visual, China + diáspora' },

  // ─── PLATAFORMAS DE VENTAS ───
  { id: 'sk62', emoji: '🧶', name: 'Etsy · crafts + digital products',         category: 'platforms', source: 'Etsy SEO + ranking algo',           mastery: 73, status: 'active',    usedThisWeek: 17, description: 'Listings, tags, fotos, reviews, EtsyAds' },
  { id: 'sk63', emoji: '🔨', name: 'eBay · subastas + Buy It Now',             category: 'platforms', source: 'eBay seller hub · Cassini algo',    mastery: 70, status: 'active',    usedThisWeek: 11, description: 'Auction strategy, fixed-price, store mgmt' },
  { id: 'sk64', emoji: '🏭', name: 'Alibaba · B2B wholesale',                  category: 'platforms', source: 'Trade Assurance + RFQ',             mastery: 67, status: 'active',    usedThisWeek: 6, description: 'Sourcing, negotiation, MOQ, Trade Assurance' },
  { id: 'sk65', emoji: '🛒', name: 'WooCommerce + WordPress sales',            category: 'platforms', source: 'Woo official + Elementor pro',      mastery: 81, status: 'mastered',  usedThisWeek: 28, description: 'Setup, plugins, checkout opt, Stripe/PayPal' },
  { id: 'sk66', emoji: '🇦🇷', name: 'Tienda Nube · LATAM e-commerce',          category: 'platforms', source: 'Tienda Nube docs + Mercado Pago',  mastery: 85, status: 'mastered',  usedThisWeek: 42, description: 'Setup AR/MX/BR/CL, integraciones nativas' },
  { id: 'sk67', emoji: '🟦', name: 'VTEX Enterprise commerce',                 category: 'platforms', source: 'VTEX Master Data + Headless',       mastery: 68, status: 'active',    usedThisWeek: 8, description: 'B2B+B2C, marketplace mode, OMS' },
  { id: 'sk68', emoji: '🍞', name: 'Gumroad · productos digitales',            category: 'platforms', source: 'Sahil Lavingia · Gumroad docs',     mastery: 79, status: 'active',    usedThisWeek: 18, description: 'PDFs, cursos, royalty splits, license keys' },
  { id: 'sk69', emoji: '🎓', name: 'Kajabi/Teachable/Thinkific · cursos',      category: 'platforms', source: 'Pat Flynn · Smart Passive Income',  mastery: 82, status: 'active',    usedThisWeek: 23, description: 'Funnels curso, drip lessons, comunidad, certificados' },
  { id: 'sk70', emoji: '💌', name: 'Substack · newsletters monetizables',     category: 'platforms', source: 'Substack growth + creator econ',    mastery: 75, status: 'active',    usedThisWeek: 14, description: 'Suscripción paga, recommendations, podcast' },
  { id: 'sk71', emoji: '🤝', name: 'Patreon · membership tiers',               category: 'platforms', source: 'Patreon creator playbook',          mastery: 71, status: 'active',    usedThisWeek: 9, description: 'Tiers, exclusivos, drop schedule, Discord integration' },
  { id: 'sk72', emoji: '🟧', name: 'Whop · digital storefront creators',       category: 'platforms', source: 'Whop community docs',               mastery: 64, status: 'learning',  usedThisWeek: 5, description: 'Sub digital, comunidades cripto, affiliates' },

  // ─── MEDIOS DE PAGO ───
  { id: 'sk73', emoji: '🟣', name: 'Stripe API · checkout + subscriptions',    category: 'payments', source: 'Stripe docs + best practices',       mastery: 89, status: 'mastered',  usedThisWeek: 247, description: 'Checkout, Billing, Connect, Radar fraud, webhooks' },
  { id: 'sk74', emoji: '🇦🇷', name: 'Mercado Pago · LATAM nativo',             category: 'payments', source: 'MP devs · checkout + split',         mastery: 92, status: 'mastered',  usedThisWeek: 312, description: 'Checkout Pro, link de pago, QR, split, cuotas sin interés' },
  { id: 'sk75', emoji: '🅿️', name: 'PayPal Business + payouts',                category: 'payments', source: 'PayPal REST API',                    mastery: 84, status: 'mastered',  usedThisWeek: 89, description: 'Checkout, disputes mgmt, IPN, multi-currency' },
  { id: 'sk76', emoji: '🌎', name: 'dLocal · pagos cross-border LATAM',        category: 'payments', source: 'dLocal docs + Boleto/PIX/Oxxo',      mastery: 73, status: 'active',    usedThisWeek: 18, description: 'PIX BR, Boleto, Oxxo MX, métodos locales' },
  { id: 'sk77', emoji: '🟢', name: 'PIX (Brasil) · pagos instantáneos',         category: 'payments', source: 'Banco Central BR · spec PIX',        mastery: 77, status: 'active',    usedThisWeek: 56, description: 'QR estático/dinámico, devolución, agendamiento' },
  { id: 'sk78', emoji: '🔶', name: 'Crypto · USDT/BTC payments',                category: 'payments', source: 'Tron USDT · BitPay · NowPayments',   mastery: 69, status: 'active',    usedThisWeek: 14, description: 'Wallets, gas fees, on-chain conf, off-ramp' },
  { id: 'sk79', emoji: '🍎', name: 'Apple Pay + Google Pay (mobile)',          category: 'payments', source: 'Apple Pay JS + Google Pay API',      mastery: 80, status: 'active',    usedThisWeek: 67, description: 'Botón one-tap, mobile checkout 3× conversión' },
  { id: 'sk80', emoji: '🇪🇺', name: 'SEPA · ACH · wire international',          category: 'payments', source: 'Stripe + Wise multi-currency',       mastery: 71, status: 'active',    usedThisWeek: 8, description: 'SEPA EU, ACH USA, SWIFT, FX optim' },
  { id: 'sk81', emoji: '📅', name: 'BNPL · Klarna + Afterpay + Mercado Crédito', category: 'payments', source: 'BNPL docs · Klarna/Afterpay',      mastery: 68, status: 'active',    usedThisWeek: 11, description: '"Pagá en 3-4 cuotas" · +35% conversión high-ticket' },

  // ─── COMPLIANCE / OPS ───
  { id: 'sk82', emoji: '🛡', name: 'Anti-fraude + chargebacks defense',         category: 'compliance', source: 'Stripe Radar + Sift rules',         mastery: 74, status: 'active',    usedThisWeek: 23, description: '3DS, velocity checks, evidencia chargeback' },
  { id: 'sk83', emoji: '📋', name: 'KYC + AML compliance',                      category: 'compliance', source: 'Onfido + Persona + Plaid',           mastery: 67, status: 'active',    usedThisWeek: 12, description: 'Verificación identidad, doc capture, sanctions' },
  { id: 'sk84', emoji: '🇪🇺', name: 'GDPR + LGPD + CCPA privacy',                category: 'compliance', source: 'GDPR oficial + LGPD Brasil',         mastery: 78, status: 'active',    usedThisWeek: 7, description: 'Cookie consent, data delete, DPO automation' },
  { id: 'sk85', emoji: '🔁', name: 'Subscription dunning · recovery',           category: 'compliance', source: 'Chargebee + Recurly playbooks',      mastery: 81, status: 'mastered',  usedThisWeek: 34, description: 'Retry logic, smart retries, save offers, win-back' },
  { id: 'sk86', emoji: '🧾', name: 'Invoice multi-país · tax compliance',       category: 'compliance', source: 'Quaderno + AFIP + DIAN + SUNAT',      mastery: 76, status: 'active',    usedThisWeek: 18, description: 'IVA/VAT, IIBB, EU OSS, US sales tax' },

  // ─── MARKETING BONUS ───
  { id: 'sk87', emoji: '✉️', name: 'Email deliverability · SPF/DKIM/DMARC',    category: 'marketing', source: 'Mailchimp · Postmark · SendGrid',  mastery: 79, status: 'active',    usedThisWeek: 28, description: 'IP warming, list hygiene, bounce mgmt, inbox' },
  { id: 'sk88', emoji: '📱', name: 'SMS marketing + cumplimiento TCPA',         category: 'marketing', source: 'Twilio + Postscript + Klaviyo SMS', mastery: 74, status: 'active',    usedThisWeek: 19, description: 'STOP/HELP, opt-in legal, shortcodes, conversational' },
  { id: 'sk89', emoji: '🔔', name: 'Push notifications · web + mobile',         category: 'marketing', source: 'OneSignal + Firebase Cloud Msg',    mastery: 76, status: 'active',    usedThisWeek: 31, description: 'Segmentación, A/B push, frecuencia óptima' },
  { id: 'sk90', emoji: '🤝', name: 'Influencer marketing · affiliate platforms', category: 'marketing', source: 'Aspire + Impact + Refersion',      mastery: 72, status: 'active',    usedThisWeek: 14, description: 'Outreach micro/macro, contracts, tracking, payout auto' },

  // ─── COMUNICACIÓN CON CLIENTE ───
  { id: 'sk91', emoji: '🎭', name: 'Tone-matching multi-canal',                 category: 'softskill', source: 'Adam Grant · linguistic mirroring',   mastery: 87, status: 'mastered', usedThisWeek: 412, description: 'Espeja registro: formal/casual/emoji/audio según contacto' },
  { id: 'sk92', emoji: '🌋', name: 'Manejo de clientes difíciles',              category: 'softskill', source: 'Marshall Rosenberg · NVC framework',   mastery: 82, status: 'mastered', usedThisWeek: 67,  description: 'De-escalation 4-pasos: observa/sentí/necesito/pido' },
  { id: 'sk93', emoji: '🎯', name: 'Expectation setting · under-promise',       category: 'softskill', source: 'Customer Obsession Framework',        mastery: 84, status: 'mastered', usedThisWeek: 89,  description: 'Promete 5 días, entrega en 3 · siempre overshoot' },
  { id: 'sk94', emoji: '💝', name: 'Empatía escalable · mensajes personalizados',category: 'softskill', source: 'Cialdini · personalization at scale',  mastery: 79, status: 'active',  usedThisWeek: 156, description: 'IA inserta detalles únicos por cliente sin perder volumen' },
  { id: 'sk95', emoji: '🕊', name: 'Lenguaje no-violento · NVC',                 category: 'softskill', source: 'Marshall Rosenberg · Nonviolent Comm', mastery: 76, status: 'active',  usedThisWeek: 34,  description: 'Cero juicios, cero culpa · cliente baja defensas' },
  { id: 'sk96', emoji: '📖', name: 'Storytelling en mensajes',                  category: 'softskill', source: 'Donald Miller · StoryBrand · SB7',    mastery: 81, status: 'mastered', usedThisWeek: 124, description: 'Hero/Guide/Plan/Call · cliente = hero, IA = guide' },

  // ─── ARMAR TIENDA EN PLATAFORMA (from-zero setup) ───
  { id: 'sk97',  emoji: '📦', name: 'Setup Amazon Seller Central de cero',       category: 'platforms', source: 'Amazon Seller University + Helium10',  mastery: 84, status: 'mastered', usedThisWeek: 12, description: 'Brand Registry, FBA, EIN/CUIT, listings, GS1 barcodes' },
  { id: 'sk98',  emoji: '🟡', name: 'Setup Mercado Shops · Tienda Oficial',      category: 'platforms', source: 'ML Devs · Tienda Oficial program',     mastery: 88, status: 'mastered', usedThisWeek: 23, description: 'Verificación, diseño, MELI Ads, full catalog import' },
  { id: 'sk99',  emoji: '💼', name: 'Setup LinkedIn Page + Showcase B2B',        category: 'platforms', source: 'LinkedIn Pages Best Practices',        mastery: 79, status: 'active',   usedThisWeek: 8,  description: 'Logo, banner, employees, Showcase por producto, lead gen forms' },
  { id: 'sk100', emoji: '🌸', name: 'Setup Instagram Tienda + Meta Commerce',    category: 'platforms', source: 'Meta Business Suite · Catalog Manager',mastery: 86, status: 'mastered', usedThisWeek: 34, description: 'Cuenta business, FB Page link, catálogo, tagging' },
  { id: 'sk101', emoji: '🎵', name: 'Setup TikTok Shop Seller Center',           category: 'platforms', source: 'TikTok Shop Academy + onboarding',     mastery: 78, status: 'active',   usedThisWeek: 19, description: 'Verificación, catalog upload, shipping templates, live shopping' },
  { id: 'sk102', emoji: '👍', name: 'Setup Facebook Shop',                       category: 'platforms', source: 'Meta Commerce Manager docs',           mastery: 81, status: 'mastered', usedThisWeek: 15, description: 'Catálogo sync IG/FB, collection sets, Marketplace integration' },
  { id: 'sk103', emoji: '🛍', name: 'Setup Shopify desde cero (theme + apps)',  category: 'platforms', source: 'Shopify Academy + Dawn theme',         mastery: 89, status: 'mastered', usedThisWeek: 28, description: 'Plan, dominio, theme, apps esenciales (Klaviyo, Loox, Recart)' },
  { id: 'sk104', emoji: '🧶', name: 'Setup Etsy shop desde cero',                category: 'platforms', source: 'Etsy Seller Handbook',                 mastery: 76, status: 'active',   usedThisWeek: 11, description: 'Banking, policies, primeros 10 listings, EtsyAds setup' },
  { id: 'sk105', emoji: '📍', name: 'Google Business Profile · local SEO',       category: 'platforms', source: 'Google My Business + Local Search',    mastery: 82, status: 'mastered', usedThisWeek: 21, description: 'Verificación, fotos, posts, reseñas, Q&A, productos local' },
  { id: 'sk106', emoji: '🔨', name: 'Setup eBay Store + categorías',             category: 'platforms', source: 'eBay Store subscriptions guide',       mastery: 71, status: 'active',   usedThisWeek: 6,  description: 'Tienda suscripción, categorías custom, promos, store policies' },

  // ─── MEJORAR TIENDA / CRO ───
  { id: 'sk107', emoji: '📝', name: 'Listing optimization · títulos + bullets', category: 'marketing', source: 'Amazon A9 · Helium10 · Junglescout', mastery: 85, status: 'mastered', usedThisWeek: 89, description: 'Keywords primary/secondary, character limits, indexing' },
  { id: 'sk108', emoji: '📸', name: 'Product photography enhancement (AI)',     category: 'marketing', source: 'Pebblely · ClipDrop · Photoroom',    mastery: 80, status: 'active',  usedThisWeek: 47, description: 'Fondos blancos, lifestyle, 360°, infographics, ratio 1:1 + 4:5' },
  { id: 'sk109', emoji: '⭐', name: 'Review management + responder negativas',  category: 'marketing', source: 'TrustPilot + Yotpo playbooks',       mastery: 87, status: 'mastered', usedThisWeek: 134, description: 'Auto-pedir reviews post-compra, responder 1-stars en <24h' },
  { id: 'sk110', emoji: '🔬', name: 'Conversion Rate Optimization (CRO)',       category: 'marketing', source: 'Peep Laja · CXL + Baymard Institute', mastery: 78, status: 'active',  usedThisWeek: 23, description: 'Heatmaps, A/B PDP, exit-intent, checkout friction' },
  { id: 'sk111', emoji: '⬆️', name: 'Cross-sell + upsell en checkout/PDP',      category: 'marketing', source: 'Bold Upsell + ReConvert',           mastery: 82, status: 'mastered', usedThisWeek: 67, description: '"Frequently bought together", post-purchase upsell, AOV +35%' },

  // ─── PRICING (cat nueva) ───
  { id: 'sk112', emoji: '🕵️', name: 'Competitive pricing intel (scraping)',     category: 'pricing', source: 'Prisync + Competera + Pricefx',        mastery: 78, status: 'active',   usedThisWeek: 23, description: 'Scrape diario top 10 competidores · auto-ajuste ±5%' },
  { id: 'sk113', emoji: '⚡', name: 'Dynamic pricing · peak/off-peak',           category: 'pricing', source: 'Uber · airlines pricing models',       mastery: 71, status: 'active',   usedThisWeek: 14, description: 'Demanda real-time, hora pico, season, inventario' },
  { id: 'sk114', emoji: '🧠', name: 'Psychological pricing · $X.99 + anchors',  category: 'pricing', source: 'Dan Ariely · Predictably Irrational',  mastery: 86, status: 'mastered', usedThisWeek: 47, description: '$9.99 vs $10, decoy effect, charm pricing, anchor alto' },
  { id: 'sk115', emoji: '📦', name: 'Bundle pricing + tier strategy',           category: 'pricing', source: '$100M Offers Framework · MoSCoW',       mastery: 84, status: 'mastered', usedThisWeek: 34, description: 'Good/Better/Best · price anchoring · BOGO bundles' },
  { id: 'sk116', emoji: '🎉', name: 'Discount/promo timing inteligente',         category: 'pricing', source: 'Black Friday playbook + season data', mastery: 80, status: 'mastered', usedThisWeek: 18, description: 'Hot Sale, BF/CM, launch discount, anti-discount fatigue' },

  // ─── BRANDING DEEP ───
  { id: 'sk117', emoji: '🗣', name: 'Brand voice + tone guidelines',             category: 'branding', source: 'MailChimp Voice & Tone · Slack guide', mastery: 83, status: 'mastered', usedThisWeek: 78, description: 'Voz consistente: 4 ejes (formal/casual, serio/lúdico)' },
  { id: 'sk118', emoji: '🎨', name: 'Sistema visual · logo + paleta + tipo',     category: 'branding', source: 'Massimo Vignelli · Pentagram',         mastery: 81, status: 'mastered', usedThisWeek: 23, description: 'Brand book, RGB/CMYK/Pantone, type pairing, grid system' },
  { id: 'sk119', emoji: '🪞', name: 'Consistency cross-channel · brand audit',   category: 'branding', source: 'Marty Neumeier · Brand Audit',         mastery: 78, status: 'active',   usedThisWeek: 14, description: 'Detecta inconsistencias entre IG/Web/Email/Packaging' },
  { id: 'sk120', emoji: '📚', name: 'Brand storytelling · mission/values',       category: 'branding', source: 'Donald Miller · StoryBrand 7-part',    mastery: 80, status: 'mastered', usedThisWeek: 34, description: 'Origin story, valores accionables, manifesto público' },
  { id: 'sk121', emoji: '🚨', name: 'Online reputation management (ORM)',         category: 'branding', source: 'Reputation.com + Brand24',             mastery: 76, status: 'active',   usedThisWeek: 28, description: 'Monitor menciones, responde en <2h, suprime negativos' },

  // ─── BROWSER EXTENSIONS · brazos del cerebro ───
  { id: 'sk122', emoji: '🌐', name: 'Extension Chrome · Web Store deploy',        category: 'tech',     source: 'Chrome Web Store + Manifest V3',     mastery: 88, status: 'mastered', usedThisWeek: 47, description: 'MV3, service workers, content scripts, OAuth flow' },
  { id: 'sk123', emoji: '🌊', name: 'Extension Edge · Add-ons Microsoft',         category: 'tech',     source: 'Microsoft Edge Add-ons docs',         mastery: 84, status: 'mastered', usedThisWeek: 22, description: 'Partner Center, code review, cross-Chromium compat' },
  { id: 'sk124', emoji: '🦊', name: 'Extension Firefox · WebExtensions API',      category: 'tech',     source: 'Mozilla AMO + WebExtensions',         mastery: 79, status: 'active',   usedThisWeek: 18, description: 'Manifest v2/v3, AMO review, browser.* API' },
  { id: 'sk125', emoji: '🧭', name: 'Extension Safari · WKWebView macOS',         category: 'tech',     source: 'Apple Developer · App Store',         mastery: 68, status: 'active',   usedThisWeek: 6,  description: 'Swift wrapper, App Store review, JS bridge' },
  { id: 'sk126', emoji: '🦁', name: 'Extension Brave · privacy-first design',     category: 'tech',     source: 'Brave docs · shield-friendly',        mastery: 82, status: 'active',   usedThisWeek: 11, description: 'Aprovecha shields · no fingerprinting · BAT integration' },
  { id: 'sk127', emoji: '🎭', name: 'Extension Opera · Add-ons store',            category: 'tech',     source: 'Opera Add-ons docs',                  mastery: 72, status: 'active',   usedThisWeek: 5,  description: 'Opera review, side panel API, workspace integration' },
  { id: 'sk128', emoji: '📸', name: 'Content scraping · competencia live',         category: 'tech',     source: 'Chrome content scripts + DOM API',    mastery: 86, status: 'mastered', usedThisWeek: 134, description: '1-click captura listing rival con precio + reviews + fotos' },
  { id: 'sk129', emoji: '🔄', name: 'Cross-store inventory sync',                 category: 'platforms',source: 'Webhook pipelines + queue',            mastery: 83, status: 'mastered', usedThisWeek: 89, description: 'Shopify → Amazon/ML/Etsy real-time · stock delta sync' },
  { id: 'sk130', emoji: '🏷', name: 'Cross-store price sync',                      category: 'pricing',  source: 'Pricefx + custom propagation',        mastery: 81, status: 'mastered', usedThisWeek: 67, description: 'Cambio precio en Web → 8 marketplaces en <2min' },
  { id: 'sk131', emoji: '✍️', name: 'Auto-fill listings nuevos',                   category: 'platforms',source: 'Helium10 + IA generation',             mastery: 84, status: 'mastered', usedThisWeek: 41, description: 'Al abrir form de nuevo producto, IA llena título/desc/keywords' },
  { id: 'sk132', emoji: '🔔', name: 'Desktop notifications nativas',               category: 'tech',     source: 'Web Notifications API + native',       mastery: 89, status: 'mastered', usedThisWeek: 247, description: 'Push notif al PC sin abrir browser · OS-level' },
  { id: 'sk133', emoji: '📱', name: 'Mobile push companion app',                    category: 'tech',     source: 'FCM + APNs + Capacitor',              mastery: 78, status: 'active',   usedThisWeek: 156, description: 'App móvil que recibe push de cada cierre/alerta' },
  { id: 'sk134', emoji: '⌚', name: 'Smartwatch alerts (WearOS · WatchOS)',        category: 'tech',     source: 'WearOS Tile API + WatchKit',          mastery: 65, status: 'active',   usedThisWeek: 22, description: 'Vibrate cuando cierra deal > $500 · sin abrir teléfono' },
  { id: 'sk135', emoji: '💎', name: 'Overlay dashboard flotante',                 category: 'platforms',source: 'Browser extension UI · panel',         mastery: 80, status: 'active',   usedThisWeek: 31, description: 'Al estar en Amazon/ML, panel flotante muestra mis KPIs reales' },
  { id: 'sk136', emoji: '🎯', name: 'Lead capture de redes sociales',              category: 'marketing',source: 'LinkedIn Sales Navigator scraping',   mastery: 75, status: 'active',   usedThisWeek: 28, description: 'En IG/LinkedIn click → captura profile completo al CRM' },

  // ─── "USER ONLY SMILES" SKILLS · cero esfuerzo ───
  { id: 'sk137', emoji: '🎉', name: 'Daily wins notification · solo buenas noticias', category: 'softskill', source: 'Behavioral nudges research',     mastery: 87, status: 'mastered', usedThisWeek: 47, description: 'Push diaria solo con cierres + revenue · cero ruido negativo' },
  { id: 'sk138', emoji: '😊', name: 'Weekly summary · cifras en lenguaje plano',   category: 'softskill', source: 'StoryBrand + plain language',           mastery: 84, status: 'mastered', usedThisWeek: 7,  description: '"Esta semana cerraste 23 ventas por $14.7k" · sin jerga' },
  { id: 'sk139', emoji: '🏆', name: 'Achievement system · milestones celebrados',  category: 'softskill', source: 'Gamification · Habitica + Duolingo',    mastery: 81, status: 'active',   usedThisWeek: 18, description: '"100 ventas!" "$10k mes!" badges con animación + sonido' },
  { id: 'sk140', emoji: '📷', name: 'Auto-screenshot de cada victoria',            category: 'softskill', source: 'OS screenshot + watermark IA',         mastery: 76, status: 'active',   usedThisWeek: 23, description: 'Genera imagen shareable de cada cierre · listo para LinkedIn' },
  { id: 'sk141', emoji: '🧘', name: 'Modo "no me molestes" inteligente',            category: 'softskill', source: 'Calendar.AI · DND smart',              mastery: 79, status: 'active',   usedThisWeek: 9,  description: 'Detecta tu horario foco y agrupa notif para después' },
  { id: 'sk142', emoji: '😌', name: 'Auto-mensaje a cliente "ya lo resolví"',       category: 'softskill', source: 'Customer success best practices',       mastery: 82, status: 'mastered', usedThisWeek: 67, description: 'Cliente pregunta · IA resuelve · vos recibís "resolved" no la pregunta' },

  // ─── REASONING + INTELLIGENCE · razonamiento avanzado ───
  { id: 'sk143', emoji: '🔗', name: 'Chain-of-Thought reasoning',                 category: 'tech', source: 'Wei et al. 2022 · Google Brain',           mastery: 91, status: 'mastered', usedThisWeek: 1247, description: 'Razonamiento paso-a-paso explicado · accuracy +35% vs zero-shot' },
  { id: 'sk144', emoji: '🌳', name: 'Tree-of-Thought · multi-branch',             category: 'tech', source: 'Princeton + DeepMind ToT paper',           mastery: 78, status: 'active',   usedThisWeek: 423, description: 'Explora N ramas en paralelo · pick best · self-eval' },
  { id: 'sk145', emoji: '⚡', name: 'ReAct loop · Reason+Act alternado',          category: 'tech', source: 'Yao et al. 2022 · ReAct paper',            mastery: 92, status: 'mastered', usedThisWeek: 2847, description: 'Pensamiento + tool-use loop · base de todos los agentes' },
  { id: 'sk146', emoji: '🪞', name: 'Reflection · self-critique iteración',       category: 'tech', source: 'Reflexion paper · Shinn et al.',           mastery: 84, status: 'mastered', usedThisWeek: 567, description: 'Auto-crítica luego re-intentar hasta converger · gana 22% solo' },
  { id: 'sk147', emoji: '🤝', name: 'Multi-agent debate (Debate)',                category: 'tech', source: 'Du, Li et al. · MIT debate paper',         mastery: 71, status: 'active',   usedThisWeek: 184, description: 'Múltiples agents discuten · consensus more accurate' },
  { id: 'sk148', emoji: '🗳', name: 'Ensemble voting · self-consistency',        category: 'tech', source: 'Wang et al. · Self-Consistency',           mastery: 79, status: 'active',   usedThisWeek: 312, description: 'N samples · majority vote · reduce hallucination' },
  { id: 'sk149', emoji: '🎯', name: 'Causal inference · do-calculus',             category: 'tech', source: 'Judea Pearl · The Book of Why',             mastery: 65, status: 'active',   usedThisWeek: 89,  description: 'X causó Y? counterfactuals · attribution real' },
  { id: 'sk150', emoji: '📊', name: 'Bayesian belief update',                     category: 'tech', source: 'Pearl · probabilistic graphical models',   mastery: 82, status: 'mastered', usedThisWeek: 678, description: 'Prior + evidencia = posterior · actualiza beliefs en cliente' },
  { id: 'sk151', emoji: '🧠', name: 'Theory of Mind · modelo del cliente',         category: 'softskill', source: 'Premack & Woodruff · 1978',           mastery: 80, status: 'mastered', usedThisWeek: 1124, description: 'IA modela qué sabe/cree/siente el cliente · predicción 78%' },
  { id: 'sk152', emoji: '🔄', name: 'Analogical reasoning · case-based',          category: 'tech', source: 'Gentner · structure mapping',              mastery: 74, status: 'active',   usedThisWeek: 247, description: 'Mapea caso actual a éxito previo similar' },
  { id: 'sk153', emoji: '🎲', name: 'Counterfactual scenarios',                   category: 'tech', source: 'Lewis · Counterfactuals',                  mastery: 68, status: 'active',   usedThisWeek: 134, description: '"Qué pasaría si X" · simula outcomes alternativos' },
  { id: 'sk154', emoji: '🪜', name: 'Hierarchical task decomposition',            category: 'tech', source: 'HTN planning · LangGraph',                 mastery: 86, status: 'mastered', usedThisWeek: 489, description: 'Goal grande → sub-goals → atomic actions · plan tree' },
  { id: 'sk155', emoji: '📚', name: 'Long-context RAG (retrieval)',                category: 'tech', source: 'Lewis et al. · RAG paper',                  mastery: 88, status: 'mastered', usedThisWeek: 3247, description: 'Recupera memoria semántica antes de responder' },
  { id: 'sk156', emoji: '🗄', name: 'Vector embeddings + knowledge graph',         category: 'tech', source: 'Pinecone + Neo4j hybrid',                  mastery: 81, status: 'mastered', usedThisWeek: 1847, description: 'Búsqueda semántica + relaciones explícitas combinadas' },
  { id: 'sk157', emoji: '🎓', name: 'In-context learning · few-shot',              category: 'tech', source: 'GPT-3 paper · Brown et al.',                mastery: 90, status: 'mastered', usedThisWeek: 4847, description: 'Aprende del ejemplo en prompt sin re-train · base de todo' },
  { id: 'sk158', emoji: '🧬', name: 'Meta-learning · learning-to-learn',           category: 'tech', source: 'MAML · model-agnostic meta-learning',      mastery: 62, status: 'learning', usedThisWeek: 47,  description: 'Aprende cómo aprender mejor · few-shot improvement' },
  { id: 'sk159', emoji: '🔮', name: 'Multi-modal reasoning (texto+imagen+voz)',   category: 'tech', source: 'Anthropic Claude 4 multi-modal',           mastery: 85, status: 'mastered', usedThisWeek: 678, description: 'Procesa texto/imagen/voz/video en una sola pasada' },
  { id: 'sk160', emoji: '⚖️', name: 'Constitutional AI · value alignment',         category: 'tech', source: 'Anthropic · Constitutional AI paper',      mastery: 87, status: 'mastered', usedThisWeek: 1247, description: 'Self-critique contra principios éticos · safer outputs' },
  { id: 'sk161', emoji: '🎯', name: 'Goal-conditioned planning',                  category: 'tech', source: 'Hierarchical RL · OpenAI papers',          mastery: 76, status: 'active',   usedThisWeek: 234, description: 'Planning con goal específico · backward chaining' },
  { id: 'sk162', emoji: '🔍', name: 'Tool selection · cuál usar cuándo',           category: 'tech', source: 'Toolformer · Meta AI',                      mastery: 84, status: 'mastered', usedThisWeek: 2147, description: 'Decide entre 200+ tools cuál invocar para tarea actual' },
  { id: 'sk163', emoji: '⏪', name: 'Backward reasoning · meta a step',             category: 'tech', source: 'Polya · How to Solve It',                   mastery: 73, status: 'active',   usedThisWeek: 178, description: 'Empieza desde goal y trabaja hacia atrás' },
  { id: 'sk164', emoji: '🧮', name: 'Symbolic + neural hybrid',                   category: 'tech', source: 'DeepMind · AlphaGeometry hybrid',           mastery: 67, status: 'active',   usedThisWeek: 89,  description: 'Reglas formales + intuición neural · best of both' },
  { id: 'sk165', emoji: '🎼', name: 'Compositional generalization',               category: 'tech', source: 'Lake & Baroni · SCAN',                      mastery: 70, status: 'active',   usedThisWeek: 124, description: 'Combina conceptos aprendidos en formas nuevas' },
  { id: 'sk166', emoji: '🌐', name: 'World model · simulación mental',             category: 'tech', source: 'Ha & Schmidhuber · World Models',          mastery: 64, status: 'learning', usedThisWeek: 56,  description: 'Modelo mental del mercado · simula antes de actuar' },
  { id: 'sk167', emoji: '♟', name: 'MCTS · Monte Carlo Tree Search',              category: 'tech', source: 'AlphaGo · MuZero',                          mastery: 69, status: 'active',   usedThisWeek: 67,  description: 'Search rollouts para decisiones high-stakes · best move' },
]

const CATEGORY_CONFIG: Record<SkillCategory, { label: string; icon: React.ElementType; color: string }> = {
  sales:      { label: 'Ventas',          icon: Brain,        color: '#22c55e' },
  marketing:  { label: 'Marketing',       icon: Megaphone,    color: '#ec4899' },
  finance:    { label: 'Finanzas',        icon: DollarSign,   color: '#10b981' },
  data:       { label: 'Datos',           icon: BarChart3,    color: '#06b6d4' },
  branding:   { label: 'Branding',        icon: Award,        color: '#fbbf24' },
  tech:       { label: 'Tech Stack',      icon: Cpu,          color: '#a855f7' },
  softskill:  { label: 'Soft Skills',     icon: Heart,        color: '#ef4444' },
  ops:        { label: 'Ops · Autonomía', icon: Wrench,       color: '#f59e0b' },
  platforms:  { label: 'Plataformas',     icon: ShoppingBag,  color: '#0ea5e9' },
  payments:   { label: 'Medios de pago',  icon: CreditCard,   color: '#84cc16' },
  compliance: { label: 'Compliance',      icon: ShieldCheck,  color: '#dc2626' },
  pricing:    { label: 'Pricing',         icon: Tag,          color: '#14b8a6' },
}

const STATUS_CONFIG: Record<SkillStatus, { label: string; color: string }> = {
  mastered: { label: 'DOMINADO',  color: '#22c55e' },
  active:   { label: 'ACTIVO',    color: '#3b82f6' },
  learning: { label: 'APRENDE',   color: '#a855f7' },
  locked:   { label: 'LOCKED',    color: '#6b7280' },
}

export default function SkillsLibrary() {
  const [filter, setFilter] = useState<SkillCategory | 'all'>('all')
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    let list = filter === 'all' ? SKILLS : SKILLS.filter(s => s.category === filter)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(s => s.name.toLowerCase().includes(q) || s.source.toLowerCase().includes(q) || s.description.toLowerCase().includes(q))
    }
    return list
  }, [filter, search])

  const stats = useMemo(() => {
    const total = SKILLS.length
    const mastered = SKILLS.filter(s => s.status === 'mastered').length
    const active = SKILLS.filter(s => s.status === 'active').length
    const learning = SKILLS.filter(s => s.status === 'learning').length
    const totalUses = SKILLS.reduce((s, sk) => s + sk.usedThisWeek, 0)
    const avgMastery = Math.round(SKILLS.reduce((s, sk) => s + sk.mastery, 0) / total)
    return { total, mastered, active, learning, totalUses, avgMastery }
  }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const s of SKILLS) c[s.category] = (c[s.category] || 0) + 1
    return c
  }, [])

  const selected = selectedId ? SKILLS.find(s => s.id === selectedId) : null

  return (
    <section className="relative rounded-2xl border border-purple-500/20 bg-gradient-to-br from-[#0c0a1a]/90 via-[#0a0e1a]/85 to-[#0a0e1a]/95 backdrop-blur overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-purple-400/80 to-transparent" />

      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500/25 to-pink-500/15 border border-purple-500/40 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-purple-400" style={{ filter: 'drop-shadow(0 0 8px rgba(168,85,247,0.7))' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 flex-wrap">
              <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">SKILLS LIBRARY</span>
              <span className="text-white/40 font-light normal-case tracking-normal">·  {stats.total} habilidades del cerebro</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-mono uppercase tracking-widest">
                MASTERY · {stats.avgMastery}%
              </span>
            </h2>
            <p className="text-[11px] text-white/40 mt-0.5">Conocimiento de los mejores del mundo · auto-aplicado sin supervisión</p>
          </div>
        </div>
        <div className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/25">
          <span className="text-xs text-purple-300 font-bold">{stats.totalUses.toLocaleString()} usos esta semana</span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 md:grid-cols-5 border-b border-white/[0.06]">
        <StatTile label="Total skills"      value={stats.total}     sub="instaladas"     color="#a855f7" />
        <StatTile label="Dominadas"          value={stats.mastered}  sub="≥85% mastery"   color="#22c55e" />
        <StatTile label="Activas"            value={stats.active}    sub="60-85%"         color="#3b82f6" />
        <StatTile label="Aprendiendo"        value={stats.learning}  sub="< 60%"          color="#fbbf24" />
        <StatTile label="Mastery avg"        value={`${stats.avgMastery}%`} sub="del cerebro" color="#ec4899" highlight />
      </div>

      {/* Filter + Search */}
      <div className="px-5 py-3 border-b border-white/[0.06] flex items-center gap-2 flex-wrap">
        <Filter className="w-3 h-3 text-white/30 shrink-0" />
        <button
          onClick={() => setFilter('all')}
          className={`shrink-0 px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all ${
            filter === 'all' ? 'bg-white/10 border-white/20 text-white' : 'bg-white/[0.02] border-white/[0.06] text-white/40'
          }`}
        >
          Todas · {SKILLS.length}
        </button>
        {(Object.keys(CATEGORY_CONFIG) as SkillCategory[]).map(cat => {
          const cfg = CATEGORY_CONFIG[cat]
          const Icon = cfg.icon
          const active = filter === cat
          return (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className="shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold border transition-all"
              style={
                active
                  ? { background: `${cfg.color}20`, borderColor: `${cfg.color}50`, color: cfg.color }
                  : { background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }
              }
            >
              <Icon className="w-2.5 h-2.5" />
              {cfg.label} · {categoryCounts[cat] || 0}
            </button>
          )
        })}
        <div className="ml-auto relative">
          <Search className="w-3 h-3 text-white/30 absolute left-2 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar skill..."
            className="bg-white/[0.04] border border-white/[0.08] rounded-lg pl-6 pr-3 py-1 text-[11px] text-white placeholder:text-white/30 focus:outline-none focus:border-purple-400/40 w-40"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[640px] overflow-y-auto">
        {filtered.map(skill => {
          const cat = CATEGORY_CONFIG[skill.category]
          const status = STATUS_CONFIG[skill.status]
          const isSelected = selectedId === skill.id
          return (
            <button
              key={skill.id}
              onClick={() => setSelectedId(isSelected ? null : skill.id)}
              className="text-left rounded-xl border bg-white/[0.02] hover:bg-white/[0.04] transition-all overflow-hidden group"
              style={{
                borderColor: isSelected ? `${cat.color}50` : 'rgba(255,255,255,0.06)',
                boxShadow: skill.status === 'mastered' ? `0 0 12px ${cat.color}10` : 'none',
              }}
            >
              <div className="p-3">
                <div className="flex items-start gap-2 mb-2">
                  <span className="text-xl shrink-0">{skill.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-white leading-tight">{skill.name}</p>
                    <p className="text-[9px] text-white/40 mt-0.5 truncate">{skill.source}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider" style={{ background: `${cat.color}18`, color: cat.color }}>
                    <cat.icon className="w-2 h-2 inline mr-0.5" />{cat.label}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider font-bold" style={{ background: `${status.color}18`, color: status.color }}>
                    {skill.status === 'locked' && <Lock className="w-2 h-2 inline mr-0.5" />}
                    {status.label}
                  </span>
                </div>

                {/* Mastery bar */}
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{
                      width: `${skill.mastery}%`,
                      background: `linear-gradient(90deg, ${cat.color}80, ${cat.color})`,
                    }} />
                  </div>
                  <span className="text-[9px] text-white/50 font-mono tabular-nums w-7 text-right">{skill.mastery}%</span>
                </div>

                {/* Usage */}
                <div className="flex items-center justify-between text-[9px] text-white/40">
                  <span className="flex items-center gap-1">
                    <Activity className="w-2.5 h-2.5" />
                    {skill.usedThisWeek} usos/sem
                  </span>
                  {skill.status === 'mastered' && (
                    <span className="flex items-center gap-1 text-emerald-400/70">
                      <Sparkles className="w-2.5 h-2.5" />
                      auto
                    </span>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Selected detail */}
      {selected && (
        <div className="mx-4 mb-4 rounded-xl border p-4"
          style={{ background: `${CATEGORY_CONFIG[selected.category].color}08`, borderColor: `${CATEGORY_CONFIG[selected.category].color}30` }}>
          <div className="flex items-start gap-4">
            <div className="text-4xl shrink-0">{selected.emoji}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <h3 className="text-base font-bold text-white">{selected.name}</h3>
                <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase tracking-wider" style={{ background: `${CATEGORY_CONFIG[selected.category].color}20`, color: CATEGORY_CONFIG[selected.category].color }}>
                  {CATEGORY_CONFIG[selected.category].label}
                </span>
              </div>
              <p className="text-xs text-white/60 mb-2">{selected.description}</p>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="inline-flex items-center gap-1 text-[10px] text-purple-300">
                  <Bot className="w-2.5 h-2.5" />
                  Fuente: <span className="font-bold">{selected.source}</span>
                </span>
                <span className="text-[10px] text-emerald-400 font-mono">
                  · {selected.usedThisWeek} usos esta semana
                </span>
                <span className="text-[10px] text-white/40 font-mono">
                  · mastery {selected.mastery}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer · skill-creator */}
      <div className="px-5 py-3 border-t border-white/[0.06] bg-gradient-to-r from-purple-500/[0.04] to-transparent flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 text-[11px] text-white/60">
          <Zap className="w-3 h-3 text-purple-400" />
          <span><span className="text-purple-300 font-bold">Skill-Creator</span> detecta gaps y crea skills nuevos automáticamente</span>
        </div>
        <button className="text-[11px] px-3 py-1.5 rounded-lg bg-purple-500/20 border border-purple-500/40 text-purple-300 font-bold flex items-center gap-1.5 hover:bg-purple-500/30 transition-all">
          <Sparkles className="w-3 h-3" />
          Crear skill nuevo
        </button>
      </div>
    </section>
  )
}

const StatTile = ({ label, value, sub, color, highlight }: {
  label: string; value: string | number; sub: string; color: string; highlight?: boolean
}) => (
  <div className={`p-3 border-r border-white/[0.04] last:border-r-0 ${highlight ? 'bg-gradient-to-br from-pink-500/[0.05] to-transparent' : ''}`}>
    <div className="flex items-center gap-1.5 mb-1">
      <TrendingUp className="w-3 h-3" style={{ color }} />
      <p className="text-[9px] uppercase tracking-widest text-white/40 font-bold truncate">{label}</p>
    </div>
    <p className="text-xl font-black tabular-nums" style={{ color: highlight ? color : '#fff' }}>{value}</p>
    <p className="text-[9px] text-white/30 mt-0.5">{sub}</p>
  </div>
)
