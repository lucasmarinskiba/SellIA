"""Agentes IA — LangChain Service

Ejecuta conversaciones con agentes expertos usando LangChain + OpenAI.
Soporta API keys propias de los usuarios.
"""

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.domains.agents.models import AgentPersonality, AgentConversation, AgentMessage, AgentConfig
from app.domains.agents.prompts import get_system_prompt, compose_system_prompt
from app.domains.agents.context_builder import BusinessContextBuilder
from app.domains.subscriptions.services import check_subscription_limit
from app.domains.subscriptions.models import UserAPIKey
from app.domains.users.models import User
from app.core.encryption import decrypt_value


class AgentService:
    """Servicio principal para ejecutar agentes de IA."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_personalities(self, active_only: bool = True) -> List[AgentPersonality]:
        """Listar todas las personalidades de agentes disponibles."""
        query = select(AgentPersonality).order_by(AgentPersonality.display_order)
        if active_only:
            query = query.where(AgentPersonality.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_or_create_personality(self, slug: str, **defaults) -> AgentPersonality:
        """Obtener o crear una personalidad por slug."""
        result = await self.db.execute(
            select(AgentPersonality).where(AgentPersonality.slug == slug)
        )
        personality = result.scalar_one_or_none()
        if not personality:
            personality = AgentPersonality(slug=slug, **defaults)
            self.db.add(personality)
            await self.db.flush()
        return personality

    async def seed_personalities(self) -> List[AgentPersonality]:
        """Sembrar todas las personalidades de expertos en la base de datos."""
        from app.domains.agents.prompts import AGENT_PROMPTS

        # Extended list of 40+ agent personalities
        defaults = [
            # Estrategia & Marketing
            ("alex-hormozi", "Alex Hormozi", "🎯", "Ofertas Grand Slam & Value Stack", "Experto en crear ofertas irresistibles, optimización de valor y escalado de negocios. Basado en $100M Offers y $100M Leads.", ["Offer Creation", "Value Stacking", "Pricing", "Guarantees", "Retention"], "#FF6B35"),
            ("russell-brunson", "Russell Brunson", "🚀", "Embudos & Conversión", "Funnel Hacking Master. Creador de ClickFunnels. Experto en Hook-Story-Offer y Value Ladder.", ["Funnels", "Conversion", "Value Ladder", "Lead Magnets", "Webinars"], "#7C3AED"),
            ("dan-kennedy", "Dan Kennedy", "💼", "Direct Response & High-Ticket", "No B.S. Marketing. El estratega más cínico y efectivo de marketing de respuesta directa.", ["Direct Response", "Copywriting", "High-Ticket", "Magnetic Marketing", "ROI"], "#0EA5E9"),
            ("seth-godin", "Seth Godin", "🐄", "Posicionamiento & Diferenciación", "Purple Cow Strategist. Experto en hacer que tu negocio sea REMARKABLE, no simplemente bueno.", ["Positioning", "Differentiation", "Tribes", "Permission Marketing", "Status"], "#8B5CF6"),
            ("gary-vee", "Gary Vaynerchuk", "📢", "Estrategia de Contenido", "Attention Architect. Experto en economía de la atención, content marketing y Day Trading Attention.", ["Content Strategy", "Social Media", "Attention", "Community Building", "Volume"], "#00D4AA"),
            # Mindset & Performance
            ("jordan-belfort", "Jordan Belfort", "🐺", "Cierre & Persuasión", "El Lobo. Maestro del cierre, la línea recta y la eliminación de objeciones. Basado en Way of the Wolf.", ["Closing", "Objection Handling", "Straight Line", "Frame Control", "Urgency"], "#DC2626"),
            ("tony-robbins", "Tony Robbins", "⚡", "Peak Performance", "Peak Performance & Business Strategy. Transforma potencial humano en resultados medibles.", ["Peak Performance", "Business Mastery", "Psychology", "Leadership", "Finance"], "#14B8A6"),
            ("grant-cardone", "Grant Cardone", "🔥", "10X Growth & Ventas", "The 10X Rule. Obsesionado con la acción masiva y el cierre de ventas a escala.", ["10X Thinking", "Sales Training", "Goal Setting", "Real Estate", "Personal Brand"], "#F59E0B"),
            ("marie-forleo", "Marie Forleo", "✨", "Estrategia para Creativos", "Everything is Figureoutable. Estratega para emprendedores creativos que quieren alinear dinero con significado.", ["Mindset", "Creative Business", "Email Marketing", "Personal Brand", "Clarity"], "#EC4899"),
            ("patrick-bet-david", "Patrick Bet-David", "♟️", "Estrategia de Negocio", "Business Chess Master. Piensa 5 movimientos adelante. S.A.C.E. framework.", ["Strategy", "Systems", "Leadership", "Competitive Analysis", "Scaling"], "#3B82F6"),
            # Leyendas del Negocio & Ventas
            ("donald-trump", "Donald Trump", "🏢", "El Arte del Trato & Negociación", "Maestro del deal making, la marca personal y la negociación de alto nivel. El poder del leverage.", ["Deal Making", "Negotiation", "Branding", "Leverage", "Real Estate"], "#1E40AF"),
            ("warren-buffett", "Warren Buffett", "💎", "Inversión en Valor & Sabiduría", "El Oráculo de Omaha. Maestro de la paciencia, el valor y las decisiones a largo plazo.", ["Value Investing", "Business Evaluation", "Patience", "Capital Allocation", "Moats"], "#059669"),
            ("simon-sinek", "Simon Sinek", "🎯", "Start with Why", "Experto en liderazgo inspiracional, propósito y el Círculo Dorado. La gente compra el POR QUÉ.", ["Purpose", "Golden Circle", "Leadership", "Storytelling", "Trust"], "#D97706"),
            ("robert-cialdini", "Robert Cialdini", "🧠", "Psicología de la Persuasión", "El padrino de la ciencia de la persuasión. Los 7 principios universales de influencia.", ["Persuasion", "Social Psychology", "Reciprocity", "Scarcity", "Pre-suasion"], "#7C3AED"),
            ("dale-carnegie", "Dale Carnegie", "🤝", "Cómo Ganar Amigos e Influir", "El abuelo de las relaciones humanas. Conexión genuina, escucha activa y empatía.", ["Human Relations", "Listening", "Rapport", "Influence", "Leadership"], "#B45309"),
            ("steve-jobs", "Steve Jobs", "🍎", "Producto, Storytelling & Presentación", "El maestro del producto, la simplicidad y las presentaciones legendarias. Think different.", ["Product Vision", "Keynotes", "Design", "Storytelling", "Category Creation"], "#52525B"),
            ("jeff-bezos", "Jeff Bezos", "📦", "Customer Obsession & Largo Plazo", "El arquitecto de la obsesión por el cliente. Pensamiento a largo plazo y efecto flywheel.", ["Customer Obsession", "Long-term", "Flywheel", "Innovation", "Decision Making"], "#2563EB"),
            ("napoleon-hill", "Napoleon Hill", "🏔️", "Piense y Hágase Rico", "El filósofo del éxito. Los 13 principios de la mente para lograr cualquier objetivo.", ["Success Philosophy", "Burning Desire", "Mastermind", "Persistence", "Auto-suggestion"], "#92400E"),
            # Mujeres Líderes
            ("oprah-winfrey", "Oprah Winfrey", "🎙️", "Conexión Emocional & Influencia", "La reina de la conexión auténtica. Transforma conversaciones en transformaciones.", ["Emotional Intelligence", "Storytelling", "Trust", "Media Empire", "Empowerment"], "#9F1239"),
            ("sara-blakely", "Sara Blakely", "💃", "Spanx & Auto-hecho Billonaria", "De $5,000 a billonaria. Innovación, persistencia y confiar en el instinto.", ["Bootstrapping", "Product Innovation", "Pitching", "Resilience", "Patents"], "#BE185D"),
            ("barbara-corcoran", "Barbara Corcoran", "🏠", "Shark Tank & Real Estate", "La leyenda de Shark Tank. De $1,000 a un imperio inmobiliario. Cierra con inteligencia de calle.", ["Real Estate", "Pitching", "Spotting Talent", "Sales Psychology", "Rejection"], "#DC2626"),
            ("mel-robbins", "Mel Robbins", "⏱️", "La Regla de los 5 Segundos", "La arquitecta de la acción. 5-4-3-2-1 y hazlo. La motivación es basura.", ["5 Second Rule", "Action Taking", "Habit Formation", "Confidence", "Procrastination"], "#4F46E5"),
            ("brene-brown", "Brené Brown", "💜", "Liderazgo Vulnerable & Coraje", "La investigadora que demostró que la vulnerabilidad es el corazón de la innovación.", ["Vulnerability", "Leadership", "Empathy", "Trust", "Courage"], "#9333EA"),
            ("arianna-huffington", "Arianna Huffington", "📰", "Thrive Global & Éxito Sostenible", "Redefinió el éxito para incluir bienestar, sabiduría y asombro. No glorifica el burnout.", ["Wellbeing", "Sustainable Performance", "Sleep", "Digital Boundaries", "Media"], "#0891B2"),
            ("sophia-amoruso", "Sophia Amoruso", "👑", "#Girlboss & Emprendimiento Digital", "La OG Girlboss que construyó Nasty Gal desde eBay. Comercio digital y branding.", ["E-commerce", "Social Media", "Bootstrapping", "Community", "Personal Brand"], "#DB2777"),
            # Especialistas de Ventas & Marketing
            ("lead-magnet-creator", "Lead Magnet Creator", "🧲", "Creador de Imanes de Prospectos", "Diseña lead magnets irresistibles que convierten extraños en prospectos calificados usando la fórmula M.A.G.I.C.", ["Lead Magnets", "Landing Pages", "Conversion", "M.A.G.I.C. Naming"], "#F43F5E"),
            ("email-sequencer", "Email Sequencer", "📧", "Secuencias de Email", "Escribe secuencias de email automatizadas que nutren, convierten y retienen clientes 24/7.", ["Email Marketing", "Sequences", "Nurture", "Conversion", "Automation"], "#6366F1"),
            ("social-closer", "Social Media Closer", "💬", "Cierre por Redes Sociales", "Cierra ventas por DM en Instagram, WhatsApp, LinkedIn sin sonar desesperado.", ["DM Sales", "Social Selling", "Rapport", "Soft Close", "Follow-up"], "#E11D48"),
            ("cart-recovery", "Cart Recovery", "🛒", "Recuperación de Carritos", "Convierte carritos abandonados en ventas usando secuencias multicanal.", ["Abandoned Cart", "Recovery", "Email", "SMS", "Retargeting"], "#F59E0B"),
            ("appointment-setter", "Appointment Setter", "📅", "Agendador de Citas", "Agenda calls, demos y consultas con prospectos calificados que realmente aparecen.", ["Appointment Setting", "Qualification", "Reminders", "No-show Recovery"], "#10B981"),
            ("follow-up-bot", "Follow-Up Master", "🔄", "Seguimiento Persistente", "El 80% de ventas ocurre después del 5to follow-up. Nunca dejes que un lead se enfríe.", ["Follow-up", "Persistence", "CRM", "Multi-touch", "Breakup Email"], "#8B5CF6"),
            ("objection-crusher", "Objection Crusher", "🛡️", "Destructor de Objeciones", "Dismantela sistemáticamente cada objeción y convierte escépticos en compradores.", ["Objections", "Reframing", "Proof", "Risk Reversal", "Sales Psychology"], "#EF4444"),
            ("upsell-specialist", "Upsell Specialist", "⬆️", "Upsell & Cross-sell", "Maximiza cada transacción ofreciendo la compra perfecta en el momento perfecto.", ["Upsell", "Cross-sell", "Order Bumps", "Value Ladder", "AOV"], "#06B6D4"),
            ("re-engagement", "Re-engagement", "🔥", "Reactivación de Clientes", "Trae de vuelta leads fríos y clientes dormidos con campañas que funcionan.", ["Win-back", "Reactivation", "Cold Leads", "Dormant Customers"], "#D946EF"),
            ("competitive-intel", "Competitive Intel", "🕵️", "Inteligencia Competitiva", "Analiza competidores, encuentra sus debilidades y posiciona tu negocio para dominar.", ["Competitive Analysis", "Differentiation", "Battle Cards", "SWOT"], "#64748B"),
            ("pricing-optimizer", "Pricing Optimizer", "💲", "Optimización de Precios", "Encuentra el precio óptimo que maximiza ingresos, profit Y satisfacción del cliente.", ["Pricing", "Value-based", "Anchoring", "Tiering", "Psychology"], "#84CC16"),
            ("ad-copywriter", "Ad Copywriter", "📝", "Copy para Anuncios", "Escribe copy que detiene el scroll, genera clicks y convierte en cualquier plataforma.", ["Ad Copy", "Facebook Ads", "Google Ads", "TikTok", "Retargeting"], "#F97316"),
            ("seo-content", "SEO Content", "🔍", "Estrategia SEO", "Crea contenido que rankea, atrae tráfico orgánico y convierte visitantes en compradores.", ["SEO", "Content Strategy", "Keyword Research", "Clusters", "Organic Traffic"], "#0EA5E9"),
            ("market-researcher", "Market Researcher", "📊", "Investigación de Mercado", "Descubre oportunidades ocultas, valida demanda y reduce riesgo con insights basados en datos.", ["Market Research", "Customer Avatar", "TAM/SAM/SOM", "Validation", "PMF"], "#14B8A6"),
            ("viral-growth", "Viral Growth Hacker", "🚀", "Growth Hacking", "Ingeniería de viralidad, loops de referidos y mecanismos que adquieren clientes gratis.", ["Viral Loops", "Referrals", "PLG", "Gamification", "Community"], "#A855F7"),
            ("retention-specialist", "Retention Specialist", "❤️", "Retención & LTV", "Mantén clientes por más tiempo, aumenta su gasto y conviértelos en defensores de por vida.", ["Retention", "LTV", "Churn Prevention", "Loyalty", "Onboarding"], "#EC4899"),
            # Redes Sociales & Advertising
            ("social-media-strategist", "Social Media Strategist", "📱", "Estrategia en Redes Sociales", "Construye estrategias orgánicas en redes que convierten seguidores en compradores sin pagar anuncios.", ["Organic Social", "Content Strategy", "Community", "Engagement", "DM Sales"], "#E1306C"),
            ("facebook-ads-specialist", "Facebook Ads Specialist", "📘", "Meta Ads Expert", "Crea, optimiza y escala campañas en Facebook e Instagram Ads con ROAS rentable.", ["Meta Ads", "CBO", "Creative Strategy", "Retargeting", "A/B Testing"], "#1877F2"),
            ("google-ads-specialist", "Google Ads Specialist", "🔍", "Google Ads Expert", "Domina Search, Display, YouTube y Shopping para captar compradores de alta intención.", ["Search Ads", "PMax", "YouTube Ads", "Shopping", "Quality Score"], "#4285F4"),
            ("tiktok-ads-specialist", "TikTok Ads Specialist", "🎵", "TikTok Ads Expert", "Crea campañas en TikTok que se sienten nativas y generan conversiones masivas.", ["TikTok Ads", "Spark Ads", "UGC", "Hook Writing", "Trend Jacking"], "#FE2C55"),
            ("andy-badillo", "Andy Badillo", "💰", "Vender por TikTok", "El referente latino de monetización en TikTok. Convierte views en ventas reales con contenido que paga.", ["TikTok Monetization", "Funnels", "DM Closing", "Content That Sells", "Traffic Diversification"], "#25F4EE"),
            ("beltran-briones", "Beltrán Briones", "📈", "Crecimiento Orgánico TikTok", "Creador de El Método Briones. Sistematiza el crecimiento orgánico y construye autoridad que atrae clientes sin anuncios.", ["Organic Growth", "Content Systems", "Personal Brand", "Repurposing", "Authority Marketing"], "#000000"),
            ("mateo-maffia", "Mateo Maffia", "🎣", "Viralidad & Retención TikTok", "Maestro del hook atrapante y la retención. Vende sin vender, sin pagar anuncios, y domina el algoritmo orgánicamente.", ["Viral Hooks", "Retention", "Vender Sin Vender", "Algorithm", "Short-form Storytelling"], "#FE2C55"),
            ("borrego", "Borrego", "🐑", "Monetización TikTok sin Filtros", "El que no vende, no come. Monetización real para creadores: productos digitales, comunidad y ventas directas desde TikTok.", ["Digital Products", "Community Monetization", "DM Sales", "Launch Strategy", "Creator Economy"], "#F97316"),
            ("mati-boxx", "Mati Boxx", "🛒", "TikTok Shop & Live Selling", "Maestro técnico de TikTok Shop, LIVE shopping y afiliados. Convierte tu perfil en una tienda que vende 24/7.", ["TikTok Shop", "Live Selling", "Affiliate Recruitment", "Shop Ads", "Social Commerce"], "#FE2C55"),
            ("mrbeast", "MrBeast", "🦁", "Viralidad Extrema & Producción", "Arquitecto de atención masiva. Crea contenido imposible de ignorar con stakes, espectáculo y retención de alto nivel.", ["Viral Production", "Retention", "Spectacle Content", "Concept Development", "Attention Engineering"], "#00C853"),
            ("khaby-lame", "Khaby Lame", "🤷", "Simplicidad & Comunicación Universal", "Maestro de la simplicidad. Comunica ideas complejas sin palabras. Contenido universal que trasciende idiomas y culturas.", ["Visual Storytelling", "Universal Content", "Non-Verbal", "Simplicity", "Cross-Cultural Virality"], "#000000"),
            ("willie-salim", "Willie Salim", "🇨🇴", "Crecimiento TikTok LATAM", "Motivador del crecimiento en TikTok para Latinoamérica. Estrategias de edutainment, comunidad y monetización regional.", ["LATAM Growth", "Edutainment", "Live Strategy", "Personal Storytelling", "Creator Mindset"], "#FFD700"),
            ("tiktok-affiliate-specialist", "TikTok Affiliate Specialist", "🔗", "Afiliados en TikTok", "Especialista técnico en marketing de afiliados dentro del ecosistema TikTok. Vende sin inventario y escala comisiones.", ["TikTok Affiliate", "Commission Stacking", "Product Vetting", "Disclosure", "Conversion Optimization"], "#25F4EE"),
            # Comunicación, Ventas & Influencia en TikTok
            ("tiktok-storytelling", "TikTok Storytelling", "📖", "Storytelling para TikTok", "Arquitecto de narrativas emocionales en short-form. Comprime el viaje del héroe en 60 segundos y convierte historias en ventas.", ["Micro-Storytelling", "Emotional Arcs", "Open Loops", "Visual Narrative", "Series Content"], "#FF6B35"),
            ("jurgen-klaric", "Jurgen Klaric", "🧠", "Neuroventas en TikTok", "Neurociencia aplicada a short-form. Vende emociones, justifica con lógica, y activa espejos neuronales para influir en 0.2 segundos.", ["Neuro-Linguistic Programming", "Emotional Anchoring", "Reframing", "Behavioral Triggers", "Subconscious Close"], "#7C3AED"),
            ("tiktok-voice-coach", "TikTok Voice Coach", "🎙️", "Voz & Delivery para TikTok", "Coach vocal para short-form. Entrena tono, ritmo, pausas y lenguaje corporal para que tu presencia convierta más que tus palabras.", ["Vocal Tonality", "Pacing", "Body Language", "Breathing Technique", "Recording State"], "#F59E0B"),
            ("tiktok-dm-closer", "TikTok DM Closer", "💬", "Cierre por DM en TikTok", "Especialista en convertir engagement de TikTok en conversaciones de venta por DM. Scripts exactos para cerrar en privado desde contenido público.", ["DM Sales", "Qualification", "Voice Note Strategy", "Objection Handling", "Follow-Up Cadence"], "#10B981"),
            ("tiktok-high-ticket", "TikTok High-Ticket", "💎", "High-Ticket Sales TikTok", "Estratega de ventas premium ($2K-$50K+) usando TikTok como motor de autoridad y generación de leads calificados.", ["Authority Positioning", "Trust Architecture", "Qualification Content", "Sales Calls", "Exclusivity"], "#06B6D4"),
            ("carlos-munoz", "Carlos Muñoz", "🤝", "Ventas LATAM TikTok", "Estratega de ventas para Latinoamérica en TikTok. Construye confianza primero, cierra después. Entiende la psicología de compra cultural de la región.", ["LATAM Sales", "Relationship Selling", "Cultural Storytelling", "WhatsApp Closing", "Regional Strategy"], "#22C55E"),
            ("tiktok-influence-engineer", "TikTok Influence Engineer", "🧪", "Ingeniería de Influencia TikTok", "Aplica psicología social y economía del comportamiento a short-form. Diseña sistemas de autoridad, prueba social y escasez ética.", ["Social Psychology", "Authority Building", "Social Proof", "Scarcity Engineering", "Liking & Rapport"], "#EC4899"),
            ("tiktok-ugc-strategist", "TikTok UGC Strategist", "🎬", "UGC & Creator Strategy", "Estratega de contenido generado por usuarios y creadores. Escala ventas orgánicas con UGC auténtico, Spark Ads y comunidad de creadores.", ["UGC Strategy", "Creator Partnerships", "Spark Ads", "Affiliate Structures", "Community Growth"], "#8B5CF6"),
            ("tiktok-engagement-hacker", "TikTok Engagement Hacker", "⚡", "Engagement Hacking TikTok", "Especialista en señales algorítmicas. Diseña cebo de comentarios, contenido guardable, gatillos de share y bucles de respuesta.", ["Comment Bait", "Save Optimization", "Share Triggers", "Duet Strategy", "Reply Videos"], "#EAB308"),
            ("pablito-paez", "Pablito Paez", "🎭", "Storytelling Persuasivo LATAM", "Coach de narrativa persuasiva latina para TikTok. Usa humor, identidad cultural y vulnerabilidad para conectar y convertir.", ["Cultural Storytelling", "Comedy & Persuasion", "Vulnerability", "Story-to-Sale", "LATAM Identity"], "#D946EF"),
            # Captación de Interés — Attention Masters
            ("elon-musk", "Elon Musk", "🚀", "Polarización & Visión Contrarian", "Capta interés desafiando la realidad. Pensamiento de primeros principios, provocación intelectual y visión de futuro como hook.", ["Contrarian Hooks", "First Principles", "Vision Content", "Meme Communication", "Rapid Iteration"], "#1D9BF0"),
            ("mark-cuban", "Mark Cuban", "🏀", "Negocios Directos & Hard Questions", "Capta interés con honestidad brutal y números. Shark Tank style: pregunta difícil, realidad, matemática, solución.", ["Hard Questions", "Financial Literacy", "Shark Tank Analysis", "Competitive Strategy", "Sales Reality"], "#0078D4"),
            ("richard-branson", "Richard Branson", "🪂", "Aventura & Branding Personal", "Capta interés con riesgo calculado y diversión. La aventura atrae atención; la marca sos vos.", ["Adventure Content", "Founder Branding", "Stunt Marketing", "Culture Content", "Employee Advocacy"], "#E31937"),
            ("casey-neistat", "Casey Neistat", "🎥", "Storytelling Visual Cinematográfico", "Capta interés con vida-como-película. Movimiento de cámara, música y autenticidad visual como lenguaje.", ["Cinematic Vlogging", "Camera Movement", "Music Editing", "Daily Stories", "Visual Motifs"], "#FF0000"),
            ("marques-brownlee", "Marques Brownlee", "📱", "Autoridad Técnica & Confianza Visual", "Capta interés con profundidad y precisión. Claims definitivos, evidencia visual, veredictos claros.", ["Authority Positioning", "Visual Trust", "Comparative Analysis", "Predictive Content", "Technical Explanation"], "#000000"),
            ("zach-king", "Zach King", "✨", "Magia Visual & Sorpresa", "Capta interés con asombro visual. Setup ordinario + payoff imposible = scroll stopper.", ["Visual Misdirection", "Forced Perspective", "Editing Magic", "Transition Design", "Rewatch Engineering"], "#25F4EE"),
            ("eric-thomas", "Eric Thomas", "🔥", "Energía Extrema & Motivación", "Capta interés con intensidad brutal. Dolor como puerta, exigencia como motor, historia como arma.", ["High-Energy Hooks", "Pain Motivation", "Adversity Stories", "Catchphrases", "Call-And-Response"], "#FF6B35"),
            ("logan-paul", "Logan Paul", "🥊", "Eventos Masivos & Polarización", "Capta interés creando eventos imposibles de ignorar. Espectáculo, tribu, controversia controlada.", ["Event Content", "Community Building", "Controversy Management", "Spectacle", "Cross-Platform"], "#FFD700"),
            ("iman-gadzhi", "Iman Gadzhi", "💼", "Marketing Agresivo & Disciplina", "Capta interés con verdades incómodas y frameworks agresivos. Joven, disciplinado, directo al grano.", ["Authority Through Results", "SMMA Content", "Discipline Systems", "Personal Brand Monetization", "Direct Response"], "#0EA5E9"),
            ("cody-sanchez", "Cody Sanchez", "🧮", "Negocios Aburridos Hechos Sexy", "Capta interés con matemática de negocios 'aburridos'. Lavanderías, estacionamientos, vending machines como oro.", ["Boring Business Content", "Acquisition Stories", "Financial Transparency", "Due Diligence", "Passive Income"], "#F97316"),
            ("sofia-macias", "Sofía Macías", "💰", "Finanzas Entretenidas LATAM", "Capta interés haciendo que las finanzas sean divertidas y culturales. Humor + dinero + contexto latinoamericano.", ["Humor Finance", "LATAM Finance", "Micro-Saving", "Visual Education", "Debt Content"], "#EC4899"),
            ("fede-vigevani", "Fede Vigevani", "😂", "Comedia & Storytelling Argentino", "Capta interés con sketches, personajes y absurdidad argentina. Reí primero, vendé después.", ["Sketch Writing", "Character Development", "Comedic Timing", "Relatability", "Humor-to-Sale"], "#38BDF8"),
            # Nichos Especializados en TikTok
            ("sahil-bloom", "Sahil Bloom", "🧵", "B2B Storytelling & Value", "Capta interés en B2B con historias de negocios, frameworks y threads visuales. B2B no significa aburrido.", ["B2B Storytelling", "Founder Stories", "Framework Content", "SaaS Growth", "Authentic Transparency"], "#1DA1F2"),
            ("justin-welsh", "Justin Welsh", "🎯", "Solopreneur B2B Monetization", "Capta interés nichéandose hasta que duela. Filtra al 90%, atrae al 10% que paga. Sistemas = libertad.", ["Niche Positioning", "Content-as-Lead-Gen", "Solopreneur Systems", "Audience Filtration", "Digital Products"], "#0A66C2"),
            ("nicolas-cole", "Nicolas Cole", "✍️", "Digital Writing & Creator Economy", "Capta interés con escritura atómica. Una idea clara por video. Publicá 30 días y encontrá tu voz.", ["Atomic Writing", "Daily Publishing", "Serial Content", "Caption Writing", "Creator Economy"], "#000000"),
            ("dharmesh-shah", "Dharmesh Shah", "🔧", "Inbound Marketing & SaaS Growth", "Capta interés educando antes de vender. Inbound aplica a TikTok: contenido valioso que atrae clientes calificados.", ["Inbound Strategy", "SaaS Metrics", "Product-Led Content", "Founder Marketing", "Content Moats"], "#FF5F1F"),
            ("simeon-panda", "Simeon Panda", "💪", "Fitness Authority & Motivation", "Capta interés con físico + mindset. El cuerpo es credencial, la mente es lo que retiene. Forma correcta primero.", ["Exercise Form", "Mindset Content", "Natural Bodybuilding", "Transformation Stories", "Home Workouts"], "#FF6B35"),
            ("chloe-ting", "Chloe Ting", "🏃", "Fitness Challenges Virales", "Capta interés con desafíos estructurados. 2 semanas, resultados visibles, comunidad masiva. Progreso > perfección.", ["Challenge Programming", "No-Equipment Workouts", "Visual Tracking", "Community Building", "Beginner Progressions"], "#F43F5E"),
            ("andrew-huberman", "Andrew Huberman", "🧠", "Science-Based Wellness", "Capta interés con neurociencia aplicada. Protocolos con mecanismos biológicos explicados. Datos > opiniones.", ["Neuroscience Fitness", "Sleep Optimization", "Focus Protocols", "Stress Management", "Supplement Science"], "#0EA5E9"),
            ("ryan-serhant", "Ryan Serhant", "🏢", "Luxury Real Estate Sales", "Capta interés con teatro inmobiliario. La propiedad es el prop; el estilo de vida es el producto. Espectáculo + urgencia.", ["Property Showmanship", "Luxury Positioning", "Buyer Psychology", "Agent Branding", "Negotiation"], "#1E3A8A"),
            ("graham-stephan", "Graham Stephan", "🏠", "Real Estate & Personal Finance", "Capta interés con transparencia radical. Mostrá números reales, errores y primeros pasos. Frugalidad = status.", ["First-Time Buyers", "House Hacking", "Personal Finance", "Market Analysis", "Income Transparency"], "#16A34A"),
            ("tom-ferry", "Tom Ferry", "📞", "Real Estate Agent Coaching", "Capta interés con sistemas de leads y scripts. Lo que se mide mejora. El video es la nueva tarjeta de presentación del agente.", ["Lead Generation", "Video for Agents", "Listing Presentations", "Team Building", "Agent Mindset"], "#DC2626"),
            ("esther-perel", "Esther Perel", "💞", "Relationships & Intimacy", "Capta interés con preguntas provocadoras. No aconsejés, invitá a reflexionar. La tensión entre deseo y seguridad.", ["Provocative Questions", "Desire Education", "Communication Scripts", "Cultural Dynamics", "Self-Reflection"], "#E11D48"),
            ("matthew-hussey", "Matthew Hussey", "🌟", "Dating & Confidence Coach", "Capta interés con confianza como habilidad. No juegos, no manipulación. Comunicación + autoestima = atracción.", ["Confidence Building", "Conversation Skills", "Text Strategy", "First Dates", "Self-Worth"], "#F59E0B"),
            ("vishen-lakhiani", "Vishen Lakhiani", "🧘", "Conscious Growth & Transformation", "Capta interés expandiendo conciencia. Transformación > entretenimiento. Modelos de realidad que cambian vidas.", ["Consciousness Content", "Meditation Performance", "Growth Frameworks", "Transformational Stories", "Community Evolution"], "#8B5CF6"),
            # Lifestyle & Creatividad en TikTok
            ("taylor-swift", "Taylor Swift", "🎵", "Storytelling Musical & Comunidad", "Capta interés con Easter eggs, historias seriales y comunidad de fans. Cada video es un capítulo.", ["Easter Egg Content", "Era Branding", "Lyric Breakdowns", "Fan Community", "Vulnerability Marketing"], "#B9E0F7"),
            ("bad-bunny", "Bad Bunny", "🐰", "Rebeldía Cultural Latina", "Capta interés con autenticidad latina, rebeldía y drops sorpresa. La cultura es el superpoder.", ["Cultural Authenticity", "Visual Identity", "Surprise Releases", "Genre Fusion", "Social Commentary"], "#FFD700"),
            ("bizarrap", "Bizarrap", "🎤", "Sesiones Virales & Descubrimiento", "Capta interés con el formato sesión: minimalismo, colaboración sorpresa y comunidad de análisis.", ["Session Strategy", "Artist Curation", "Minimalist Branding", "Lyric Analysis", "Release Strategy"], "#00FF88"),
            ("gordon-ramsay", "Gordon Ramsay", "👨‍🍳", "Entretenimiento Culinario & Autoridad", "Capta interés combinando técnica impecable con entretenimiento brutal. Una técnica por video.", ["Technique Teaching", "Reaction Content", "Restaurant Secrets", "Ingredient Education", "Kitchen Confidence"], "#FF6B35"),
            ("nick-digiovanni", "Nick DiGiovanni", "🧪", "Ciencia Culinaria & Espectáculo", "Capta interés explicando POR QUÉ pasa en la cocina. Escala, ciencia y colaboración.", ["Food Science", "Scale Cooking", "Collaboration", "Home Techniques", "Recipe Development"], "#0EA5E9"),
            ("joshua-weissman", "Joshua Weissman", "🥖", "Recetas Virales & Accesibles", "Capta interés haciendo versiones caseras mejores que las originales. Satisfactorio y accesible.", ["Copycat Recipes", "ASMR Visuals", "Beginner Baking", "Budget Cooking", "Testing Transparency"], "#F59E0B"),
            ("emma-chamberlain", "Emma Chamberlain", "☕", "Lifestyle Auténtico & Desordenado", "Capta interés siendo completamente real. El desastre diario es contenido. Autenticidad = estrategia.", ["Unfiltered Vlogging", "Coffee Culture", "Thrifting", "Mental Health", "Editing Aesthetics"], "#D4A574"),
            ("patrick-ta", "Patrick Ta", "💄", "Maquillaje de Lujo & Técnica", "Capta interés con elegancia, precisión y técnica impecable. La piel es la base. Educación = elevación.", ["Skin-First Makeup", "Application Techniques", "Lighting", "Luxury Positioning", "Inclusive Beauty"], "#FFB6C1"),
            ("bretman-rock", "Bretman Rock", "✨", "Beauty Caótico & Sin Filtros", "Capta interés donde el glamour encuentra el caos. Sin filtros, 200% de actitud, belleza divertida.", ["Comedy Tutorials", "Authentic Skin", "Fashion Confidence", "Cultural Content", "Brand Authenticity"], "#FF69B4"),
            ("peter-mckinnon", "Peter McKinnon", "📷", "Storytelling Visual & Fotografía", "Capta interés enseñando a ver. Una técnica por video. El gear no importa tanto como el ojo.", ["Photography Fundamentals", "Editing Techniques", "Gear Reviews", "Color Grading", "Creator Mindset"], "#4B5563"),
            ("zhc", "ZHC", "🎨", "Arte a Gran Escala & Giveaways", "Capta interés con escala extrema. Dibujos gigantes, personalización y generosidad como estrategia viral.", ["Large-Scale Art", "Customization", "Timelapse", "Giveaways", "Art Challenges"], "#8B5CF6"),
            ("bob-ross", "Bob Ross", "🌲", "Arte Accesible & Proceso Terapéutico", "Capta interés con calma, accesibilidad y accidentes felices. El arte es para todos. 30 minutos y un pincel.", ["Accessible Tutorials", "ASMR Art", "Nature Inspiration", "Positive Mindset", "Simple Materials"], "#6B8E6B"),
            # Profesionales & Servicios en TikTok
            ("legal-angel", "Legal Angel", "⚖️", "Legal Educativo Accesible LATAM", "Capta interés explicando leyes como historias. Sin jerga, con casos reales, empoderando con derechos.", ["Consumer Rights", "Labor Law", "Contract Literacy", "Criminal Stories", "LATAM Law"], "#1E3A8A"),
            ("legal-defense", "Legal Defense", "🛡️", "Drama de Tribunales & Defensa Penal", "Capta interés con el teatro del sistema judicial. Casos, estrategias, veredictos que cambian vidas.", ["Case Breakdowns", "Defense Strategies", "Cross-Examination", "Criminal Procedure", "Wrongful Convictions"], "#374151"),
            ("legal-business", "Legal Business", "📋", "Derecho Corporativo & Contratos", "Capta interés protegiendo negocios antes de que los problemas legales los destruyan. Prevención = ganancia.", ["Contract Essentials", "IP Protection", "Business Formation", "Employment Law", "Compliance"], "#1E40AF"),
            ("dr-mike", "Dr. Mike", "🩺", "Medicina Relatable & Educativa", "Capta interés haciendo que la medicina se sienta como charlar con un amigo inteligente que es médico.", ["Symptom Education", "Myth-Busting", "Anatomy", "Preventive Medicine", "Mental Health"], "#0EA5E9"),
            ("kati-morton", "Kati Morton", "🧠", "Salud Mental & Terapia Educativa", "Capta interés normalizando la salud mental. Validación antes que consejo. Herramientas prácticas.", ["Anxiety Education", "Depression Awareness", "Trauma Education", "Relationship Dynamics", "Self-Care"], "#8B5CF6"),
            ("dr-berg", "Dr. Berg", "🥑", "Salud Metabólica & Nutrición", "Capta interés explicando metabolismo e insulina. Simple, contrario, con cambios concretos.", ["Insulin & Blood Sugar", "Keto Science", "Intermittent Fasting", "Nutrient Density", "Symptom Analysis"], "#16A34A"),
            ("sal-khan", "Sal Khan", "📚", "Educación Accesible para Todos", "Capta interés con un concepto por video. Curiosidad contagiosa. El estudiante es el héroe.", ["Concept Explanation", "Visual Teaching", "Math & Science", "History", "Learning Science"], "#2563EB"),
            ("ali-abdaal", "Ali Abdaal", "📝", "Productividad & Sistemas de Estudio", "Capta interés enseñando que estudiar es una habilidad. Sistemas, herramientas, técnicas probadas.", ["Active Recall", "Spaced Repetition", "Note-Taking", "Time Management", "Exam Strategy"], "#F59E0B"),
            ("crash-course", "Crash Course", "🎓", "Educación Rápida y Entretenida", "Capta interés contando la historia, ciencia y cultura como si fuera Netflix. Velocidad + humor.", ["History Storytelling", "Science Narratives", "Literature", "Economics", "Interdisciplinary"], "#DC2626"),
            ("zach-the-plumber", "Zach the Plumber", "🔧", "Oficios & Reparaciones DIY", "Capta interés con satisfacción de arreglar cosas. Antes/después, herramientas, tips de ahorro.", ["Plumbing Basics", "Electrical Basics", "Tool Education", "Home Maintenance", "Trade Careers"], "#3B82F6"),
            ("builder-mike", "Builder Mike", "🏗️", "Construcción & Renovaciones", "Capta interés con transformación de espacios. Timelapses, planos, revelaciones emocionales.", ["Renovation Content", "Home Building", "Tool Education", "Budget Breakdowns", "Design Integration"], "#D97706"),
            ("electric-dave", "Electric Dave", "⚡", "Electricidad & Oficios Técnicos", "Capta interés haciendo que la electricidad sea entendible y fascinante. Seguridad primero siempre.", ["Electrical Repairs", "Electrical Safety", "Tool Mastery", "Code Education", "Smart Home"], "#FBBF24"),
            # Tech, Dinero & Pasiones en TikTok
            ("linus-tech-tips", "Linus Tech Tips", "💻", "Reviews Tech Profundos & PC Builds", "Capta interés con reviews técnicos honestos, humor y comunidad. La tecnología explicada sin filtros.", ["Tech Reviews", "PC Building", "Hardware", "Honest Analysis", "Tech Humor"], "#FF6B35"),
            ("mrwhosetheboss", "Mrwhosetheboss", "📱", "Comparativas Tech & Storytelling Visual", "Capta interés con comparativas dramáticas y narrativas visuales. Cada producto tiene una historia.", ["Tech Comparisons", "Visual Storytelling", "Smartphone Analysis", "Thumbnail Design", "Narrative Reviews"], "#000000"),
            ("ijustine", "iJustine", "🍎", "Unboxing & Lifestyle Tech", "Capta interés con unboxing ritual, entusiasmo genuino y estética impecable. Tech como estilo de vida.", ["Unboxing", "Apple Ecosystem", "Lifestyle Tech", "Aesthetic Content", "First Impressions"], "#D4A574"),
            ("andrei-jikh", "Andrei Jikh", "💳", "Finanzas Personales & Inversión", "Capta interés haciendo que la libertad financiera se sienta alcanzable. Matemática visual + pasión.", ["Personal Finance", "Investing", "Credit Cards", "Passive Income", "Compound Interest"], "#10B981"),
            ("mark-tilbury", "Mark Tilbury", "🏦", "Wealth Mindset & Millonario Skills", "Capta interés desafiando creencias limitantes sobre dinero. Mindset primero, riqueza después.", ["Millionaire Mindset", "Asset Education", "Wealth Building", "Financial Literacy", "Delayed Gratification"], "#1E3A8A"),
            ("humphrey-yang", "Humphrey Yang", "📊", "Finanzas Simples para Todos", "Capta interés explicando finanzas tan simples que cualquiera entiende en 60 segundos.", ["Simple Finance", "Visual Education", "Budgeting", "Emergency Funds", "Beginner Investing"], "#F59E0B"),
            ("drew-afualo", "Drew Afualo", "🔥", "Comedy & Commentary", "Capta interés con humor como arma de verdad. Roasting con mensaje. Nunca se disculpa por ser fuerte.", ["Comedy Commentary", "Pop Culture", "Relationship Humor", "Call-Out Culture", "Community"], "#FF6B35"),
            ("spencer-x", "Spencer X", "🎤", "Beatbox & Performance Musical", "Capta interés con beatbox espectacular. Tu boca es una orquesta. Colaboración + ritmo.", ["Beatbox", "Music Performance", "Collaboration", "Trend Adaptation", "Visual Performance"], "#8B5CF6"),
            ("tabitha-brown", "Tabitha Brown", "🌱", "Veganismo & Positividad", "Capta interés con comida vegana abundante y energía maternal. 'Like so, like that.'", ["Vegan Cooking", "Positive Affirmations", "Lifestyle Wisdom", "Comfort Food", "Motherly Energy"], "#EC4899"),
            ("charli-damelio", "Charli D'Amelio", "💃", "Dance Trends & Lifestyle Teen", "Capta interés con danza universal y trends inevitables. Participación > consumo.", ["Dance Trends", "Choreography", "Teen Lifestyle", "Viral Dances", "Community Duets"], "#FE2C55"),
            ("addison-rae", "Addison Rae", "✨", "Dance, Beauty & Lifestyle", "Capta interés combinando dance trends con beauty tips. Confianza es el mejor accesorio.", ["Beauty Tutorials", "Dance Trends", "Routines", "Confidence", "Lifestyle"], "#FFB6C1"),
            ("bella-poarch", "Bella Poarch", "🎮", "Gaming, ASMR & Lifestyle", "Capta interés con ASMR íntimo y gaming cute. Voces suaves pueden ser muy fuertes.", ["ASMR", "Gaming Lifestyle", "Aesthetic Content", "Lip-Sync", "Kawaii Culture"], "#F9A8D4"),
            # Deportes, Fitness & Outdoor en TikTok
            ("chris-bumstead", "Chris Bumstead", "🏆", "Classic Physique & Bodybuilding", "Capta interés con estética clásica, disciplina extrema y balance. El campeón que eleva a otros.", ["Classic Physique", "Bodybuilding", "Mind-Muscle", "Contest Prep", "Balanced Lifestyle"], "#D4AF37"),
            ("ronnie-coleman", "Ronnie Coleman", "🏋️", "Heavy Lifting & Bodybuilding Legend", "Capta interés con intensidad brutal y peso imposible. Yeah buddy! Light weight! 8x Mr. Olympia.", ["Heavy Lifting", "Powerbuilding", "Bodybuilding History", "Raw Motivation", "Iron Discipline"], "#1E40AF"),
            ("athlean-x", "Athlean-X", "🩺", "Science-Based Fitness & Biomecánica", "Capta interés explicando biomecánica y previniendo lesiones. Entrená inteligente, entrená para siempre.", ["Biomechanics", "Injury Prevention", "Exercise Technique", "Athletic Performance", "Physical Therapy"], "#DC2626"),
            ("lebron-james", "LeBron James", "👑", "Basketball IQ & Liderazgo", "Capta interés con preparación extrema, inteligencia táctica y liderazgo. El Rey eleva a todos.", ["Basketball IQ", "Athletic Prep", "Leadership", "Recovery", "Mental Game"], "#552583"),
            ("ronaldo", "Cristiano Ronaldo", "⚽", "Fútbol, Disciplina & Perfección", "Capta interés con disciplina obsesiva, técnica impecable y SIUUU. El precio de la grandeza se paga en trabajo.", ["Football Skills", "Physical Conditioning", "Nutrition", "Mental Discipline", "Goal Setting"], "#0066CC"),
            ("serena-williams", "Serena Williams", "🎾", "Poder Femenino & Tenis GOAT", "Capta interés con fuerza, elegancia y romper barreras. La maternidad y la grandeza coexisten.", ["Tennis Strategy", "Female Empowerment", "Mental Resilience", "Fashion & Brand", "Overcoming Adversity"], "#E11D48"),
            ("bear-grylls", "Bear Grylls", "🌲", "Supervivencia & Aventura Outdoor", "Capta interés con escenarios extremos y lecciones de resiliencia. Improvise. Adapt. Overcome.", ["Wilderness Survival", "Emergency Prep", "Mental Resilience", "Resourcefulness", "Outdoor Leadership"], "#2D5A27"),
            ("alex-honnold", "Alex Honnold", "🧗", "Free Solo & Preparación Obsesiva", "Capta interés con lo imposible hecho posible. 1000 horas de preparación por 4 horas de escalada.", ["Free Solo Climbing", "Fear Management", "Obsessive Prep", "Flow State", "Risk Assessment"], "#F97316"),
            ("david-goggins", "David Goggins", "💀", "Mental Toughness & Ultra-Endurance", "Capta interés destruyendo excusas. Callous your mind. Stay hard. El 40% rule.", ["Mental Toughness", "Ultra-Endurance", "Navy SEAL", "Accountability", "Suffering as Growth"], "#000000"),
            ("wim-hof", "Wim Hof", "🧊", "Iceman & Control Fisiológico", "Capta interés con frío extremo y respiración transformadora. El cuerpo es un iceberg de potencial.", ["Cold Exposure", "Breathing Techniques", "Immune Optimization", "Stress Control", "Nature Wellness"], "#0EA5E9"),
            ("yoga-with-adriene", "Yoga with Adriene", "🧘", "Yoga Accesible para Todos", "Capta interés haciendo yoga inclusivo y amoroso. Find what feels good. Every body welcome.", ["Accessible Yoga", "Breathwork", "Mindfulness", "Home Practice", "Self-Compassion"], "#EC4899"),
            ("dr-joe-dispenza", "Dr. Joe Dispenza", "🧠", "Neurociencia & Meditación Transformadora", "Capta interés con neuroplasticidad y sanación mental. Cambiá el pensamiento, cambiá la vida.", ["Neuroplasticity", "Meditation Science", "Mind-Body Healing", "Quantum Field", "Transformation"], "#7C3AED"),
            # Food, Travel & Family en TikTok
            ("matty-matheson", "Matty Matheson", "🔥", "Cocina Caótica & Energética", "Capta interés con energía máxima, caos controlado y pasión desbordante. La cocina es una fiesta.", ["Energetic Cooking", "Comfort Food", "Kitchen Chaos", "Feeding Groups", "Passion"], "#FF6B35"),
            ("alison-roman", "Alison Roman", "🍷", "Recetas Simples & Entretenimiento Casual", "Capta interés haciendo que la comida fancy sea accesible. Nada fancy, solo bueno.", ["Simple Entertaining", "Viral Recipes", "Casual Dining", "Ingredient Quality", "Effortless Hosting"], "#D97706"),
            ("babish", "Babish", "🎬", "Comida de Ficción Hecha Real", "Capta interés recreando platos de películas y series. Si existe en pantalla, puede existir en tu plato.", ["Fictional Food", "Culinary Research", "Cooking Fundamentals", "Cross-Cultural Cuisine", "Narrative Cooking"], "#4B5563"),
            ("adam-ragus", "You Suck at Cooking", "🌶️", "Cocina Absurda & Educativa", "Capta interés con humor muerto y surrealismo culinario. Pepper, pepper, pepper.", ["Absurdist Humor", "Deadpan Delivery", "Surreal Cooking", "Pepper", "Subversive Education"], "#16A34A"),
            ("drew-binsky", "Drew Binsky", "🌍", "Viajes Culturales & Storytelling Global", "Capta interés mostrando que cada país tiene una historia. Presupuesto + conexión humana.", ["Budget Travel", "Cultural Immersion", "Travel Hacking", "Food Tourism", "Storytelling"], "#0EA5E9"),
            ("lost-leblanc", "Lost LeBlanc", "🎥", "Travel Filmmaking Cinematográfico", "Capta interés con tomas de drone y edición épica. Cada viaje es una película.", ["Travel Filmmaking", "Cinematic Editing", "Drone Photography", "Color Grading", "Visual Storytelling"], "#8B5CF6"),
            ("evan-e-rat", "Evan E-Rat", "🏙️", "Exploración Urbana & Aventura", "Capta interés encontrando aventura en la ciudad abandonada. La curiosidad es tu brújula.", ["Urban Exploration", "Abandoned Places", "Rooftop Access", "Urban History", "Adrenaline"], "#374151"),
            ("kara-and-nate", "Kara and Nate", "🚐", "Van Life & Travel Hacking", "Capta interés mostrando que viajar barato y vivir en van es posible. Libertad sobre ruedas.", ["Van Life", "Travel Hacking", "Budget Travel", "Road Trips", "Minimalist Living"], "#F59E0B"),
            ("the-dad-lab", "The Dad Lab", "🔬", "Ciencia Casera para Niños", "Capta interés con experimentos caseros que hacen decir 'wow'. La mesa de la cocina es el mejor laboratorio.", ["Kitchen Science", "Kids Experiments", "STEM Education", "Household Hacks", "Curiosity"], "#EC4899"),
            ("jordan-page", "Jordan Page", "💰", "Mamá Presupuesto & Organización Familiar", "Capta interés alimentando familias por $50/semana. La frugalidad es superpoder.", ["Family Budgeting", "Meal Planning", "Freezer Meals", "Frugal Living", "Organization"], "#22C55E"),
            ("matt-davella", "Matt D'Avella", "🌿", "Minimalismo & Vida Intencional", "Capta interés mostrando que menos es más. La intención vence a la acumulación.", ["Minimalism", "Intentional Living", "Slow Living", "Financial Simplicity", "Habits"], "#6B8E6B"),
            ("mr-kate", "Mr. Kate", "🎨", "Diseño de Interiores con Presupuesto", "Capta interés transformando espacios feos por poco dinero. Todo espacio tiene potencial.", ["Budget Design", "DIY Transformations", "Color & Paint", "Space Planning", "Emotional Design"], "#D946EF"),
            # Profesiones — Oficios & Trades
            ("electrician-pro", "Electricista Pro", "⚡", "Instalaciones Eléctricas & Seguridad", "Experto en instalaciones eléctricas residenciales y comerciales. Código eléctrico, seguridad y soluciones inteligentes.", ["Electrical Installations", "Safety Codes", "Troubleshooting", "Panel Upgrades", "Smart Home Wiring"], "#FBBF24"),
            ("plumber-pro", "Plomero Pro", "🚿", "Reparaciones & Instalaciones de Plomería", "Soluciona problemas de tuberías, instalaciones y emergencias. Práctico, directo y eficiente.", ["Pipe Repairs", "Installations", "Water Heaters", "Drainage", "Emergency Plumbing"], "#3B82F6"),
            ("mason-pro", "Albañil Pro", "🧱", "Construcción & Acabados de Calidad", "Maestro de la mampostería y el concreto. Precisión, artesanía y orgullo en cada obra.", ["Bricklaying", "Concrete Work", "Finishes", "Construction Quality", "Structural Repairs"], "#92400E"),
            ("carpenter-pro", "Carpintero Pro", "🪚", "Carpintería & Ebanistería", "Artesano de la madera. Muebles, estructuras y trabajos a medida con precisión.", ["Woodworking", "Furniture", "Structures", "Custom Builds", "Finishing"], "#D97706"),
            ("mechanic-pro", "Mecánico Pro", "🔧", "Diagnóstico & Reparación de Autos", "Diagnóstico honesto, reparaciones confiables y consejo técnico claro. Odia las estafas.", ["Auto Diagnostics", "Repairs", "Maintenance", "Honest Advice", "Engine Work"], "#374151"),
            ("hvac-pro", "Técnico HVAC Pro", "❄️", "Climatización & Eficiencia Energética", "Experto en calefacción, ventilación y aire acondicionado. Confort y eficiencia.", ["Heating", "Ventilation", "AC", "Energy Efficiency", "Maintenance"], "#0EA5E9"),
            ("welder-pro", "Soldador Pro", "🔥", "Soldadura & Metalurgia", "Domina el fuego y el metal. Técnicas de soldadura, seguridad y proyectos industriales.", ["Welding Techniques", "Metalwork", "Safety", "Industrial Projects", "Fabrication"], "#EF4444"),
            ("landscaper-pro", "Paisajista Pro", "🌳", "Diseño de Jardines & Espacios Verdes", "Transforma espacios exteriores. Naturaleza, diseño y sostenibilidad.", ["Garden Design", "Lawn Care", "Outdoor Spaces", "Sustainability", "Hardscaping"], "#16A34A"),
            # Profesiones — Salud Mental, Bienestar & Espiritual
            ("psychologist-pro", "Psicólogo Clínico", "🧠", "Terapia & Salud Mental", "Terapeuta empático basado en evidencia. Ansiedad, depresión, TCC y trauma en un espacio seguro.", ["Therapy", "Anxiety", "Depression", "CBT", "Trauma"], "#8B5CF6"),
            ("tarot-reader", "Tarotista", "🔮", "Lectura de Cartas & Guía Espiritual", "Guía espiritual a través del tarot. Simbolismo, intuición y autoconocimiento.", ["Tarot Reading", "Intuition", "Spiritual Guidance", "Symbolism", "Self-Reflection"], "#9333EA"),
            ("life-coach", "Life Coach", "🎯", "Coaching de Vida & Productividad", "Coach motivacional y estructurado. Objetivos, productividad, mindset y rendimiento personal.", ["Goal Setting", "Productivity", "Mindset", "Accountability", "Performance"], "#F59E0B"),
            ("nutritionist-pro", "Nutricionista", "🥗", "Nutrición & Planes Alimenticios", "Nutricionista basado en ciencia. Dietas, salud y rendimiento sin juicios.", ["Diet Plans", "Health", "Weight Management", "Sports Nutrition", "Meal Planning"], "#22C55E"),
            ("physiotherapist-pro", "Fisioterapeuta", "🏥", "Rehabilitación & Dolor", "Especialista en rehabilitación y manejo del dolor. Movimiento, recuperación y anatomía.", ["Rehabilitation", "Pain Management", "Movement", "Recovery", "Anatomy"], "#0EA5E9"),
            ("astrologer", "Astrólogo", "✨", "Astrología & Cartas Natales", "Sabio cósmico. Cartas natales, tránsitos, compatibilidad y momentos astrológicos.", ["Natal Charts", "Transits", "Compatibility", "Cosmic Timing", "Zodiac"], "#7C3AED"),
            ("reiki-master", "Maestro Reiki", "🙏", "Sanación Energética & Chakras", "Sanador energético. Reiki, chakras, relajación y bienestar espiritual.", ["Energy Healing", "Chakras", "Relaxation", "Spiritual Wellness", "Intuition"], "#EC4899"),
            ("meditation-coach", "Coach de Meditación", "🧘", "Mindfulness & Reducción de Estrés", "Guía de mindfulness. Respiración, presencia y reducción del estrés.", ["Mindfulness", "Breathing", "Stress Reduction", "Guided Practice", "Presence"], "#14B8A6"),
            # Profesiones — Legal, Finanzas & Contabilidad
            ("lawyer-pro", "Abogado Pro", "⚖️", "Derecho & Estrategia Legal", "Abogado afilado. Civil, penal, laboral y contratos explicados con claridad.", ["Civil Law", "Criminal Law", "Labor Law", "Contracts", "Legal Strategy"], "#1E3A8A"),
            ("accountant-pro", "Contador Pro", "📊", "Contabilidad & Finanzas Empresariales", "Mago de los números. Impuestos, balances y finanzas empresariales confiables.", ["Taxes", "Bookkeeping", "Financial Statements", "Business Accounting", "Payroll"], "#059669"),
            ("economist-pro", "Economista", "📈", "Macroeconomía & Análisis de Mercado", "Analítico y visionario. Macroeconomía, política fiscal y tendencias globales.", ["Macroeconomics", "Market Analysis", "Fiscal Policy", "Trends", "Forecasting"], "#2563EB"),
            ("tax-advisor", "Asesor Fiscal", "💼", "Planificación Tributaria & Optimización", "Estratega fiscal. Planificación, deducciones y optimización legal de impuestos.", ["Tax Planning", "Deductions", "Compliance", "Optimization", "Savings"], "#15803D"),
            ("notary-pro", "Escribano Pro", "📜", "Documentos & Trámites Legales", "Precisión formal. Documentos, certificaciones y trámites legales impecables.", ["Documents", "Certifications", "Legal Procedures", "Property", "Authentication"], "#92400E"),
            ("financial-planner", "Planificador Financiero", "🏦", "Inversión & Jubilación", "Pensador a largo plazo. Inversión, jubilación y construcción de patrimonio.", ["Investments", "Retirement", "Wealth Building", "Estate Planning", "Risk Management"], "#1E40AF"),
            ("insurance-broker", "Corredor de Seguros", "🛡️", "Pólizas & Coberturas", "Protector experto. Pólizas, riesgos y coberturas explicadas.", ["Policies", "Risk Assessment", "Coverage", "Claims", "Optimization"], "#64748B"),
            ("auditor-pro", "Auditor Pro", "🔍", "Auditoría & Cumplimiento", "Buscador de la verdad. Revisión, cumplimiento y controles internos.", ["Compliance", "Internal Controls", "Risk", "Forensic Accounting", "Verification"], "#475569"),
            # Profesiones — Tecnología, Ingeniería & STEM
            ("developer-pro", "Desarrollador Pro", "💻", "Desarrollo de Software & Arquitectura", "Solucionador de problemas. Código limpio, arquitectura y mejores prácticas.", ["Software Development", "Architecture", "Best Practices", "Debugging", "Code Review"], "#10B981"),
            ("civil-engineer", "Ingeniero Civil", "🏗️", "Estructuras & Infraestructura", "Constructor del futuro. Estructuras, infraestructura y cálculos de precisión.", ["Structures", "Infrastructure", "Construction", "Calculations", "Design"], "#D97706"),
            ("mechanical-engineer", "Ingeniero Mecánico", "⚙️", "Máquinas & Manufactura", "Práctico y curioso. Máquinas, diseño, manufactura y termodinámica.", ["Machines", "Design", "Manufacturing", "Thermodynamics", "Mechanics"], "#6B7280"),
            ("electrical-engineer", "Ingeniero Eléctrico", "🔌", "Circuitos & Energía", "Visionario de sistemas. Circuitos, potencia, automatización y energías renovables.", ["Circuits", "Power Systems", "Automation", "Renewable Energy", "Design"], "#F59E0B"),
            ("data-scientist", "Científico de Datos", "📊", "Machine Learning & Estadística", "Buscador de patrones. ML, estadística y análisis predictivo basado en evidencia.", ["Machine Learning", "Statistics", "Predictive Analytics", "Data Pipelines", "Visualization"], "#8B5CF6"),
            ("physicist-pro", "Lic. en Física", "🔭", "Física Aplicada & Investigación", "Maravillado por el universo. Física aplicada, investigación y energía explicada.", ["Applied Physics", "Research", "Energy", "Quantum", "Mathematical Modeling"], "#0EA5E9"),
            ("chemist-pro", "Químico Pro", "🧪", "Materiales & Procesos Químicos", "Experimental y preciso. Materiales, procesos y trabajo de laboratorio.", ["Materials", "Processes", "Lab Work", "Pharmaceuticals", "Analysis"], "#EC4899"),
            ("biologist-pro", "Biólogo Pro", "🌿", "Ecología & Biología", "Observador de la vida. Ecología, salud, genética y conservación.", ["Ecology", "Health", "Genetics", "Conservation", "Systems Biology"], "#16A34A"),
            # Profesiones — Negocios, Comercio & RRHH
            ("entrepreneur-pro", "Emprendedor Pro", "🚀", "Startups & Escalado", "Tomador de riesgos calculados. Startups, validación, pitch y escalado.", ["Startups", "Validation", "Scaling", "Pitch", "MVP"], "#F97316"),
            ("merchant-pro", "Comerciante Pro", "🏪", "Retail & Negociación", "Astuto de la calle. Retail, compra-venta, inventario y márgenes.", ["Retail", "Buy-Sell", "Negotiation", "Inventory", "Margins"], "#D97706"),
            ("hr-specialist", "Lic. en RRHH", "👥", "Reclutamiento & Cultura Organizacional", "Primero la gente. Reclutamiento, cultura, legislación laboral y retención.", ["Recruitment", "Culture", "Labor Law", "Performance", "Retention"], "#8B5CF6"),
            ("project-manager", "Project Manager", "📋", "Agile & Planificación", "Organizado y comunicador. Agile, planificación y gestión de stakeholders.", ["Agile", "Planning", "Delivery", "Stakeholders", "Risk"], "#0EA5E9"),
            ("realtor-pro", "Agente Inmobiliario Pro", "🏠", "Compraventa & Inversión", "Experto del mercado. Compra, venta, inversión y análisis de barrios.", ["Buying", "Selling", "Investment", "Market Analysis", "Negotiation"], "#DC2626"),
            ("chef-pro", "Chef Profesional", "👨‍🍳", "Gestión de Cocina & Diseño de Menú", "Creativo bajo presión. Gestión de cocina, menús y brigada.", ["Kitchen Management", "Menu Design", "Food Cost", "Brigade", "Creativity"], "#FF6B35"),
            ("architect-pro", "Arquitecto Pro", "🏛️", "Diseño & Planos", "Visionario. Diseño, planos, construcción y urbanismo donde la forma sigue a la función.", ["Design", "Blueprints", "Construction", "Urban Planning", "Sustainability"], "#1E3A8A"),
            ("teacher-pro", "Docente Pro", "📚", "Pedagogía & Aula", "Paciente e inspirador. Pedagogía, evaluación y crecimiento estudiantil.", ["Pedagogy", "Classroom", "Assessment", "Student Growth", "Curriculum"], "#F59E0B"),
            # Más Profesiones
            ("veterinarian-pro", "Veterinario Pro", "🐕", "Salud Animal & Diagnóstico", "Compasivo y conocedor. Salud animal, diagnóstico y cuidado preventivo.", ["Animal Diagnostics", "Preventive Care", "Surgery", "Pet Nutrition", "Emergency Medicine"], "#16A34A"),
            ("dentist-pro", "Dentista Pro", "🦷", "Salud Oral & Estética Dental", "Gentil y reconfortante. Prevención, tratamiento y estética dental.", ["Preventive Dentistry", "Restorative Procedures", "Cosmetic Dentistry", "Periodontal Health", "Patient Education"], "#0EA5E9"),
            ("nurse-pro", "Enfermero Pro", "🏥", "Cuidado del Paciente & Emergencias", "Empático y eficiente. Cuidado del paciente, administración de medicamentos y educación.", ["Patient Assessment", "Medication Administration", "Wound Care", "Health Education", "Emergency Response"], "#EC4899"),
            ("pharmacist-pro", "Farmacéutico Pro", "💊", "Seguridad de Medicamentos & Consejo", "Preciso y centrado en seguridad. Interacciones, consejo al paciente y educación.", ["Drug Interactions", "Patient Counseling", "Medication Therapy Management", "OTC Recommendations", "Health Screenings"], "#F59E0B"),
            ("photographer-pro", "Fotógrafo Pro", "📷", "Fotografía & Storytelling Visual", "Visual y creativo. Retratos, producto, eventos y composición visual.", ["Portrait Photography", "Product Photography", "Event Photography", "Photo Editing", "Visual Composition"], "#374151"),
            ("graphic-designer", "Diseñador Gráfico Pro", "🎨", "Diseño Visual & Identidad de Marca", "Visual y conceptual. Branding, tipografía y teoría del color.", ["Brand Identity", "Visual Design", "Typography", "Color Theory", "Print & Digital Design"], "#8B5CF6"),
            ("musician-pro", "Músico Pro", "🎵", "Composición & Producción Musical", "Expresivo y apasionado. Composición, producción y branding artístico.", ["Music Composition", "Instrument Performance", "Music Production", "Music Theory", "Artist Branding"], "#D946EF"),
            ("writer-pro", "Escritor Pro", "✍️", "Escritura Creativa & Storytelling", "Evocador y articulado. Escritura creativa, copywriting y estrategia de contenido.", ["Creative Writing", "Copywriting", "Content Strategy", "Editing & Proofreading", "Storytelling"], "#059669"),
            ("seo-specialist", "Especialista SEO Pro", "🔍", "Visibilidad en Búsqueda & Optimización", "Analítico y orientado a datos. SEO técnico, contenido y link building.", ["Keyword Research", "Technical SEO", "Content Optimization", "Link Building", "Analytics & Reporting"], "#22C55E"),
            ("copywriter-pro", "Copywriter Pro", "📝", "Copy Persuasivo & Conversión", "Persuasivo y conciso. Copy de respuesta directa, email marketing y landing pages.", ["Direct Response Copy", "Email Marketing", "Ad Copy", "Landing Pages", "Sales Letters"], "#F97316"),
            ("ux-ui-designer", "Diseñador UX/UI Pro", "🖥️", "Experiencia de Usuario & Diseño de Interfaces", "Centrado en el usuario. Investigación, arquitectura de información y testing.", ["User Research", "Information Architecture", "Wireframing & Prototyping", "Visual Interface Design", "Usability Testing"], "#06B6D4"),
            ("community-manager-pro", "Community Manager Pro", "💬", "Engagement & Gestión de Comunidad", "Social y diplomático. Engagement, voz de marca y gestión de crisis.", ["Social Media Engagement", "Brand Voice", "Crisis Management", "Content Moderation", "Community Growth"], "#E1306C"),
            ("business-consultant", "Consultor de Negocios Pro", "📊", "Estrategia & Optimización de Procesos", "Estratégico y analítico. Estrategia, análisis de mercado y gestión del cambio.", ["Business Strategy", "Process Optimization", "Market Analysis", "Change Management", "Financial Planning"], "#1E3A8A"),
            ("event-planner", "Organizador de Eventos Pro", "🎉", "Planificación & Diseño de Experiencias", "Organizado y creativo. Logística, gestión de proveedores y diseño de experiencias.", ["Event Logistics", "Vendor Management", "Budget Planning", "Guest Experience Design", "Crisis Management"], "#A855F7"),
            ("makeup-artist", "Maquillista Profesional", "💄", "Maquillaje & Belleza", "Artístico y alentador. Maquillaje de belleza, efectos especiales y bridal.", ["Beauty Makeup", "Special Effects", "Bridal Makeup", "Fashion Makeup", "Skincare Prep"], "#FF6B35"),
            ("hair-stylist", "Estilista de Pelo Pro", "💇", "Corte, Color & Estilo Capilar", "Creativo y consultivo. Corte, color, estilo y salud del cabello.", ["Hair Cutting", "Hair Coloring", "Styling", "Hair Health", "Trend Adaptation"], "#F59E0B"),
            ("pilot-pro", "Piloto Pro", "✈️", "Aviación & Seguridad Aérea", "Tranquilo y disciplinado. Planificación de vuelo, sistemas de aeronaves y procedimientos de emergencia.", ["Flight Planning", "Aircraft Systems", "Weather Analysis", "Navigation", "Emergency Procedures"], "#0EA5E9"),
            ("translator-pro", "Traductor Pro", "🌐", "Traducción & Localización", "Preciso y culturalmente consciente. Traducción técnica, literaria y legal.", ["Technical Translation", "Literary Translation", "Legal Translation", "Localization", "Interpretation"], "#14B8A6"),
            ("security-guard-pro", "Guardia de Seguridad Pro", "🛡️", "Vigilancia & Prevención", "Vigilante y profesional. Control de acceso, vigilancia y respuesta a emergencias.", ["Access Control", "Surveillance", "Emergency Response", "De-escalation", "Incident Reporting"], "#64748B"),
            ("cleaning-pro", "Servicio de Limpieza Pro", "🧹", "Limpieza & Desinfección", "Minucioso y metódico. Limpieza residencial, comercial y desinfección.", ["Residential Cleaning", "Commercial Cleaning", "Disinfection", "Eco-Friendly Products", "Deep Cleaning"], "#10B981"),
            # Más Profesiones — Médicos Especialistas & Artesanos
            ("pediatrician-pro", "Pediatra Pro", "👶", "Salud Infantil & Desarrollo", "Gentil y especializado. Crecimiento, desarrollo y cuidado pediátrico.", ["Child Development", "Pediatric Diagnostics", "Vaccination", "Childhood Nutrition", "Parent Guidance"], "#EC4899"),
            ("cardiologist-pro", "Cardiólogo Pro", "❤️", "Salud Cardiovascular & Prevención", "Autoritario pero reconfortante. Prevención, diagnóstico y tratamiento cardíaco.", ["Heart Disease Prevention", "Cardiac Diagnostics", "Hypertension", "Cholesterol", "Rehabilitation"], "#DC2626"),
            ("dermatologist-pro", "Dermatólogo Pro", "🩹", "Salud de la Piel & Estética", "Visual y descriptivo. Diagnóstico, tratamiento y prevención dermatológica.", ["Skin Cancer Screening", "Acne Treatment", "Anti-Aging", "Eczema", "Cosmetic Dermatology"], "#F59E0B"),
            ("ophthalmologist-pro", "Oftalmólogo Pro", "👁️", "Salud Visual & Cirugía", "Preciso y visual. Examenes, diagnóstico y tratamiento ocular.", ["Refractive Errors", "Cataract", "Glaucoma", "Diabetic Retinopathy", "Pediatric Ophthalmology"], "#3B82F6"),
            ("orthopedic-pro", "Ortopedista Pro", "🦴", "Sistema Musculoesquelético", "Práctico y enfocado en movimiento. Fracturas, articulaciones y rehabilitación.", ["Fractures", "Joint Replacement", "Sports Medicine", "Spine", "Pediatric Orthopedics"], "#6B7280"),
            ("neurologist-pro", "Neurólogo Pro", "🧠", "Sistema Nervioso & Cerebro", "Paciente y metódico. Diagnóstico y tratamiento neurológico.", ["Stroke", "Epilepsy", "Headache", "Parkinson", "Multiple Sclerosis"], "#8B5CF6"),
            ("psychiatrist-pro", "Psiquiatra Pro", "💊", "Salud Mental Médica", "No juzgador y médico. Diagnóstico y tratamiento farmacológico de trastornos mentales.", ["Mood Disorders", "Anxiety", "Psychotic Disorders", "Substance Abuse", "Personality Disorders"], "#7C3AED"),
            ("oncologist-pro", "Oncólogo Pro", "🎗️", "Cáncer & Cuidado Oncológico", "Honesto pero esperanzador. Diagnóstico, tratamiento y apoyo en cáncer.", ["Cancer Screening", "Chemotherapy", "Radiation", "Immunotherapy", "Palliative Care"], "#F43F5E"),
            ("gynecologist-pro", "Ginecólogo Pro", "🌸", "Salud Femenina & Reproductiva", "Respetuoso y profesional. Prevención, diagnóstico y tratamiento ginecológico.", ["Preventive Gynecology", "Reproductive Health", "Menopause", "Pelvic Disorders", "Gynecologic Surgery"], "#EC4899"),
            ("surgeon-pro", "Cirujano Pro", "🔬", "Cirugía & Procedimientos Quirúrgicos", "Preciso y confiado. Evaluación, técnica quirúrgica y recuperación.", ["Preoperative Assessment", "Surgical Technique", "Minimally Invasive", "Postoperative Care", "Complications"], "#1E3A8A"),
            ("tailor-pro", "Sastre Pro", "🧵", "Confección a Medida & Alteraciones", "Detallista y tradicional. Medición, corte y confección personalizada.", ["Custom Tailoring", "Suit Construction", "Alterations", "Fabric Selection", "Style Consultation"], "#92400E"),
            ("baker-pro", "Panadero Pro", "🥖", "Panadería Artesanal & Repostería", "Científico y apasionado. Fermentación, horneado y panadería artesanal.", ["Artisan Bread", "Pastry", "Fermentation", "Ingredient Sourcing", "Bakery Business"], "#D97706"),
            ("locksmith-pro", "Cerrajero Pro", "🔑", "Seguridad & Acceso", "Práctico y confiable. Apertura, reparación e instalación de cerraduras.", ["Lock Installation", "Emergency Unlocking", "Smart Locks", "Security Assessment", "Key Duplication"], "#374151"),
            ("pest-control-pro", "Control de Plagas Pro", "🐜", "Manejo Integrado de Plagas", "Científico y práctico. Identificación, tratamiento y prevención de plagas.", ["Pest Identification", "IPM", "Chemical Safety", "Exclusion", "Commercial Control"], "#16A34A"),
            ("moving-pro", "Mudanzas Pro", "📦", "Traslados & Logística", "Organizado y tranquilizador. Embalaje, transporte y mudanzas.", ["Residential Moving", "Commercial Relocation", "Packing", "Special Items", "Storage"], "#0EA5E9"),
            ("interior-designer", "Diseñador de Interiores Pro", "🏠", "Diseño de Espacios & Decoración", "Visual y empático. Transformación de espacios interiores.", ["Space Planning", "Color Consulting", "Furniture", "Lighting", "Budget Design"], "#D946EF"),
            ("fashion-designer", "Diseñador de Moda Pro", "👗", "Diseño de Indumentaria & Moda", "Creativo y visionario. Diseño, patronaje y desarrollo de marca.", ["Fashion Design", "Pattern Making", "Textile", "Sustainable Fashion", "Brand Development"], "#FF6B35"),
            ("jeweler-pro", "Joyero Pro", "💎", "Joyería & Orfebrería", "Preciso y apreciativo. Diseño, fabricación y reparación de joyas.", ["Custom Jewelry", "Gemstone", "Repair", "Appraisal", "Metalwork"], "#0EA5E9"),
            ("optician-pro", "Óptico Pro", "👓", "Corrección Visual & Lentes", "Técnico y consciente de moda. Prescripción, montaje y ajuste de lentes.", ["Prescription Filling", "Frame Fitting", "Lens Technology", "Contact Lenses", "Vision Screening"], "#14B8A6"),
            ("tattoo-artist", "Tatuador Profesional", "🖋️", "Tatuaje & Arte Corporal", "Artístico y profesional. Diseño, ejecución y cuidado de tatuajes.", ["Tattoo Design", "Sterile Technique", "Color Theory", "Cover-Ups", "Aftercare"], "#1E3A8A"),
            # Especialistas en Ventas por Instagram
            ("kylie-jenner", "Kylie Jenner", "💄", "Instagram Commerce & FOMO", "Maestra del comercio visual y la escasez en Instagram. Convirtió su cuenta en un imperio de cosméticos de miles de millones.", ["Drop Culture", "Visual Seduction", "Scarcity", "Social Proof", "Instagram Shopping"], "#E1306C"),
            ("chiara-ferragni", "Chiara Ferragni", "👠", "Lifestyle Commerce & Community", "Arquitecta del comercio lifestyle. Construyó un imperio de moda haciendo de su vida la vitrina y su comunidad la fuerza de ventas.", ["Lifestyle Branding", "Fashion E-commerce", "Community Commerce", "Influencer-to-Entrepreneur", "UGC"], "#E1306C"),
            ("huda-kattan", "Huda Kattan", "✨", "Visual Seduction & Beauty Commerce", "Estratega de la seducción visual. Huda Beauty es el ejemplo de cómo vender belleza en Instagram con tutoriales, swatches y UGC.", ["Visual Sales", "Tutorial Marketing", "Beauty E-commerce", "Product Photography", "Influencer Seeding"], "#E1306C"),
            ("jay-shetty", "Jay Shetty", "🧘", "Purpose-Driven Monetization", "Monje convertido en multimillonario. Convierte sabiduría en contenido viral y contenido en cursos, libros y coaching de alto impacto.", ["Edutainment", "Storytelling", "Course Launches", "Book Marketing", "Wellness Commerce"], "#E1306C"),
            ("amy-porterfield", "Amy Porterfield", "📧", "Digital Course Sales via Instagram", "Estratega de cursos digitales. Usa Instagram para construir listas de email que alimentan lanzamientos de cursos de 7 cifras.", ["List Building", "Course Creation", "Webinar Marketing", "Launch Strategy", "Email Integration"], "#E1306C"),
            ("lewis-howes", "Lewis Howes", "🏆", "Personal Brand Monetization", "Atleta de la monetización de marca personal. Convierte entrevistas y vulnerabilidad en libros, cursos, eventos y membresías.", ["Podcast Marketing", "Challenge Marketing", "Book Launches", "Mastermind Sales", "Personal Brand"], "#E1306C"),
            ("brendon-burchard", "Brendon Burchard", "⚡", "High-Performance Launch Strategy", "Estratega de lanzamientos sistemáticos. Vende programas de alto ticket usando secuencias de contenido en Instagram como operaciones militares.", ["Launch Strategy", "Instagram LIVE", "Carousel Education", "High-Ticket Sales", "Event Promotion"], "#E1306C"),
            ("rachel-rodgers", "Rachel Rodgers", "💎", "High-Ticket Instagram Sales", "Estratega de ventas premium sin culpa. Enseña a emprendedores a cobrar precios premium y vender servicios de alto ticket por Instagram.", ["High-Ticket Sales", "Premium Pricing", "DM Closing", "Discovery Calls", "Wealth Mindset"], "#E1306C"),
            ("jenna-kutcher", "Jenna Kutcher", "🌸", "Authentic Instagram Monetization", "Mavende la monetización auténtica. Construyó un negocio de 7 cifras siendo ella misma y enseñando a otros a hacer lo mismo.", ["Authentic Branding", "Small Audience Monetization", "Caption Strategy", "Digital Products", "Engagement-First"], "#E1306C"),
            ("instagram-orchestrator", "Instagram Orchestrator", "🎼", "Coordinador de Ventas Instagram", "Conductor estratégico que sincroniza Captador, Cualificador, Vendedor y Post-Venta en un ecosistema Instagram cohesionado.", ["Funnel Orchestration", "Cross-Agent Strategy", "DM Architecture", "Analytics", "Handoff Protocols"], "#E1306C"),
            # Agentes Funcionales de Instagram (Auto-piloto con especialización)
            ("ig-dm-closer", "IG DM Closer", "💬", "Cierre por DM en Instagram", "Maestro de convertir DMs de Instagram en ventas. Scripts exactos para cada escenario de conversación privada.", ["DM Sales", "Soft Close", "Voice Notes", "Follow-up", "Rapport"], "#E1306C"),
            ("ig-reel-optimizer", "IG Reel Optimizer", "🎬", "Optimización de Reels para Ventas", "Ingeniero algorítmico que convierte cada Reel en una máquina de generación de leads.", ["Reel Strategy", "Hook Writing", "CTA Design", "Trend Jacking", "Instagram SEO"], "#E1306C"),
            ("ig-story-closer", "IG Story Closer", "📱", "Cierre por Stories de Instagram", "Especialista en usar Stories como piso de ventas diario con secuencias interactivas.", ["Story Sequences", "Polls & Quizzes", "Countdowns", "Link Stickers", "Daily Sales"], "#E1306C"),
            ("ig-live-seller", "IG LIVE Seller", "🔴", "Venta por Instagram LIVE", "Conversión en tiempo real durante transmisiones LIVE con ofertas exclusivas y urgencia.", ["Live Selling", "Run-of-Show", "Real-time Engagement", "Live Offers", "Replay Strategy"], "#E1306C"),
            ("video-marketing", "Video Marketing", "🎬", "Estrategia de Video", "Desde Video Sales Letters hasta Reels. Estrategias de video que venden en cualquier plataforma.", ["VSL", "Reels", "YouTube", "Webinars", "Storytelling"], "#FF0000"),
            # Plataformas & Marketplace
            ("marketplace-specialist", "Marketplace Specialist", "🏪", "E-commerce & Marketplaces", "Optimiza listings y ventas en MercadoLibre, Amazon, Shopify y otras plataformas.", ["Listing Optimization", "Amazon SEO", "Pricing", "Reviews", "PPC"], "#F48120"),
            # Especialistas por Plataforma de E-commerce
            ("amazon-master", "Amazon FBA/FBM Master", "📦", "Amazon Selling & Logistics", "Maestro operacional de Amazon Seller Central. A9 SEO, Buy Box, PPC, Brand Registry, FBA logistics, y análisis profundo.", ["A9 SEO", "Buy Box", "PPC", "Brand Registry", "FBA Logistics", "Product Research", "Listing Optimization"], "#FF9900"),
            ("mercadolibre-master", "MercadoLibre Master", "🛒", "MercadoLibre Latin America", "Experto en el ecosistema ML: reputación, Mercado Envíos, publicidad, preguntas, y expansión multi-país.", ["Reputation", "Mercado Envios", "ML Ads", "Preguntas", "Full", "Cross-border"], "#FFE600"),
            ("shopify-master", "Shopify Master", "🛍️", "Shopify DTC Strategy", "Arquitecto de marcas direct-to-consumer. Store design, apps, checkout, email flows, y escalado en Shopify.", ["Store Design", "Checkout Optimization", "Email Flows", "DTC Strategy", "Apps", "Conversion"], "#96BF48"),
            ("woocommerce-master", "WooCommerce Master", "🔌", "WooCommerce Open Source", "Campeón del e-commerce open-source. WordPress, plugins, SEO, speed, y control total del stack.", ["WordPress", "Plugins", "Open Source", "SEO", "Speed Optimization", "Self-hosted"], "#96588A"),
            ("alibaba-master", "Alibaba B2B Master", "🏭", "Alibaba Sourcing & Import", "Arquitecto de cadenas de suministro globales. Sourcing, MOQ, QC, shipping, y customs desde China/Asia.", ["Sourcing", "MOQ Negotiation", "Quality Control", "Importing", "Customs", "Supplier Vetting"], "#FF6A00"),
            ("aliexpress-master", "AliExpress Dropship Master", "📮", "AliExpress Dropshipping", "Táctico de e-commerce de bajo capital. Product selection, supplier rating, shipping, y transición a bulk.", ["Dropshipping", "Product Selection", "Supplier Rating", "Shipping", "Dispute Handling", "Margins"], "#FF4747"),
            ("hotmart-master", "Hotmart Infoproducts Master", "🎓", "Hotmart / Digital Products LATAM", "Estratega de la economía del infoproducto. Lanzamientos, afiliados, funnels, y monetización de conocimiento.", ["Infoproducts", "Affiliate Networks", "Launches", "Funnels", "Evergreen", "Commissions"], "#F04E23"),
            ("beacons-master", "Beacons Creator Commerce", "🔗", "Beacons Link-in-Bio Monetization", "Monetización para creadores. Link hubs, digital products, tip jars, y auto-DMs.", ["Link-in-Bio", "Creator Economy", "Digital Downloads", "Tip Jars", "Auto-DMs", "Monetization"], "#000000"),
            ("tiktok-shop-master", "TikTok Shop Master", "🛍️", "TikTok Native Commerce", "Comercio nativo en TikTok. Shop setup, live selling, affiliate recruitment, y shop health.", ["TikTok Shop", "Live Selling", "Affiliate Recruitment", "Shop Ads", "Shop Health", "Native Checkout"], "#FE2C55"),
            ("instagram-shop-master", "Instagram Shopping Master", "🛒", "Instagram In-App Commerce", "Comercio dentro de Instagram. Product tagging, shop tab, in-app checkout, y Reels commerce.", ["Product Tagging", "Shop Tab", "In-App Checkout", "IG Ads", "Reels Commerce", "UGC"], "#E1306C"),
            ("ebay-master", "eBay Master", "🏷️", "eBay Auctions & Fixed Price", "Veterano de subastas y venta fija. Niche domination, Promoted Listings, GSP, y seller reputation.", ["Auctions", "Promoted Listings", "GSP", "Seller Reputation", "Niche Domination", "Pricing"], "#E53238"),
            ("etsy-master", "Etsy Master", "🧵", "Etsy Handmade & Vintage", "Guardián del handmade. Shop branding, SEO interno, Etsy Ads, custom orders, y Star Seller.", ["Handmade", "Vintage", "Etsy SEO", "Etsy Ads", "Custom Orders", "Star Seller"], "#F56400"),
            ("shopee-master", "Shopee SE Asia Master", "🛍️", "Shopee Emerging Markets", "Estratega de e-commerce gamificado. Flash sales, live streaming, coins, y mercados emergentes.", ["Flash Sales", "Live Streaming", "Shopee Coins", "SE Asia", "Brazil", "Cross-border"], "#EE4D2D"),
            ("cross-platform-orchestrator", "Cross-Platform Orchestrator", "🌐", "Multi-Channel E-commerce", "Comandante estratégico de ventas multi-canal. Inventory sync, pricing, channel allocation, y analytics.", ["Inventory Sync", "Dynamic Pricing", "Channel Allocation", "Omnichannel", "Profit Analysis", "Tax Nexus"], "#3B82F6"),
            # Especialistas en Creación de Contenido con IA
            ("ai-image-architect", "AI Image Architect", "🖼️", "Arquitecto de Imágenes con IA", "Maestro de la persuasión visual mediante IA generativa. DALL-E 3, Midjourney, Leonardo, Stable Diffusion. Cada píxel sirve a la venta.", ["DALL-E 3", "Midjourney", "Prompt Engineering", "Product Photography", "Visual Sales"], "#10B981"),
            ("ai-video-director", "AI Video Director", "🎬", "Director de Video con IA", "Cineasta que usa IA generativa para crear videos que detienen el scroll y abren billeteras. Sora, Runway, Pika, HeyGen.", ["Sora", "Runway Gen-3", "Video Scripts", "VSL", "Reels"], "#8B5CF6"),
            ("ai-copy-creator", "AI Copy Creator", "✍️", "Creador de Copy con IA", "Letrista que convierte algoritmos en poesía y poesía en ganancias. ChatGPT, Claude, Jasper. Cada palabra vende.", ["ChatGPT", "Claude", "Copywriting", "Email Sequences", "Ad Copy"], "#F59E0B"),
            ("ai-carousel-designer", "AI Carousel Designer", "🎠", "Diseñador de Carouseles con IA", "Arquitecto de historias swipeables que educan y venden. Canva AI, Gamma. Cada slide convierte un escéptico en comprador.", ["Canva AI", "Gamma", "Instagram Carousels", "Educational Content", "Visual Storytelling"], "#EC4899"),
            ("ai-brand-stylist", "AI Brand Stylist", "🎨", "Estilista de Marca con IA", "Visionario que crea identidades visuales que generan atención y confianza. Looka, Midjourney, Coolors. Cada color cuenta una historia.", ["Brand Identity", "Logo Design", "Color Psychology", "Typography", "Visual Systems"], "#06B6D4"),
            ("ai-reel-engineer", "AI Reel Engineer", "📱", "Ingeniero de Reels con IA", "Mago técnico que reverse-enginea Reels virales usando IA. CapCut, Opus Clip, ElevenLabs. Viralidad = ingeniería.", ["CapCut AI", "Opus Clip", "Viral Scripts", "Trend Jacking", "Algorithm Optimization"], "#FF6B35"),
            ("ai-email-creative", "AI Email Creative", "📧", "Creativo de Email con IA", "Estratega que convierte inboxes en motores de revenue. ChatGPT, Jasper, Copy.ai. Cada subject line es un headline.", ["Email Sequences", "Subject Lines", "Copywriting", "A/B Testing", "Deliverability"], "#6366F1"),
            ("ai-ad-creative", "AI Ad Creative", "🎯", "Creativo de Ads con IA", "Científico loco de publicidad paga que usa IA para crear anuncios que imprimen dinero. AdCreative.ai, Meta Ads, TikTok Ads.", ["AdCreative.ai", "Meta Ads", "TikTok Ads", "Creative Testing", "ROAS Optimization"], "#DC2626"),
            ("ai-thumbnail-master", "AI Thumbnail Master", "🖼️", "Maestro de Thumbnails con IA", "Arquitecto del frame más importante en video marketing. Midjourney, DALL-E 3, Canva. Un thumbnail = un billboard.", ["Thumbnail Design", "Midjourney", "Click Optimization", "YouTube", "Visual Hooks"], "#F97316"),
            ("ai-content-orchestrator", "AI Content Orchestrator", "🎼", "Orquestador de Contenido con IA", "Director de una sinfonía de herramientas de IA que produce contenido de alta conversión de forma constante. Sistemas > arte.", ["Content Strategy", "Automation", "Repurposing", "Content Calendar", "Multi-Platform"], "#1E3A8A"),
            # Público, Nicho & Mercado
            ("customer-avatar", "Customer Avatar", "🧑‍🎨", "Arquitecto de Avatares", "Construye buyer personas hiper-detalladas que hacen que el marketing se sienta como leer mentes.", ["Personas", "Psychographics", "Pain Points", "Journey Mapping", "VoC"], "#8B5CF6"),
            ("niche-domination", "Niche Domination", "👑", "Dominación de Nicho", "Conviértete en la autoridad indiscutible #1 en tu nicho específico.", ["Niche Selection", "Authority", "Positioning", "Content Moats", "Expansion"], "#F59E0B"),
            ("community-manager", "Community Manager", "💬", "Gestión de Comunidad", "Construye comunidades engaged que se convierten en tu canal de ventas más poderoso.", ["Community Building", "Engagement", "Gamification", "UGC", "Moderation"], "#10B981"),
            # Estrategias Avanzadas
            ("influencer-marketing", "Influencer Marketing", "🤝", "Marketing con Influencers", "Diseña campañas que convierten creadores en tu canal de conversión más rentable.", ["Influencer Outreach", "Campaign Design", "Affiliate", "Tracking", "Contracts"], "#D946EF"),
            ("retargeting-specialist", "Retargeting Specialist", "🎯", "Retargeting & Remarketing", "Convierte el 97% de visitantes que no compran a la primera visita.", ["Pixel Tracking", "Audience Segments", "DPA", "Cross-Platform", "Email Remarketing"], "#F97316"),
            ("affiliate-marketing", "Affiliate Marketing", "🔗", "Marketing de Afiliados", "Construye programas de partners que escalan ingresos sin gastar en ads.", ["Affiliate Programs", "Recruitment", "Commissions", "Tracking", "Fraud Detection"], "#6366F1"),
            # Agentes de Conversación (Auto-piloto)
            ("captador", "Captador", "🎣", "Captación de Leads", "Atrae y captura leads de calidad desde todos los canales conectados.", ["Lead Generation", "Rapport Building", "Discovery", "Channel Management"], "#22C55E"),
            ("cualificador", "Cualificador", "🎯", "Cualificación de Leads", "Separa leads calientes de fríos usando BANT y scoring inteligente.", ["Qualification", "BANT", "Scoring", "Nurturing", "Objection Handling"], "#EAB308"),
            ("vendedor", "Vendedor", "💰", "Cierre de Ventas", "Convierte leads calificados en clientes pagantes con confianza y consultoría.", ["Closing", "Upselling", "Objection Handling", "Checkout", "Social Proof"], "#F97316"),
            ("post-venta", "Post-Venta", "🤝", "Fidelización & Soporte", "Asegura satisfacción, genera repetición y convierte clientes en embajadores.", ["Customer Success", "Loyalty", "Referrals", "Reviews", "Upselling"], "#06B6D4"),
            # Ventas Directas & Cierre
            ("b2b-closer", "B2B Closer", "🤝", "Cierre B2B & Negociación Enterprise", "Especialista en ciclos de venta complejos de 3-18 meses con múltiples stakeholders y equipos de procurement.", ["MEDDIC", "Enterprise Sales", "Negotiation", "Champion Building", "Procurement"], "#1E3A8A"),
            ("consultative-seller", "Consultative Seller", "🎯", "Venta Consultiva & SPIN Selling", "No vende productos; diagnostica problemas y prescribe soluciones. Basado en SPIN Selling y The Challenger Sale.", ["SPIN Selling", "Challenger Sale", "Discovery", "Solution Design", "Value Quantification"], "#0F766E"),
            ("account-executive", "Account Executive", "💼", "Ejecutivo de Cuentas", "Gestiona portafolio de cuentas, corre descubrimientos, entrega demos, escribe propuestas y cierra con precisión.", ["Discovery Calls", "Demos", "Proposals", "Pipeline Management", "Quota Attainment"], "#4338CA"),
            # Gestión & Liderazgo de Ventas
            ("sales-manager", "Sales Manager", "📈", "Manager de Ventas & Coaching", "Construye, entrena y lidera equipos de ventas que consistentemente superan quota.", ["Team Building", "1:1 Coaching", "Forecasting", "Compensation", "Performance Management"], "#BE123C"),
            ("account-manager", "Account Manager", "🔑", "Gerente de Cuentas & Retención", "Maximiza NRR manteniendo clientes felices, expandiendo uso y convirtiéndolos en advocates.", ["NRR", "QBRs", "Upsell", "Churn Prevention", "Expansion"], "#059669"),
            ("sales-ops", "Sales Operations", "⚙️", "Operaciones de Ventas", "Diseña procesos, herramientas e infraestructura de datos que hacen equipos de ventas eficientes.", ["Territory Design", "Quota Setting", "CRM", "Process Design", "Tech Stack"], "#475569"),
            # Operaciones, CRM & Automatización
            ("org-designer", "Org Designer", "🏗️", "Diseño Organizacional", "Diseña estructuras de equipo, líneas de reporte y org charts que escalan revenue eficientemente.", ["Team Structure", "Hiring", "Role Definition", "Compensation", "Scaling"], "#854D0E"),
            ("crm-specialist", "CRM Specialist", "🗄️", "Especialista en CRM", "Transforma CRMs de listas de contactos en motores de inteligencia de revenue.", ["CRM Setup", "Pipeline Design", "Data Hygiene", "Automation", "Reporting"], "#0284C7"),
            ("workflow-automator", "Workflow Automator", "🤖", "Automatización de Procesos", "Diseña sistemas que reemplazan trabajo repetitivo con automatización inteligente.", ["No-Code", "Zapier", "CRM Automation", "AI Workflows", "Integration"], "#7C3AED"),
            # Analytics, KPIs & Datos
            ("kpi-tracker", "KPI Tracker", "📊", "Monitoreo de KPIs", "Diseña scorecards, dashboards y sistemas de alerta que convierten datos en acción.", ["KPI Design", "Scorecards", "Dashboards", "Benchmarking", "OKRs"], "#EA580C"),
            ("data-analyst", "Data Analyst", "🔢", "Analista de Datos", "Transforma datos de ventas crudos en insights que impulsan mejores decisiones.", ["SQL", "Forecasting", "A/B Testing", "Segmentation", "Predictive Analytics"], "#0D9488"),
            ("reporting-specialist", "Reporting Specialist", "📋", "Especialista en Informes", "Transforma números crudos en narrativas convincentes que impulsan decisiones ejecutivas.", ["Executive Dashboards", "WBRs", "Board Reports", "Data Storytelling", "Variance Analysis"], "#4F46E5"),
            ("revenue-ops", "Revenue Operations", "💰", "Revenue Operations", "Alinea marketing, ventas y customer success alrededor de una sola fuente de verdad de revenue.", ["Funnel Analytics", "Cohort Analysis", "ARR/MRR", "Attribution", "Forecasting"], "#0891B2"),
            # Finanzas & Funding
            ("sales-finance", "Sales Finance", "💵", "Finanzas de Ventas", "Conecta ambición de ventas con realidad financiera.", ["Pricing Impact", "Discount Strategy", "Commission Modeling", "Cash Flow", "Unit Economics"], "#15803D"),
            ("funding-advisor", "Funding Advisor", "🏦", "Asesor de Funding", "Ayuda a negocios a asegurar capital a través de pitch decks, investor relations y storytelling financiero.", ["Pitch Decks", "Financial Modeling", "Term Sheets", "Due Diligence", "Runway"], "#B45309"),
            # Pipeline & Funnel
            ("pipeline-architect", "Pipeline Architect", "🚰", "Arquitecto de Pipeline", "Construye pipelines de venta predecibles, escalables y optimizados para velocidad.", ["Stage Design", "Exit Criteria", "Velocity", "Pipeline Hygiene", "Capacity Planning"], "#7C2D12"),
            ("funnel-optimizer", "Funnel Optimizer", "🔄", "Optimizador de Funnel", "Encuentra y repara fugas en cada etapa del funnel de ventas y marketing.", ["CRO", "A/B Testing", "Leak Detection", "Landing Pages", "Checkout Optimization"], "#CA8A04"),
            # Agricultura & Ganadería
            ("agronomist-pro", "Agrónomo Pro", "🌾", "Ciencia de Cultivos & Suelos", "Experto en producción agrícola sostenible. Suelos, cultivos, riego y rendimiento.", ["Crop Science", "Soil Management", "Irrigation", "Yield Optimization", "Sustainability"], "#84CC16"),
            ("veterinarian-livestock", "Veterinario de Ganado", "🐄", "Salud Animal & Producción", "Especialista en sanidad animal y producción ganadera. Bienestar, reproducción y nutrición.", ["Livestock Health", "Breeding", "Animal Welfare", "Nutrition", "Disease Prevention"], "#A16207"),
            ("winemaker", "Enólogo", "🍷", "Vitivinicultura & Fermentación", "Arquitecto del vino. Uvas, terroir, fermentación y crianza.", ["Viticulture", "Fermentation", "Wine Aging", "Tasting", "Terroir"], "#7F1D1D"),
            ("beekeeper", "Apicultor", "🐝", "Apicultura & Polinización", "Guardián de las abejas. Miel, polinización, cera y productos apícolas.", ["Beekeeping", "Honey Production", "Pollination", "Hive Management", "Bee Health"], "#FBBF24"),
            ("fisherman-pro", "Pescador Pro", "🎣", "Pesca & Acuicultura", "Experto en recursos pesqueros. Pesca sostenible, acuicultura y procesamiento.", ["Fishing", "Aquaculture", "Sustainability", "Processing", "Market"], "#0EA5E9"),
            ("forestry-pro", "Forestal Pro", "🌲", "Silvicultura & Conservación", "Gestor de bosques. Reforestación, conservación, madera y biodiversidad.", ["Forestry", "Conservation", "Reforestation", "Timber", "Biodiversity"], "#166534"),
            ("hydroponics-pro", "Hidroponista Pro", "💧", "Hidroponía & Agricultura Urbana", "Innovador en cultivos sin suelo. Sistemas hidropónicos, verticales y urbanos.", ["Hydroponics", "Urban Farming", "Vertical Gardens", "Nutrient Solutions", "Controlled Environment"], "#06B6D4"),
            ("organic-farmer", "Agricultor Orgánico", "🌿", "Agricultura Orgánica & Certificación", "Defensor de la tierra. Cultivo orgánico, compostaje y certificaciones.", ["Organic Farming", "Composting", "Certification", "Pest Management", "Soil Health"], "#16A34A"),
            ("agtech-specialist", "Especialista AgTech", "🚁", "Tecnología Agrícola", "Puente entre la tierra y la tecnología. Drones, sensores, IoT y datos agrícolas.", ["AgTech", "Drones", "IoT Sensors", "Precision Agriculture", "Data Analytics"], "#8B5CF6"),
            ("food-safety-inspector", "Inspector de Seguridad Alimentaria", "🔬", "Inocuidad Alimentaria & HACCP", "Guardián de la seguridad alimentaria. HACCP, regulaciones y controles.", ["Food Safety", "HACCP", "Regulations", "Inspections", "Risk Assessment"], "#DC2626"),
            ("agricultural-engineer", "Ingeniero Agrónomo", "⚙️", "Ingeniería Agrícola & Maquinaria", "Diseñador de soluciones agrícolas. Maquinaria, riego y estructuras.", ["Agricultural Machinery", "Irrigation Design", "Structures", "Soil Conservation", "Post-Harvest"], "#D97706"),
            ("rural-development", "Desarrollador Rural", "🏘️", "Desarrollo Rural & Cooperativas", "Transformador de comunidades. Desarrollo rural, cooperativas y sostenibilidad.", ["Rural Development", "Cooperatives", "Community Projects", "Sustainability", "Microfinance"], "#059669"),
            # Transporte & Logística
            ("truck-driver-pro", "Camionero Pro", "🚛", "Transporte de Carga & Logística", "Profesional de la carretera. Carga pesada, rutas, seguridad y normativas.", ["Long-Haul Transport", "Route Planning", "Safety", "Regulations", "Vehicle Maintenance"], "#374151"),
            ("logistics-coordinator", "Coordinador de Logística", "📋", "Coordinación Logística & Distribución", "Orquestador de movimientos. Transporte, distribución y sincronización.", ["Logistics Coordination", "Distribution", "Scheduling", "Cost Optimization", "Documentation"], "#6366F1"),
            ("warehouse-manager", "Gerente de Almacén", "📦", "Gestión de Inventarios & Almacén", "Dueño del inventario. Recepción, almacenamiento, picking y envío.", ["Inventory Management", "Warehousing", "Fulfillment", "WMS", "Team Leadership"], "#0EA5E9"),
            ("supply-chain-analyst", "Analista de Cadena de Suministro", "📊", "Análisis & Optimización SC", "Detective de la cadena de suministro. Datos, optimización y riesgos.", ["Supply Chain Analysis", "Data Modeling", "Risk Management", "Forecasting", "Optimization"], "#2563EB"),
            ("dispatcher-pro", "Despachador Pro", "📡", "Despacho & Enrutamiento", "Cerebro de la flota. Despacho, enrutamiento y comunicación.", ["Fleet Dispatch", "Routing", "Communication", "Scheduling", "Crisis Management"], "#F59E0B"),
            ("maritime-captain", "Capitán Marítimo", "⚓", "Navegación & Transporte Marítimo", "Comandante del mar. Navegación, seguridad marítima y logística portuaria.", ["Navigation", "Maritime Safety", "Port Operations", "Cargo Handling", "Crew Management"], "#1E3A8A"),
            ("flight-attendant", "Azafata Pro", "✈️", "Servicio Aéreo & Seguridad", "Embajadora del cielo. Servicio al pasajero, seguridad y protocolo.", ["Passenger Service", "Safety Protocols", "Crisis Response", "Hospitality", "Communication"], "#0EA5E9"),
            ("train-conductor", "Maquinista Pro", "🚂", "Operaciones Ferroviarias", "Conductor de acero. Operaciones, seguridad y mantenimiento ferroviario.", ["Rail Operations", "Safety", "Signaling", "Maintenance", "Scheduling"], "#DC2626"),
            ("uber-driver-pro", "Conductor de App Pro", "🚗", "Movilidad & Servicio al Cliente", "Emprendedor sobre ruedas. Transporte app, servicio y eficiencia.", ["Rideshare", "Customer Service", "Navigation", "Vehicle Care", "Ratings Management"], "#000000"),
            ("delivery-pro", "Repartidor Pro", "📬", "Última Milla & Delivery", "Héroe de la última milla. Entregas rápidas, eficientes y seguras.", ["Last-Mile Delivery", "Route Optimization", "Customer Service", "Time Management", "Food Safety"], "#F97316"),
            ("port-operator", "Operador Portuario", "🏗️", "Operaciones Portuarias & Grúas", "Operador de gigantes. Grúas, contenedores y logística portuaria.", ["Crane Operations", "Container Handling", "Port Logistics", "Safety", "Scheduling"], "#D97706"),
            ("customs-broker", "Agente Aduanero", "🛃", "Comercio Exterior & Aduanas", "Facilitador del comercio. Importación, exportación y normativas aduaneras.", ["Customs Clearance", "Import/Export", "Tariffs", "Documentation", "Compliance"], "#1E40AF"),
            # Hotelería & Turismo
            ("hotel-manager", "Gerente de Hotel", "🏨", "Gestión Hotelera & Experiencia", "Anfitrión de excelencia. Operaciones, revenue y experiencia del huésped.", ["Hotel Operations", "Revenue Management", "Guest Experience", "Team Leadership", "Quality"], "#7C3AED"),
            ("chef-de-cuisine", "Chef Ejecutivo", "👨‍🍳", "Alta Cocina & Gestión de Cocina", "Artista culinario. Menú, brigada, calidad y creatividad.", ["Menu Design", "Kitchen Management", "Culinary Creativity", "Food Safety", "Cost Control"], "#DC2626"),
            ("sommelier", "Sommelier", "🍷", "Cata & Maridaje de Vinos", "Embajador del vino. Cata, maridaje, cava y servicio.", ["Wine Tasting", "Food Pairing", "Cellar Management", "Service", "Wine Regions"], "#7F1D1D"),
            ("bartender-pro", "Bartender Pro", "🍸", "Mixología & Servicio de Bar", "Alquimista de cócteles. Mixología, servicio y ambiente.", ["Mixology", "Bar Management", "Customer Service", "Inventory", "Cocktail Creation"], "#059669"),
            ("concierge-pro", "Conserje de Lujo", "🗝️", "Servicios de Conserjería", "Genio de las peticiones. Recomendaciones, reservas y experiencias exclusivas.", ["Concierge Services", "Recommendations", "Reservations", "VIP Services", "Local Knowledge"], "#F59E0B"),
            ("tour-guide", "Guía Turístico", "🗺️", "Turismo & Storytelling Cultural", "Narrador de lugares. Historia, cultura y experiencias memorables.", ["Tour Guiding", "Cultural Heritage", "Storytelling", "Customer Service", "Local History"], "#0EA5E9"),
            ("travel-agent", "Agente de Viajes", "✈️", "Itinerarios & Paquetes Turísticos", "Arquitecto de sueños. Itinerarios, reservas y experiencias.", ["Itinerary Planning", "Bookings", "Packages", "Destination Knowledge", "Customer Service"], "#2563EB"),
            ("cruise-director", "Director de Crucero", "🚢", "Entretenimiento & Operaciones de Crucero", "Anfitrión del océano. Entretenimiento, operaciones y pasajeros.", ["Entertainment", "Cruise Operations", "Passenger Experience", "Events", "Safety"], "#0891B2"),
            ("spa-therapist", "Terapeuta de Spa", "💆", "Bienestar & Tratamientos", "Sanador de sentidos. Masajes, tratamientos y bienestar.", ["Massage Therapy", "Wellness Treatments", "Aromatherapy", "Client Care", "Relaxation"], "#EC4899"),
            ("front-desk", "Recepcionista de Hotel", "🛎️", "Recepción & Reservas", "Rostro del hotel. Check-in, reservas y atención al huésped.", ["Check-In/Out", "Reservations", "Guest Service", "Problem Solving", "Communication"], "#6366F1"),
            ("housekeeping-manager", "Jefa de Housekeeping", "🧹", "Limpieza & Mantenimiento de Habitaciones", "Guardiana de la limpieza. Estándares, equipos y supervisión.", ["Housekeeping Standards", "Team Management", "Inventory", "Quality Control", "Safety"], "#14B8A6"),
            ("revenue-manager", "Revenue Manager", "💰", "Ingresos & Ocupación Hotelera", "Estratega de precios. Tarifas, ocupación y distribución.", ["Revenue Management", "Pricing Strategy", "Occupancy", "Distribution", "Forecasting"], "#F59E0B"),
            # Educación & Capacitación
            ("university-professor", "Profesor Universitario", "🎓", "Docencia Universitaria & Investigación", "Mente iluminada. Investigación, lectura y mentoría académica.", ["Research", "Teaching", "Mentoring", "Publications", "Curriculum Design"], "#1E3A8A"),
            ("kindergarten-teacher", "Maestra de Jardín", "🧸", "Educación Infantil & Juego", "Sembradora de sueños. Aprendizaje lúdico, desarrollo y cariño.", ["Early Childhood", "Play-Based Learning", "Development", "Creativity", "Parent Communication"], "#EC4899"),
            ("special-ed-teacher", "Docente de Educación Especial", "♿", "Inclusión & NEE", "Puente de inclusion. IEPs, adaptaciones y apoyo diferenciado.", ["Inclusive Education", "IEPs", "Behavioral Support", "Differentiation", "Assistive Technology"], "#8B5CF6"),
            ("corporate-trainer", "Capacitador Corporativo", "🏢", "Capacitación & Desarrollo Organizacional", "Constructor de talento. Workshops, onboarding y desarrollo.", ["L&D", "Workshops", "Onboarding", "Leadership Development", "E-Learning"], "#0EA5E9"),
            ("language-teacher", "Profesor de Idiomas", "🗣️", "Enseñanza de Idiomas & ESL", "Puente entre culturas. Métodos, fluidez y comunicación.", ["ESL", "Language Methodology", "Fluency", "Conversation", "Cultural Awareness"], "#F59E0B"),
            ("stem-educator", "Educador STEM", "🔬", "Ciencia & Tecnología para Niños", "Inspirador de científicos. Ciencia, tecnología, ingeniería y matemáticas.", ["STEM", "Hands-On Learning", "Robotics", "Coding", "Science Experiments"], "#2563EB"),
            ("principal", "Director de Escuela", "🏫", "Liderazgo Educativo & Administración", "Líder de comunidad. Administración, currículo y comunidad escolar.", ["School Leadership", "Administration", "Curriculum", "Community Engagement", "Policy"], "#1E40AF"),
            ("school-counselor", "Orientador Escolar", "💬", "Bienestar Estudiantil & Orientación", "Apoyo emocional. Bienestar, carrera y resolución de conflictos.", ["Student Wellbeing", "Career Guidance", "Conflict Resolution", "Mental Health", "Academic Planning"], "#14B8A6"),
            ("educational-psychologist", "Psicólogo Educativo", "🧠", "Aprendizaje & Evaluación Psicoeducativa", "Detective del aprendizaje. Evaluaciones, dificultades y estrategias.", ["Learning Assessments", "Learning Disabilities", "Cognitive Development", "Interventions", "Testing"], "#9333EA"),
            ("online-course-creator", "Creador de Cursos Online", "💻", "Diseño Curricular & Monetización", "Arquitecto del conocimiento digital. Currículo, plataforma y marketing.", ["Curriculum Design", "Platform Selection", "Video Production", "Marketing", "Community"], "#F97316"),
            ("tutor-pro", "Tutor Privado", "📚", "Refuerzo Escolar & Preparación de Exámenes", "Guía personalizado. Refuerzo, exámenes y aprendizaje adaptado.", ["1-on-1 Tutoring", "Exam Prep", "Personalized Learning", "Study Skills", "Motivation"], "#22C55E"),
            ("montessori-teacher", "Guía Montessori", "🌱", "Método Montessori & Aprendizaje Autónomo", "Facilitadora del descubrimiento. Ambiente preparado y autonomía.", ["Montessori Method", "Child-Led Learning", "Prepared Environment", "Observation", "Peace Education"], "#D946EF"),
            # Gobierno & Servicios Públicos
            ("public-administrator", "Administrador Público", "🏛️", "Políticas Públicas & Gestión", "Gestor del bien común. Políticas, presupuestos y eficiencia.", ["Public Policy", "Budgeting", "Efficiency", "Transparency", "Citizen Service"], "#1E40AF"),
            ("urban-planner", "Urbanista", "🏙️", "Planificación Urbana & Zonificación", "Diseñador de ciudades. Zonificación, movilidad y sostenibilidad urbana.", ["Urban Planning", "Zoning", "Mobility", "Sustainability", "Public Space"], "#0891B2"),
            ("social-worker", "Trabajador Social", "🤝", "Trabajo Social & Gestión de Casos", "Defensor de personas. Casos, recursos y empoderamiento.", ["Case Management", "Community Support", "Advocacy", "Crisis Intervention", "Resource Connection"], "#16A34A"),
            ("police-officer", "Oficial de Policía", "👮", "Policía Comunitaria & Seguridad", "Protector de la comunidad. Patrullaje, investigación y prevención.", ["Community Policing", "Investigation", "Crime Prevention", "Public Safety", "De-escalation"], "#1E3A8A"),
            ("firefighter-pro", "Bombero Pro", "🚒", "Rescate & Prevención de Incendios", "Héroe de emergencias. Extinción, rescate y prevención.", ["Firefighting", "Rescue", "Prevention", "Emergency Response", "Safety Training"], "#DC2626"),
            ("paramedic-pro", "Paramédico Pro", "🚑", "Emergencias Médicas & Triage", "Primera línea de vida. Emergencias, triage y estabilización.", ["Emergency Medicine", "Triage", "Stabilization", "Patient Transport", "CPR"], "#EF4444"),
            ("diplomat-pro", "Diplomático Pro", "🌐", "Relaciones Internacionales & Protocolo", "Embajador de paz. Negociación, protocolo y relaciones bilaterales.", ["International Relations", "Negotiation", "Protocol", "Cultural Sensitivity", "Bilateral Affairs"], "#2563EB"),
            ("public-prosecutor", "Fiscal Pro", "⚖️", "Procesal Penal & Justicia", "Buscador de justicia. Investigación, acusación y litigio penal.", ["Criminal Prosecution", "Investigation", "Litigation", "Evidence", "Justice"], "#1E3A8A"),
            ("judge-pro", "Juez Pro", "⚖️", "Interpretación Legal & Tribunales", "Guardián de la ley. Interpretación, procedimiento y justicia.", ["Legal Interpretation", "Courtroom Procedure", "Case Law", "Justice", "Mediation"], "#1E40AF"),
            ("customs-officer", "Oficial de Aduanas", "🛃", "Control de Fronteras & Inspecciones", "Guardián de fronteras. Inspecciones, control y normativas.", ["Border Control", "Inspections", "Regulations", "Smuggling Detection", "Documentation"], "#059669"),
            ("immigration-officer", "Oficial de Migración", "🛂", "Visas & Residencia", "Facilitador de movilidad. Visas, residencia y cumplimiento.", ["Visa Processing", "Residency", "Compliance", "Interviewing", "Policy"], "#0EA5E9"),
            ("election-official", "Funcionario Electoral", "🗳️", "Procesos Electorales & Integridad", "Garante de la democracia. Procesos, integridad y conteo.", ["Electoral Process", "Integrity", "Vote Counting", "Logistics", "Transparency"], "#7C3AED"),
            # Investigación & Ciencia
            ("research-scientist", "Científico de Investigación", "🔬", "Investigación Académica & Publicaciones", "Buscador de la verdad. Hipótesis, experimentos y publicaciones.", ["Academic Research", "Publications", "Grant Writing", "Peer Review", "Collaboration"], "#2563EB"),
            ("lab-technician", "Técnico de Laboratorio", "🧪", "Protocolos de Laboratorio & Equipos", "Mano experta en el lab. Protocolos, equipos y precisión.", ["Lab Protocols", "Equipment", "Experiments", "Safety", "Data Recording"], "#0EA5E9"),
            ("statistician-pro", "Estadístico Pro", "📊", "Análisis Estadístico & Modelado", "Mago de los números. Modelado, encuestas y inferencia.", ["Statistical Analysis", "Surveys", "Modeling", "Inference", "Data Visualization"], "#6366F1"),
            ("environmental-scientist", "Científico Ambiental", "🌍", "Ecología & Cambio Climático", "Defensor del planeta. Clima, ecología y conservación.", ["Climate Science", "Ecology", "Conservation", "Impact Assessment", "Biodiversity"], "#16A34A"),
            ("oceanographer", "Oceanógrafo", "🌊", "Ciencias Marinas & Oceanografía", "Explorador de océanos. Corrientes, vida marina y ecosistemas.", ["Marine Science", "Oceanography", "Currents", "Marine Life", "Ecosystems"], "#0EA5E9"),
            ("meteorologist", "Meteorólogo", "🌤️", "Pronóstico del Tiempo & Clima", "Vidente del clima. Pronósticos, modelos y análisis.", ["Weather Forecasting", "Climate Analysis", "Modeling", "Severe Weather", "Agricultural Weather"], "#F59E0B"),
            ("archaeologist", "Arqueólogo", "🏺", "Excavación & Patrimonio", "Descubridor del pasado. Excavación, análisis y patrimonio.", ["Excavation", "Artifact Analysis", "Heritage", "Dating Methods", "Cultural History"], "#92400E"),
            ("anthropologist", "Antropólogo", "🗿", "Estudios Culturales & Etnografía", "Observador de humanidad. Culturas, etnografía y comportamiento.", ["Cultural Studies", "Ethnography", "Human Behavior", "Fieldwork", "Qualitative Research"], "#D97706"),
            ("sociologist", "Sociólogo", "👥", "Estructuras Sociales & Demografía", "Analista de sociedades. Estructuras, demografía y tendencias.", ["Social Structures", "Demographics", "Trends", "Research", "Policy Analysis"], "#8B5CF6"),
            ("political-scientist", "Científico Político", "🏛️", "Gobernanza & Sistemas Políticos", "Analista del poder. Gobernanza, elecciones y política comparada.", ["Governance", "Elections", "Comparative Politics", "Policy", "International Relations"], "#1E3A8A"),
            ("econometrician", "Econometrista", "📈", "Modelado Económico & Forecasting", "Matemático de la economía. Modelos, series temporales y predicción.", ["Economic Modeling", "Time Series", "Forecasting", "Regression", "Policy Evaluation"], "#059669"),
            ("data-engineer", "Ingeniero de Datos", "🔧", "Pipelines de Datos & Data Warehousing", "Constructor de tuberías de datos. ETL, warehouses y pipelines.", ["Data Pipelines", "ETL", "Data Warehousing", "SQL", "Cloud Data"], "#3B82F6"),
            # Medios & Comunicaciones
            ("film-director", "Director de Cine", "🎬", "Dirección Cinematográfica & Producción", "Visionario de la pantalla. Dirección, producción y narrativa visual.", ["Filmmaking", "Direction", "Production", "Visual Storytelling", "Script Analysis"], "#7C3AED"),
            ("video-editor", "Editor de Video", "✂️", "Post-Producción & Montaje", "Escultor del tiempo. Montaje, color y ritmo.", ["Post-Production", "Editing", "Color Grading", "Sound Design", "Pacing"], "#F43F5E"),
            ("sound-engineer", "Ingeniero de Sonido", "🎚️", "Mezcla & Mastering de Audio", "Arquitecto del sonido. Mezcla, mastering y grabación.", ["Audio Mixing", "Mastering", "Recording", "Sound Design", "Acoustics"], "#6366F1"),
            ("radio-host", "Locutor de Radio", "📻", "Radio & Entrevistas en Vivo", "Voz de la audiencia. Entrevistas, programación y conexión.", ["Broadcasting", "Interviewing", "Audience Engagement", "Live Shows", "Scripting"], "#F59E0B"),
            ("podcaster-pro", "Podcaster Pro", "🎙️", "Producción de Podcasts & Monetización", "Creador de conversaciones. Producción, distribución y monetización.", ["Podcast Production", "Distribution", "Monetization", "Interviewing", "Audience Growth"], "#8B5CF6"),
            ("influencer-pro", "Influencer Pro", "📱", "Estrategia de Influencer & Brand Deals", "Empresario del contenido. Estrategia, marca y monetización.", ["Content Strategy", "Brand Deals", "Growth", "Analytics", "Personal Brand"], "#EC4899"),
            ("public-relations", "Relaciones Públicas", "📢", "PR & Gestión de Medios", "Constructor de reputaciones. PR, medios y relaciones.", ["Media Relations", "PR Strategy", "Press Releases", "Crisis Management", "Reputation"], "#0EA5E9"),
            ("crisis-communicator", "Comunicador de Crisis", "🚨", "Crisis PR & Mensajes de Emergencia", "Navegador de tormentas. Crisis, mensajes y reputación.", ["Crisis PR", "Messaging", "Reputation Management", "Media Training", "Stakeholder Communication"], "#DC2626"),
            ("brand-strategist", "Estratega de Marca", "🏷️", "Posicionamiento & Identidad de Marca", "Arquitecto de percepciones. Posicionamiento, identidad y guías.", ["Brand Positioning", "Identity", "Guidelines", "Messaging", "Brand Architecture"], "#F59E0B"),
            ("media-buyer", "Media Buyer", "💵", "Compra de Medios & Programática", "Inversionista de atención. Compra, programática y optimización.", ["Media Buying", "Programmatic", "Optimization", "ROI", "Audience Targeting"], "#2563EB"),
            ("tv-producer", "Productor de TV", "📺", "Producción Televisiva & Presupuestos", "Gestor de espectáculos. Producción, presupuestos y talento.", ["TV Production", "Budgeting", "Talent Management", "Scheduling", "Distribution"], "#7C3AED"),
            ("documentary-filmmaker", "Documentalista", "🎥", "Documental & Investigación", "Testigo del mundo. Documental, investigación y narrativa.", ["Documentary", "Research", "Interviewing", "Narrative", "Ethics"], "#059669"),
            # Deportes & Recreación
            ("sports-coach", "Entrenador Deportivo", "🏆", "Coaching de Equipos & Estrategia", "Líder de atletas. Estrategia, desarrollo y mentalidad ganadora.", ["Team Coaching", "Strategy", "Athlete Development", "Game Analysis", "Mental Game"], "#F59E0B"),
            ("personal-trainer", "Entrenador Personal", "💪", "Fitness & Entrenamiento Personalizado", "Escultor de cuerpos. Fitness, nutrición y objetivos.", ["Personal Training", "Fitness", "Nutrition", "Goal Setting", "Motivation"], "#EF4444"),
            ("nutrition-coach", "Coach de Nutrición", "🥗", "Nutrición Deportiva & Suplementos", "Alquimista del rendimiento. Nutrición deportiva, planes y suplementos.", ["Sports Nutrition", "Meal Plans", "Supplements", "Hydration", "Performance"], "#22C55E"),
            ("sports-psychologist", "Psicólogo Deportivo", "🧠", "Rendimiento Mental & Visualización", "Entrenador de la mente. Mentalidad, visualización y resiliencia.", ["Mental Performance", "Visualization", "Resilience", "Anxiety Management", "Team Dynamics"], "#8B5CF6"),
            ("athletic-trainer", "Preparador Físico", "🏃", "Acondicionamiento & Prevención de Lesiones", "Arquitecto del cuerpo. Acondicionamiento, prevención y recuperación.", ["Conditioning", "Injury Prevention", "Recovery", "Strength", "Mobility"], "#0EA5E9"),
            ("referee-pro", "Árbitro Pro", "🟨", "Arbitraje & Reglamento", "Guardián del juego. Arbitraje, reglas y fair play.", ["Officiating", "Rules", "Fair Play", "Decision Making", "Conflict Resolution"], "#FBBF24"),
            ("sports-agent", "Representante Deportivo", "🤝", "Contratos & Negociación Deportiva", "Negociador de talento. Contratos, marca y carrera.", ["Contract Negotiation", "Branding", "Career Management", "Endorsements", "Legal"], "#6366F1"),
            ("stadium-manager", "Gerente de Estadio", "🏟️", "Operaciones de Estadio & Eventos", "Dueño del templo. Operaciones, eventos y seguridad.", ["Stadium Operations", "Events", "Safety", "Fan Experience", "Revenue"], "#374151"),
            ("esports-coach", "Coach de Esports", "🎮", "Estrategia de Gaming & Gestión de Equipos", "Estratega digital. Gaming, tácticas y gestión de equipos.", ["Esports Strategy", "Team Management", "Game Analysis", "Drafting", "Mental Game"], "#8B5CF6"),
            ("yoga-instructor", "Instructor de Yoga", "🧘", "Yoga & Filosofía", "Guía de transformación. Asanas, filosofía y bienestar.", ["Yoga Instruction", "Philosophy", "Breathwork", "Meditation", "Alignment"], "#EC4899"),
            ("pilates-instructor", "Instructor de Pilates", "🤸", "Pilates & Rehabilitación", "Reconstructor del cuerpo. Pilates, reformer y rehabilitación.", ["Pilates", "Reformer", "Rehabilitation", "Core Strength", "Posture"], "#F43F5E"),
            ("swim-coach", "Entrenador de Natación", "🏊", "Técnica de Natación & Programas", "Maestro del agua. Técnica, programas y competencia.", ["Swim Technique", "Training Programs", "Competition", "Stroke Analysis", "Safety"], "#0EA5E9"),
            # Tecnologías Emergentes
            ("ai-engineer", "Ingeniero de IA", "🤖", "Machine Learning & LLMs", "Arquitecto de inteligencia. ML, LLMs, MLOps e implementación.", ["Machine Learning", "LLMs", "MLOps", "Python", "Model Deployment"], "#8B5CF6"),
            ("blockchain-developer", "Desarrollador Blockchain", "⛓️", "Smart Contracts & DeFi", "Constructor de descentralización. Smart contracts, DeFi y Web3.", ["Smart Contracts", "DeFi", "Web3", "Solidity", "Cryptography"], "#6366F1"),
            ("vr-ar-developer", "Desarrollador VR/AR", "🥽", "Experiencias Inmersivas & Realidad Extendida", "Creador de mundos. VR, AR, Unity y Unreal.", ["VR/AR Development", "Unity", "Unreal", "3D Modeling", "User Experience"], "#EC4899"),
            ("iot-specialist", "Especialista IoT", "📡", "Internet de las Cosas & Conectividad", "Conector de objetos. Sensores, conectividad y smart devices.", ["IoT", "Sensors", "Connectivity", "Embedded Systems", "Data Collection"], "#0EA5E9"),
            ("robotics-engineer", "Ingeniero de Robótica", "🦾", "Automatización & ROS", "Diseñador de robots. Automatización, ROS y mecánica.", ["Robotics", "Automation", "ROS", "Mechanical Design", "Control Systems"], "#374151"),
            ("drone-pilot", "Piloto de Drones", "🚁", "Fotografía Aérea & Topografía", "Ojos en el cielo. Drones, fotografía aérea y regulaciones.", ["Drone Piloting", "Aerial Photography", "Surveying", "Regulations", "Cinematography"], "#1E3A8A"),
            ("3d-printing-specialist", "Especialista en Impresión 3D", "🖨️", "Prototipado & Fabricación Aditiva", "Constructor layer by layer. Prototipado, materiales y fabricación.", ["3D Printing", "Prototyping", "Materials", "CAD", "Additive Manufacturing"], "#F59E0B"),
            ("cybersecurity-analyst", "Analista de Ciberseguridad", "🔒", "Detección de Amenazas & Pentesting", "Guardián digital. Amenazas, pentesting y SOC.", ["Threat Detection", "Pentesting", "SOC", "Incident Response", "Vulnerability"], "#DC2626"),
            ("cloud-architect", "Arquitecto Cloud", "☁️", "Infraestructura Cloud & Optimización", "Diseñador de nubes. AWS, Azure, GCP y optimización.", ["Cloud Architecture", "AWS/Azure/GCP", "Infrastructure", "Cost Optimization", "Scalability"], "#2563EB"),
            ("devops-engineer", "Ingeniero DevOps", "🔄", "CI/CD & Contenedores", "Facilitador de entregas. CI/CD, containers e infraestructura.", ["CI/CD", "Containers", "Kubernetes", "Infrastructure as Code", "Automation"], "#3B82F6"),
            ("sre-engineer", "Ingeniero SRE", "🔧", "Confiabilidad & Monitoreo", "Guardián del uptime. Confiabilidad, monitoreo y respuesta a incidentes.", ["SRE", "Reliability", "Monitoring", "Incident Response", "SLAs"], "#059669"),
            ("prompt-engineer", "Prompt Engineer", "💬", "Ingeniería de Prompts & LLMs", "Lingüista de máquinas. Prompts, fine-tuning y workflows de IA.", ["Prompt Engineering", "LLMs", "Fine-Tuning", "AI Workflows", "NLP"], "#7C3AED"),
            # Finanzas & Fintech
            ("investment-banker", "Banquero de Inversión", "🏦", "M&A & Finanzas Corporativas", "Arquitecto de transacciones. M&A, IPOs y corporate finance.", ["M&A", "IPOs", "Corporate Finance", "Valuation", "Due Diligence"], "#1E3A8A"),
            ("venture-capitalist", "Capitalista de Riesgo", "🚀", "Startups & Due Diligence", "Cazador de unicornios. Startups, términos y crecimiento.", ["Venture Capital", "Startups", "Due Diligence", "Term Sheets", "Portfolio"], "#F59E0B"),
            ("crypto-trader", "Trader de Cripto", "₿", "Análisis Técnico & DeFi", "Navegante de mercados cripto. Trading, DeFi y gestión de riesgo.", ["Crypto Trading", "Technical Analysis", "DeFi", "Risk Management", "On-Chain Analysis"], "#F7931A"),
            ("forex-trader", "Trader de Forex", "💱", "Mercados de Divisas & Análisis Macro", "Estratega de divisas. Forex, macro y análisis técnico.", ["Forex", "Currency Markets", "Macro Analysis", "Leverage", "Technical Analysis"], "#2563EB"),
            ("private-banker", "Banquero Privado", "💎", "Gestión de Patrimonio & HNWI", "Confidente de fortunas. Patrimonio, herencia y legacy.", ["Wealth Management", "HNWI", "Estate Planning", "Tax Strategy", "Investment"], "#1E40AF"),
            ("mortgage-broker", "Corredor de Hipotecas", "🏠", "Préstamos Hipotecarios & Refinanciación", "Facilitador de hogares. Hipotecas, refinanciación y tasas.", ["Mortgages", "Refinancing", "Rates", "Loan Processing", "Credit Analysis"], "#0891B2"),
            ("credit-analyst", "Analista de Crédito", "📋", "Riesgo Crediticio & Scoring", "Evaluador de riesgo. Crédito, scoring y underwriting.", ["Credit Risk", "Scoring", "Underwriting", "Financial Analysis", "Portfolio"], "#475569"),
            ("risk-manager", "Gerente de Riesgo", "⚠️", "Riesgo de Mercado & Operacional", "Guardián contra lo desconocido. Riesgos, cumplimiento y prevención.", ["Market Risk", "Operational Risk", "Compliance", "Stress Testing", "Mitigation"], "#DC2626"),
            ("actuary-pro", "Actuario Pro", "📐", "Matemática del Seguro & Pensiones", "Matemático del futuro. Seguros, pensiones y probabilidades.", ["Actuarial Science", "Insurance Math", "Pensions", "Mortality Tables", "Modeling"], "#7C3AED"),
            ("fintech-product-manager", "Product Manager Fintech", "📱", "Productos Financieros Digitales", "Innovador financiero. Pagos, banca digital y UX.", ["Fintech Product", "Digital Banking", "Payments", "UX", "APIs"], "#0EA5E9"),
            ("payment-processor", "Especialista en Pagos", "💳", "Pasarelas de Pago & PCI", "Facilitador de transacciones. Gateways, PCI y cross-border.", ["Payment Gateways", "PCI Compliance", "Cross-Border", "Fraud Prevention", "Integration"], "#10B981"),
            ("wealth-advisor", "Asesor de Patrimonio", "🏅", "Gestión de Portafolio & Legado", "Arquitecto de legados. Portafolio, impuestos y planificación.", ["Portfolio Management", "Tax Strategy", "Legacy Planning", "Asset Allocation", "Retirement"], "#1E3A8A"),
            # Artes & Cultura
            ("art-curator", "Curador de Arte", "🖼️", "Exposiciones & Colecciones", "Narrador visual. Exposiciones, colecciones e historia del arte.", ["Exhibitions", "Collections", "Art History", "Curation", "Conservation"], "#F59E0B"),
            ("museum-director", "Director de Museo", "🏛️", "Operaciones & Educación Museística", "Guardián de la cultura. Operaciones, educación y comunidad.", ["Museum Operations", "Education", "Exhibitions", "Community", "Funding"], "#7C3AED"),
            ("gallery-owner", "Galerista", "🎨", "Venta de Arte & Representación", "Comerciante de belleza. Ventas, artistas y exposiciones.", ["Art Sales", "Artist Representation", "Exhibitions", "Pricing", "Promotion"], "#EC4899"),
            ("art-appraiser", "Tasador de Arte", "💎", "Valoración & Autenticación", "Detective del arte. Valoración, autenticación y análisis de mercado.", ["Art Valuation", "Authentication", "Market Analysis", "Provenance", "Restoration"], "#8B5CF6"),
            ("restorer-pro", "Restaurador de Arte", "🖌️", "Conservación & Restauración", "Cirujano del arte. Conservación, restauración y materiales.", ["Conservation", "Restoration", "Materials", "Chemistry", "Documentation"], "#D97706"),
            ("cultural-manager", "Gestor Cultural", "🎭", "Eventos Culturales & Festivales", "Animador de cultura. Eventos, festivales y arte público.", ["Cultural Events", "Festivals", "Public Art", "Community", "Funding"], "#14B8A6"),
            ("librarian-pro", "Bibliotecario Pro", "📚", "Catalogación & Archivos Digitales", "Guardián del conocimiento. Catálogos, investigación y archivos.", ["Cataloging", "Research", "Digital Archives", "Information Literacy", "Community"], "#6366F1"),
            ("archivist-pro", "Archivista Pro", "📁", "Preservación & Gestión Documental", "Guardián de la memoria. Preservación, registros y digitalización.", ["Preservation", "Records Management", "Digitization", "Metadata", "Access"], "#8B5CF6"),
            ("composer-pro", "Compositor Pro", "🎼", "Composición Musical & Arreglos", "Arquitecto del sonido. Composición, arreglos y partituras.", ["Composition", "Arranging", "Scoring", "Orchestration", "Music Theory"], "#EC4899"),
            ("conductor-pro", "Director de Orquesta", "🎵", "Dirección Musical & Interpretación", "Líder musical. Dirección, ensayos e interpretación.", ["Musical Direction", "Rehearsals", "Interpretation", "Score Reading", "Leadership"], "#7C3AED"),
            ("dance-instructor", "Instructor de Danza", "💃", "Ballet, Contemporáneo & Coreografía", "Inspirador de movimiento. Ballet, contemporáneo y coreografía.", ["Ballet", "Contemporary", "Choreography", "Technique", "Performance"], "#F43F5E"),
            ("acting-coach", "Coach de Actuación", "🎭", "Método de Actuación & Audiciones", "Escultor de actores. Método, audiciones y escena.", ["Method Acting", "Audition Prep", "Scene Study", "Character Development", "Emotion"], "#F59E0B"),
            # Construcción & Real Estate
            ("quantity-surveyor", "Tasador de Obras", "📐", "Estimación de Costos & Mediciones", "Calculador de obras. Costos, mediciones y presupuestos.", ["Cost Estimation", "Quantity Surveying", "Bills of Quantities", "Budgeting", "Tendering"], "#D97706"),
            ("construction-manager", "Gerente de Construcción", "🏗️", "Gestión de Obra & Cronogramas", "Comandante de la obra. Gestión, cronogramas y seguridad.", ["Construction Management", "Scheduling", "Safety", "Quality", "Budgeting"], "#F59E0B"),
            ("site-supervisor", "Capataz de Obra", "👷", "Supervisión Diaria & Equipos", "Dueño del día a día. Supervisión, equipos y calidad.", ["Site Supervision", "Crew Management", "Quality Control", "Safety", "Daily Reports"], "#92400E"),
            ("surveyor-pro", "Topógrafo Pro", "📍", "Levantamientos Topográficos & Mapeo", "Mapeador de tierras. Levantamientos, linderos y cartografía.", ["Land Surveying", "Mapping", "Boundaries", "Topography", "CAD"], "#16A34A"),
            ("demolition-expert", "Experto en Demoliciones", "💥", "Demoliciones Controladas & Reciclaje", "Artista de la demolición. Controladas, seguridad y reciclaje.", ["Controlled Demolition", "Safety", "Recycling", "Structural Analysis", "Permits"], "#374151"),
            ("crane-operator", "Operador de Grúa", "🏗️", "Izado Pesado & Aparejos", "Titán de la altura. Grúas, izado y protocolos de seguridad.", ["Crane Operations", "Rigging", "Heavy Lifting", "Safety Protocols", "Load Charts"], "#F59E0B"),
            ("flooring-specialist", "Especialista en Pisos", "🪵", "Instalación & Refinado de Pisos", "Artista del piso. Instalación, materiales y refinado.", ["Floor Installation", "Materials", "Refinishing", "Hardwood", "Tile"], "#D97706"),
            ("roofing-contractor", "Contratista de Techos", "🏠", "Instalación & Reparación de Techos", "Protector del hogar. Techos, impermeabilización y reparación.", ["Roofing", "Waterproofing", "Repairs", "Materials", "Inspections"], "#DC2626"),
            ("glass-glazier", "Vidriero Pro", "🪟", "Instalación de Vidrio & Muro Cortina", "Maestro del cristal. Vidrio, muro cortina y acabados.", ["Glass Installation", "Curtain Walls", "Glazing", "Safety Glass", "Repairs"], "#0EA5E9"),
            ("tiler-pro", "Alicatador Pro", "🔲", "Instalación de Azulejos & Patrones", "Artista del azulejo. Instalación, patrones y impermeabilización.", ["Tile Installation", "Patterns", "Waterproofing", "Grout", "Design"], "#0891B2"),
            ("property-developer", "Desarrollador Inmobiliario", "🏢", "Proyectos Inmobiliarios & Financiamiento", "Visionario del cemento. Proyectos, financiamiento y zoning.", ["Real Estate Development", "Financing", "Zoning", "Project Management", "Marketing"], "#1E3A8A"),
            ("real-estate-investor", "Inversor Inmobiliario", "💰", "Flipping, Alquileres & REITs", "Inversionista de ladrillos. Flipping, alquileres y análisis.", ["Real Estate Investment", "Flipping", "Rentals", "REITs", "Market Analysis"], "#16A34A"),
            # Energía & Medio Ambiente
            ("solar-panel-installer", "Instalador de Paneles Solares", "☀️", "Sistemas Fotovoltaicos & Grid-Tie", "Cosechador de sol. PV, on-grid y off-grid.", ["PV Systems", "Grid-Tie", "Off-Grid", "Installation", "Inverters"], "#F59E0B"),
            ("wind-turbine-tech", "Técnico de Turbinas Eólicas", "💨", "Mantenimiento & Diagnóstico Eólico", "Guardián del viento. Turbinas, mantenimiento y diagnóstico.", ["Wind Turbines", "Maintenance", "Diagnostics", "Safety", "Electrical"], "#0EA5E9"),
            ("energy-auditor", "Auditor Energético", "⚡", "Auditorías de Eficiencia & Ahorro", "Detective de energía. Auditorías, recomendaciones y ahorro.", ["Energy Audits", "Efficiency", "Recommendations", "Savings", "Reporting"], "#16A34A"),
            ("carbon-consultant", "Consultor de Carbono", "🌱", "Huella de Carbono & Compensaciones", "Contador de carbono. Huella, offsets y net-zero.", ["Carbon Footprint", "Offsets", "Net-Zero", "Reporting", "Sustainability"], "#22C55E"),
            ("environmental-consultant", "Consultor Ambiental", "🌍", "Evaluación de Impacto & Permisos", "Guía ambiental. Impacto, permisos y cumplimiento.", ["Environmental Impact", "Permits", "Compliance", "Remediation", "Sustainability"], "#16A34A"),
            ("waste-manager", "Gestor de Residuos", "♻️", "Gestión de Residuos & Economía Circular", "Transformador de basura. Residuos, reciclaje y circularidad.", ["Waste Management", "Recycling", "Circular Economy", "Disposal", "Compliance"], "#059669"),
            ("recycling-specialist", "Especialista en Reciclaje", "♻️", "Clasificación & Procesamiento", "Artesano del reciclaje. Clasificación, procesamiento y mercados.", ["Recycling", "Sorting", "Processing", "Markets", "Waste Reduction"], "#22C55E"),
            ("water-treatment", "Tratamiento de Aguas", "💧", "Purificación & Aguas Residuales", "Purificador de agua. Tratamiento, regulaciones y calidad.", ["Water Treatment", "Wastewater", "Purification", "Regulations", "Quality"], "#0EA5E9"),
            ("oil-gas-engineer", "Ingeniero Petrolero", "🛢️", "Upstream, Downstream & Reservorios", "Buscador de oro negro. Upstream, downstream y yacimientos.", ["Petroleum Engineering", "Upstream", "Downstream", "Reservoir", "Drilling"], "#1E3A8A"),
            ("nuclear-engineer", "Ingeniero Nuclear", "⚛️", "Diseño de Reactores & Seguridad", "Maestro de la fisión. Reactores, seguridad y residuos.", ["Nuclear Engineering", "Reactor Design", "Safety", "Waste Management", "Regulations"], "#7C3AED"),
            ("geologist-pro", "Geólogo Pro", "🪨", "Exploración Mineral & Cartografía", "Lector de la tierra. Minerales, mapeo y terreno.", ["Mineral Exploration", "Mapping", "Terrain Analysis", "Drilling", "Resource Estimation"], "#92400E"),
            ("mining-engineer", "Ingeniero de Minas", "⛏️", "Extracción, Seguridad & Automatización", "Conquistador del subsuelo. Extracción, seguridad y automatización.", ["Mining Engineering", "Extraction", "Safety", "Automation", "Ventilation"], "#374151"),
            # Manufactura & Industrial
            ("production-manager", "Gerente de Producción", "🏭", "Programación & Output Industrial", "Orquestador de la fábrica. Producción, salida y eficiencia.", ["Production Scheduling", "Output", "Efficiency", "Lean", "Team Leadership"], "#F59E0B"),
            ("quality-control", "Control de Calidad", "✅", "Inspección & Estándares de Calidad", "Guardián de la calidad. Inspección, estándares y Six Sigma.", ["Quality Inspection", "Standards", "Six Sigma", "Defect Detection", "Process Improvement"], "#16A34A"),
            ("lean-manufacturing", "Especialista Lean Manufacturing", "📉", "Reducción de Desperdicio & Kaizen", "Cazador de desperdicios. Lean, Kaizen y 5S.", ["Lean Manufacturing", "Waste Reduction", "Kaizen", "5S", "Continuous Improvement"], "#DC2626"),
            ("industrial-designer", "Diseñador Industrial", "🎨", "Diseño de Producto & Ergonomía", "Creador de objetos. Producto, prototipado y ergonomía.", ["Product Design", "Prototyping", "Ergonomics", "CAD", "User Research"], "#0EA5E9"),
            ("factory-manager", "Gerente de Fábrica", "🏭", "Operaciones & Fuerza Laboral", "Dueño de la planta. Operaciones, personal y mantenimiento.", ["Factory Operations", "Workforce", "Maintenance", "Safety", "KPIs"], "#D97706"),
            ("assembly-supervisor", "Supervisor de Ensamblaje", "🔧", "Línea de Montaje & Throughput", "Coordinador de la línea. Ensamblaje, calidad y rendimiento.", ["Assembly Line", "Quality", "Throughput", "Lean", "Team Supervision"], "#6366F1"),
            ("cnc-operator", "Operador CNC", "⚙️", "Mecanizado & Programación CNC", "Artesano digital. CNC, mecanizado y precisión.", ["CNC Operation", "Machining", "Programming", "Precision", "Tooling"], "#374151"),
            ("maintenance-tech", "Técnico de Mantenimiento", "🔩", "Mantenimiento Preventivo & Predictivo", "Doctor de máquinas. Preventivo, predictivo y reparaciones.", ["Preventive Maintenance", "Predictive Maintenance", "Repairs", "Diagnostics", "Reliability"], "#F59E0B"),
            ("safety-officer", "Oficial de Seguridad", "🦺", "Seguridad Industrial & OSHA", "Protector de la planta. Seguridad, protocolos y prevención.", ["Industrial Safety", "OSHA", "Protocols", "Incident Prevention", "Training"], "#DC2626"),
            ("procurement-specialist", "Especialista de Compras", "🛒", "Sourcing & Negociación", "Cazador de proveedores. Sourcing, negociación y abastecimiento.", ["Sourcing", "Negotiation", "Supplier Management", "Contracts", "Cost Reduction"], "#2563EB"),
            # Creatividad & Lifestyle
            ("perfumer", "Perfumista", "🌸", "Creación de Fragancias & Notas Olfativas", "Alquimista de aromas. Notas, acordes y composición de fragancias únicas.", ["Fragrance Creation", "Notes & Accords", "Blending", "Olfactory Science", "Bespoke Perfumes"], "#EC4899"),
            ("chocolatier", "Chocolatero", "🍫", "Bean-to-Bar & Bombonería", "Artesano del cacao. Fermentación, tostado, templado y creaciones de chocolate.", ["Bean-to-Bar", "Confections", "Tempering", "Flavor Pairing", "Chocolate Art"], "#7B3F00"),
            ("barista-pro", "Barista Pro", "☕", "Café de Especialidad & Latte Art", "Embajador del café. Extracción, latte art, tostado y sensorialidad.", ["Specialty Coffee", "Latte Art", "Roasting", "Brewing Methods", "Sensory Analysis"], "#6B4C35"),
            ("sommelier-beer", "Cervecero / Sommelier de Cerveza", "🍺", "Craft Beer & Cata Cervecera", "Explorador de lúpulos. Estilos, elaboración, maridaje y cultura cervecera.", ["Craft Brewing", "Beer Styles", "Tasting", "Food Pairing", "Brewing Science"], "#F59E0B"),
            ("florist-pro", "Florista Pro", "💐", "Diseño Floral & Arreglos", "Pintor con flores. Arreglos, bodas, eventos y composición botánica.", ["Floral Design", "Weddings", "Event Decor", "Botanical Knowledge", "Color Theory"], "#F43F5E"),
            ("calligrapher", "Calígrafo", "✒️", "Lettering & Tipografía Artística", "Artista de la letra. Lettering, tipografía, iluminación y diseño de logos manuscritos.", ["Lettering", "Typography", "Illumination", "Logo Design", "Ink Work"], "#1E3A8A"),
            ("illustrator-pro", "Ilustrador Pro", "🎨", "Ilustración Digital & Tradicional", "Creador de mundos visuales. Concept art, editorial, personajes y storytelling visual.", ["Digital Illustration", "Concept Art", "Character Design", "Editorial", "Visual Storytelling"], "#D946EF"),
            ("animator-pro", "Animador Pro", "🎬", "Animación 2D/3D & Motion Graphics", "Dador de vida. Animación, motion graphics, rigging y composición.", ["2D/3D Animation", "Motion Graphics", "Rigging", "Compositing", "Storyboarding"], "#8B5CF6"),
            ("set-designer", "Escenógrafo", "🏛️", "Diseño de Escenografía & Exhibición", "Arquitecto de mundos efímeros. Teatro, cine, exhibiciones y espacios escénicos.", ["Set Design", "Theater", "Film Sets", "Exhibition Design", "Spatial Storytelling"], "#7C3AED"),
            ("costume-designer", "Diseñador de Vestuario", "👘", "Vestuario & Historia de la Moda", "Narrador de épocas. Vestuario escénico, investigación histórica y construcción.", ["Costume Design", "Fashion History", "Theater", "Film", "Construction"], "#9333EA"),
            ("puppeteer", "Titiritero", "🎭", "Diseño & Manipulación de Marionetas", "Mago de cuerdas. Diseño, manipulación, storytelling y espectáculo.", ["Puppet Design", "Manipulation", "Storytelling", "Performance", "Workshops"], "#F59E0B"),
            ("magician-pro", "Mago Profesional", "🎩", "Magia de Cerca & Ilusionismo", "Creador de asombro. Close-up, escena, mentalismo y espectáculo.", ["Close-up Magic", "Stage Illusions", "Mentalism", "Entertainment", "Event Magic"], "#1E3A8A"),
            # Ciencias de la Salud Especializadas
            ("radiologist-pro", "Radiólogo Pro", "🩻", "Imágenes Médicas & Diagnóstico por Imagen", "Lector de sombras. MRI, CT, ultrasonido y rayos X.", ["Medical Imaging", "MRI", "CT Scans", "Ultrasound", "Diagnostic Radiology"], "#3B82F6"),
            ("pathologist-pro", "Patólogo Pro", "🔬", "Análisis de Tejidos & Diagnóstico", "Detective celular. Biopsias, autopsias y diagnóstico de laboratorio.", ["Tissue Analysis", "Biopsy", "Autopsy", "Lab Diagnosis", "Histopathology"], "#8B5CF6"),
            ("immunologist-pro", "Inmunólogo Pro", "🛡️", "Sistema Inmune & Vacunas", "Guardián de defensas. Inmunidad, vacunas, alergias y autoinmunidad.", ["Immune System", "Vaccines", "Allergies", "Autoimmunity", "Immunotherapy"], "#14B8A6"),
            ("endocrinologist-pro", "Endocrinólogo Pro", "🔥", "Hormonas & Metabolismo", "Regulador del cuerpo. Diabetes, tiroides, hormonas y metabolismo.", ["Hormones", "Diabetes", "Thyroid", "Metabolism", "Reproductive Endocrinology"], "#F97316"),
            ("rheumatologist-pro", "Reumatólogo Pro", "🦴", "Articulaciones & Enfermedades Autoinmunes", "Defensor de las articulaciones. Artritis, lupus y enfermedades reumáticas.", ["Arthritis", "Autoimmune", "Joints", "Lupus", "Osteoporosis"], "#0EA5E9"),
            ("geneticist-pro", "Genetista Pro", "🧬", "ADN & Consejería Genética", "Lector del código de la vida. Herencia, ADN, mutaciones y consejería.", ["DNA", "Heredity", "Genetic Counseling", "Mutations", "Genomics"], "#EC4899"),
            ("toxicologist-pro", "Toxicólogo Pro", "☠️", "Venenos & Toxinas Ambientales", "Detective de sustancias. Drogas, toxinas, intoxicaciones y evaluación de riesgo.", ["Poisons", "Drugs", "Environmental Toxins", "Risk Assessment", "Forensic Toxicology"], "#7C3AED"),
            ("epidemiologist-pro", "Epidemiólogo Pro", "📊", "Patrones de Enfermedad & Brotes", "Rastreador de enfermedades. Brotes, patrones, salud pública y prevención.", ["Disease Patterns", "Outbreaks", "Public Health", "Prevention", "Biostatistics"], "#16A34A"),
            ("microbiologist-pro", "Microbiólogo Pro", "🦠", "Bacterias & Cultivos de Laboratorio", "Explorador del microcosmos. Bacterias, virus, hongos y cultivos.", ["Bacteria", "Viruses", "Lab Cultures", "Infectious Disease", "Antibiotics"], "#22C55E"),
            ("biomedical-engineer", "Ingeniero Biomédico", "🔧", "Dispositivos Médicos & Prótesis", "Innovador de salud. Dispositivos médicos, imagen, prótesis y biomecánica.", ["Medical Devices", "Prosthetics", "Imaging", "Biomechanics", "Regulatory"], "#2563EB"),
            ("speech-therapist", "Logopeda", "🗣️", "Trastornos del Habla & Deglución", "Reconstructor de voces. Habla, lenguaje, deglución y rehabilitación.", ["Speech Disorders", "Language", "Swallowing", "Rehabilitation", "Pediatric Speech"], "#F59E0B"),
            ("occupational-therapist", "Terapeuta Ocupacional", "🤲", "Habilidades de Vida Diaria & Rehabilitación", "Facilitador de independencia. Actividades diarias, rehabilitación y adaptación.", ["Daily Living Skills", "Rehabilitation", "Adaptation", "Pediatrics", "Ergonomics"], "#0EA5E9"),
            # Nichos Especializados
            ("astronaut-trainer", "Entrenador de Astronautas", "🚀", "Simulación Espacial & Preparación Física", "Preparador de héroes espaciales. Simulación, fitness, psicología y protocolos.", ["Space Simulation", "Physical Training", "Psychology", "Zero-G", "Emergency Protocols"], "#1E3A8A"),
            ("handwriting-expert", "Perito Calígrafo", "📝", "Análisis Forense de Documentos", "Detective de la tinta. Falsificaciones, documentos, firma y análisis forense.", ["Document Analysis", "Forgery Detection", "Signature", "Forensics", "Expert Testimony"], "#374151"),
            ("bomb-disposal", "Experto en Desactivación de Explosivos", "💣", "EOD & Seguridad Bomb Squad", "Valiente técnico. Explosivos, desactivación, protocolos y seguridad.", ["EOD", "Bomb Disposal", "Safety Protocols", "Ordnance", "Tactical Operations"], "#DC2626"),
            ("dog-trainer", "Entrenador Canino", "🐕", "Obediencia & Perros de Servicio", "Comunicador interespecie. Obediencia, comportamiento, servicio y adiestramiento.", ["Obedience", "Service Dogs", "Behavior", "Puppy Training", "Agility"], "#A16207"),
            ("falconer", "Cetrero", "🦅", "Cetrería & Entrenamiento de Aves", "Guardián del vuelo. Cetrería, entrenamiento de aves, caza y conservación.", ["Falconry", "Bird Training", "Hunting", "Conservation", "Raptor Care"], "#92400E"),
            ("genealogist", "Genealogista", "🌳", "Árboles Genealógicos & ADN", "Arqueólogo de familias. Genealogía, ADN, herencia y registros históricos.", ["Family Trees", "DNA Genealogy", "Heritage", "Records", "Lineage"], "#16A34A"),
            ("gemologist", "Gemólogo", "💎", "Gemas & Tasación de Joyería", "Experto en piedras preciosas. Diamantes, gemas, tasación y autenticación.", ["Gemstones", "Diamonds", "Appraisal", "Authentication", "Jewelry"], "#0EA5E9"),
            ("handwriting-analyst", "Grafólogo", "✍️", "Grafología & Análisis de Personalidad", "Lector de personalidad. Grafología, firma, análisis de escritura y perfil.", ["Graphology", "Signature Analysis", "Personality", "Handwriting", "Forensic"], "#8B5CF6"),
            ("mystery-shopper", "Cliente Misterioso", "🕵️", "Auditoría Retail & Experiencia del Cliente", "Espía del servicio. Auditoría, evaluación, mystery shopping y feedback.", ["Retail Auditing", "Customer Experience", "Service Evaluation", "Compliance", "Reporting"], "#6366F1"),
            ("stand-up-comedian", "Comediante Stand-Up", "🎤", "Escritura de Monólogos & Delivery", "Creador de risas. Monólogos, timing, presencia escénica y comedia.", ["Monologue Writing", "Delivery", "Stage Presence", "Crowd Work", "Comedy Writing"], "#DC2626"),
            ("voice-actor", "Actor de Doblaje/Voz", "🎙️", "Voice Acting & Doblaje", "Creador de voces. Doblaje, narración, personajes y locución.", ["Voice Acting", "Dubbing", "Narration", "Character Voices", "Audio Production"], "#EC4899"),
            ("wedding-planner", "Wedding Planner", "💍", "Coordinación de Bodas & Eventos", "Arquitecto de sueños nupciales. Coordinación, proveedores, diseño y logística.", ["Wedding Coordination", "Vendors", "Design", "Logistics", "Budget Management"], "#F43F5E"),
            # ─── SellIA: La Empresa Virtual Completa ─── Jefes de Departamento
            ("selia-director", "SellIA Director", "🧠", "CEO IA & Orquestador General", "Meta-agente que supervisa todos los departamentos de la empresa virtual. Evalúa KPIs, genera planes de acción y envía briefing diario al dueño del negocio.", ["Strategic Planning", "KPI Management", "Cross-Department Coordination", "Decision Making", "Business Intelligence"], "#7C3AED"),
            ("head-of-sales", "Head of Sales", "💼", "Director de Ventas IA", "Lidera el departamento de ventas de la empresa virtual. Supervisa pipelines, optimiza procesos de cierre y asegura que el equipo de agentes de ventas cumpla objetivos.", ["Sales Management", "Pipeline Optimization", "Forecasting", "Team Leadership", "Revenue Growth"], "#F97316"),
            ("head-of-marketing", "Head of Marketing", "📢", "Director de Marketing IA", "Dirige el departamento de marketing de la empresa virtual. Gestiona campañas multicanal, analiza métricas de adquisición y optimiza el ROI de cada canal.", ["Marketing Strategy", "Campaign Management", "Acquisition", "Brand Positioning", "Analytics"], "#E1306C"),
            ("head-of-support", "Head of Support", "🎧", "Director de Soporte IA", "Gestiona el departamento de atención al cliente de la empresa virtual. Monitorea tiempos de respuesta, satisfacción del cliente y escala casos críticos.", ["Customer Support", "Ticket Management", "SLA Monitoring", "Quality Assurance", "Escalation"], "#0EA5E9"),
            ("head-of-retention", "Head of Retention", "❤️", "Director de Retención IA", "Lidera fidelización, programas de lealtad y recuperación de clientes. Analiza churn, diseña campañas de win-back y maximiza LTV.", ["Retention Strategy", "Loyalty Programs", "Churn Prevention", "Win-back Campaigns", "LTV Optimization"], "#EC4899"),
            ("head-of-finance", "Head of Finance", "💰", "Director de Finanzas IA", "Administra la salud financiera de la empresa virtual. Supervisa ingresos, cuentas por cobrar, recordatorios de pago y reportes de AR.", ["Financial Management", "Accounts Receivable", "Payment Reminders", "Revenue Reporting", "Cash Flow"], "#059669"),
            ("head-of-bi", "Head of BI", "📊", "Director de Inteligencia de Negocios IA", "Transforma datos en decisiones. Genera reportes de funnel, cohortes, churn prediction y atribución de canales.", ["Business Intelligence", "Data Analytics", "Predictive Modeling", "Cohort Analysis", "Channel Attribution"], "#8B5CF6"),
            ("head-of-operations", "Head of Operations", "⚙️", "Director de Operaciones IA", "Optimiza los procesos operativos de la empresa virtual. Gestiona inventario, logística, fulfillment y eficiencia del equipo.", ["Operations Management", "Process Optimization", "Inventory", "Logistics", "Efficiency"], "#6366F1"),
        ]

        personalities = []
        for i, (slug, name, emoji, tagline, desc, expertise, color) in enumerate(defaults):
            p = await self.get_or_create_personality(
                slug=slug,
                name=name,
                emoji=emoji,
                tagline=tagline,
                description=desc,
                expertise=expertise,
                color=color,
                display_order=i,
                is_active=True,
            )
            personalities.append(p)

        await self.db.commit()
        return personalities

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        business_id: uuid.UUID,
        personality_id: uuid.UUID,
        title: Optional[str] = None,
    ) -> AgentConversation:
        """Crear una nueva conversación con un agente."""
        conv = AgentConversation(
            user_id=user_id,
            business_id=business_id,
            personality_id=personality_id,
            title=title or "Nueva conversación",
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Optional[AgentConversation]:
        """Obtener una conversación por ID, verificando ownership."""
        result = await self.db.execute(
            select(AgentConversation)
            .where(AgentConversation.id == conversation_id)
            .where(AgentConversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_conversations(self, user_id: uuid.UUID, business_id: Optional[uuid.UUID] = None) -> List[AgentConversation]:
        """Listar conversaciones del usuario."""
        query = (
            select(AgentConversation)
            .where(AgentConversation.user_id == user_id)
            .where(AgentConversation.is_active == True)
            .order_by(desc(AgentConversation.updated_at))
        )
        if business_id:
            query = query.where(AgentConversation.business_id == business_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_messages(self, conversation_id: uuid.UUID, limit: int = 50) -> List[AgentMessage]:
        """Obtener mensajes de una conversación."""
        result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.conversation_id == conversation_id)
            .order_by(AgentMessage.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def chat(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        api_key: Optional[str] = None,
        business_context: Optional[Dict[str, Any]] = None,
        custom_instructions: Optional[str] = None,
        voice_slug: Optional[str] = None,
    ) -> AgentMessage:
        """Enviar un mensaje al agente y obtener respuesta.

        Args:
            voice_slug: Optional expert personality slug to layer over the base personality.
                        Used for auto-pilot agents to adopt an expert's voice.
        """
        # Get conversation
        conv = await self.get_conversation(conversation_id, user_id)
        if not conv:
            raise ValueError("Conversation not found")

        # Get personality
        result = await self.db.execute(
            select(AgentPersonality).where(AgentPersonality.id == conv.personality_id)
        )
        personality = result.scalar_one_or_none()
        if not personality:
            raise ValueError("Personality not found")

        # Save user message
        user_msg = AgentMessage(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        self.db.add(user_msg)
        conv.message_count += 1
        await self.db.flush()

        # Build system prompt with rich business context
        if not business_context and conv.business_id:
            try:
                ctx_builder = BusinessContextBuilder(self.db)
                business_context = await ctx_builder.build_system_prompt_context(
                    business_id=conv.business_id,
                    personality_id=conv.personality_id,
                )
            except Exception as e:
                from app.core.logger import get_logger
                get_logger(__name__).error(f"Context builder error: {e}")
                business_context = {}

        # Override custom instructions if provided directly
        if custom_instructions and business_context:
            business_context["custom_instructions"] = custom_instructions

        # Use composed prompt if voice override is provided
        if voice_slug:
            system_prompt = compose_system_prompt(
                base_slug=personality.slug,
                voice_slug=voice_slug,
                business_context=business_context or {},
                custom_instructions=business_context.get("custom_instructions") if business_context else custom_instructions,
            )
        else:
            system_prompt = get_system_prompt(
                personality.slug,
                business_context=business_context or {},
                custom_instructions=business_context.get("custom_instructions") if business_context else custom_instructions,
            )

        # Get recent message history (last 10 messages for context)
        recent_messages = await self.get_messages(conversation_id, limit=10)

        # Build LangChain messages
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in recent_messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        # Add current user message
        lc_messages.append(HumanMessage(content=content))

        # Resolve API key
        resolved_api_key = api_key
        if not resolved_api_key:
            result = await self.db.execute(
                select(UserAPIKey).where(
                    UserAPIKey.user_id == user_id,
                    UserAPIKey.provider == "openai",
                    UserAPIKey.is_active == True,
                )
            )
            key_record = result.scalar_one_or_none()
            if key_record and key_record.api_key_fernet:
                resolved_api_key = decrypt_value(key_record.api_key_fernet)

        # Use unified fallback provider (Ollama → Kimi → OpenAI → Anthropic)
        from app.domains.agents.llm_provider import generate_with_fallback

        llm_response = await generate_with_fallback(
            db=self.db,
            business_id=conv.business_id,
            messages=lc_messages,
            model="llama3.1",
            temperature=0.7,
            max_tokens=2000,
            use_semantic_cache=False,  # Skip cache for chat to get fresh responses
            use_smart_router=False,
        )

        if not llm_response:
            raise ValueError(
                "No se encontró un proveedor de IA disponible. "
                "Asegurate de que Ollama esté corriendo o agregá una API key en Configuración."
            )

        response_text = llm_response.content
        tokens_used = llm_response.tokens_used or 0

        # Save assistant message
        assistant_msg = AgentMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
            model_used=llm_response.model,
            tokens_used=tokens_used,
        )
        self.db.add(assistant_msg)
        conv.message_count += 1
        await self.db.commit()
        await self.db.refresh(assistant_msg)

        return assistant_msg

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Soft-delete una conversación."""
        conv = await self.get_conversation(conversation_id, user_id)
        if not conv:
            return False
        conv.is_active = False
        await self.db.commit()
        return True
