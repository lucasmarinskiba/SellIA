"""Content Generator — Auto-create captions + content for growth.

Genera captions contextuales basadas en trending topics + product.
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ContentStyle(str, Enum):
    """Estilos de contenido."""
    EDUCATIONAL = "educational"  # Tips, how-to
    MOTIVATIONAL = "motivational"  # Inspiración
    ENTERTAINING = "entertaining"  # Diversión
    STORYTELLING = "storytelling"  # Narrativa
    TESTIMONIAL = "testimonial"  # Caso de éxito
    PROMOTIONAL = "promotional"  # Venta directa


class ContentTemplate:
    """Template para generar contenido."""

    TEMPLATES = {
        ContentStyle.EDUCATIONAL: [
            "🔥 {tip_number} tip para {topic}:\n{insight}\n\n💡 {action}\n\n{hashtags}",
            "¿Sabías que {fact}?\n\nAcá está cómo {solution}:\n{steps}\n\n{hashtags}",
            "Guía completa: {topic}\n\n✅ {benefit}\n📌 {detail}\n🎯 {cta}\n\n{hashtags}",
        ],
        ContentStyle.MOTIVATIONAL: [
            "El {successful_person} hizo {action}. Vos también podés.\n\n{motivation}\n\n{hashtags}",
            "De {before} a {after}? Sí, es posible.\n\n{story}\n\n{hashtags}",
            "No es suerte, es {strategy}.\n\n{explanation}\n\n{hashtags}",
        ],
        ContentStyle.TESTIMONIAL: [
            "\"Ganamos {amount} en {timeframe}\" - {customer}\n\n{story}\n\n¿Vos querés lo mismo?\n\n{hashtags}",
            "Cliente: {name}\nResultado: {result}\nTiempo: {time}\n\n{detail}\n\n{hashtags}",
        ],
        ContentStyle.ENTERTAINING: [
            "POV: Eres {persona}...\n\n{scenario}\n\n{punchline}\n\n{hashtags}",
            "Cuando vs Cuando no:\n{contrast_1} ❌\n{contrast_2} ✅\n\n{hashtags}",
        ],
        ContentStyle.PROMOTIONAL: [
            "🎁 Oferta limitada: {offer}\n\n✨ {benefit}\n⚡ {urgency}\n\n{cta}\n\n{hashtags}",
            "Por {limited_time}: {product}\n\n{value}\n\n→ {link}\n\n{hashtags}",
        ],
    }

    HOOKS = [
        "¿Cuál es tu? Yo elegiría...",
        "Si solo tuvieras 1 tip...",
        "Nadie te va a decir esto pero...",
        "Esto cambió todo para mí...",
        "La mayoría falla en...",
        "Te muestro exactamente cómo...",
        "Los que ganan saben...",
        "La verdad es que...",
    ]

    def __init__(self):
        self.logger = logger

    def generate_caption(
        self,
        product_info: Dict[str, Any],
        trending_topic: str,
        style: ContentStyle,
        platform: str,  # instagram, tiktok
    ) -> str:
        """Genera caption automático."""
        try:
            # Seleccionar template
            templates = self.TEMPLATES.get(style, self.TEMPLATES[ContentStyle.EDUCATIONAL])
            template = templates[0]  # Usar primer template por ahora

            # Contexto base
            context = {
                "topic": trending_topic,
                "product": product_info.get("name", "producto"),
                "price": product_info.get("price", "99"),
                "benefit": product_info.get("benefit", "cambiar tu vida"),
                "tip_number": self._get_tip_number(),
                "insight": f"La mayoría intenta vender sin {trending_topic}",
                "action": f"Aquí está el secreto...",
                "hashtags": self._generate_hashtags(trending_topic, platform),
                "successful_person": "Hormozi",
                "action_text": "construyó su imperio",
                "motivation": "Vos también podés. No es tarde.",
                "before": "$0/mes",
                "after": "$10k/mes",
                "story": f"Después de aprender {trending_topic}",
                "strategy": "disciplina diaria",
                "explanation": f"Aplicando {trending_topic} correctamente",
                "amount": "$50k",
                "timeframe": "30 días",
                "customer": "Juan",
                "result": f"Domina {trending_topic}",
                "time": "3 meses",
                "detail": "Y puede enseñarte cómo...",
                "name": "María",
                "persona": "un emprendedor",
                "scenario": f"aprendiendo {trending_topic}",
                "punchline": "Cambio total de vida 🚀",
                "contrast_1": "Trabajar sin {topic}",
                "contrast_2": f"Usar {topic} estratégicamente",
                "offer": f"30% OFF en {product_info.get('name')}",
                "urgency": "Solo hoy",
                "cta": "→ Compra ahora",
                "link": "linktr.ee/tulink",
                "limited_time": "hoy",
                "value": f"Acceso a {product_info.get('features', '10 lecciones')}",
            }

            # Rellenar template
            caption = template.format(**context)

            # Limitar a 2200 chars (Instagram max)
            if len(caption) > 2200:
                caption = caption[:2197] + "..."

            self.logger.info(f"Generated caption: {len(caption)} chars | style={style.value}")

            return caption

        except Exception as e:
            self.logger.error(f"Error generating caption: {e}")
            return f"🔥 {trending_topic}\n\n{product_info.get('name')} te espera.\n\n#growth #viralcontent"

    def _get_tip_number(self) -> str:
        """Random tip number 1-10."""
        import random
        return str(random.randint(1, 10))

    def _generate_hashtags(self, trending_topic: str, platform: str) -> str:
        """Genera hashtags relevantes."""
        base_hashtags = [
            f"#{trending_topic.replace(' ', '')}",
            "#growth",
            "#viral",
            "#motivation",
            "#business",
            "#sales",
        ]

        if platform == "tiktok":
            base_hashtags.extend(["#foryou", "#viral", "#trending", "#challenge"])

        return " ".join(base_hashtags[:12])

    def select_image_theme(self, trending_topic: str) -> Dict[str, Any]:
        """Sugiere tema de imagen para trending topic."""
        themes = {
            "hustle_culture": {
                "description": "Person working at desk, laptop, coffee",
                "colors": ["#1a1a1a", "#FFD700", "#FFFFFF"],
                "mood": "determined, focused",
            },
            "personal_finance": {
                "description": "Money, graphs, upward trend",
                "colors": ["#2E7D32", "#1976D2", "#FFC107"],
                "mood": "confident, prosperous",
            },
            "ai_tools": {
                "description": "Tech interface, automation, productivity",
                "colors": ["#0D47A1", "#7B1FA2", "#F50057"],
                "mood": "futuristic, innovative",
            },
            "transformation": {
                "description": "Before/after, growth chart, success",
                "colors": ["#FF6F00", "#1B5E20", "#FFFFFF"],
                "mood": "inspiring, powerful",
            },
        }

        # Match topic to theme
        for theme_name, theme_data in themes.items():
            if theme_name in trending_topic.lower():
                return theme_data

        # Default
        return {
            "description": "Professional, clean, motivational",
            "colors": ["#000000", "#FFFFFF", "#FF5722"],
            "mood": "professional, engaging",
        }


def get_content_generator() -> ContentTemplate:
    return ContentTemplate()
