'use client'

import { logger } from '@/lib/logger';
import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { agentsApi, AgentPersonality, AgentConversation, AgentMessage } from '@/lib/agents'
import AutopilotVoiceConfigPanel from './AutopilotVoiceConfig'
import { businessApi } from '@/lib/business'
import Button from '@/components/ui/Button'
import { useRouter } from 'next/navigation'
import {
  MessageSquare, Plus, Trash2, Send, Bot, ArrowLeft,
  Sparkles, Loader2, User, Zap, Search, SlidersHorizontal,
  ChevronRight, Star, Crown, Target, Handshake, Package,
  Shield, TrendingUp, CheckCircle2, AlertCircle, Play,
  DollarSign, Award, Lightbulb, ArrowRight, X
} from 'lucide-react'

// ─── Pipeline Stage Data ───────────────────────────────────────────────────────
const PIPELINE_STAGES = [
  { id: 'prospecting', emoji: '🎯', label: 'Prospección', methodology: 'Gary Vee', color: '#3b82f6', description: 'Captá prospectos con contenido orgánico y outreach frío estratégico.', sample: 'Dame 10 mensajes de prospección para dueños de PyMEs en LinkedIn que no me conozcan...' },
  { id: 'qualifying', emoji: '🔍', label: 'Calificación', methodology: 'BANT+MEDDIC', color: '#6366f1', description: 'Filtrá leads calificados usando los marcos BANT y MEDDIC.', sample: 'Este lead dice que tiene presupuesto pero no sé si tiene autoridad. Ayúdame a calificarlo...' },
  { id: 'nurturing', emoji: '🌱', label: 'Nutrición', methodology: 'Email Sequences', color: '#14b8a6', description: 'Convertí leads fríos en calientes con secuencias de valor.', sample: 'Tengo un lead tibio que no responde hace 2 semanas. Dame una secuencia de 5 toques...' },
  { id: 'discovery', emoji: '💡', label: 'Diagnóstico', methodology: 'SPIN Selling', color: '#06b6d4', description: 'Descubrí la necesidad real del cliente con preguntas SPIN.', sample: 'Tengo una llamada de discovery mañana con un e-commerce de moda. Dame las preguntas SPIN...' },
  { id: 'proposal', emoji: '📦', label: 'Propuesta', methodology: 'Hormozi Grand Slam', color: '#f59e0b', description: 'Construí una oferta irresistible con la Value Equation de Hormozi.', sample: 'Necesito armar una propuesta para un cliente que vende cursos online. Precio: $297...' },
  { id: 'objection', emoji: '🛡️', label: 'Objeciones', methodology: 'Belfort + Cialdini', color: '#f97316', description: 'Manejá cualquier objeción con el sistema de Jordan Belfort.', sample: 'El cliente dice "es muy caro" y "voy a pensarlo". Dame las respuestas exactas...' },
  { id: 'closing', emoji: '🤝', label: 'Cierre', methodology: 'Ziglar + Cardone', color: '#22c55e', description: 'Cerrá la venta con técnicas probadas de Ziglar y Cardone.', sample: 'El cliente está listo pero dice que necesita hablar con su socio. ¿Cómo cierro hoy?...' },
  { id: 'onboarding', emoji: '🚀', label: 'Bienvenida', methodology: 'Bezos CX', color: '#10b981', description: 'Generá la primera victoria del cliente en las primeras 48hs.', sample: 'Mi cliente acaba de pagar $500. Dame el protocolo de bienvenida perfecto...' },
  { id: 'retention', emoji: '💎', label: 'Retención', methodology: 'RFM + LTV', color: '#a855f7', description: 'Maximizá el LTV con upsells y programas de lealtad.', sample: 'Tengo 20 clientes que compraron hace 3 meses y no volvieron. ¿Cómo los reactivo?...' },
]

// ─── Negotiation Expert Data ───────────────────────────────────────────────────
const NEGOTIATION_EXPERTS = [
  {
    id: 'chris-voss', emoji: '🎯', name: 'Chris Voss', title: 'FBI Master Negotiator',
    color: '#ef4444', methodology: 'Never Split the Difference',
    tagline: 'Tactical empathy y calibrated questions para negociaciones de alto riesgo.',
    techniques: ['Tactical Empathy', 'Mirroring', 'Labeling', 'Accusation Audit', 'Black Swan'],
    opening: '"Parece que esto es importante para vos..." — abre el espacio emocional',
    best_for: ['Precios y contratos', 'Negociaciones tensas', 'Cuando el otro lado es agresivo'],
  },
  {
    id: 'roger-fisher', emoji: '🏛️', name: 'Roger Fisher', title: 'Harvard Negotiation Project',
    color: '#3b82f6', methodology: 'Getting to Yes — BATNA',
    tagline: 'Separar personas de problemas. Centrarse en intereses, no posiciones.',
    techniques: ['BATNA', 'Separar personas de problemas', 'Criterios objetivos', 'Opciones de mutuo beneficio'],
    opening: '"¿Cuál es el interés detrás de esa posición?" — va a la raíz',
    best_for: ['Negociaciones colaborativas', 'Contratos complejos', 'Cuando querés una relación larga'],
  },
  {
    id: 'herb-cohen', emoji: '⚡', name: 'Herb Cohen', title: 'Power Negotiation',
    color: '#f59e0b', methodology: 'You Can Negotiate Anything',
    tagline: 'Todo es negociable. Usá el tiempo, la información y el poder percibido.',
    techniques: ['Tiempo como arma', 'Información es poder', 'Poder percibido', 'Bogey tactic', 'Good cop / Bad cop'],
    opening: '"Me encanta el producto pero mi presupuesto es limitado..." — crea presión',
    best_for: ['Compras grandes', 'Negociar salarios', 'Situaciones donde tenés menos poder'],
  },
  {
    id: 'stuart-diamond', emoji: '❤️', name: 'Stuart Diamond', title: 'Wharton Business School',
    color: '#ec4899', methodology: 'Getting More — Emotional Intelligence',
    tagline: 'Las emociones, percepciones y los estándares del otro lado son la clave.',
    techniques: ['Mapear el otro lado', 'Usar sus estándares', 'Imágenes y emociones', 'Pequeñas concesiones'],
    opening: '"Entiendo que para vos esto es importante porque..." — usa sus criterios',
    best_for: ['Negociaciones culturales', 'Equipos y colaboraciones', 'Cuando el factor emocional es alto'],
  },
  {
    id: 'william-ury', emoji: '🌉', name: 'William Ury', title: 'Harvard / Getting Past No',
    color: '#8b5cf6', methodology: 'Golden Bridge Strategy',
    tagline: 'Construí un puente dorado para que el otro lado pueda decir que sí con dignidad.',
    techniques: ['Golden Bridge', 'Balcón (pausa)', 'Replantear', 'Construir puentes de salida', 'BATNA alternativo'],
    opening: '"¿Cómo podríamos hacer que esto funcione para los dos?" — invita a colaborar',
    best_for: ['Negociaciones bloqueadas', 'Mediación de conflictos', 'Cuando el otro dice que no'],
  },
]

/* ============================================================
   DASHBOARD AGENTES — Modern AI Agent Platform
   ============================================================ */

function AgentAvatar({ emoji, color, size = 48 }: { emoji: string; color: string; size?: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-2xl text-2xl shrink-0 relative"
      style={{
        width: size,
        height: size,
        background: `${color}18`,
        border: `1.5px solid ${color}35`,
        boxShadow: `0 0 20px ${color}15`,
      }}
    >
      {emoji}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3">
      <div className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 rounded-full bg-white/30 animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  )
}

const categories = [
  {
    id: 'legends',
    title: '🏆 Leyendas del Negocio & Ventas',
    color: 'text-yellow-400',
    slugs: ['donald-trump','warren-buffett','steve-jobs','jeff-bezos','napoleon-hill','dale-carnegie','robert-cialdini','simon-sinek'],
    gradient: 'from-yellow-400/10 to-transparent',
  },
  {
    id: 'women',
    title: '👑 Mujeres Líderes & Emprendedoras',
    color: 'text-pink-400',
    slugs: ['oprah-winfrey','sara-blakely','barbara-corcoran','mel-robbins','brene-brown','arianna-huffington','sophia-amoruso','marie-forleo'],
    gradient: 'from-pink-400/10 to-transparent',
  },
  {
    id: 'sales-direct',
    title: '🤝 Ventas Directas & Cierre',
    color: 'text-blue-400',
    slugs: ['b2b-closer','consultative-seller','account-executive','jordan-belfort'],
    gradient: 'from-blue-400/10 to-transparent',
  },
  {
    id: 'sales-mgmt',
    title: '👔 Gestión & Liderazgo de Ventas',
    color: 'text-red-400',
    slugs: ['sales-manager','account-manager','sales-ops'],
    gradient: 'from-red-400/10 to-transparent',
  },
  {
    id: 'operations',
    title: '⚙️ Operaciones, CRM & Automatización',
    color: 'text-slate-400',
    slugs: ['org-designer','crm-specialist','workflow-automator'],
    gradient: 'from-slate-400/10 to-transparent',
  },
  {
    id: 'analytics',
    title: '📊 Analytics, KPIs & Datos',
    color: 'text-teal-400',
    slugs: ['kpi-tracker','data-analyst','reporting-specialist','revenue-ops'],
    gradient: 'from-teal-400/10 to-transparent',
  },
  {
    id: 'finance',
    title: '💵 Finanzas & Funding',
    color: 'text-green-400',
    slugs: ['sales-finance','funding-advisor'],
    gradient: 'from-green-400/10 to-transparent',
  },
  {
    id: 'pipeline',
    title: '🚰 Pipeline & Funnel',
    color: 'text-orange-400',
    slugs: ['pipeline-architect','funnel-optimizer','russell-brunson'],
    gradient: 'from-orange-400/10 to-transparent',
  },
  {
    id: 'strategy',
    title: '🚀 Estrategia & Marketing',
    color: 'text-brand-orange',
    slugs: ['alex-hormozi','russell-brunson','dan-kennedy','seth-godin','gary-vee','market-researcher','competitive-intel','niche-domination'],
    gradient: 'from-brand-orange/10 to-transparent',
  },
  {
    id: 'social',
    title: '📱 Redes Sociales, Ads & Video',
    color: 'text-pink-500',
    slugs: ['social-media-strategist','facebook-ads-specialist','google-ads-specialist','tiktok-ads-specialist','andy-badillo','beltran-briones','mateo-maffia','borrego','mati-boxx','mrbeast','khaby-lame','willie-salim','tiktok-affiliate-specialist','tiktok-storytelling','jurgen-klaric','tiktok-voice-coach','tiktok-dm-closer','tiktok-high-ticket','carlos-munoz','tiktok-influence-engineer','tiktok-ugc-strategist','tiktok-engagement-hacker','pablito-paez','elon-musk','mark-cuban','richard-branson','casey-neistat','marques-brownlee','zach-king','eric-thomas','logan-paul','iman-gadzhi','cody-sanchez','sofia-macias','fede-vigevani','sahil-bloom','justin-welsh','nicolas-cole','dharmesh-shah','simeon-panda','chloe-ting','andrew-huberman','ryan-serhant','graham-stephan','tom-ferry','esther-perel','matthew-hussey','vishen-lakhiani','taylor-swift','bad-bunny','bizarrap','gordon-ramsay','nick-digiovanni','joshua-weissman','emma-chamberlain','patrick-ta','bretman-rock','peter-mckinnon','zhc','bob-ross','legal-angel','legal-defense','legal-business','dr-mike','kati-morton','dr-berg','sal-khan','ali-abdaal','crash-course','zach-the-plumber','builder-mike','electric-dave','linus-tech-tips','mrwhosetheboss','ijustine','andrei-jikh','mark-tilbury','humphrey-yang','drew-afualo','spencer-x','tabitha-brown','charli-damelio','addison-rae','bella-poarch','chris-bumstead','ronnie-coleman','athlean-x','lebron-james','ronaldo','serena-williams','bear-grylls','alex-honnold','david-goggins','wim-hof','yoga-with-adriene','dr-joe-dispenza','matty-matheson','alison-roman','babish','adam-ragus','drew-binsky','lost-leblanc','evan-e-rat','kara-and-nate','the-dad-lab','jordan-page','matt-davella','mr-kate','video-marketing','ad-copywriter','viral-growth','retargeting-specialist'],
    gradient: 'from-pink-500/10 to-transparent',
  },
  {
    id: 'professions',
    title: '⚒️ Profesiones & Oficios',
    color: 'text-emerald-400',
    slugs: ['electrician-pro','plumber-pro','mason-pro','carpenter-pro','mechanic-pro','hvac-pro','welder-pro','landscaper-pro','psychologist-pro','tarot-reader','life-coach','nutritionist-pro','physiotherapist-pro','astrologer','reiki-master','meditation-coach','lawyer-pro','accountant-pro','economist-pro','tax-advisor','notary-pro','financial-planner','insurance-broker','auditor-pro','developer-pro','civil-engineer','mechanical-engineer','electrical-engineer','data-scientist','physicist-pro','chemist-pro','biologist-pro','entrepreneur-pro','merchant-pro','hr-specialist','project-manager','realtor-pro','chef-pro','architect-pro','teacher-pro','veterinarian-pro','dentist-pro','nurse-pro','pharmacist-pro','photographer-pro','graphic-designer','musician-pro','writer-pro','seo-specialist','copywriter-pro','ux-ui-designer','community-manager-pro','business-consultant','event-planner','makeup-artist','hair-stylist','pilot-pro','translator-pro','security-guard-pro','cleaning-pro','pediatrician-pro','cardiologist-pro','dermatologist-pro','ophthalmologist-pro','orthopedic-pro','neurologist-pro','psychiatrist-pro','oncologist-pro','gynecologist-pro','surgeon-pro','tailor-pro','baker-pro','locksmith-pro','pest-control-pro','moving-pro','interior-designer','fashion-designer','jeweler-pro','optician-pro','tattoo-artist','agronomist-pro','veterinarian-livestock','winemaker','beekeeper','fisherman-pro','forestry-pro','hydroponics-pro','organic-farmer','agtech-specialist','food-safety-inspector','agricultural-engineer','rural-development','truck-driver-pro','logistics-coordinator','warehouse-manager','supply-chain-analyst','dispatcher-pro','maritime-captain','flight-attendant','train-conductor','uber-driver-pro','delivery-pro','port-operator','customs-broker','hotel-manager','chef-de-cuisine','sommelier','bartender-pro','concierge-pro','tour-guide','travel-agent','cruise-director','spa-therapist','front-desk','housekeeping-manager','revenue-manager','university-professor','kindergarten-teacher','special-ed-teacher','corporate-trainer','language-teacher','stem-educator','principal','school-counselor','educational-psychologist','online-course-creator','tutor-pro','montessori-teacher','public-administrator','urban-planner','social-worker','police-officer','firefighter-pro','paramedic-pro','diplomat-pro','public-prosecutor','judge-pro','customs-officer','immigration-officer','election-official','research-scientist','lab-technician','statistician-pro','environmental-scientist','oceanographer','meteorologist','archaeologist','anthropologist','sociologist','political-scientist','econometrician','data-engineer','film-director','video-editor','sound-engineer','radio-host','podcaster-pro','influencer-pro','public-relations','crisis-communicator','brand-strategist','media-buyer','tv-producer','documentary-filmmaker','sports-coach','personal-trainer','nutrition-coach','sports-psychologist','athletic-trainer','referee-pro','sports-agent','stadium-manager','esports-coach','yoga-instructor','pilates-instructor','swim-coach','ai-engineer','blockchain-developer','vr-ar-developer','iot-specialist','robotics-engineer','drone-pilot','3d-printing-specialist','cybersecurity-analyst','cloud-architect','devops-engineer','sre-engineer','prompt-engineer','investment-banker','venture-capitalist','crypto-trader','forex-trader','private-banker','mortgage-broker','credit-analyst','risk-manager','actuary-pro','fintech-product-manager','payment-processor','wealth-advisor','art-curator','museum-director','gallery-owner','art-appraiser','restorer-pro','cultural-manager','librarian-pro','archivist-pro','composer-pro','conductor-pro','dance-instructor','acting-coach','quantity-surveyor','construction-manager','site-supervisor','surveyor-pro','demolition-expert','crane-operator','flooring-specialist','roofing-contractor','glass-glazier','tiler-pro','property-developer','real-estate-investor','solar-panel-installer','wind-turbine-tech','energy-auditor','carbon-consultant','environmental-consultant','waste-manager','recycling-specialist','water-treatment','oil-gas-engineer','nuclear-engineer','geologist-pro','mining-engineer','production-manager','quality-control','lean-manufacturing','industrial-designer','factory-manager','assembly-supervisor','cnc-operator','maintenance-tech','safety-officer','procurement-specialist','perfumer','chocolatier','barista-pro','sommelier-beer','florist-pro','calligrapher','illustrator-pro','animator-pro','set-designer','costume-designer','puppeteer','magician-pro','radiologist-pro','pathologist-pro','immunologist-pro','endocrinologist-pro','rheumatologist-pro','geneticist-pro','toxicologist-pro','epidemiologist-pro','microbiologist-pro','biomedical-engineer','speech-therapist','occupational-therapist','astronaut-trainer','handwriting-expert','bomb-disposal','dog-trainer','falconer','genealogist','gemologist','handwriting-analyst','mystery-shopper','stand-up-comedian','voice-actor','wedding-planner'],
    gradient: 'from-emerald-400/10 to-transparent',
  },
  {
    id: 'ecommerce',
    title: '🏪 E-commerce & Marketplaces',
    color: 'text-amber-500',
    slugs: ['marketplace-specialist','seo-content','cart-recovery','pricing-optimizer','upsell-specialist'],
    gradient: 'from-amber-500/10 to-transparent',
  },
  {
    id: 'mindset',
    title: '⚡ Mindset & Performance',
    color: 'text-brand-teal',
    slugs: ['tony-robbins','grant-cardone','patrick-bet-david','jordan-belfort'],
    gradient: 'from-brand-teal/10 to-transparent',
  },
  {
    id: 'conversion',
    title: '🎯 Conversión & Funnel',
    color: 'text-brand-violet',
    slugs: ['lead-magnet-creator','email-sequencer','social-closer','appointment-setter','follow-up-bot','objection-crusher','re-engagement','retention-specialist'],
    gradient: 'from-brand-violet/10 to-transparent',
  },
  {
    id: 'audience',
    title: '🧑‍🎨 Audiencia & Comunidad',
    color: 'text-blue-500',
    slugs: ['customer-avatar','community-manager','influencer-marketing','affiliate-marketing'],
    gradient: 'from-blue-500/10 to-transparent',
  },
  {
    id: 'autopilot',
    title: '💬 Agentes de Ventas (Auto-piloto)',
    color: 'text-brand-orange-light',
    slugs: ['captador','cualificador','vendedor','post-venta'],
    gradient: 'from-amber-500/10 to-transparent',
    compact: true,
  },
]

export default function AgentesPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [personalities, setPersonalities] = useState<AgentPersonality[]>([])
  const [conversations, setConversations] = useState<AgentConversation[]>([])
  const [activeConversation, setActiveConversation] = useState<AgentConversation | null>(null)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const [businesses, setBusinesses] = useState<any[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<string>('')
  const [view, setView] = useState<'grid' | 'chat'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [mounted, setMounted] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Section state from URL
  const section = searchParams?.get('section') || 'agents'
  const initialStage = searchParams?.get('stage') || null
  const initialExpert = searchParams?.get('expert') || null
  const initialProduct = searchParams?.get('product') || null

  const setSection = (s: string) => {
    router.push(s === 'agents' ? '/dashboard/agentes' : `/dashboard/agentes?section=${s}`)
  }

  useEffect(() => { setMounted(true) }, [])

  // Load initial data
  useEffect(() => {
    const load = async () => {
      try {
        const [pers, convs, bizs] = await Promise.all([
          agentsApi.getPersonalities(),
          agentsApi.getConversations(),
          businessApi.list(),
        ])
        setPersonalities(pers)
        setConversations(convs)
        setBusinesses(bizs)
        if (bizs.length > 0) setSelectedBusinessId(bizs[0].id)

        const convId = searchParams?.get('conversation')
        if (convId) {
          const conv = await agentsApi.getConversation(convId)
          setActiveConversation(conv)
          setMessages(conv.messages || [])
          setView('chat')
        }
      } catch (e) {
        logger.error(String(e))
      } finally {
        setInitialLoading(false)
      }
    }
    load()
  }, [searchParams])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const startConversation = async (personality: AgentPersonality) => {
    if (!selectedBusinessId) {
      alert('Primero creá un negocio en la sección Negocios')
      return
    }
    try {
      setLoading(true)
      const conv = await agentsApi.createConversation({
        business_id: selectedBusinessId,
        personality_id: personality.id,
        title: `Chat con ${personality.name}`,
      })
      setConversations(prev => [conv, ...prev])
      setActiveConversation(conv)
      setMessages([])
      setView('chat')
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Error al crear conversación')
    } finally {
      setLoading(false)
    }
  }

  const openConversation = async (conv: AgentConversation) => {
    try {
      setLoading(true)
      const full = await agentsApi.getConversation(conv.id)
      setActiveConversation(full)
      setMessages(full.messages || [])
      setView('chat')
    } catch (e) {
      logger.error(String(e))
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || !activeConversation || loading) return
    const content = input.trim()
    setInput('')
    setLoading(true)

    const tempUserMsg: AgentMessage = {
      id: 'temp',
      conversation_id: activeConversation.id,
      role: 'user',
      content,
      model_used: null,
      tokens_used: null,
      extra_data: {},
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMsg])

    try {
      const res = await agentsApi.sendMessage(activeConversation.id, content)
      setMessages(prev => [...prev.filter(m => m.id !== 'temp'), tempUserMsg, res.message])
    } catch (e: any) {
      const errMsg = e.response?.data?.detail || 'Error al enviar mensaje'
      setMessages(prev => [
        ...prev.filter(m => m.id !== 'temp'),
        tempUserMsg,
        {
          id: 'error',
          conversation_id: activeConversation.id,
          role: 'assistant',
          content: `❌ ${errMsg}`,
          model_used: null,
          tokens_used: null,
          extra_data: {},
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const deleteConv = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('¿Eliminar esta conversación?')) return
    try {
      await agentsApi.deleteConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))
      if (activeConversation?.id === id) {
        setActiveConversation(null)
        setMessages([])
        setView('grid')
      }
    } catch (e) {
      logger.error(String(e))
    }
  }

  const filteredPersonalities = personalities.filter(p => {
    const matchesSearch = !searchQuery ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.tagline.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' ||
      categories.find(c => c.id === selectedCategory)?.slugs.includes(p.slug)
    return matchesSearch && matchesCategory
  })

  if (initialLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-12 h-12 rounded-2xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center animate-pulse">
              <Bot className="w-6 h-6 text-brand-orange" />
            </div>
            <div className="absolute inset-0 rounded-2xl bg-brand-orange/20 blur-xl animate-pulse" />
          </div>
          <p className="text-sm text-white/40">Despertando agentes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex overflow-hidden">
      {/* ===== Sidebar ===== */}
      <div className={`w-80 border-r border-white/5 bg-[#070a14] flex flex-col shrink-0 transition-all duration-300 ${mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`}>
        {/* Sidebar header */}
        <div className="p-5 border-b border-white/5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-brand-orange" />
            </div>
            <h2 className="text-sm font-semibold text-white/90">Conversaciones</h2>
          </div>
          <button
            onClick={() => { setView('grid'); setActiveConversation(null); setMessages([]) }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-orange/10 hover:bg-brand-orange/20 border border-brand-orange/20 text-brand-orange text-sm font-medium rounded-xl transition-all active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            Nueva conversación
          </button>
        </div>

        {/* Conversations list */}
        <div className="flex-1 overflow-y-auto no-scrollbar p-3 space-y-1.5">
          {conversations.length === 0 && (
            <div className="text-center py-10 px-4">
              <div className="w-14 h-14 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mx-auto mb-3">
                <MessageSquare className="w-6 h-6 text-white/10" />
              </div>
              <p className="text-xs text-white/25 font-medium">No hay conversaciones aún</p>
              <p className="text-xs text-white/15 mt-1">Seleccioná un agente para empezar</p>
            </div>
          )}

          {conversations.map(conv => {
            const personality = personalities.find(p => p.id === conv.personality_id)
            const isActive = activeConversation?.id === conv.id
            return (
              <button
                key={conv.id}
                onClick={() => openConversation(conv)}
                className={`w-full text-left p-3 rounded-xl transition-all group relative ${
                  isActive
                    ? 'bg-white/[0.08] border border-white/10 shadow-lg shadow-black/20'
                    : 'hover:bg-white/[0.04] border border-transparent'
                }`}
              >
                <div className="flex items-start gap-3">
                  {personality ? (
                    <AgentAvatar emoji={personality.emoji} color={personality.color} size={36} />
                  ) : (
                    <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center text-sm">🤖</div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white/90 truncate">{conv.title || 'Sin título'}</p>
                    <p className="text-[11px] text-white/30 mt-0.5 flex items-center gap-1">
                      {personality?.name || 'Agente'}
                      <span className="w-0.5 h-0.5 rounded-full bg-white/20" />
                      {conv.message_count} mensajes
                    </p>
                  </div>
                  {isActive && <div className="w-1.5 h-1.5 rounded-full bg-brand-orange mt-2" />}
                </div>
                <button
                  onClick={e => deleteConv(conv.id, e)}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/10 hover:text-red-400 text-white/20 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </button>
            )
          })}
        </div>

        {/* Sidebar footer */}
        <div className="p-4 border-t border-white/5">
          <div className="glass-card p-3 bg-gradient-to-br from-brand-night/50 to-transparent">
            <div className="flex items-center gap-2 text-xs text-white/40">
              <Zap className="w-3.5 h-3.5 text-brand-orange" />
              <span>Usá tu API key de OpenAI para chats ilimitados</span>
            </div>
          </div>
        </div>
      </div>

      {/* ===== Main Content ===== */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#060812]">
        {view === 'grid' ? (
          /* ===== Agent Grid / Sections ===== */
          <div className="flex-1 overflow-y-auto no-scrollbar">

            {/* ── Section Tab Bar ── */}
            <div className="sticky top-0 z-20 bg-[#060812]/95 backdrop-blur-sm border-b border-white/[0.06] px-6">
              <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-3">
                {[
                  { id: 'agents', icon: Bot, label: '500+ Agentes', color: 'text-brand-orange' },
                  { id: 'pipeline', icon: Target, label: 'Pipeline IA', color: 'text-emerald-400' },
                  { id: 'negotiate', icon: Handshake, label: 'Negociación', color: 'text-blue-400' },
                  { id: 'offer', icon: Package, label: 'Offer Builder', color: 'text-amber-400' },
                ].map(tab => {
                  const isActive = section === tab.id
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setSection(tab.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                        isActive
                          ? 'bg-white/10 border border-white/15 text-white'
                          : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                      }`}
                    >
                      <tab.icon className={`w-4 h-4 ${isActive ? tab.color : ''}`} />
                      {tab.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* ── Pipeline Section ── */}
            {section === 'pipeline' && (
              <PipelineSection
                initialStage={initialStage}
                onActivate={(stageId) => {
                  const p = personalities.find(x => x.slug === stageId + '-agent' || x.slug === stageId)
                  if (p) startConversation(p)
                  else {
                    setInput(`Actuá como el agente especializado en la etapa de ${PIPELINE_STAGES.find(s => s.id === stageId)?.label}. ${PIPELINE_STAGES.find(s => s.id === stageId)?.sample}`)
                    const fallback = personalities[0]
                    if (fallback) startConversation(fallback)
                  }
                }}
              />
            )}

            {/* ── Negotiation Section ── */}
            {section === 'negotiate' && (
              <NegotiationSection
                initialExpert={initialExpert}
                onActivate={(expertId, situation) => {
                  const expert = NEGOTIATION_EXPERTS.find(e => e.id === expertId)
                  if (!expert) return
                  setInput(`Actuá como ${expert.name} usando ${expert.methodology}. ${situation ? `Situación: ${situation}` : 'Ayúdame a preparar una negociación.'}`)
                  const p = personalities.find(x => x.slug === expertId) || personalities[0]
                  if (p) startConversation(p)
                }}
              />
            )}

            {/* ── Offer Builder Section ── */}
            {section === 'offer' && (
              <OfferBuilderSection
                initialProduct={initialProduct}
                onActivate={(productName, audience, price, pains) => {
                  setInput(`Actuá como Alex Hormozi y construí una Grand Slam Offer para: Producto: "${productName}", Audiencia: "${audience}", Precio objetivo: $${price}. Puntos de dolor: ${pains}. Quiero el Value Stack completo, garantía y framing de precio.`)
                  const p = personalities.find(x => x.slug === 'alex-hormozi') || personalities[0]
                  if (p) startConversation(p)
                }}
              />
            )}

            {/* ── Default Agent Grid ── */}
            {section === 'agents' && <>
            {/* Hero banner */}
            <div className="relative overflow-hidden border-b border-white/5">
              <div className="absolute inset-0 bg-gradient-to-r from-brand-orange/5 via-transparent to-brand-violet/5" />
              <div className="absolute top-0 right-0 w-[400px] h-[200px] bg-brand-orange/5 blur-[100px] pointer-events-none" />
              <div className="relative max-w-6xl mx-auto px-6 py-8">
                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="flex -space-x-2">
                        {['🎯','🐺','⚡','🚀','💼','🎙️','👑','💎'].map((emoji, i) => (
                          <div key={i} className="w-7 h-7 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center text-sm z-[1]">
                            {emoji}
                          </div>
                        ))}
                      </div>
                      <span className="text-xs text-white/30 font-medium ml-1">500+ expertos disponibles</span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">
                      Tu Equipo de <span className="gradient-text">Expertos IA</span> 🤖
                    </h1>
                    <p className="text-sm text-white/40 max-w-lg">
                      Chateá con agentes especializados basados en los mejores estrategas de marketing y ventas del mundo.
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    {/* Search */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        placeholder="Buscar agente..."
                        className="pl-9 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange/30 w-48 transition-all"
                      />
                    </div>
                    {/* Category Filter */}
                    <select
                      value={selectedCategory}
                      onChange={e => setSelectedCategory(e.target.value)}
                      className="px-3 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white/80 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                    >
                      <option value="all" className="bg-[#0A0E1A]">Todas las categorías</option>
                      {categories.map(cat => (
                        <option key={cat.id} value={cat.id} className="bg-[#0A0E1A]">{cat.title}</option>
                      ))}
                    </select>
                    {/* Auto-pilot voice config */}
                    {businesses.length > 0 && selectedBusinessId && (
                      <AutopilotVoiceConfigPanel
                        personalities={personalities}
                        businessId={selectedBusinessId}
                      />
                    )}
                    {/* Business selector */}
                    {businesses.length > 0 && (
                      <select
                        value={selectedBusinessId}
                        onChange={e => setSelectedBusinessId(e.target.value)}
                        className="px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white/80 focus:outline-none focus:ring-2 focus:ring-brand-orange/20"
                      >
                        {businesses.map(b => (
                          <option key={b.id} value={b.id} className="bg-[#0A0E1A]">{b.name}</option>
                        ))}
                      </select>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Categories */}
            <div className="max-w-6xl mx-auto px-6 py-8 space-y-10">
              {categories.map((cat, ci) => {
                const catAgents = filteredPersonalities.filter(p => cat.slugs.includes(p.slug))
                if (catAgents.length === 0) return null
                return (
                  <section key={cat.id} className={`transition-all duration-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`} style={{ transitionDelay: `${ci * 100 + 200}ms` }}>
                    <div className="flex items-center gap-3 mb-5">
                      <div className={`h-px flex-1 bg-gradient-to-r ${cat.gradient}`} />
                      <h2 className={`text-xs font-semibold ${cat.color} uppercase tracking-widest whitespace-nowrap`}>{cat.title}</h2>
                      <div className={`h-px flex-1 bg-gradient-to-l ${cat.gradient}`} />
                    </div>
                    <div className={`grid gap-4 ${cat.compact ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'}`}>
                      {catAgents.map(p => (
                        <AgentCard
                          key={p.id}
                          personality={p}
                          onClick={() => startConversation(p)}
                          loading={loading}
                          compact={cat.compact}
                        />
                      ))}
                    </div>
                  </section>
                )
              })}

              {searchQuery && filteredPersonalities.length === 0 && (
                <div className="text-center py-20">
                  <Search className="w-12 h-12 text-white/10 mx-auto mb-3" />
                  <p className="text-white/30 text-sm">No se encontraron agentes para &ldquo;{searchQuery}&rdquo;</p>
                </div>
              )}
            </div>
            </>}
          </div>
        ) : (
          /* ===== Chat View ===== */
          <>
            {/* Chat header */}
            <div className="h-16 border-b border-white/5 flex items-center px-6 shrink-0 bg-[#070a14]/50 backdrop-blur-sm">
              <button
                onClick={() => setView('grid')}
                className="mr-4 p-2 rounded-xl hover:bg-white/5 text-white/40 hover:text-white/70 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
              </button>
              {activeConversation && (() => {
                const p = personalities.find(x => x.id === activeConversation.personality_id)
                return p ? (
                  <div className="flex items-center gap-3">
                    <AgentAvatar emoji={p.emoji} color={p.color} size={36} />
                    <div>
                      <p className="text-sm font-semibold text-white">{p.name}</p>
                      <p className="text-[11px] text-white/35">{p.tagline}</p>
                    </div>
                  </div>
                ) : null
              })()}
              <div className="ml-auto flex items-center gap-2">
                <span className="text-[10px] px-2 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-green-400 animate-pulse" />
                  Activo
                </span>
              </div>
            </div>

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto no-scrollbar p-6 space-y-5">
              {messages.length === 0 && activeConversation && (() => {
                const p = personalities.find(x => x.id === activeConversation.personality_id)
                return p ? (
                  <div className="flex flex-col items-center justify-center h-full text-center min-h-[400px]">
                    <div className="relative mb-6">
                      <AgentAvatar emoji={p.emoji} color={p.color} size={72} />
                      <div className="absolute inset-0 rounded-2xl blur-2xl opacity-30" style={{ background: p.color }} />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{p.name}</h3>
                    <p className="text-sm text-white/40 max-w-sm mb-4">{p.description}</p>
                    <div className="flex flex-wrap gap-2 justify-center mb-6">
                      {p.expertise.map(e => (
                        <span key={e} className="text-xs px-3 py-1.5 rounded-full bg-white/5 text-white/50 border border-white/10">{e}</span>
                      ))}
                    </div>
                    <div className="glass-card p-4 max-w-sm">
                      <p className="text-xs text-white/30 mb-2">Sugerencias para empezar:</p>
                      <div className="space-y-2">
                        {[
                          '¿Cómo puedo mejorar mi oferta?',
                          'Dame una estrategia de contenido',
                          'Ayúdame a cerrar más ventas',
                        ].map((suggestion, i) => (
                          <button
                            key={i}
                            onClick={() => { setInput(suggestion); setTimeout(() => { setInput(''); sendMessage(); }, 0); }}
                            className="w-full text-left text-sm text-white/50 hover:text-white/80 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-2"
                          >
                            <ChevronRight className="w-3 h-3 text-brand-orange" />
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null
              })()}

              {messages.map((msg, i) => (
                <div key={msg.id + i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && activeConversation && (() => {
                    const p = personalities.find(x => x.id === activeConversation.personality_id)
                    return p ? (
                      <AgentAvatar emoji={p.emoji} color={p.color} size={32} />
                    ) : (
                      <div className="w-8 h-8 rounded-xl bg-brand-orange/20 flex items-center justify-center text-sm shrink-0">🤖</div>
                    )
                  })()}

                  <div className={`max-w-[75%] px-5 py-3.5 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-brand-orange to-brand-orange-dark text-white rounded-br-md shadow-lg shadow-brand-orange/10'
                      : 'bg-white/[0.04] text-white/80 border border-white/[0.06] rounded-bl-md backdrop-blur-sm'
                  }`}>
                    {msg.content.split('\n').map((line, li) => (
                      <p key={li} className={li > 0 ? 'mt-2' : ''}>{line}</p>
                    ))}
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-white/50" />
                    </div>
                  )}
                </div>
              ))}

              {loading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="p-4 border-t border-white/5 shrink-0 bg-[#070a14]/50 backdrop-blur-sm">
              <div className="max-w-3xl mx-auto">
                <div className="flex gap-3 items-end">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                      placeholder="Escribí tu pregunta al experto..."
                      className="w-full px-5 py-3.5 pr-12 bg-white/5 border border-white/10 rounded-2xl text-white text-sm placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-brand-orange/20 focus:border-brand-orange/30 transition-all"
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!input.trim() || loading}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-brand-orange text-white rounded-xl hover:bg-brand-orange-dark transition-all active:scale-[0.95] disabled:opacity-0 disabled:pointer-events-none"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-center text-[10px] text-white/15 mt-2">
                  Los agentes usan GPT-4o-mini con tu API key de OpenAI. Los mensajes se guardan encriptados.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

/* ===== Agent Card ===== */
function AgentCard({
  personality,
  onClick,
  loading,
  compact = false,
}: {
  personality: AgentPersonality
  onClick: () => void
  loading: boolean
  compact?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`group text-left rounded-2xl bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:border-white/[0.12] transition-all duration-300 relative overflow-hidden ${
        compact ? 'p-4' : 'p-5'
      }`}
    >
      {/* Hover glow */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ background: `radial-gradient(600px circle at 50% 0%, ${personality.color}08, transparent 40%)` }}
      />

      <div className="relative flex items-start gap-3">
        <div className="relative">
          <AgentAvatar emoji={personality.emoji} color={personality.color} size={compact ? 40 : 48} />
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-500 border-2 border-[#060812]" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`font-semibold text-white group-hover:text-white transition-colors ${compact ? 'text-sm' : 'text-base'}`}>
            {personality.name}
          </h3>
          <p className="text-[11px] text-white/40 mt-0.5">{personality.tagline}</p>
          {!compact && (
            <>
              <p className="text-xs text-white/30 mt-2 line-clamp-2 leading-relaxed">{personality.description}</p>
              <div className="flex flex-wrap gap-1.5 mt-3">
                {personality.expertise.slice(0, 3).map(e => (
                  <span key={e} className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-white/40 border border-white/[0.04]">
                    {e}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-1.5 mt-3 text-[10px] text-brand-orange opacity-0 group-hover:opacity-100 transition-opacity">
                <MessageSquare className="w-3 h-3" />
                Chatear ahora
                <ChevronRight className="w-3 h-3" />
              </div>
            </>
          )}
        </div>
      </div>
    </button>
  )
}

// ═══════════════════════════════════════════════════════════════
// PIPELINE SECTION
// ═══════════════════════════════════════════════════════════════
function PipelineSection({ initialStage, onActivate }: {
  initialStage: string | null
  onActivate: (stageId: string) => void
}) {
  const [activeStage, setActiveStage] = useState<string | null>(initialStage)
  const selected = PIPELINE_STAGES.find(s => s.id === activeStage)

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center">
            <Target className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Pipeline de Ventas IA</h2>
            <p className="text-white/40 text-sm">9 agentes especializados — uno por cada etapa de tu proceso de ventas</p>
          </div>
        </div>
      </div>

      {/* Stage Grid */}
      <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-9 gap-2">
        {PIPELINE_STAGES.map((stage, i) => {
          const isActive = activeStage === stage.id
          return (
            <button
              key={stage.id}
              onClick={() => setActiveStage(isActive ? null : stage.id)}
              className={`flex flex-col items-center gap-1.5 p-3 rounded-2xl border transition-all ${
                isActive
                  ? 'border-opacity-50 scale-105'
                  : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.07] hover:border-white/[0.15]'
              }`}
              style={isActive ? { background: `${stage.color}18`, borderColor: `${stage.color}50` } : {}}
            >
              <span className="text-2xl">{stage.emoji}</span>
              <span className="text-[10px] font-medium text-white/70 text-center leading-tight">{stage.label}</span>
              <span className="text-[9px] text-white/30 text-center leading-tight">{stage.methodology}</span>
              {i < PIPELINE_STAGES.length - 1 && (
                <div className="hidden lg:block absolute right-0 top-1/2 -translate-y-1/2">
                  <ArrowRight className="w-2 h-2 text-white/10" />
                </div>
              )}
            </button>
          )
        })}
      </div>

      {/* Selected Stage Detail */}
      {selected ? (
        <div
          className="rounded-2xl border p-6 transition-all"
          style={{ background: `${selected.color}0c`, borderColor: `${selected.color}35` }}
        >
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-4xl">{selected.emoji}</span>
                <div>
                  <h3 className="text-lg font-bold text-white">{selected.label}</h3>
                  <span
                    className="text-xs px-2.5 py-1 rounded-full border font-medium"
                    style={{ background: `${selected.color}20`, borderColor: `${selected.color}40`, color: selected.color }}
                  >
                    {selected.methodology}
                  </span>
                </div>
              </div>
              <p className="text-white/60 text-sm mb-4 leading-relaxed">{selected.description}</p>

              {/* Sample prompt preview */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-4">
                <p className="text-white/30 text-[10px] mb-2 uppercase tracking-wide">Ejemplo de uso</p>
                <p className="text-white/60 text-sm italic">"{selected.sample}"</p>
              </div>
            </div>
            <button
              onClick={() => onActivate(selected.id)}
              className="shrink-0 flex flex-col items-center gap-2 px-6 py-4 rounded-2xl border font-medium text-sm transition-all hover:scale-105"
              style={{ background: `${selected.color}20`, borderColor: `${selected.color}50`, color: selected.color }}
            >
              <Play className="w-6 h-6" />
              <span>Activar<br />Agente</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-8 text-center">
          <Target className="w-10 h-10 text-white/10 mx-auto mb-3" />
          <p className="text-white/30 text-sm">Seleccioná una etapa para ver el agente especializado</p>
          <p className="text-white/15 text-xs mt-1">Cada agente usa la metodología exacta de esa etapa</p>
        </div>
      )}

      {/* Full pipeline flow */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Flujo completo del pipeline</h3>
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {PIPELINE_STAGES.map((stage, i) => (
            <div key={stage.id} className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setActiveStage(stage.id)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl border transition-all hover:scale-105"
                style={{ background: `${stage.color}12`, borderColor: `${stage.color}30` }}
              >
                <span>{stage.emoji}</span>
                <span className="text-xs text-white/70">{stage.label}</span>
              </button>
              {i < PIPELINE_STAGES.length - 1 && (
                <ArrowRight className="w-3 h-3 text-white/20 shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// NEGOTIATION SECTION
// ═══════════════════════════════════════════════════════════════
function NegotiationSection({ initialExpert, onActivate }: {
  initialExpert: string | null
  onActivate: (expertId: string, situation: string) => void
}) {
  const [selectedExpert, setSelectedExpert] = useState<string | null>(initialExpert || NEGOTIATION_EXPERTS[0].id)
  const [situation, setSituation] = useState('')
  const expert = NEGOTIATION_EXPERTS.find(e => e.id === selectedExpert)

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-2xl bg-blue-500/15 border border-blue-500/30 flex items-center justify-center">
          <Handshake className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Mesa de Negociación</h2>
          <p className="text-white/40 text-sm">5 expertos mundiales — elegí la estrategia ideal para cada situación</p>
        </div>
      </div>

      {/* Expert Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
        {NEGOTIATION_EXPERTS.map(exp => {
          const isActive = selectedExpert === exp.id
          return (
            <button
              key={exp.id}
              onClick={() => setSelectedExpert(exp.id)}
              className={`text-left p-4 rounded-2xl border transition-all ${
                isActive ? 'scale-105' : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.06]'
              }`}
              style={isActive ? { background: `${exp.color}15`, borderColor: `${exp.color}45` } : {}}
            >
              <div className="text-2xl mb-2">{exp.emoji}</div>
              <p className="text-white font-semibold text-sm">{exp.name}</p>
              <p className="text-white/40 text-[10px] mt-0.5">{exp.title}</p>
              <p
                className="text-[9px] mt-1.5 font-medium px-1.5 py-0.5 rounded-md w-fit"
                style={{ background: `${exp.color}20`, color: exp.color }}
              >
                {exp.methodology}
              </p>
            </button>
          )
        })}
      </div>

      {/* Selected Expert Detail */}
      {expert && (
        <div
          className="rounded-2xl border p-6"
          style={{ background: `${expert.color}0a`, borderColor: `${expert.color}30` }}
        >
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Expert profile */}
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-5xl">{expert.emoji}</span>
                <div>
                  <h3 className="text-xl font-bold text-white">{expert.name}</h3>
                  <p className="text-white/40 text-sm">{expert.title}</p>
                  <span
                    className="text-xs font-medium px-2.5 py-0.5 rounded-full mt-1 inline-block"
                    style={{ background: `${expert.color}25`, color: expert.color }}
                  >
                    {expert.methodology}
                  </span>
                </div>
              </div>
              <p className="text-white/60 text-sm mb-4 leading-relaxed">{expert.tagline}</p>

              {/* Techniques */}
              <div className="mb-4">
                <p className="text-white/30 text-xs uppercase tracking-wide mb-2">Técnicas clave</p>
                <div className="flex flex-wrap gap-2">
                  {expert.techniques.map(t => (
                    <span key={t} className="text-xs px-3 py-1.5 rounded-xl border"
                      style={{ background: `${expert.color}15`, borderColor: `${expert.color}35`, color: expert.color }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              {/* Opening line */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-4">
                <p className="text-white/30 text-[10px] mb-2 uppercase tracking-wide">Frase de apertura</p>
                <p className="text-white/70 text-sm italic">{expert.opening}</p>
              </div>

              {/* Best for */}
              <div>
                <p className="text-white/30 text-[10px] uppercase tracking-wide mb-2">Ideal para</p>
                <div className="space-y-1">
                  {expert.best_for.map(b => (
                    <div key={b} className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" style={{ color: expert.color }} />
                      <span className="text-white/60 text-sm">{b}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Situation input */}
            <div className="flex flex-col gap-4">
              <div>
                <label className="text-white/50 text-xs uppercase tracking-wide mb-2 block">
                  Describí tu situación de negociación
                </label>
                <textarea
                  value={situation}
                  onChange={e => setSituation(e.target.value)}
                  placeholder={`Ejemplo: El cliente quiere un 30% de descuento en mi servicio de $500/mes. Ya le mostré resultados pero dice que es muy caro...`}
                  rows={5}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 resize-none"
                  style={{ '--tw-ring-color': `${expert.color}40` } as any}
                />
              </div>
              <button
                onClick={() => onActivate(expert.id, situation)}
                className="w-full py-4 rounded-2xl text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2"
                style={{ background: `linear-gradient(135deg, ${expert.color}30, ${expert.color}20)`, borderColor: `${expert.color}50`, border: '1px solid' }}
              >
                <span className="text-lg">{expert.emoji}</span>
                <span className="text-white">Activar estrategia de {expert.name}</span>
                <ArrowRight className="w-4 h-4 text-white/60" />
              </button>
              <p className="text-white/20 text-xs text-center">El agente usará exactamente las técnicas de {expert.methodology}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// OFFER BUILDER SECTION
// ═══════════════════════════════════════════════════════════════
function OfferBuilderSection({ initialProduct, onActivate }: {
  initialProduct: string | null
  onActivate: (product: string, audience: string, price: string, pains: string) => void
}) {
  const [product, setProduct] = useState(initialProduct || '')
  const [audience, setAudience] = useState('')
  const [price, setPrice] = useState('')
  const [pains, setPains] = useState('')

  const isReady = product.trim() && audience.trim() && price.trim()

  return (
    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
          <Package className="w-5 h-5 text-amber-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Grand Slam Offer Builder</h2>
          <p className="text-white/40 text-sm">Metodología de Alex Hormozi — Value Equation para crear ofertas irresistibles</p>
        </div>
      </div>

      {/* Hormozi Value Equation visual */}
      <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-5">
        <p className="text-amber-400 text-xs uppercase tracking-wide mb-3 font-semibold">Value Equation de Hormozi</p>
        <div className="flex items-center gap-2 flex-wrap text-sm">
          {[
            { label: 'Resultado Soñado', color: 'text-emerald-400' },
            { label: '×', color: 'text-white/30' },
            { label: 'Probabilidad percibida', color: 'text-blue-400' },
          ].map((item, i) => (
            <span key={i} className={`font-semibold ${item.color}`}>{item.label}</span>
          ))}
          <span className="text-white/30 font-bold text-lg">÷</span>
          {[
            { label: 'Tiempo de espera', color: 'text-orange-400' },
            { label: '×', color: 'text-white/30' },
            { label: 'Esfuerzo / Sacrificio', color: 'text-red-400' },
          ].map((item, i) => (
            <span key={i} className={`font-semibold ${item.color}`}>{item.label}</span>
          ))}
          <span className="text-white/30 ml-2">=</span>
          <span className="text-amber-400 font-bold">💎 Valor percibido</span>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-white/50 text-xs uppercase tracking-wide mb-2 block">
              Nombre del producto / servicio *
            </label>
            <input
              type="text"
              value={product}
              onChange={e => setProduct(e.target.value)}
              placeholder="Ej: Coaching de ventas 1:1"
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/30"
            />
          </div>
          <div>
            <label className="text-white/50 text-xs uppercase tracking-wide mb-2 block">
              Audiencia objetivo *
            </label>
            <input
              type="text"
              value={audience}
              onChange={e => setAudience(e.target.value)}
              placeholder="Ej: Dueños de PyMEs que quieren escalar"
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/30"
            />
          </div>
          <div>
            <label className="text-white/50 text-xs uppercase tracking-wide mb-2 block">
              Precio objetivo ($) *
            </label>
            <input
              type="number"
              value={price}
              onChange={e => setPrice(e.target.value)}
              placeholder="Ej: 997"
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/30"
            />
            {price && Number(price) > 0 && (
              <p className="text-amber-400/60 text-xs mt-1">
                Hormozi recomienda: el valor percibido debería ser ≥ ${(Number(price) * 10).toLocaleString()}
              </p>
            )}
          </div>
          <div>
            <label className="text-white/50 text-xs uppercase tracking-wide mb-2 block">
              Puntos de dolor del cliente
            </label>
            <input
              type="text"
              value={pains}
              onChange={e => setPains(e.target.value)}
              placeholder="Ej: no cierra ventas, no tiene sistema"
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/30"
            />
          </div>
        </div>

        {/* What Hormozi will generate */}
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4">
          <p className="text-white/30 text-xs uppercase tracking-wide mb-3">El agente Hormozi va a generar</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {[
              { emoji: '📦', label: 'Value Stack completo' },
              { emoji: '💎', label: 'Precio irresistible' },
              { emoji: '🛡️', label: 'Garantía de riesgo cero' },
              { emoji: '⚡', label: 'Bonos estratégicos' },
              { emoji: '🎯', label: 'Framing de precio' },
              { emoji: '💬', label: 'Manejo de objeciones' },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-2">
                <span>{item.emoji}</span>
                <span className="text-white/50 text-xs">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={() => onActivate(product, audience, price, pains)}
          disabled={!isReady}
          className="w-full py-4 rounded-2xl text-sm font-bold transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-30 disabled:pointer-events-none flex items-center justify-center gap-3 bg-gradient-to-r from-amber-500/30 to-amber-400/20 border border-amber-500/40 text-amber-300"
        >
          <span className="text-xl">💰</span>
          Generar Grand Slam Offer con Alex Hormozi
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
