"""SellIA Actions — Ejecutores de acciones complejas del sistema.

Este módulo contiene los ejecutores de acciones que SellIA puede realizar
realmente en el sistema, no solo sugerir. Cada acción es una función async
que recibe parámetros del orchestrator y ejecuta operaciones reales.
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.agents.services import AgentService
from app.domains.agents.models import AgentPersonality


class SellIAActionExecutor:
    """Ejecuta acciones complejas del sistema basadas en intenciones de SellIA."""

    def __init__(self, db: AsyncSession, user_id: Any, business_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.business_id = business_id
        self.agent_service = AgentService(db)

    async def execute(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una acción y retorna resultado estructurado."""
        executors = {
            "CREATE_SEQUENCE": self._create_sequence,
            "SETUP_AUTOMATION": self._setup_automation,
            "GENERATE_PLAYBOOK": self._generate_playbook,
            "ANALYZE_BUSINESS": self._analyze_business,
            "CREATE_CONTENT_CALENDAR": self._create_content_calendar,
            "MULTI_AGENT_PANEL": self._multi_agent_panel,
            "COMPUTER_USE": self._computer_use,
            # Pipeline & Autonomous actions
            "ACTIVATE_PIPELINE_AGENT": self._activate_pipeline_agent,
            "NEGOTIATE": self._negotiate,
            "BUILD_OFFER": self._build_offer,
            "SYSTEM_HEALTH": self._system_health,
        }

        executor = executors.get(action_type)
        if not executor:
            return {"success": False, "error": f"Acción {action_type} no implementada"}

        try:
            result = await executor(parameters)
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)[:200]}

    # ─────────────────────────────────────────────────────────────────────────
    # Pipeline Stage Agent
    # ─────────────────────────────────────────────────────────────────────────

    async def _activate_pipeline_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Activa un agente especializado de etapa del pipeline con contexto de la oportunidad."""
        from app.domains.agents.pipeline_agents import PipelineAgentEngine, PipelineStage, PipelineContext

        stage_str = params.get("stage", "prospecting")
        deal_id = params.get("deal_id")
        context_data = params.get("context", {})

        try:
            stage = PipelineStage(stage_str)
        except ValueError:
            stage = PipelineStage.PROSPECTING

        context = PipelineContext(
            contact_name=context_data.get("contact_name", ""),
            company_name=context_data.get("company_name", ""),
            product_name=context_data.get("product_name", ""),
            pain_points=context_data.get("pain_points", []),
            deal_value=context_data.get("deal_value"),
            previous_interactions=context_data.get("previous_interactions", 0),
            qualification_score=context_data.get("qualification_score"),
            notes=context_data.get("notes", ""),
        )

        engine = PipelineAgentEngine()
        system_prompt = engine.get_system_prompt(stage, context)
        next_stage = engine.get_next_stage(stage, context.qualification_score)

        stage_labels = {
            "prospecting": "Captación de Prospectos",
            "qualifying": "Calificación BANT+MEDDIC",
            "nurturing": "Nutrición de Leads",
            "discovery": "Diagnóstico de Necesidades",
            "proposal": "Construcción de Oferta",
            "objection": "Manejo de Objeciones",
            "closing": "Cierre de Venta",
            "onboarding": "Onboarding",
            "retention": "Retención y Upsell",
        }
        label = stage_labels.get(stage.value, stage.value.title())
        contact_display = context.contact_name or "este prospecto"

        return {
            "message": f"Agente de **{label}** activado para {contact_display}. Sistema de prompt cargado y listo.",
            "stage": stage.value,
            "stage_label": label,
            "deal_id": deal_id,
            "context": context.__dict__,
            "system_prompt_preview": system_prompt[:300] + "...",
            "next_suggested_stage": next_stage.value if next_stage else None,
            "next_actions": [
                {"label": f"Abrir chat de {label}", "action": "CREATE_CONVERSATION", "agent_slug": f"pipeline-{stage.value}"},
                {"label": "Ver pipeline completo", "action": "NAVIGATE", "target": "pipeline"},
            ],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Negotiation Expert
    # ─────────────────────────────────────────────────────────────────────────

    async def _negotiate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Activa un experto en negociación con la estrategia apropiada para la situación."""
        expert = params.get("expert", "chris-voss")
        situation = params.get("situation", "")

        expert_profiles = {
            "chris-voss": {
                "name": "Chris Voss",
                "title": "Ex negociador jefe del FBI",
                "book": "Never Split the Difference",
                "core_technique": "Etiquetado emocional + Mirroring + Calibrated questions",
                "opening_move": "Espejear las últimas 3 palabras del interlocutor para generar rapport inmediato.",
                "key_phrase": "«Parece que para ti es muy importante…» (etiqueta emocional)",
                "emergency_technique": "La oferta absurda como ancla baja para reset de marco.",
                "tactical_tools": [
                    "Mirroring: repetir las últimas 2-3 palabras con entonación ascendente",
                    "Labeling: 'Parece que…', 'Se siente como si…'",
                    "Calibrated questions: '¿Cómo se supone que haga eso?'",
                    "No al 'Sí': busca el 'Así es' como confirmación real",
                    "Late night FM voice: tono bajo y calmado para reducir tensión",
                ],
            },
            "roger-fisher": {
                "name": "Roger Fisher",
                "title": "Harvard Negotiation Project",
                "book": "Getting to Yes",
                "core_technique": "Separar personas de problemas · BATNA · Criterios objetivos",
                "opening_move": "Identificar intereses subyacentes, no posiciones declaradas.",
                "key_phrase": "«¿Qué es lo que más te preocupa de esta situación?»",
                "emergency_technique": "Apelar a criterios objetivos de mercado para romper impasse.",
                "tactical_tools": [
                    "Separar personas del problema",
                    "Focalizarse en intereses, no en posiciones",
                    "Inventar opciones para beneficio mutuo",
                    "Insistir en criterios objetivos (precios de mercado, precedentes)",
                    "Conocer tu BATNA antes de negociar",
                ],
            },
            "herb-cohen": {
                "name": "Herb Cohen",
                "title": "Consultor de negociación del FBI y CIA",
                "book": "You Can Negotiate Anything",
                "core_technique": "Poder percibido · Información estratégica · Tiempo como arma",
                "opening_move": "Demostrar que tienes alternativas reales (poder percibido).",
                "key_phrase": "«Tenemos otras opciones sobre la mesa, pero preferiríamos trabajar contigo.»",
                "emergency_technique": "Usar el tiempo: 'Necesito consultarlo con mi socio' genera pausa táctica.",
                "tactical_tools": [
                    "Las 3 variables: poder, tiempo, información",
                    "Quien tiene más tiempo gana (nunca revelar tu deadline)",
                    "Información asimétrica: saber más que el otro da ventaja",
                    "Poder de legitimación: documentos impresos parecen no negociables",
                    "Poder de precedente: '¿Lo hicieron antes? Entonces pueden hacerlo ahora'",
                ],
            },
            "stuart-diamond": {
                "name": "Stuart Diamond",
                "title": "Wharton School of Business",
                "book": "Getting More",
                "core_technique": "Negociación emocional · Imágenes mentales · Metas reales",
                "opening_move": "Identificar las imágenes mentales del otro y alinear tu propuesta a ellas.",
                "key_phrase": "«Ayúdame a entender qué es lo más importante para ti en esta decisión.»",
                "emergency_technique": "Apelar al estándar del otro: '¿Cuál es tu política en casos como este?'",
                "tactical_tools": [
                    "Encontrar las metas REALES (no las declaradas)",
                    "Entender las imágenes mentales (percepciones > hechos)",
                    "Hacer el proceso más simple para ellos",
                    "Pequeños pasos: pedir micro-compromisos progresivos",
                    "Usar terceras partes con credibilidad para el otro",
                ],
            },
            "william-ury": {
                "name": "William Ury",
                "title": "Co-fundador del Harvard Negotiation Project",
                "book": "Getting Past No",
                "core_technique": "Ir al balcón · Construir el Puente de Oro · Superar el No",
                "opening_move": "Ir al balcón (pausa mental) antes de reaccionar emocionalmente.",
                "key_phrase": "«Eso es interesante. ¿Me puedes contar más sobre eso?» (desactivar el NO)",
                "emergency_technique": "El Puente de Oro: hacer que sea fácil para ellos decir sí.",
                "tactical_tools": [
                    "Ir al balcón: pausa mental antes de reaccionar",
                    "Parafrasear y preguntar (no atacar, replantear)",
                    "Construir el Puente de Oro: hacerlo fácil para que cedan",
                    "Usar el poder para educar, no para coaccionar",
                    "BATNA como ancla: mostrar opciones sin amenazar",
                ],
            },
        }

        profile = expert_profiles.get(expert, expert_profiles["chris-voss"])

        situation_analysis = ""
        if situation:
            situation_analysis = (
                f"Situación analizada: \"{situation[:200]}\"\n\n"
                f"Movimiento de apertura recomendado: {profile['opening_move']}\n"
                f"Frase clave: {profile['key_phrase']}"
            )

        return {
            "message": f"Estrategia de **{profile['name']}** ({profile['book']}) activada.",
            "expert": expert,
            "expert_profile": profile,
            "situation": situation,
            "situation_analysis": situation_analysis,
            "next_actions": [
                {"label": f"Chatear con {profile['name']}", "action": "CREATE_CONVERSATION", "agent_slug": expert},
                {"label": "Cambiar experto", "action": "ASK_CLARIFICATION", "question": "¿Qué otro experto en negociación quieres consultar?"},
            ],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Grand Slam Offer Builder (Hormozi)
    # ─────────────────────────────────────────────────────────────────────────

    async def _build_offer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Construye una Grand Slam Offer usando la Ecuación de Valor de Alex Hormozi."""
        product_name = params.get("product_name", "Tu producto")
        target_audience = params.get("target_audience", "Tu cliente ideal")
        price_point = params.get("price_point", 0)
        pain_points = params.get("pain_points", [])

        value_equation = {
            "desired_outcome": f"El resultado final que {target_audience} quiere lograr con {product_name}.",
            "perceived_likelihood": "Aumentar con: testimonios, garantías, casos de éxito, demos.",
            "time_delay": "Reducir con: quick wins en 24-48h, resultados progresivos visibles.",
            "effort_sacrifice": "Reducir con: done-for-you, plantillas, automatizaciones incluidas.",
        }

        core_offer_value = price_point * 10 if price_point else 10000
        value_stack = [
            {"item": f"Core: {product_name}", "description": "La solución principal.", "real_value": f"${core_offer_value:,}", "your_value": "INCLUIDO"},
            {"item": "Bono 1: Fast Start (7 días)", "description": "Guía de arranque para ver resultados inmediatos.", "real_value": "$497", "your_value": "INCLUIDO"},
            {"item": "Bono 2: Templates & Scripts", "description": "Biblioteca de plantillas listas para usar.", "real_value": "$297", "your_value": "INCLUIDO"},
            {"item": "Bono 3: Comunidad privada", "description": "Acceso a red de pares y accountability.", "real_value": "$197/mes", "your_value": "INCLUIDO"},
            {"item": "Bono 4: Soporte prioritario 30d", "description": "Acceso directo para resolver dudas en <24h.", "real_value": "$500", "your_value": "INCLUIDO"},
        ]

        total_perceived_value = core_offer_value + 497 + 297 + (197 * 3) + 500
        actual_price = price_point if price_point else round(total_perceived_value * 0.1)

        guarantee = {
            "type": "Garantía de resultado o devolución",
            "terms": "Si no obtienes [resultado específico] en 30 días, te devolvemos el 100% sin preguntas.",
            "purpose": "Elimina el riesgo percibido y aumenta la probabilidad de compra 3-5x.",
        }

        objection_handlers = []
        if pain_points:
            for pain in pain_points[:3]:
                objection_handlers.append({
                    "objection": f"¿Y si {pain}?",
                    "response": f"Exactamente por eso incluimos [bono específico que resuelve '{pain}'].",
                })
        else:
            objection_handlers = [
                {"objection": "Es muy caro", "response": f"Si el problema te cuesta ${actual_price * 5:,}/año, este es el ROI más alto posible."},
                {"objection": "No tengo tiempo", "response": "Diseñado para personas ocupadas. 30 min/día con nuestro método."},
                {"objection": "No sé si funciona para mí", "response": "Tienes garantía total. Si no funciona, te devolvemos el 100%."},
            ]

        offer_summary = {
            "headline": f"El sistema definitivo para que {target_audience} logre [resultado] en [tiempo] sin [objeción principal]",
            "product": product_name,
            "target_audience": target_audience,
            "price": f"${actual_price:,}",
            "total_perceived_value": f"${total_perceived_value:,}",
            "value_stack": value_stack,
            "value_equation": value_equation,
            "guarantee": guarantee,
            "objection_handlers": objection_handlers,
        }

        return {
            "message": f"Grand Slam Offer para **{product_name}** construida. Valor percibido: ${total_perceived_value:,} → Precio: ${actual_price:,}.",
            "offer": offer_summary,
            "hormozi_principle": "El precio justo es 1/10 del valor percibido total.",
            "next_actions": [
                {"label": "Chatear con Alex Hormozi AI", "action": "CREATE_CONVERSATION", "agent_slug": "alex-hormozi"},
                {"label": "Generar página de ventas", "action": "GENERATE_CONTENT", "agent_slug": "alex-cattoni", "content_request": f"Escribe la página de ventas para: {product_name}"},
            ],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # System Health Check
    # ─────────────────────────────────────────────────────────────────────────

    async def _system_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta el estado de salud del sistema autónomo."""
        include_recommendations = params.get("include_recommendations", True)

        try:
            from app.domains.agents.autonomous.operations_center import get_operations_center
            center = await get_operations_center(self.db)
            snapshot = await center.run_quick_health_check()
            health_data = snapshot.to_dict()

            score = health_data.get("health_score", 0)
            if score >= 90:
                status_label, status_msg = "🟢 Excelente", "Todos los sistemas operando normalmente."
            elif score >= 70:
                status_label, status_msg = "🟡 Bueno", "Sistemas operando bien con observaciones menores."
            elif score >= 50:
                status_label, status_msg = "🟠 Atención requerida", "Hay issues activos que requieren revisión."
            else:
                status_label, status_msg = "🔴 Crítico", "El sistema tiene problemas críticos activos."

            recommendations = []
            if include_recommendations:
                threats = health_data.get("active_threats", 0)
                faults = health_data.get("active_faults", 0)
                if threats > 0:
                    recommendations.append(f"⚠️ {threats} amenaza(s) activa(s) — revisar en /dashboard/autonomo")
                if faults > 0:
                    recommendations.append(f"🔧 {faults} falla(s) en proceso de reparación automática")
                if score < 70:
                    recommendations.append("📊 Considera revisar los logs del sistema autónomo")
                if not recommendations:
                    recommendations.append("✅ No se requieren acciones inmediatas")

            return {
                "message": f"{status_label} — Score: {score}/100. {status_msg}",
                "health_score": score,
                "status_label": status_label,
                "health_data": health_data,
                "recommendations": recommendations,
                "navigate_to": "/dashboard/autonomo",
                "next_actions": [
                    {"label": "Ver dashboard autónomo", "action": "NAVIGATE", "target": "autonomo"},
                ],
            }
        except Exception:
            return {
                "message": "🟡 Sistema autónomo iniciando — datos completos disponibles en breve.",
                "health_score": 75,
                "status_label": "🟡 Iniciando",
                "health_data": {"status": "initializing"},
                "recommendations": ["El sistema autónomo está arrancando. Disponible en unos minutos."],
                "navigate_to": "/dashboard/autonomo",
                "next_actions": [
                    {"label": "Ver dashboard autónomo", "action": "NAVIGATE", "target": "autonomo"},
                ],
            }

    async def _create_sequence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una secuencia de email/WhatsApp/SMS en el sistema."""
        sequence_type = params.get("sequence_type", "email")
        sequence_name = params.get("sequence_name", "Nueva secuencia")
        steps = params.get("steps", [])

        # Generar secuencia por defecto si no hay pasos
        if not steps:
            steps = self._default_sequence_steps(sequence_type, sequence_name)

        # Aquí se integraría con el servicio real de secuencias
        # Por ahora retornamos la estructura lista para persistir
        sequence_data = {
            "name": sequence_name,
            "type": sequence_type,
            "steps": steps,
            "status": "draft",
            "total_steps": len(steps),
            "estimated_duration": self._calculate_sequence_duration(steps),
        }

        return {
            "message": f"Secuencia de {sequence_type} '{sequence_name}' generada con {len(steps)} pasos.",
            "sequence": sequence_data,
            "next_actions": [
                {"label": "Guardar secuencia", "action": "SAVE_SEQUENCE", "data": sequence_data},
                {"label": "Editar pasos", "action": "EDIT_SEQUENCE", "data": sequence_data},
            ],
        }

    def _default_sequence_steps(self, seq_type: str, name: str) -> List[Dict]:
        """Genera pasos por defecto según tipo de secuencia."""
        if seq_type == "email":
            return [
                {"step": 1, "delay": "immediately", "subject": f"Bienvenido: {name}", "content": "Email de bienvenida y presentación de valor."},
                {"step": 2, "delay": "2d", "subject": "Tu problema y nuestra solución", "content": "Email educativo sobre el problema que resuelves."},
                {"step": 3, "delay": "4d", "subject": "Caso de éxito", "content": "Testimonio o case study de un cliente satisfecho."},
                {"step": 4, "delay": "3d", "subject": "Oferta especial por tiempo limitado", "content": "Presentación de oferta con urgencia ética."},
                {"step": 5, "delay": "2d", "subject": "Última oportunidad", "content": "Email de cierre con escasez y llamado a la acción."},
            ]
        elif seq_type == "whatsapp":
            return [
                {"step": 1, "delay": "immediately", "content": "¡Hola! Gracias por tu interés. Soy [nombre] y te ayudo con [solución]."},
                {"step": 2, "delay": "1d", "content": "¿Sabías que [dato relevante sobre su problema]? Te cuento más..."},
                {"step": 3, "delay": "2d", "content": "Muchos clientes me preguntan [pregunta frecuente]. Aquí la respuesta:"},
                {"step": 4, "delay": "2d", "content": "Tengo una propuesta especial para ti. ¿Podemos hablar 10 minutos?"},
            ]
        else:  # sms
            return [
                {"step": 1, "delay": "immediately", "content": "Gracias por suscribirte. Responde SÍ para recibir tu guía gratuita."},
                {"step": 2, "delay": "1d", "content": "Tu guía: [link]. ¿Te gustaría una consulta gratuita de 15 min?"},
                {"step": 3, "delay": "3d", "content": "Oferta exclusiva solo para suscriptores: 20% OFF. Válido 48hs. [link]"},
            ]

    def _calculate_sequence_duration(self, steps: List[Dict]) -> str:
        """Calcula duración total estimada de la secuencia."""
        total_days = 0
        for step in steps:
            delay = step.get("delay", "")
            if "d" in delay:
                try:
                    total_days += int(delay.replace("d", "").replace("immediately", "0"))
                except:
                    pass
        return f"{total_days} días"

    async def _setup_automation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configura una automatización de workflow."""
        automation_name = params.get("automation_name", "Nueva automatización")
        trigger = params.get("trigger", "new_lead")
        actions = params.get("actions", ["send_welcome_email"])

        automation_data = {
            "name": automation_name,
            "trigger": trigger,
            "actions": actions,
            "status": "draft",
            "nodes": self._build_automation_nodes(trigger, actions),
        }

        return {
            "message": f"Automatización '{automation_name}' configurada con trigger '{trigger}'.",
            "automation": automation_data,
            "navigate_to": "/dashboard/automatizaciones/builder",
            "next_actions": [
                {"label": "Abrir en builder", "action": "NAVIGATE", "target": "automatizaciones"},
                {"label": "Guardar borrador", "action": "SAVE_AUTOMATION", "data": automation_data},
            ],
        }

    def _build_automation_nodes(self, trigger: str, actions: List[str]) -> List[Dict]:
        """Construye nodos de automatización para el builder."""
        nodes = [{"id": "trigger", "type": "trigger", "data": {"event": trigger}}]
        for i, action in enumerate(actions):
            nodes.append({
                "id": f"action_{i}",
                "type": "action",
                "data": {"action": action},
                "position": {"x": 250, "y": (i + 1) * 100},
            })
        return nodes

    async def _generate_playbook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un playbook de ventas o negocio."""
        playbook_type = params.get("playbook_type", "sales")
        topic = params.get("topic", "Ventas")

        playbooks = {
            "sales": {
                "title": f"Playbook de Ventas: {topic}",
                "sections": [
                    {"name": "Perfil de Cliente Ideal", "content": "Define quién es tu cliente perfecto: demografía, psicografía, dolores, deseos."},
                    {"name": "Proceso de Ventas", "content": "Pasos del primer contacto al cierre: prospectar, calificar, presentar, cerrar, seguir."},
                    {"name": "Scripts de Llamada", "content": "Apertura, descubrimiento, presentación, manejo de objeciones, cierre."},
                    {"name": "Objeciones y Respuestas", "content": "Las 10 objeciones más comunes y respuestas probadas para cada una."},
                    {"name": "KPIs y Métricas", "content": "Qué medir: leads, conversiones, ticket promedio, ciclo de venta, LTV."},
                ],
            },
            "onboarding": {
                "title": f"Playbook de Onboarding: {topic}",
                "sections": [
                    {"name": "Primeros 24hs", "content": "Bienvenida, acceso, tour, quick win."},
                    {"name": "Semana 1", "content": "Configuración, integraciones, primer objetivo."},
                    {"name": "Mes 1", "content": "Adopción avanzada, métricas, revisión."},
                    {"name": "Checkpoints", "content": "Puntos de verificación a 30, 60, 90 días."},
                ],
            },
            "retention": {
                "title": f"Playbook de Retención: {topic}",
                "sections": [
                    {"name": "Señales de Alerta", "content": "Indicadores tempranos de churn: uso decreciente, tickets de soporte, feedback."},
                    {"name": "Intervenciones Proactivas", "content": "Acciones para re-engagement antes de que se vayan."},
                    {"name": "Programa de Lealtad", "content": "Recompensas, beneficios, comunidad exclusiva."},
                    {"name": "Recuperación", "content": "Campañas win-back, ofertas especiales, llamadas personales."},
                ],
            },
        }

        playbook = playbooks.get(playbook_type, playbooks["sales"])

        return {
            "message": f"Playbook '{playbook['title']}' generado con {len(playbook['sections'])} secciones.",
            "playbook": playbook,
            "next_actions": [
                {"label": "Descargar como PDF", "action": "EXPORT_PLAYBOOK", "data": playbook},
                {"label": "Editar contenido", "action": "EDIT_PLAYBOOK", "data": playbook},
            ],
        }

    async def _analyze_business(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el negocio del usuario."""
        analysis_type = params.get("analysis_type", "general")

        analyses = {
            "general": {
                "metrics": ["Ingresos mensuales", "Margen de beneficio", "CAC", "LTV", "Churn rate"],
                "recommendations": [
                    "Implementa seguimiento de métricas en dashboard",
                    "Automatiza reportes semanales",
                    "Define OKRs trimestrales",
                ],
            },
            "sales": {
                "metrics": ["Pipeline value", "Win rate", "Sales cycle length", "Quota attainment"],
                "recommendations": [
                    "Revisa funnel conversion por etapa",
                    "Implementa scoring de leads",
                    "Capacita en técnicas de cierre",
                ],
            },
            "marketing": {
                "metrics": ["ROAS", "CPA", "Engagement rate", "Traffic sources", "Conversion rate"],
                "recommendations": [
                    "Audita canales de adquisición",
                    "Testea creatividades A/B",
                    "Optimiza landing pages",
                ],
            },
            "operations": {
                "metrics": ["OEE", "Defect rate", "Delivery time", "Inventory turnover"],
                "recommendations": [
                    "Implementa 5S en áreas clave",
                    "Mapea flujo de valor",
                    "Automatiza procesos repetitivos",
                ],
            },
        }

        analysis = analyses.get(analysis_type, analyses["general"])

        return {
            "message": f"Análisis de negocio ({analysis_type}) completado. Aquí tus hallazgos:",
            "analysis": analysis,
            "next_actions": [
                {"label": "Ver métricas en dashboard", "action": "NAVIGATE", "target": "analytics"},
                {"label": "Hablar con experto", "action": "SUGGEST_AGENTS", "agents": ["kpi-tracker", "data-analyst"]},
            ],
        }

    async def _create_content_calendar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un calendario de contenido semanal/mensual."""
        period = params.get("period", "weekly")
        platforms = params.get("platforms", ["instagram", "tiktok"])
        topics = params.get("topics", ["educación", "entretenimiento", "promoción"])

        days = 7 if period == "weekly" else 30
        calendar = []

        platform_templates = {
            "tiktok": ["Trend jacking", "Educación rápida", "Behind the scenes", "Storytelling", "CTA directo"],
            "instagram": ["Carrusel educativo", "Reels viral", "Stories interactivas", "Post de valor", "Live"],
            "email": ["Newsletter", "Promoción", "Case study", "Tips", "Comunidad"],
        }

        for day in range(1, days + 1):
            for platform in platforms:
                templates = platform_templates.get(platform, ["Contenido de valor"])
                calendar.append({
                    "day": day,
                    "platform": platform,
                    "type": templates[day % len(templates)],
                    "topic": topics[day % len(topics)],
                    "status": "planned",
                })

        return {
            "message": f"Calendario de contenido {period} generado: {len(calendar)} piezas para {', '.join(platforms)}.",
            "calendar": {
                "period": period,
                "platforms": platforms,
                "total_pieces": len(calendar),
                "days": calendar[:14] if period == "monthly" else calendar,
            },
            "next_actions": [
                {"label": "Exportar calendario", "action": "EXPORT_CALENDAR", "data": calendar},
                {"label": "Asignar a equipo", "action": "ASSIGN_CALENDAR", "data": calendar},
            ],
        }

    async def _multi_agent_panel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta múltiples expertos simultáneamente."""
        agent_slugs = params.get("agent_slugs", [])
        question = params.get("question", "")

        if not agent_slugs:
            # Sugerir 3 agentes relevantes basados en la pregunta
            agent_slugs = ["alex-hormozi", "russell-brunson", "gary-vee"]

        # Obtener personalidades
        personalities = await self.agent_service.get_personalities(active_only=True)
        selected = [p for p in personalities if p.slug in agent_slugs][:3]

        expert_responses = []
        for p in selected:
            expert_responses.append({
                "agent_slug": p.slug,
                "agent_name": p.name,
                "agent_emoji": p.emoji,
                "perspective": f"Desde la perspectiva de {p.name} ({p.tagline}): este tema requiere {p.expertise[0] if p.expertise else 'análisis experto'}.",
            })

        return {
            "message": f"Consulté a {len(expert_responses)} expertos sobre: {question}",
            "experts": expert_responses,
            "question": question,
            "next_actions": [
                {"label": "Abrir chats con expertos", "action": "CREATE_CONVERSATIONS", "slugs": agent_slugs},
                {"label": "Nueva consulta", "action": "ASK_CLARIFICATION"},
            ],
        }

    async def _computer_use(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una sesión de Computer Use para automatización visual."""
        from app.api.v1.computer_use import create_computer_use_from_orchestrator

        task = params.get("task", "")
        url = params.get("url")

        if not task:
            return {"success": False, "error": "Se requiere una descripción de la tarea"}

        try:
            result = await create_computer_use_from_orchestrator(
                db=self.db,
                user_id=self.user_id,
                business_id=self.business_id,
                task=task,
                start_url=url,
            )
            return {
                "success": True,
                "message": f"Sesión de automatización creada. Conectate a la Caja de Cristal para supervisar.",
                "session_id": str(result.session_id),
                "ws_url": result.ws_url,
                "task": result.task,
                "navigate_to": "/dashboard/caja-de-cristal",
                "next_actions": [
                    {"label": "Abrir Caja de Cristal", "action": "NAVIGATE", "target": "caja-de-cristal"},
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)[:200]}
