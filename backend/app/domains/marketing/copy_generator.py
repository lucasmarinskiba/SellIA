"""Copy and content generation for marketing."""

from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class CopyKit:
    channel: str
    headlines: List[str]
    descriptions: List[str]
    calls_to_action: List[str]
    sample_posts: List[Dict[str, str]]
    email_templates: List[Dict[str, str]]
    best_practices: List[str]


class CopyGenerator:
    """Generate marketing copy by channel"""

    def generate_copy(
        self, business_name: str, channel: str, business_model: str = ""
    ) -> CopyKit:
        """Generate copy kit for channel"""

        if channel == "google_maps":
            return self._copy_google_maps(business_name)
        elif channel == "instagram":
            return self._copy_instagram(business_name)
        elif channel == "whatsapp":
            return self._copy_whatsapp(business_name)
        elif channel == "linkedin":
            return self._copy_linkedin(business_name)
        elif channel == "email":
            return self._copy_email(business_name)
        else:
            return self._copy_generic(business_name)

    def _copy_google_maps(self, business_name: str) -> CopyKit:
        """Google Maps copy"""

        return CopyKit(
            channel="google_maps",
            headlines=[
                f"{business_name} - Servicios de calidad en [ciudad]",
                f"{business_name} - Tu solución confiable",
                f"{business_name} - Expertos en [especialidad]",
                f"{business_name} - Respuesta rápida garantizada",
            ],
            descriptions=[
                f"Contáctanos hoy para solucionar tu problema. Respuesta en 30 minutos. "
                f"Presupuesto sin compromiso.",
                f"Somos especialistas en [especialidad]. Más de 10 años de experiencia. "
                f"Clientes satisfechos.",
                f"Servicio profesional y confiable. Disponibles 24/7. "
                f"Garantía en todos nuestros trabajos.",
            ],
            calls_to_action=[
                "Llama ahora",
                "Solicita un presupuesto",
                "WhatsApp",
                "Agenda una cita",
                "Envía tu consulta"
            ],
            sample_posts=[
                {
                    "title": "Promoción especial",
                    "content": "¡Descuento 20% en servicios este mes! Llama ahora."
                },
                {
                    "title": "Tips útiles",
                    "content": "¿Cómo mantener [producto/servicio]? Aquí 5 tips para alargar su vida."
                },
                {
                    "title": "Caso de éxito",
                    "content": "Transforma tu [espacio/proyecto] con nuestros servicios. Ver antes y después."
                }
            ],
            email_templates=[],
            best_practices=[
                "Responde rápido a comentarios y mensajes (máx 2 horas)",
                "Publica 2 veces por semana",
                "Solicita reviews regularmente",
                "Incluye fotos de trabajos realizados",
                "Destaca garantías y certificados"
            ]
        )

    def _copy_instagram(self, business_name: str) -> CopyKit:
        """Instagram copy"""

        return CopyKit(
            channel="instagram",
            headlines=[
                f"Descubre {business_name} ✨",
                f"Transforma tu [espacio] con nosotros",
                f"Calidad profesional a tu alcance",
                f"Somos tu solución número 1"
            ],
            descriptions=[
                f"Especialistas en [especialidad]. Síguenos para tips, antes y después, "
                f"y ofertas exclusivas. 👇",
                f"Tus [productos/servicios] de confianza. Calidad premium. "
                f"Envío rápido. ¡Síguenos!",
            ],
            calls_to_action=[
                "Compra ahora",
                "Conoce nuestros servicios",
                "Chatea con nosotros",
                "Mira nuestro catálogo",
                "Descubre más"
            ],
            sample_posts=[
                {
                    "type": "Reel",
                    "content": "30 segundos: before/after del proyecto. Trending music. "
                    "CTA al final."
                },
                {
                    "type": "Carousel",
                    "content": "5 slides: Step-by-step del proceso. Tips en cada slide."
                },
                {
                    "type": "Story",
                    "content": "Behind-the-scenes. Equipo trabajando. Customer testimonial."
                },
                {
                    "type": "Post",
                    "content": "Foto del producto/servicio + caption con hashtags + CTA"
                }
            ],
            email_templates=[],
            best_practices=[
                "Publica 4-5 veces por semana",
                "Usa reels 3-4 veces por semana (algoritmo los favorece)",
                "Responde a todos los comentarios en 24 horas",
                "Usa 20-30 hashtags relevantes",
                "Crea historias diarias",
                "Etiqueta a clientes satisfechos",
                "Colabora con micro-influencers"
            ]
        )

    def _copy_whatsapp(self, business_name: str) -> CopyKit:
        """WhatsApp copy"""

        return CopyKit(
            channel="whatsapp",
            headlines=[
                f"¡Hola! Gracias por contactar a {business_name}",
                f"Bienvenido a {business_name}",
            ],
            descriptions=[],
            calls_to_action=[],
            sample_posts=[],
            email_templates=[
                {
                    "name": "Auto-respuesta inicial",
                    "content": "¡Hola! Gracias por tu mensaje. Te respondemos en máximo 2 horas. "
                    "¿En qué te podemos ayudar? 😊"
                },
                {
                    "name": "Presupuesto",
                    "content": "Claro, aquí te comparto el presupuesto: [detalles]. "
                    "¿Te parece bien? ¿Alguna pregunta?"
                },
                {
                    "name": "Seguimiento",
                    "content": "Solo quería confirmar que recibiste el presupuesto. "
                    "¿Tienes dudas? Estoy disponible para aclarlas. ☺️"
                },
                {
                    "name": "Promoción",
                    "content": "⚡ OFERTA ESPECIAL ⚡\n"
                    "Este mes: 20% descuento en [servicio]. "
                    "Válido hasta fin de mes. ¿Agendamos?"
                }
            ],
            best_practices=[
                "Responde en máx 30 minutos",
                "Usa emojis para calidez",
                "Confirma datos del cliente",
                "Envía presupuesto rápido",
                "Ofrece múltiples opciones de pago",
                "Crea grupos exclusivos para ofertas"
            ]
        )

    def _copy_linkedin(self, business_name: str) -> CopyKit:
        """LinkedIn copy"""

        return CopyKit(
            channel="linkedin",
            headlines=[
                f"Transforma tu negocio con {business_name}",
                f"Soluciones empresariales que crecen con tu empresa",
                f"Expertos en [industria]",
            ],
            descriptions=[
                f"Ayudamos a empresas a [lograr objetivo]. Experiencia de 10+ años. "
                f"Conectemos y exploremos oportunidades.",
            ],
            calls_to_action=[
                "Conectemos",
                "Solicita una demo",
                "Agenda una llamada",
                "Conoce nuestro caso de estudio"
            ],
            sample_posts=[
                {
                    "type": "Article",
                    "content": "10 insights sobre [tema] que todo empresario debe saber"
                },
                {
                    "type": "Post",
                    "content": "Caso de éxito: Cómo [empresa] aumentó sus ventas 200% con nosotros"
                },
                {
                    "type": "Comment",
                    "content": "Respuesta a post relevante con valor agregado"
                }
            ],
            email_templates=[
                {
                    "name": "Cold outreach",
                    "content": "Hola [nombre],\n\n"
                    "He visto que trabajas en [empresa] y noté que [observación relevante].\n"
                    "En [company], ayudamos a empresas como la tuya a [beneficio].\n"
                    "¿Podríamos charlar 15 minutos para explorar oportunidades?\n\n"
                    "Saludos,\n[Tu nombre]"
                }
            ],
            best_practices=[
                "Publica 2-3 veces por semana",
                "Escribe con autoridad sobre tu industria",
                "Responde a comentarios con valor",
                "Conecta con decisores en tu target",
                "Personaliza mensajes de conexión",
                "Comparte estudios de caso"
            ]
        )

    def _copy_email(self, business_name: str) -> CopyKit:
        """Email copy"""

        return CopyKit(
            channel="email",
            headlines=[
                f"¿Quieres aumentar tus ventas 40% en 30 días?",
                f"El secreto que tus competidores no quieren que sepas",
                f"Oferta exclusiva para {business_name}",
                f"Transforma tu negocio: aquí está cómo",
            ],
            descriptions=[],
            calls_to_action=[
                "Ver oferta",
                "Solicita tu demo gratuita",
                "Aprende más",
                "Reclama tu descuento"
            ],
            sample_posts=[],
            email_templates=[
                {
                    "name": "Welcome series - Email 1",
                    "subject": "Bienvenido a {business_name} 🚀",
                    "content": "Hola [nombre],\n\nGracias por suscribirte. Te enviaremos tips "
                    "exclusivos cada semana...",
                },
                {
                    "name": "Promotional",
                    "subject": "⚡ Oferta limitada: 30% descuento",
                    "content": "Válido solo por 48 horas...",
                },
                {
                    "name": "Re-engagement",
                    "subject": "Te echamos de menos 😔",
                    "content": "Notamos que no has abierto nuestros últimos emails...",
                }
            ],
            best_practices=[
                "Subject line corto y llamativo",
                "Preheader optimizado",
                "Mobile-friendly design",
                "CTA claro y en alto",
                "Test A/B de subject lines",
                "Segmenta tu lista",
                "Envía 1-2 emails por semana"
            ]
        )

    def _copy_generic(self, business_name: str) -> CopyKit:
        """Generic copy"""

        return CopyKit(
            channel="generic",
            headlines=[f"Bienvenido a {business_name}"],
            descriptions=[],
            calls_to_action=["Contacta con nosotros"],
            sample_posts=[],
            email_templates=[],
            best_practices=[]
        )
