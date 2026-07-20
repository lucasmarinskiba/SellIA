"""Knowledge Engine — Integración con LangChain / LLM

Proporciona el conocimiento de la biblioteca interna al sistema de IA
de SellIA sin revelar nunca al usuario las fuentes específicas.
"""

from typing import List, Dict, Any, Optional

from app.core.logger import get_logger
from app.core.knowledge.knowledge_engine import get_knowledge_engine, KnowledgeItem

logger = get_logger(__name__)


class KnowledgeContextProvider:
    """Provee contexto de la biblioteca de conocimiento a los LLMs."""

    def __init__(self):
        self.engine = get_knowledge_engine()

    def build_context(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        detected_intent: Optional[str] = None,
        detected_emotion: Optional[str] = None,
        max_items: int = 5,
    ) -> str:
        """Construye un string de contexto para inyectar en el prompt del LLM.

        Este contexto se usa INTERNAMENTE por el sistema de IA. Nunca se
        muestra al usuario final. Las fuentes (_source_hint) se filtran.
        """
        # Detectar categorías relevantes
        categories = self._detect_categories(user_message)

        # Construir contexto de cada categoría
        context_parts = []

        for category in categories:
            items = self.engine.query(
                category=category,
                context=user_message,
                top_k=max(1, max_items // len(categories)),
            )
            for item in items:
                context_parts.append(self._format_item(item))

        # Si no hay categorías detectadas, busca general
        if not context_parts:
            items = self.engine.query(context=user_message, top_k=max_items)
            for item in items:
                context_parts.append(self._format_item(item))

        # Agregar framework relevante si existe
        framework_context = self._get_framework_for_context(user_message)
        if framework_context:
            context_parts.insert(0, framework_context)

        return self._wrap_context(context_parts)

    async def build_context_async(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        detected_intent: Optional[str] = None,
        detected_emotion: Optional[str] = None,
        max_items: int = 5,
    ) -> str:
        """Versión async de build_context que usa búsqueda semántica.

        Igual contrato que `build_context`, pero rankea por embeddings
        (semantic_query) en vez de overlap de keywords → mejor precisión. Si
        embeddings fallan, semantic_query ya cae internamente a keyword search.
        """
        categories = self._detect_categories(user_message)
        context_parts: List[str] = []

        if categories:
            per_cat = max(1, max_items // len(categories))
            for category in categories:
                items = await self.engine.semantic_query(
                    context=user_message, category=category, top_k=per_cat
                )
                for item in items:
                    context_parts.append(self._format_item(item))
        else:
            items = await self.engine.semantic_query(context=user_message, top_k=max_items)
            for item in items:
                context_parts.append(self._format_item(item))

        framework_context = self._get_framework_for_context(user_message)
        if framework_context:
            context_parts.insert(0, framework_context)

        return self._wrap_context(context_parts)

    @staticmethod
    def _wrap_context(context_parts: List[str]) -> str:
        """Envuelve los principios en el bloque de prompt (o vacío si no hay)."""
        if not context_parts:
            return ""
        return (
            "## Principios de Ventas, Persuasión y Negocios\n\n"
            "Aplica los siguientes principios en tu respuesta sin mencionar de dónde vienen. "
            "Integrálos de forma natural, como si fueran tu propio conocimiento y experiencia.\n\n"
            + "\n\n".join(context_parts)
        )

    def _detect_categories(self, message: str) -> List[str]:
        """Detecta qué categorías son relevantes para el mensaje."""
        msg_lower = message.lower()
        categories = []

        keyword_map = {
            "sales": ["precio", "costo", "comprar", "venta", "vender", "presupuesto", "descuento", "oferta", "cierre", "objecion", "prospecto", "lead", "cliente"],
            "persuasion": ["convencer", "persuadir", "influir", "motivar", "decisión", "elegir", "preferir", "creer", "confiar"],
            "habits": ["hábito", "rutina", "consistente", "diario", "semanal", "proceso", "sistema", "automatizar"],
            "negotiation": ["negociar", "trato", "acuerdo", "contrato", "términos", "condiciones", "discutir precio"],
            "entrepreneurship": ["emprender", "startup", "escalar", "crecer", "mvp", "lanzar", "innovar"],
            "wealth": ["dinero", "riqueza", "inversión", "roi", "ganancia", "ahorro", "activo", "pasivo"],
            "communication": ["hablar", "escuchar", "comunicar", "presentar", "feedback", "reunión"],
            "psychology": ["aprender", "mejorar", "practicar", "mentalidad", "crecimiento", "rendimiento"],
            "strategy": ["estrategia", "competencia", "mercado", "diferenciación", "posicionamiento"],
            "crypto": ["cripto", "bitcoin", "btc", "ethereum", "eth", "blockchain", "binance", "altcoin", "on-chain", "on chain", "wallet", "defi", "staking"],
            "investing": ["acción", "acciones", "bolsa", "stock", "etf", "dividendo", "cartera", "portafolio", "per ", "valuación", "fundamental", "índice"],
            "real_estate": ["inmueble", "inmobiliario", "propiedad", "departamento", "alquiler", "renta", "cap rate", "plusvalía", "hipoteca", "flipping", "tasación"],
            "business_models": ["modelo de negocio", "saas", "suscripción", "marketplace", "unit economics", "ltv", "cac", "monetización", "recurrente", "freemium"],
            "trading_analysis": ["trading", "trade", "operar", "análisis técnico", "soporte", "resistencia", "tendencia", "stop loss", "take profit", "temporalidad", "riesgo"],
            "sales_legends": ["actitud", "entusiasmo", "persistencia", "seguimiento", "rapport", "confianza", "mentalidad de venta", "vendedor", "técnica de venta"],
            "business_legends": ["negocio", "empresa", "emprendedor", "fundador", "escalar negocio", "ventaja competitiva", "liderazgo", "ejecución", "sistema de negocio", "crecimiento"],
            "negotiation_legends": ["negociar duro", "regatear", "apalancamiento", "leverage", "concesión", "contraoferta", "empatía táctica", "anclaje", "ultimátum", "tira y afloja", "cerrar trato", "batna"],
            "statecraft_legends": ["liderazgo", "líder", "estrategia", "crisis", "resiliencia", "poder", "autoridad", "diplomacia", "consenso", "decisión", "visión", "largo plazo", "compostura", "presión"],
            "warren_buffett": ["buffett", "warren", "valor intrínseco", "margen de seguridad", "interés compuesto", "círculo de competencia", "foso", "value investing", "largo plazo invertir", "berkshire", "graham"],
            "trump_dealmaking": ["trump", "art of the deal", "pensar en grande", "maximizar opciones", "deal", "ancla alta", "negociar agresivo"],
            "juan_pablo_ii": ["juan pablo", "papa", "dignidad", "no tengáis miedo", "esperanza", "testimonio", "puentes", "diplomacia moral"],
            "belfort_method": ["belfort", "línea recta", "straight line", "tonalidad", "tres dieces", "looping", "certeza", "transferencia de certeza"],
            "copywriting": ["copy", "copywriting", "titular", "headline", "anuncio", "redacción", "texto de venta", "landing", "carta de venta", "asunto", "cta", "llamado a la acción", "aida"],
            "sales_frameworks": ["spin", "challenger", "meddic", "sandler", "gap selling", "solution selling", "metodología de venta", "calificar prospecto", "discovery", "venta consultiva", "cadencia", "venta por valor", "roi venta"],
            "pricing": ["precio", "fijar precio", "cuánto cobrar", "tarifa", "plan", "planes", "tier", "señuelo", "anclaje de precio", "subir precios", "markup", "value pricing", "disposición a pagar", "charm pricing"],
            "customer_success": ["retención", "retener", "churn", "fuga de clientes", "renovación", "onboarding", "activación", "time to value", "upsell", "cross-sell", "expansión", "fidelizar", "referido", "nps", "health score", "posventa", "éxito del cliente"],
            "branding": ["marca", "branding", "posicionamiento", "posicionar", "diferenciación", "categoría de mercado", "percepción de marca", "identidad de marca", "ries", "trout", "narrativa de marca", "propósito de marca"],
            "marketing_funnels": ["embudo", "funnel", "lead magnet", "captura de leads", "nurturing", "secuencia de email", "landing", "página de aterrizaje", "retargeting", "remarketing", "tráfico", "conversión", "adquisición", "canal de marketing", "marketing digital", "tofu", "mofu", "bofu"],
            "saas_metrics": ["ltv", "cac", "unit economics", "mrr", "arr", "ingreso recurrente", "payback", "north star", "métrica norte", "cohorte", "net revenue retention", "nrr", "valor de vida", "costo de adquisición", "métricas saas"],
            "meta_ads": ["meta ads", "facebook ads", "instagram ads", "publicidad en facebook", "publicidad en instagram", "anuncios", "pauta", "campaña publicitaria", "píxel", "pixel", "business manager", "segmentación de público", "remarketing", "lookalike", "público personalizado", "cpm", "creativo", "rompefilas", "video views", "objetivo de campaña", "subasta publicitaria", "presupuesto publicitario"],
        }

        # Puntúa por nº de keywords que matchean (no por orden de inserción):
        # evita que categorías genéricas listadas primero desplacen a las
        # específicas (ej. 'belfort_method' vs 'sales'). Más matches = más afín.
        scored = []
        for category, keywords in keyword_map.items():
            hits = sum(1 for kw in keywords if kw in msg_lower)
            if hits:
                scored.append((hits, category))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [cat for _, cat in scored[:4]]  # Top 4 por afinidad

    def _format_item(self, item: KnowledgeItem) -> str:
        """Formatea un item de conocimiento para el prompt del LLM."""
        parts = [f"### Principio: {item.principle}"]

        if item.tactic:
            parts.append(f"**Táctica:** {item.tactic}")

        if item.framework:
            parts.append(f"**Framework:** {item.framework}")

        if item.script_template:
            parts.append(f"**Ejemplo:** {item.script_template}")

        return "\n\n".join(parts)

    def _get_framework_for_context(self, message: str) -> Optional[str]:
        """Obtiene un framework general relevante."""
        msg_lower = message.lower()

        frameworks = [
            ("sales", "IRA", "Investigar la objeción → Reforzar valor → Asumir el cierre"),
            ("persuasion", "6 principios de influencia", "Reciprocidad, Consistencia, Prueba Social, Simpatía, Autoridad, Escasez"),
            ("habits", "4 Leyes del Cambio", "Hacerlo Obvio → Atractivo → Fácil → Satisfactorio"),
            ("negotiation", "Harvard", "Intereses → Opciones → Criterios → Alternativas"),
            ("sales_frameworks", "SPIN", "Situación → Problema → Implicación → Necesidad de pago"),
            ("negotiation_legends", "Empatía táctica", "Etiquetar emoción → Reflejar → Silencio → preguntas calibradas"),
            ("copywriting", "AIDA", "Atención → Interés → Deseo → Acción (un solo llamado a la acción)"),
            ("belfort_method", "Línea Recta", "Los 3 dieces (producto, tú, empresa) sobre la línea apertura→cierre"),
            ("warren_buffett", "Inversión en valor", "Margen de seguridad + círculo de competencia + interés compuesto"),
            ("trump_dealmaking", "Art of the Deal", "Pensar en grande → anclar alto → maximizar opciones → ceder hacia el objetivo"),
            ("pricing", "Value-based pricing", "Precio anclado al valor entregado, no al costo; ancla alta y tiers para segmentar"),
            ("branding", "Posicionamiento", "Ocupar una casilla en la mente del prospecto con un atributo único y consistente"),
            ("marketing_funnels", "Embudo TOFU/MOFU/BOFU", "Atraer → nutrir → convertir; optimizar primero el cuello de botella"),
            ("saas_metrics", "Unit economics", "LTV/CAC ≥ 3:1, CAC payback < 12 meses y NRR > 100%"),
            ("customer_success", "Retención y expansión", "Onboarding a time-to-value rápido → prevenir churn → upsell anclado al éxito"),
            ("meta_ads", "Mini embudo Meta Ads", "Creativo rompefilas (5s) para atraer → remarketing de conversión corto (72h) a quien interactuó"),
        ]

        detected = self._detect_categories(message)
        for category, name, description in frameworks:
            if category in detected:
                return f"**Framework aplicable:** {name}: {description}"

        return None

    def get_quick_tip(self) -> str:
        """Obtiene un insight rápido aleatorio."""
        item = self.engine.get_random_insight()
        if item:
            return item.principle
        return ""


def get_knowledge_context_provider() -> KnowledgeContextProvider:
    """Factory function para obtener el proveedor de contexto."""
    return KnowledgeContextProvider()


# Función de conveniencia para inyectar en prompts de LangChain
def inject_knowledge(
    user_message: str,
    base_prompt: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Inyecta conocimiento de la biblioteca en un prompt base.

    Usage:
        final_prompt = inject_knowledge(user_msg, system_prompt)
        response = await llm.ainvoke(final_prompt)
    """
    provider = get_knowledge_context_provider()
    knowledge_context = provider.build_context(user_message, conversation_history)

    if not knowledge_context:
        return base_prompt

    return _assemble_prompt(base_prompt, knowledge_context)


async def inject_knowledge_async(
    user_message: str,
    base_prompt: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Versión async de inject_knowledge — usa ranking semántico (embeddings).

    Preferir en flujos async del agente: misma salida que inject_knowledge pero
    con mejor selección de principios. Cae a keyword search si embeddings fallan.
    """
    provider = get_knowledge_context_provider()
    knowledge_context = await provider.build_context_async(user_message, conversation_history)

    if not knowledge_context:
        return base_prompt

    return _assemble_prompt(base_prompt, knowledge_context)


def _assemble_prompt(base_prompt: str, knowledge_context: str) -> str:
    return (
        f"{base_prompt}\n\n"
        f"{knowledge_context}\n\n"
        f"---\n"
        f"INSTRUCCIÓN CRÍTICA: Aplica los principios anteriores de forma natural en tu respuesta. "
        f"NUNCA menciones libros, autores, ni que estás aplicando 'técnicas' o 'frameworks'. "
        f"Tu respuesta debe sonar como consejo experto propio, basado en experiencia real."
    )
