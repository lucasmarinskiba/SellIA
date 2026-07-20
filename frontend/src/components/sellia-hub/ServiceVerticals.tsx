'use client'

/**
 * SERVICE VERTICALS
 *
 * Catálogo de industrias de servicios donde SellIA está pre-configurado.
 * Cada vertical = playbook IA específico (skills + legends + canales + pricing).
 */

import { useState, useMemo } from 'react'
import {
  Stethoscope, Building2, Wrench, Scale, Hammer, Sparkles, Activity,
  Camera, Code2, Calendar, Home, ChefHat, Palette, Heart, GraduationCap,
  Filter, Bot, Target, MessageCircle, Crown, ChevronRight, ShoppingBag,
  Pizza, Dog, Car, Hotel
} from 'lucide-react'

// ── Design tokens ──────────────────────────────────────────────────────────────
const T = {
  bgApp:       '#0B0F19',
  bgCard:      '#151B2B',
  border:      '#2A3441',
  textPrim:    '#F3F4F6',
  textSub:     '#9CA3AF',
  cyan:        '#06B6D4',
  emerald:     '#10B981',
  amber:       '#F59E0B',
  glowCyan:    '0 0 22px rgba(6,182,212,0.50)',
  glowEmerald: '0 0 22px rgba(16,185,129,0.50)',
} as const

type VerticalCategory = 'health' | 'trades' | 'pro' | 'realestate' | 'events' | 'creative' | 'tech' | 'personal' | 'education' | 'goods' | 'food' | 'pets' | 'hospitality' | 'auto'
type SalesMotion = 'B2C' | 'B2B' | 'D2C' | 'B2B2C'
type Ticket = 'low' | 'mid' | 'high' | 'enterprise'
type Cycle = 'instant' | 'days' | 'weeks' | 'months'

interface Vertical {
  id: string
  emoji: string
  name: string
  category: VerticalCategory
  motion: SalesMotion
  ticket: Ticket
  cycle: Cycle
  topChannel: string
  pain: string
  iaPlaybook: string
  legendTutor: string
  skillsUsed: string[]
  color: string
  active: number
}

const VERTICALS: Vertical[] = [
  { id: 'v1',  emoji: '🩺', name: 'Consultorio médico',          category: 'health',     motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'WhatsApp + Google Business', pain: 'Agenda vacía + no-shows', iaPlaybook: 'Recordatorios automáticos · re-agenda no-shows · upsell tratamientos', legendTutor: 'Zig Ziglar · asumptive close', skillsUsed: ['Tone-matching médico', 'Local SEO', 'WA Business catalog'], color: '#0ea5e9', active: 47 },
  { id: 'v2',  emoji: '🏥', name: 'Hospital / Sanatorio',         category: 'health',     motion: 'B2C',   ticket: 'high',       cycle: 'weeks',   topChannel: 'Web + WA + portal', pain: 'Coordinar especialidades + cobros obra social', iaPlaybook: 'Triage IA · derivación especialista · gestión OS', legendTutor: 'Bezos · Customer Obsession', skillsUsed: ['Multi-stakeholder', 'OS billing', 'Empatía clínica'], color: '#06b6d4', active: 8 },
  { id: 'v3',  emoji: '🦷', name: 'Odontología',                  category: 'health',     motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + WA', pain: 'Tratamientos largos · abandono mitad', iaPlaybook: 'Follow-up entre sesiones · plan financiado · before/after IG', legendTutor: 'Joe Girard · Law of 250', skillsUsed: ['Long-term care', 'Before/after photo', 'BNPL'], color: '#14b8a6', active: 23 },
  { id: 'v4',  emoji: '🥗', name: 'Nutrición / Kinesio',         category: 'health',     motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + Email', pain: 'Conseguir paquetes mensuales no sesión única', iaPlaybook: 'Onboarding 21d · seguimiento weight/foto · upsell pack 3 meses', legendTutor: 'Mary Kay · reconocimiento', skillsUsed: ['Coaching loops', 'Habit tracking', 'Sub mensual'], color: '#22c55e', active: 34 },
  { id: 'v5',  emoji: '🧠', name: 'Psicología / Terapia',         category: 'health',     motion: 'B2C',   ticket: 'mid',        cycle: 'instant', topChannel: 'Web + WA discreto', pain: 'Discreción + agenda + cobro recurrente', iaPlaybook: 'Booking anónimo · pre-screen IA · billing weekly auto', legendTutor: 'Carnegie · empatía', skillsUsed: ['NVC', 'Anonymized intake', 'Subscription dunning'], color: '#a855f7', active: 28 },
  { id: 'v6',  emoji: '⚡', name: 'Electricista',                category: 'trades',     motion: 'B2C',   ticket: 'mid',        cycle: 'instant', topChannel: 'Google Business + WA', pain: 'Cliente busca urgente · gana el primero', iaPlaybook: 'Respuesta WA en <30seg · cotización con foto · agenda hoy', legendTutor: 'Sam Walton · 10-foot rule', skillsUsed: ['Local SEO', 'Quote-by-photo', 'Speed-to-lead'], color: '#fbbf24', active: 19 },
  { id: 'v7',  emoji: '🔧', name: 'Plomero / Gasista',           category: 'trades',     motion: 'B2C',   ticket: 'low',        cycle: 'instant', topChannel: 'Google Maps + WA', pain: 'Mucha competencia · margen bajo', iaPlaybook: 'Bundle preventivo (rev anual) · garantía 1 año · reviews', legendTutor: 'Ron Popeil · stacking', skillsUsed: ['Bundle pricing', 'Review automation', 'Google Maps SEO'], color: '#f59e0b', active: 32 },
  { id: 'v8',  emoji: '🧱', name: 'Albañil / Construcción',       category: 'trades',     motion: 'B2C',   ticket: 'high',       cycle: 'weeks',   topChannel: 'Referidos + Facebook', pain: 'Presupuestos grandes que no cierran', iaPlaybook: 'Storytelling antes/después · cuotas · garantía obra', legendTutor: 'Ben Feldman · story-sell', skillsUsed: ['Before/after', 'Plan pagos', 'Trust building'], color: '#f97316', active: 14 },
  { id: 'v9',  emoji: '🎨', name: 'Pintor / Decorador',           category: 'trades',     motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + Pinterest', pain: 'Mostrar portfolio + cerrar visual', iaPlaybook: 'Portfolio IG curated · simulador color · cierre por reel', legendTutor: 'Erica Feidner · sell the dream', skillsUsed: ['Visual storytelling', 'Pinterest commerce', 'AR preview'], color: '#ec4899', active: 11 },
  { id: 'v10', emoji: '🔐', name: 'Cerrajero',                    category: 'trades',     motion: 'B2C',   ticket: 'low',        cycle: 'instant', topChannel: 'Google Business · urgente', pain: '24/7 urgencias · ganar al primero', iaPlaybook: 'Geo-targeted ads · respuesta call/WA <15seg · cobro QR onsite', legendTutor: 'Cardone · 10X velocidad', skillsUsed: ['Geofencing ads', 'Mobile payment', 'Speed-to-lead'], color: '#ef4444', active: 7 },
  { id: 'v11', emoji: '⚖️', name: 'Abogado',                     category: 'pro',        motion: 'B2C',   ticket: 'high',       cycle: 'weeks',   topChannel: 'LinkedIn + referidos + Web SEO', pain: 'Lead frío no se convierte · alta valuación', iaPlaybook: 'Consulta inicial gratis · pre-screening IA · NDA auto', legendTutor: 'Voss · tactical empathy', skillsUsed: ['Discovery legal', 'Pre-screen', 'Privacy compliance'], color: '#3b82f6', active: 18 },
  { id: 'v12', emoji: '📊', name: 'Contador / Tax advisor',       category: 'pro',        motion: 'B2B',   ticket: 'mid',        cycle: 'months',  topChannel: 'LinkedIn + Web + email', pain: 'Cliente solo busca en marzo · resto se va', iaPlaybook: 'Suscripción mensual valor agregado · reportes auto · sub mensual', legendTutor: 'Bob Burg · referrals', skillsUsed: ['Subscription mgmt', 'Multi-país tax', 'Retention'], color: '#10b981', active: 22 },
  { id: 'v13', emoji: '🏗', name: 'Ingeniería / Consultoría',     category: 'pro',        motion: 'B2B',   ticket: 'enterprise', cycle: 'months',  topChannel: 'LinkedIn + RFP + email', pain: 'Ciclo largo · multi-decisor · propuestas extensas', iaPlaybook: 'MEDDIC mapping · proposal auto · stakeholder tracking', legendTutor: 'Neil Rackham · SPIN', skillsUsed: ['Enterprise sales', 'RFP automation', 'Champion enablement'], color: '#6366f1', active: 6 },
  { id: 'v14', emoji: '📐', name: 'Arquitectura',                 category: 'pro',        motion: 'B2C',   ticket: 'high',       cycle: 'weeks',   topChannel: 'Instagram + portfolio + ref', pain: 'Vender visión sin obra construida', iaPlaybook: '3D renders auto · portfolio IG · video walkthrough', legendTutor: 'Steve Jobs · demo mastery', skillsUsed: ['3D rendering', 'Portfolio curation', 'Vision selling'], color: '#8b5cf6', active: 9 },
  { id: 'v15', emoji: '💼', name: 'Consultor de negocios',       category: 'pro',        motion: 'B2B',   ticket: 'high',       cycle: 'weeks',   topChannel: 'LinkedIn + content', pain: 'Demostrar valor antes de cobrar', iaPlaybook: 'Free diagnostic · case studies · monthly retainer pitch', legendTutor: 'Hormozi · Grand Slam', skillsUsed: ['Authority content', 'Diagnostic offer', 'Retainer pricing'], color: '#d946ef', active: 12 },
  { id: 'v16', emoji: '🏠', name: 'Corredor inmobiliario',       category: 'realestate', motion: 'B2C',   ticket: 'enterprise', cycle: 'months',  topChannel: 'Instagram + portales + WA', pain: 'Tour físico · cliente decide en 3 meses', iaPlaybook: 'Tour virtual 360° · pre-aprobación crédito · seguimiento 90d', legendTutor: 'Tom Hopkins · #1 real estate USA', skillsUsed: ['Virtual tours', 'Mortgage pre-qual', '90-day nurture'], color: '#0ea5e9', active: 16 },
  { id: 'v17', emoji: '🏢', name: 'Desarrollador inmobiliario',   category: 'realestate', motion: 'B2C',   ticket: 'enterprise', cycle: 'months',  topChannel: 'Web + eventos + ads premium', pain: 'Pre-venta de pozo · convencer sin obra', iaPlaybook: 'CGI render · plan pagos · garantía entrega · tour obra mensual', legendTutor: 'Trump · Art of the Deal', skillsUsed: ['CGI/3D', 'Mortgage plans', 'Construction transparency'], color: '#3b82f6', active: 3 },
  { id: 'v18', emoji: '💍', name: 'Wedding planner',             category: 'events',     motion: 'B2C',   ticket: 'high',       cycle: 'months',  topChannel: 'Instagram + Pinterest + ref', pain: 'Vender experiencia única · venta emocional', iaPlaybook: 'Mood-board personalizado · vendor matching · pago etapas', legendTutor: 'Mary Kay · imagine sign', skillsUsed: ['Mood-board AI', 'Vendor mgmt', 'Milestone billing'], color: '#ec4899', active: 11 },
  { id: 'v19', emoji: '🎉', name: 'Planeador de fiestas',         category: 'events',     motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + WA + TikTok', pain: 'Fechas concurridas · capacity limits', iaPlaybook: 'Booking system real-time · package builder · upsell ad-ons', legendTutor: 'Lori Greiner · live demo', skillsUsed: ['Dynamic pricing', 'Capacity mgmt', 'Live shopping'], color: '#f472b6', active: 14 },
  { id: 'v20', emoji: '🏛', name: 'Centro de eventos',           category: 'events',     motion: 'B2B2C', ticket: 'high',       cycle: 'weeks',   topChannel: 'Web + WhatsApp + portales', pain: 'Calendario lleno o vacío · sin gestión visual', iaPlaybook: 'Calendar pública · cotización auto · contrato e-firma', legendTutor: 'Patterson · scripted excellence', skillsUsed: ['Live calendar', 'Auto-quote', 'E-signature'], color: '#a855f7', active: 8 },
  { id: 'v21', emoji: '🍽', name: 'Catering / Banquetes',         category: 'events',     motion: 'B2B2C', ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + Web', pain: 'Menus tailored + alergias + headcount cambios', iaPlaybook: 'Menu wizard IA · headcount tracker · pago fraccionado', legendTutor: 'Hormozi · value stack', skillsUsed: ['Menu personalization', 'Allergen mgmt', 'Pay in installments'], color: '#f59e0b', active: 19 },
  { id: 'v22', emoji: '🎨', name: 'Diseñador gráfico',           category: 'creative',   motion: 'B2B',   ticket: 'mid',        cycle: 'days',    topChannel: 'LinkedIn + IG + Behance', pain: 'Cliente cambia briefs · scope creep', iaPlaybook: 'Brief IA estructurado · revisiones limitadas · contrato auto', legendTutor: 'Ogilvy · facts over fluff', skillsUsed: ['Brief automation', 'Scope mgmt', 'Contract gen'], color: '#ec4899', active: 24 },
  { id: 'v23', emoji: '👗', name: 'Diseñador de moda',           category: 'creative',   motion: 'D2C',   ticket: 'mid',        cycle: 'instant', topChannel: 'Instagram + TikTok Shop', pain: 'Inventario justo · drops virales sold-out', iaPlaybook: 'Drop calendar · waitlist · live shopping TikTok', legendTutor: 'Estée Lauder · samples + touch', skillsUsed: ['Drop strategy', 'TikTok Shop live', 'Waitlist mgmt'], color: '#f472b6', active: 17 },
  { id: 'v24', emoji: '📷', name: 'Fotógrafo / Videógrafo',       category: 'creative',   motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + portfolio web', pain: 'Reservas estacionales · upsell álbumes', iaPlaybook: 'Mini-sessions · álbum upsell · gallery proof gates', legendTutor: 'Joe Sugarman · curiosity gap', skillsUsed: ['Gallery proofing', 'Print upsell', 'Season pricing'], color: '#06b6d4', active: 13 },
  { id: 'v25', emoji: '🎬', name: 'UGC creator / Content',       category: 'creative',   motion: 'B2B',   ticket: 'mid',        cycle: 'weeks',   topChannel: 'TikTok + IG + LinkedIn', pain: 'Brand deals esporádicos · pricing opaco', iaPlaybook: 'Media kit auto · rate calculator · outreach a marcas', legendTutor: 'Gary Vee · attention', skillsUsed: ['Media kit gen', 'Rate calc', 'Brand outreach'], color: '#fbbf24', active: 21 },
  { id: 'v26', emoji: '💻', name: 'Dev apps / web / sistemas',   category: 'tech',       motion: 'B2B',   ticket: 'high',       cycle: 'weeks',   topChannel: 'LinkedIn + UpWork + ref', pain: 'Discovery largo · cliente no sabe qué quiere', iaPlaybook: 'Spec wizard IA · MVP scoping · sprint billing', legendTutor: 'Rackham · SPIN questions', skillsUsed: ['Spec automation', 'Sprint billing', 'Scope guard'], color: '#a855f7', active: 15 },
  { id: 'v27', emoji: '🛠', name: 'Mantenimiento IT',             category: 'tech',       motion: 'B2B',   ticket: 'mid',        cycle: 'months',  topChannel: 'LinkedIn + Google + ref', pain: 'Convertir tickets sueltos en retainer', iaPlaybook: 'Free audit · monthly SLA · ticket dashboard', legendTutor: 'Chet Holmes · Dream 100', skillsUsed: ['SLA mgmt', 'Ticket retention', 'Audit-as-funnel'], color: '#8b5cf6', active: 9 },
  { id: 'v28', emoji: '🔮', name: 'Tarotismo / Espiritual',      category: 'personal',   motion: 'B2C',   ticket: 'low',        cycle: 'instant', topChannel: 'TikTok + Instagram + WA', pain: 'Audiencia volátil · cobrar online discreto', iaPlaybook: 'Sesión-by-minute · paquetes mensuales · sub Patreon-like', legendTutor: 'Tony Robbins · state mgmt', skillsUsed: ['Pay-per-minute', 'Membership tiers', 'Discrete billing'], color: '#a855f7', active: 31 },
  { id: 'v29', emoji: '👞', name: 'Zapatero / Sastrería',         category: 'personal',   motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Google Business + IG + WA', pain: 'Custom takes time · cobro y entrega', iaPlaybook: 'Custom builder · medidas video · pago anticipo + final', legendTutor: 'Feidner · piano-matching', skillsUsed: ['Custom wizard', 'Video measure', 'Split payment'], color: '#f59e0b', active: 8 },
  { id: 'v30', emoji: '💇', name: 'Peluquería / Estética',       category: 'personal',   motion: 'B2C',   ticket: 'low',        cycle: 'days',    topChannel: 'Instagram + WA + Google', pain: 'No-shows · agenda hueca · upsell tratamientos', iaPlaybook: 'Recordatorio 24h · upsell post-cita · loyalty points', legendTutor: 'Mary Kay · loyalty', skillsUsed: ['Loyalty program', 'Upsell mid-service', 'No-show fee'], color: '#ec4899', active: 27 },
  { id: 'v31', emoji: '🎓', name: 'Academia / Tutor / Coach',    category: 'education',  motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Instagram + TikTok + Kajabi', pain: 'Conseguir cohorte · retención fin de curso', iaPlaybook: 'Funnel lead magnet · cohorte cerrada · alumni community', legendTutor: 'Mandino · 10 scrolls daily', skillsUsed: ['Cohort enrolment', 'Drip lessons', 'Community building'], color: '#06b6d4', active: 19 },
  { id: 'v32', emoji: '🌍', name: 'Profesor de idiomas',         category: 'education',  motion: 'B2C',   ticket: 'low',        cycle: 'days',    topChannel: 'Italki + IG + Preply', pain: 'Cliente compra 4 clases y desaparece', iaPlaybook: 'Diagnóstico nivel · plan 90 días · gamification streak', legendTutor: 'Tony Robbins · state', skillsUsed: ['Habit tracking', 'Subscription', 'Streak gamification'], color: '#0ea5e9', active: 16 },
  { id: 'v33', emoji: '🎵', name: 'Música / Clases instrumento', category: 'education',  motion: 'B2C',   ticket: 'low',        cycle: 'days',    topChannel: 'YouTube + IG + Bandcamp', pain: 'Demostrar avance al alumno · evitar abandono', iaPlaybook: 'Video sesiones · práctica diaria recordatorio · recital online', legendTutor: 'Feidner · sell the dream', skillsUsed: ['Video lessons', 'Practice tracking', 'Recital events'], color: '#a855f7', active: 11 },
  { id: 'v34', emoji: '👕', name: 'Ropa / Indumentaria',         category: 'goods',      motion: 'D2C',   ticket: 'mid',        cycle: 'instant', topChannel: 'IG + TikTok Shop + Shopify', pain: 'Inventario · talles · devoluciones', iaPlaybook: 'Drop calendar · TikTok live shopping · size matcher AI', legendTutor: 'Estée Lauder · samples', skillsUsed: ['Drop strategy', 'Size matcher', 'Return automation'], color: '#ec4899', active: 38 },
  { id: 'v35', emoji: '👟', name: 'Calzado · sneakers',          category: 'goods',      motion: 'D2C',   ticket: 'mid',        cycle: 'instant', topChannel: 'IG + StockX + TikTok', pain: 'Resell market + autenticidad', iaPlaybook: 'Drop alerts · authenticity badge · pre-order waitlist', legendTutor: 'Phil Knight · vision', skillsUsed: ['Drop strategy', 'Authenticity proof', 'Pre-order'], color: '#f59e0b', active: 22 },
  { id: 'v36', emoji: '💎', name: 'Joyería / Bijouterie',        category: 'goods',      motion: 'D2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'IG + Pinterest + WA', pain: 'High-touch · cliente quiere ver/tocar', iaPlaybook: 'Try-on AR · video personalizado · entrega premium', legendTutor: 'Feidner · piano-matching', skillsUsed: ['AR try-on', 'Personalized video', 'Premium delivery'], color: '#fbbf24', active: 14 },
  { id: 'v37', emoji: '📱', name: 'Electrónica · gadgets',       category: 'goods',      motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Amazon + ML + Web propia', pain: 'Comparación precio constante · garantía', iaPlaybook: 'Precio competitivo dinámico · bundle accesorios · post-venta', legendTutor: 'Wheeler · sell the sizzle', skillsUsed: ['Dynamic pricing', 'Bundle pricing', 'Post-sale support'], color: '#3b82f6', active: 26 },
  { id: 'v38', emoji: '🛋', name: 'Muebles / Decoración',         category: 'goods',      motion: 'B2C',   ticket: 'high',       cycle: 'days',    topChannel: 'IG + Pinterest + Showroom', pain: 'Cliente necesita visualizar en su casa', iaPlaybook: 'AR room preview · armado a medida · logística incluida', legendTutor: 'Ogilvy · facts over fluff', skillsUsed: ['AR preview', 'Custom orders', 'Last-mile delivery'], color: '#a855f7', active: 12 },
  { id: 'v39', emoji: '💄', name: 'Cosméticos / Skincare',       category: 'goods',      motion: 'D2C',   ticket: 'low',        cycle: 'instant', topChannel: 'TikTok + IG + Sephora-like', pain: 'Educar uso + suscripción recurrente', iaPlaybook: 'Skin diagnostic AI · sub mensual · UGC creators', legendTutor: 'Mary Kay · samples', skillsUsed: ['Skin diagnostic', 'Subscription', 'UGC outreach'], color: '#f472b6', active: 31 },
  { id: 'v40', emoji: '📚', name: 'Libros / Editorial',          category: 'goods',      motion: 'D2C',   ticket: 'low',        cycle: 'days',    topChannel: 'IG + Amazon KDP + Substack', pain: 'Difícil sostener ventas post-lanzamiento', iaPlaybook: 'Newsletter Substack · book club · serializar', legendTutor: 'Sugarman · curiosity hook', skillsUsed: ['Newsletter mgmt', 'Book club community', 'KDP optimization'], color: '#10b981', active: 8 },
  { id: 'v41', emoji: '🍷', name: 'Vinos / Bebidas',             category: 'goods',      motion: 'D2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'WA + Web + IG + clubs', pain: 'Logística + impuestos por jurisdicción', iaPlaybook: 'Wine club mensual · catas virtuales · split shipment', legendTutor: 'Ben Feldman · story-sell', skillsUsed: ['Subscription box', 'Virtual tastings', 'Multi-país tax'], color: '#dc2626', active: 9 },
  { id: 'v42', emoji: '🌱', name: 'Plantas / Vivero',            category: 'goods',      motion: 'B2C',   ticket: 'low',        cycle: 'days',    topChannel: 'IG + TikTok + Google Maps', pain: 'Logística frágil · supervivencia post-venta', iaPlaybook: 'Care guide auto · garantía reposición · plant ID AI', legendTutor: 'Ron Popeil · stacking bonuses', skillsUsed: ['Plant ID AI', 'Care reminders', 'Replacement guarantee'], color: '#22c55e', active: 13 },
  { id: 'v43', emoji: '🎨', name: 'Artesanías handmade',         category: 'goods',      motion: 'D2C',   ticket: 'low',        cycle: 'days',    topChannel: 'Etsy + IG + ferias', pain: 'Scaling sin perder essence handmade', iaPlaybook: 'Etsy SEO · pre-orders por lote · story per piece', legendTutor: 'Markita Andrews · ask big', skillsUsed: ['Etsy optimization', 'Made-to-order', 'Storytelling pieces'], color: '#f97316', active: 19 },
  { id: 'v44', emoji: '🧸', name: 'Juguetes / Bebés',            category: 'goods',      motion: 'B2C',   ticket: 'low',        cycle: 'instant', topChannel: 'IG + Amazon + ML', pain: 'Estacionalidad fuerte (Navidad/Reyes)', iaPlaybook: 'Pre-Christmas waitlist · gift-bundles · gift card', legendTutor: 'Kevin Harrington · TV-style', skillsUsed: ['Seasonal pricing', 'Gift bundles', 'Wishlist gating'], color: '#fbbf24', active: 15 },
  { id: 'v45', emoji: '🍔', name: 'Restaurante / Bar',           category: 'food',       motion: 'B2C',   ticket: 'low',        cycle: 'instant', topChannel: 'IG + TikTok + Google Maps', pain: 'Mesa vacía hora baja · no-shows reserva', iaPlaybook: 'Happy-hour dynamic · waitlist · upsell digital menu', legendTutor: 'Wheeler · sell the sizzle', skillsUsed: ['Dynamic pricing', 'Reservation mgmt', 'QR menu upsell'], color: '#ef4444', active: 23 },
  { id: 'v46', emoji: '🚚', name: 'Food truck / Delivery',       category: 'food',       motion: 'D2C',   ticket: 'low',        cycle: 'instant', topChannel: 'IG + WA + Rappi/PedidosYa', pain: 'Cambio ubicación + clientes pierdan track', iaPlaybook: 'Geo-broadcast IG stories · WA list location daily', legendTutor: 'Sam Walton · 10-foot rule', skillsUsed: ['Geo broadcasting', 'Daily push', 'Delivery integration'], color: '#f59e0b', active: 11 },
  { id: 'v47', emoji: '🍳', name: 'Comida gourmet / Catering',    category: 'food',       motion: 'B2B2C', ticket: 'mid',        cycle: 'days',    topChannel: 'IG + Web + WhatsApp', pain: 'Menus tailored + headcount cambia', iaPlaybook: 'Menu wizard · allergen mgmt · pago fraccionado', legendTutor: 'Hormozi · value stack', skillsUsed: ['Menu personalization', 'Allergen mgmt', 'Split billing'], color: '#10b981', active: 17 },
  { id: 'v48', emoji: '🥗', name: 'Healthy food / Meal prep',    category: 'food',       motion: 'D2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'IG + Web + WA subscriptions', pain: 'Retención semanal · variedad menú', iaPlaybook: 'Plan semanal IA personalizado · sub semanal · macro tracker', legendTutor: 'Mary Kay · loyalty', skillsUsed: ['Meal planning AI', 'Weekly subscription', 'Macro tracker'], color: '#22c55e', active: 21 },
  { id: 'v49', emoji: '🐶', name: 'Veterinaria',                 category: 'pets',       motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'WA + Google Maps + IG', pain: 'Plan sanitario anual + emergencias', iaPlaybook: 'Plan anual sub · alertas vacunas · tele-vet 24/7', legendTutor: 'Bezos · CX obsession', skillsUsed: ['Subscription health', 'Vaccine reminders', 'Tele-vet'], color: '#06b6d4', active: 14 },
  { id: 'v50', emoji: '🦴', name: 'Pet store · alimento + accs', category: 'pets',       motion: 'D2C',   ticket: 'low',        cycle: 'instant', topChannel: 'IG + Web + WA + Rappi', pain: 'Recurrencia alimento + cliente compra a competencia', iaPlaybook: 'Auto-reorder calculado por peso/edad · cupón fidelidad', legendTutor: 'Cardone · 10X follow-up', skillsUsed: ['Auto-reorder', 'Loyalty points', 'Cross-sell accessorios'], color: '#f59e0b', active: 19 },
  { id: 'v51', emoji: '🐕', name: 'Pet grooming · paseo',         category: 'pets',       motion: 'B2C',   ticket: 'low',        cycle: 'days',    topChannel: 'IG + WA + Google Maps', pain: 'Agenda + no-show + cliente cambia provider', iaPlaybook: 'Recordatorios · plan mensual · before/after IG', legendTutor: 'Joe Girard · referrals', skillsUsed: ['Schedule mgmt', 'Before/after photos', 'Monthly plans'], color: '#a855f7', active: 12 },
  { id: 'v52', emoji: '🏨', name: 'Hotel / Hostería',            category: 'hospitality',motion: 'B2C',   ticket: 'high',       cycle: 'days',    topChannel: 'Booking + Airbnb + Web + IG', pain: 'Vacíos temporada baja · OTA toma 20%', iaPlaybook: 'Direct booking incentive · dynamic pricing · concierge IA', legendTutor: 'Lori Greiner · QVC live', skillsUsed: ['Dynamic pricing', 'Direct booking', 'Concierge bot'], color: '#3b82f6', active: 10 },
  { id: 'v53', emoji: '🏡', name: 'Airbnb / Alquiler temporario',category: 'hospitality',motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Airbnb + Booking + Web', pain: 'Multi-platform sync + checkin remoto', iaPlaybook: 'Sync calendar multi-OTA · checkin auto WA · upsell tours', legendTutor: 'Bezos · CX', skillsUsed: ['OTA sync', 'Remote checkin', 'Tour upsell'], color: '#06b6d4', active: 18 },
  { id: 'v54', emoji: '💆', name: 'Spa / Masajes / Estética',    category: 'hospitality',motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'IG + Google Maps + WA', pain: 'Sesión única · convertir en sub', iaPlaybook: 'Bono 10 sesiones · loyalty tiers · gift cards', legendTutor: 'Mary Kay · recognition', skillsUsed: ['Session packs', 'Loyalty tiers', 'Gift cards'], color: '#ec4899', active: 15 },
  { id: 'v55', emoji: '💪', name: 'Gimnasio / Personal trainer', category: 'hospitality',motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'IG + TikTok + WA + app', pain: 'Churn alto · audiencia frustrada', iaPlaybook: 'Onboarding 30d · habit streak · check-in semanal', legendTutor: 'Tony Robbins · state', skillsUsed: ['Habit tracking', 'Streak gamification', 'Weekly check-in'], color: '#22c55e', active: 24 },
  { id: 'v56', emoji: '🔧', name: 'Mecánico / Taller automotor', category: 'auto',       motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Google Maps + WA + IG', pain: 'Cliente solo viene cuando se rompe', iaPlaybook: 'Plan servicio anual · alertas km · before/after video', legendTutor: 'Patterson · scripted excellence', skillsUsed: ['Service plan sub', 'KM reminders', 'Trust-by-video'], color: '#f59e0b', active: 16 },
  { id: 'v57', emoji: '🚗', name: 'Lavadero / Detailing',        category: 'auto',       motion: 'B2C',   ticket: 'low',        cycle: 'instant', topChannel: 'IG + Google Maps + WA', pain: 'Lluvia mata el día · capacity vacía', iaPlaybook: 'Weather-based promos · sub mensual · gift cards', legendTutor: 'Cardone · velocidad', skillsUsed: ['Weather pricing', 'Subscription', 'Gift cards'], color: '#3b82f6', active: 9 },
  { id: 'v58', emoji: '🚚', name: 'Mudanzas / Logística',        category: 'auto',       motion: 'B2C',   ticket: 'mid',        cycle: 'days',    topChannel: 'Google + IG + Web + WA', pain: 'Estimar precio remoto · variedad volumen', iaPlaybook: 'Quote-by-video · seguro incluido · payment milestones', legendTutor: 'Hormozi · stack value', skillsUsed: ['Video quote', 'Insurance bundle', 'Milestone payment'], color: '#a855f7', active: 7 },
]

const CATEGORY_CONFIG: Record<VerticalCategory, { label: string; emoji: string; color: string; icon: React.ElementType }> = {
  health:      { label: 'Salud',           emoji: '🩺', color: '#0ea5e9', icon: Stethoscope },
  trades:      { label: 'Oficios',         emoji: '🔧', color: '#f59e0b', icon: Hammer },
  pro:         { label: 'Profesionales',   emoji: '⚖️', color: '#6366f1', icon: Scale },
  realestate:  { label: 'Inmobiliario',    emoji: '🏠', color: '#3b82f6', icon: Home },
  events:      { label: 'Eventos',         emoji: '🎉', color: '#ec4899', icon: Calendar },
  creative:    { label: 'Creativos',       emoji: '🎨', color: '#fbbf24', icon: Palette },
  tech:        { label: 'Tech / Apps',     emoji: '💻', color: '#a855f7', icon: Code2 },
  personal:    { label: 'Servicios pers.', emoji: '🔮', color: '#f472b6', icon: Sparkles },
  education:   { label: 'Educación',       emoji: '🎓', color: '#06b6d4', icon: GraduationCap },
  goods:       { label: 'Bienes / Retail', emoji: '🛍', color: '#ec4899', icon: ShoppingBag },
  food:        { label: 'Gastronomía',     emoji: '🍔', color: '#ef4444', icon: Pizza },
  pets:        { label: 'Mascotas',        emoji: '🐶', color: '#84cc16', icon: Dog },
  hospitality: { label: 'Hospitalidad',    emoji: '🏨', color: '#22c55e', icon: Hotel },
  auto:        { label: 'Automotor',       emoji: '🚗', color: '#dc2626', icon: Car },
}

const MOTION_CONFIG: Record<SalesMotion, { color: string; label: string }> = {
  B2C:   { color: '#22c55e', label: 'B2C' },
  B2B:   { color: '#3b82f6', label: 'B2B' },
  D2C:   { color: '#ec4899', label: 'D2C' },
  B2B2C: { color: '#a855f7', label: 'B2B2C' },
}

const TICKET_CONFIG: Record<Ticket, { color: string; label: string }> = {
  low:        { color: '#10b981', label: 'Low ticket' },
  mid:        { color: '#fbbf24', label: 'Mid ticket' },
  high:       { color: '#ef4444', label: 'High ticket' },
  enterprise: { color: '#a855f7', label: 'Enterprise' },
}

const CYCLE_LABEL: Record<Cycle, string> = {
  instant: '⚡ minutos',
  days:    '📅 días',
  weeks:   '🗓 semanas',
  months:  '🌙 meses',
}

const card = (extra?: React.CSSProperties): React.CSSProperties => ({
  background: T.bgCard,
  border: `1px solid ${T.border}`,
  borderRadius: 16,
  ...extra,
})

export default function ServiceVerticals() {
  const [filter, setFilter] = useState<VerticalCategory | 'all'>('all')
  const [selectedId, setSelectedId] = useState<string>(VERTICALS[0].id)

  const filtered = useMemo(
    () => filter === 'all' ? VERTICALS : VERTICALS.filter(v => v.category === filter),
    [filter]
  )

  const stats = useMemo(() => {
    const totalActive = VERTICALS.reduce((s, v) => s + v.active, 0)
    const topVertical = [...VERTICALS].sort((a, b) => b.active - a.active)[0]
    return { total: VERTICALS.length, totalActive, topVertical }
  }, [])

  const categoryCounts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const v of VERTICALS) c[v.category] = (c[v.category] || 0) + 1
    return c
  }, [])

  const selected = VERTICALS.find(v => v.id === selectedId)!
  const cat = CATEGORY_CONFIG[selected.category]

  return (
    <section style={{ background: T.bgApp, border: `1px solid ${T.border}`, borderRadius: 16, overflow: 'hidden', position: 'relative' }}>
      {/* Accent line */}
      <div style={{ height: 2, background: `linear-gradient(90deg, ${T.emerald}, ${T.cyan}, transparent)` }} />

      {/* Header */}
      <div style={{ padding: '20px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(20,184,166,0.12)', border: '1px solid rgba(20,184,166,0.30)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Building2 style={{ width: 20, height: 20, color: '#14b8a6', filter: 'drop-shadow(0 0 8px rgba(20,184,166,0.6))' }} />
          </div>
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 900, color: T.textPrim, textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
              SERVICE <span style={{ color: '#14b8a6' }}>VERTICALS</span>
              <span style={{ color: T.textSub, fontWeight: 400, fontSize: 11, marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· {stats.total} industrias pre-configuradas</span>
              <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, background: 'rgba(16,185,129,0.15)', color: T.emerald, border: `1px solid rgba(16,185,129,0.30)`, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', marginLeft: 8 }}>
                {stats.totalActive} clientes activos
              </span>
            </h2>
            <p style={{ fontSize: 11, color: T.textSub, margin: '4px 0 0' }}>SellIA cambia tono, técnicas, canales y pricing según industria · plug-and-play</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderRadius: 10, background: 'rgba(20,184,166,0.08)', border: '1px solid rgba(20,184,166,0.28)' }}>
          <Crown style={{ width: 12, height: 12, color: '#14b8a6' }} />
          <span style={{ fontSize: 10, color: '#5eead4' }}>Top: <span style={{ fontWeight: 700 }}>{stats.topVertical.name}</span> · {stats.topVertical.active} cuentas</span>
        </div>
      </div>

      {/* Category filter */}
      <div style={{ padding: '12px 24px', borderBottom: `1px solid ${T.border}`, display: 'flex', alignItems: 'center', gap: 8, overflowX: 'auto' }}>
        <Filter style={{ width: 12, height: 12, color: T.textSub, flexShrink: 0 }} />
        <button
          onClick={() => setFilter('all')}
          style={{ flexShrink: 0, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: filter === 'all' ? 'rgba(255,255,255,0.10)' : T.bgCard, border: filter === 'all' ? '1px solid rgba(255,255,255,0.20)' : `1px solid ${T.border}`, color: filter === 'all' ? T.textPrim : T.textSub }}>
          Todas · {VERTICALS.length}
        </button>
        {(Object.keys(CATEGORY_CONFIG) as VerticalCategory[]).map(c => {
          const cfg = CATEGORY_CONFIG[c]
          const Icon = cfg.icon
          const active = filter === c
          return (
            <button
              key={c}
              onClick={() => setFilter(c)}
              style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', borderRadius: 999, fontSize: 10, fontWeight: 700, cursor: 'pointer', background: active ? `${cfg.color}20` : T.bgCard, border: active ? `1px solid ${cfg.color}50` : `1px solid ${T.border}`, color: active ? cfg.color : T.textSub }}
            >
              <Icon style={{ width: 10, height: 10 }} />
              {cfg.label} · {categoryCounts[c] || 0}
            </button>
          )
        })}
      </div>

      {/* Vertical grid */}
      <div style={{ padding: 20, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 10, maxHeight: 640, overflowY: 'auto' }}>
        {filtered.map(v => {
          const motion = MOTION_CONFIG[v.motion]
          const ticket = TICKET_CONFIG[v.ticket]
          const isSelected = selectedId === v.id
          return (
            <button
              key={v.id}
              onClick={() => setSelectedId(v.id)}
              style={{
                textAlign: 'left', background: isSelected ? `${v.color}08` : T.bgCard,
                border: `1px solid ${isSelected ? `${v.color}50` : T.border}`,
                borderRadius: 16, overflow: 'hidden', cursor: 'pointer',
                boxShadow: isSelected ? `0 0 16px ${v.color}15` : 'none',
              }}
            >
              <div style={{ height: 2, background: `linear-gradient(90deg, ${v.color}${isSelected ? 'cc' : '66'}, ${motion.color}55, transparent)` }} />
              <div style={{ padding: '12px 14px' }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, flexShrink: 0, background: `${v.color}15`, border: `1px solid ${v.color}30` }}>
                    {v.emoji}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 13, fontWeight: 700, color: T.textPrim, lineHeight: 1.3, margin: '0 0 3px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.name}</p>
                    <p style={{ fontSize: 10, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: v.color }}>{v.topChannel}</p>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <p style={{ fontSize: 18, fontWeight: 900, fontVariantNumeric: 'tabular-nums', lineHeight: 1, margin: 0, color: v.color, textShadow: `0 0 16px ${v.color}88` }}>{v.active}</p>
                    <p style={{ fontSize: 7, color: T.textSub, textTransform: 'uppercase', fontFamily: 'monospace', margin: '2px 0 0' }}>cuentas</p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                  <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 6, fontFamily: 'monospace', fontWeight: 700, background: `${motion.color}20`, color: motion.color, border: `1px solid ${motion.color}28` }}>
                    {motion.label}
                  </span>
                  <span style={{ fontSize: 9, padding: '2px 7px', borderRadius: 6, fontFamily: 'monospace', fontWeight: 700, background: `${ticket.color}18`, color: ticket.color, border: `1px solid ${ticket.color}25` }}>
                    {ticket.label}
                  </span>
                  <span style={{ fontSize: 9, color: T.textSub }}>{CYCLE_LABEL[v.cycle]}</span>
                </div>

                <p style={{ fontSize: 10, color: T.textSub, lineHeight: 1.4, margin: 0, fontStyle: 'italic', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>"{v.pain}"</p>
              </div>
            </button>
          )
        })}
      </div>

      {/* Selected detail */}
      <div style={{ margin: '0 20px 20px', padding: '20px 24px', borderRadius: 16, background: `linear-gradient(135deg, ${selected.color}0a, transparent)`, border: `1px solid ${selected.color}30`, boxShadow: `0 0 24px ${selected.color}10` }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
          <div style={{ width: 64, height: 64, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 36, flexShrink: 0, background: `${selected.color}18`, border: `2px solid ${selected.color}50`, boxShadow: `0 0 16px ${selected.color}30` }}>
            {selected.emoji}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3 style={{ fontSize: 20, fontWeight: 900, color: T.textPrim, margin: '0 0 6px' }}>{selected.name}</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', fontSize: 10 }}>
              <span style={{ padding: '2px 7px', borderRadius: 6, fontFamily: 'monospace', fontWeight: 700, background: `${MOTION_CONFIG[selected.motion].color}20`, color: MOTION_CONFIG[selected.motion].color }}>
                {MOTION_CONFIG[selected.motion].label}
              </span>
              <span style={{ padding: '2px 7px', borderRadius: 6, fontFamily: 'monospace', fontWeight: 700, background: `${TICKET_CONFIG[selected.ticket].color}18`, color: TICKET_CONFIG[selected.ticket].color }}>
                {TICKET_CONFIG[selected.ticket].label}
              </span>
              <span style={{ color: T.textSub }}>ciclo: {CYCLE_LABEL[selected.cycle]}</span>
              <span style={{ color: T.textSub }}>·</span>
              <span style={{ color: cat.color }}>{cat.label}</span>
            </div>
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontFamily: 'monospace', margin: '0 0 4px' }}>Cuentas activas</p>
            <p style={{ fontSize: 28, fontWeight: 900, fontVariantNumeric: 'tabular-nums', margin: 0, color: selected.color, textShadow: `0 0 22px ${selected.color}aa` }}>{selected.active}</p>
          </div>
        </div>

        {/* Pain + Playbook + Canal */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 12, marginBottom: 12 }}>
          <div style={{ padding: '12px 14px', borderRadius: 12, background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.22)' }}>
            <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#ef4444', fontWeight: 700, margin: '0 0 6px', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Target style={{ width: 10, height: 10 }} /> PAIN COMÚN
            </p>
            <p style={{ fontSize: 12, color: T.textPrim, fontStyle: 'italic', lineHeight: 1.4, margin: 0 }}>"{selected.pain}"</p>
          </div>
          <div style={{ padding: '12px 14px', borderRadius: 12, background: 'rgba(16,185,129,0.05)', border: `1px solid rgba(16,185,129,0.22)` }}>
            <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.emerald, fontWeight: 700, margin: '0 0 6px', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Bot style={{ width: 10, height: 10 }} /> PLAYBOOK IA
            </p>
            <p style={{ fontSize: 12, color: T.textPrim, lineHeight: 1.4, margin: 0 }}>{selected.iaPlaybook}</p>
          </div>
          <div style={{ padding: '12px 14px', borderRadius: 12, background: T.bgApp, border: `1px solid ${T.border}` }}>
            <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: T.textSub, fontWeight: 700, margin: '0 0 6px', display: 'flex', alignItems: 'center', gap: 4 }}>
              <MessageCircle style={{ width: 10, height: 10 }} /> CANAL ESTRELLA
            </p>
            <p style={{ fontSize: 12, fontWeight: 700, color: T.textPrim, lineHeight: 1.4, margin: 0 }}>{selected.topChannel}</p>
          </div>
        </div>

        {/* Skills */}
        <div style={{ padding: '12px 14px', borderRadius: 12, background: 'rgba(168,85,247,0.05)', border: `1px solid rgba(168,85,247,0.22)` }}>
          <p style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#c084fc', fontWeight: 700, margin: '0 0 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Sparkles style={{ width: 10, height: 10 }} /> SKILLS IA QUE SE ACTIVAN
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {selected.skillsUsed.map((s, i) => (
              <span key={i} style={{ fontSize: 10, padding: '5px 10px', borderRadius: 8, background: T.bgApp, border: `1px solid ${T.border}`, color: T.textPrim }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '14px 24px', borderTop: `1px solid ${T.border}`, background: 'rgba(20,184,166,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: T.textSub }}>
          <Wrench style={{ width: 12, height: 12, color: '#14b8a6' }} />
          <span>Cada vertical = playbook plug-and-play · IA aprende del rubro en &lt;48h</span>
        </div>
        <button style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, padding: '8px 16px', borderRadius: 999, background: 'rgba(20,184,166,0.10)', border: '1px solid rgba(20,184,166,0.35)', color: '#14b8a6', fontWeight: 700, cursor: 'pointer' }}>
          <Sparkles style={{ width: 12, height: 12 }} />
          Solicitar vertical nueva
        </button>
      </div>
    </section>
  )
}
