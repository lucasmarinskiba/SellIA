"""Gamification & Experience Service

Makes the user feel the thrill of progress, achievement, and ownership.
The system becomes their HOME — something they love, nurture, and grow.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gamification.models import (
    UserGamificationProfile, Achievement, UserAchievement,
    CelebrationEvent, AchievementCategory, AchievementTier,
)
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)

# Level titles
LEVEL_TITLES = {
    1: "Emprendedor Novato",
    2: "Cazador de Oportunidades",
    3: "Constructor de Puentes",
    4: "Arquitecto de Ventas",
    5: "Capitán del Crecimiento",
    6: "Comandante del Mercado",
    7: "Visionario Digital",
    8: "Magnate en Formación",
    9: "Leyenda del Ecommerce",
    10: "Dueño de su Destino",
    15: "Emperador del Auto-Piloto",
    20: "Dios del Sueño Tranquilo",
    25: "Semidiós del Cashflow",
    30: "Inmortal de los Negocios",
}

# Achievement definitions (seeded into DB)
ACHIEVEMENT_DEFINITIONS = [
    # SALES
    {"slug": "first-sale", "name": "Primera Venta", "description": "Cerraste tu primera venta con SellIA", "category": AchievementCategory.SALES, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 50, "icon": "shopping-bag", "color": "#CD7F32"},
    {"slug": "sale-streak-7", "name": "Semana Dorada", "description": "7 ventas en 7 días", "category": AchievementCategory.SALES, "tier": AchievementTier.SILVER, "requirement_type": "streak", "requirement_value": 7, "xp_reward": 150, "icon": "zap", "color": "#C0C0C0"},
    {"slug": "sale-100", "name": "Centurión", "description": "100 ventas cerradas", "category": AchievementCategory.SALES, "tier": AchievementTier.GOLD, "requirement_type": "count", "requirement_value": 100, "xp_reward": 500, "icon": "award", "color": "#FFD700"},
    {"slug": "big-deal-10k", "name": "El Gran Cierre", "description": "Una venta de $10,000+", "category": AchievementCategory.SALES, "tier": AchievementTier.PLATINUM, "requirement_type": "threshold", "requirement_value": 10000, "xp_reward": 1000, "icon": "crown", "color": "#E5E4E2"},

    # GROWTH
    {"slug": "first-lead", "name": "Primer Interesado", "description": "Tu primer lead orgánico", "category": AchievementCategory.GROWTH, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 25, "icon": "user-plus", "color": "#CD7F32"},
    {"slug": "leads-100", "name": "Imán Humano", "description": "100 leads capturados", "category": AchievementCategory.GROWTH, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 100, "xp_reward": 200, "icon": "users", "color": "#C0C0C0"},
    {"slug": "leads-1000", "name": "Fuerza de la Naturaleza", "description": "1,000 leads capturados", "category": AchievementCategory.GROWTH, "tier": AchievementTier.GOLD, "requirement_type": "count", "requirement_value": 1000, "xp_reward": 750, "icon": "trending-up", "color": "#FFD700"},
    {"slug": "viral-k-1", "name": "Efecto Domino", "description": "Alcanzaste K-Factor >= 1.0 en referidos", "category": AchievementCategory.GROWTH, "tier": AchievementTier.PLATINUM, "requirement_type": "threshold", "requirement_value": 100, "xp_reward": 1000, "icon": "share-2", "color": "#E5E4E2"},

    # CONSISTENCY
    {"slug": "login-3", "name": "Ritual Diario", "description": "3 días seguidos usando SellIA", "category": AchievementCategory.CONSISTENCY, "tier": AchievementTier.BRONZE, "requirement_type": "streak", "requirement_value": 3, "xp_reward": 30, "icon": "calendar", "color": "#CD7F32"},
    {"slug": "login-7", "name": "Disciplina de Hierro", "description": "7 días seguidos", "category": AchievementCategory.CONSISTENCY, "tier": AchievementTier.SILVER, "requirement_type": "streak", "requirement_value": 7, "xp_reward": 100, "icon": "flame", "color": "#C0C0C0"},
    {"slug": "login-30", "name": "Maratonista", "description": "30 días seguidos", "category": AchievementCategory.CONSISTENCY, "tier": AchievementTier.GOLD, "requirement_type": "streak", "requirement_value": 30, "xp_reward": 500, "icon": "star", "color": "#FFD700"},
    {"slug": "autopilot-7", "name": "Confianza Total", "description": "7 días seguidos con autopilot activo", "category": AchievementCategory.CONSISTENCY, "tier": AchievementTier.SILVER, "requirement_type": "streak", "requirement_value": 7, "xp_reward": 150, "icon": "shield", "color": "#C0C0C0"},

    # MASTERY
    {"slug": "first-campaign", "name": "Director de Marketing", "description": "Creaste tu primera campaña de growth", "category": AchievementCategory.MASTERY, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 40, "icon": "megaphone", "color": "#CD7F32"},
    {"slug": "lead-magnet-5", "name": "Arquitecto de Imanes", "description": "5 lead magnets creados", "category": AchievementCategory.MASTERY, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 5, "xp_reward": 120, "icon": "gift", "color": "#C0C0C0"},
    {"slug": "seo-content-10", "name": "Escritor Fantasma", "description": "10 artículos SEO generados", "category": AchievementCategory.MASTERY, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 10, "xp_reward": 150, "icon": "book-open", "color": "#C0C0C0"},

    # SOCIAL
    {"slug": "first-review", "name": "Amor Recibido", "description": "Tu primera review de cliente", "category": AchievementCategory.SOCIAL, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 35, "icon": "heart", "color": "#CD7F32"},
    {"slug": "reviews-10", "name": "Querido por Todos", "description": "10 reviews positivas", "category": AchievementCategory.SOCIAL, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 10, "xp_reward": 120, "icon": "thumbs-up", "color": "#C0C0C0"},
    {"slug": "first-referral", "name": "Boca en Boca", "description": "Tu primer cliente referido", "category": AchievementCategory.SOCIAL, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 40, "icon": "message-circle", "color": "#CD7F32"},
    {"slug": "referrals-10", "name": "Red de Influencia", "description": "10 clientes referidos", "category": AchievementCategory.SOCIAL, "tier": AchievementTier.GOLD, "requirement_type": "count", "requirement_value": 10, "xp_reward": 400, "icon": "network", "color": "#FFD700"},

    # ZEN
    {"slug": "first-night-sale", "name": "Vendiendo Mientras Dormía", "description": "Tu primera venta autopilot nocturna", "category": AchievementCategory.ZEN, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 75, "icon": "moon", "color": "#CD7F32"},
    {"slug": "night-sales-10", "name": "El Sistema No Duerme", "description": "10 ventas nocturnas autopilot", "category": AchievementCategory.ZEN, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 10, "xp_reward": 200, "icon": "cloud-moon", "color": "#C0C0C0"},
    {"slug": "hands-off-week", "name": "Libertad Real", "description": "7 días sin tocar nada y el sistema vendió", "category": AchievementCategory.ZEN, "tier": AchievementTier.GOLD, "requirement_type": "streak", "requirement_value": 7, "xp_reward": 600, "icon": "coffee", "color": "#FFD700"},

    # MILESTONE
    {"slug": "month-1", "name": "Primer Mes Juntos", "description": "1 mes usando SellIA", "category": AchievementCategory.MILESTONE, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 100, "icon": "calendar-check", "color": "#CD7F32"},
    {"slug": "month-6", "name": "Medio Año de Crecimiento", "description": "6 meses transformando tu negocio", "category": AchievementCategory.MILESTONE, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 6, "xp_reward": 350, "icon": "calendar-days", "color": "#C0C0C0"},
    {"slug": "year-1", "name": "Veterano SellIA", "description": "1 año juntos", "category": AchievementCategory.MILESTONE, "tier": AchievementTier.GOLD, "requirement_type": "count", "requirement_value": 12, "xp_reward": 1000, "icon": "crown", "color": "#FFD700"},

    # MISSIONS
    {"slug": "first-mission", "name": "Primer Misión", "description": "Aprobaste y ejecutaste tu primera misión con SellIA", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.BRONZE, "requirement_type": "count", "requirement_value": 1, "xp_reward": 75, "icon": "rocket", "color": "#CD7F32"},
    {"slug": "mission-completed-5", "name": "Estratega en Acción", "description": "5 misiones completadas", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 5, "xp_reward": 250, "icon": "target", "color": "#C0C0C0"},
    {"slug": "mission-completed-25", "name": "Maestro de Misiones", "description": "25 misiones completadas", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.GOLD, "requirement_type": "count", "requirement_value": 25, "xp_reward": 800, "icon": "crosshair", "color": "#FFD700"},
    {"slug": "mission-completed-100", "name": "Legado Automatizado", "description": "100 misiones completadas — tu negocio prácticamente se maneja solo", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.PLATINUM, "requirement_type": "count", "requirement_value": 100, "xp_reward": 2500, "icon": "crown", "color": "#E5E4E2"},
    {"slug": "computer-use-pioneer", "name": "Pionero del Computer Use", "description": "Completaste 3 misiones usando navegación autónoma", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 3, "xp_reward": 300, "icon": "monitor", "color": "#C0C0C0", "requirement_context": {"platform": "computer_use"}},
    {"slug": "multi-platform-guru", "name": "Gurú Multi-Plataforma", "description": "Automatizaste 5 plataformas distintas", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.GOLD, "requirement_type": "count", "requirement_value": 5, "xp_reward": 600, "icon": "globe", "color": "#FFD700", "requirement_context": {"metric": "total_platforms_automated"}},
    {"slug": "diagnostic-master", "name": "Detective de Negocios", "description": "Ejecutaste 10 diagnósticos y actuaste sobre los resultados", "category": AchievementCategory.MISSIONS, "tier": AchievementTier.SILVER, "requirement_type": "count", "requirement_value": 10, "xp_reward": 200, "icon": "stethoscope", "color": "#C0C0C0", "requirement_context": {"action": "run_diagnostic"}},
]


class GamificationEngine:
    """Main engine for points, levels, achievements, and celebrations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, user_id: uuid.UUID, business_id: uuid.UUID) -> UserGamificationProfile:
        """Get or create user gamification profile."""
        result = await self.db.execute(
            select(UserGamificationProfile).where(
                UserGamificationProfile.user_id == user_id,
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserGamificationProfile(
                user_id=user_id,
                business_id=business_id,
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
        return profile

    async def add_xp(self, user_id: uuid.UUID, business_id: uuid.UUID, amount: int, reason: str = "") -> UserGamificationProfile:
        """Add XP to user and check for level ups."""
        profile = await self.get_or_create_profile(user_id, business_id)
        profile.total_xp += amount

        # Check level up
        while profile.total_xp >= profile.xp_to_next_level:
            profile.total_xp -= profile.xp_to_next_level
            profile.level += 1
            profile.xp_to_next_level = int(profile.xp_to_next_level * 1.5)
            profile.level_title = LEVEL_TITLES.get(profile.level, f"Nivel {profile.level}")

            # Celebration for level up
            await self._create_celebration(
                user_id=user_id,
                business_id=business_id,
                event_type="level_up",
                event_title=f"¡Subiste de nivel! Nivel {profile.level}",
                event_description=f"Ahora sos {profile.level_title}",
                intensity="big",
            )

        profile.progress_pct = (profile.total_xp / profile.xp_to_next_level) * 100
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def check_achievements(self, user_id: uuid.UUID, business_id: uuid.UUID) -> List[Achievement]:
        """Check and unlock any newly earned achievements."""
        profile = await self.get_or_create_profile(user_id, business_id)

        # Get all achievements
        all_achievements = await self.db.execute(select(Achievement).where(Achievement.is_active == True))
        achievements = all_achievements.scalars().all()

        # Get already unlocked
        unlocked_result = await self.db.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        )
        unlocked_ids = {r[0] for r in unlocked_result.all()}

        new_unlocks = []
        for achievement in achievements:
            if achievement.id in unlocked_ids:
                continue

            if await self._meets_requirement(profile, achievement):
                # Unlock!
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                )
                self.db.add(ua)
                profile.total_achievements += 1

                # Add XP
                await self.add_xp(user_id, business_id, achievement.xp_reward, f"achievement:{achievement.slug}")

                # Update garden
                garden_reward = achievement.garden_reward or {}
                if garden_reward:
                    for key, val in garden_reward.items():
                        profile.garden_state[key] = profile.garden_state.get(key, 0) + val

                # Celebration
                await self._create_celebration(
                    user_id=user_id,
                    business_id=business_id,
                    event_type="achievement",
                    event_title=f"¡Logro desbloqueado: {achievement.name}!",
                    event_description=achievement.description,
                    intensity={"bronze": "small", "silver": "medium", "gold": "big", "platinum": "epic", "diamond": "epic"}.get(achievement.tier.value, "medium"),
                    companion_message=await self._generate_companion_achievement_message(achievement),
                )

                new_unlocks.append(achievement)

        if new_unlocks:
            await self.db.commit()
            await self.db.refresh(profile)

        return new_unlocks

    async def _meets_requirement(self, profile: UserGamificationProfile, achievement: Achievement) -> bool:
        """Check if user meets achievement requirement."""
        req_type = achievement.requirement_type
        req_val = achievement.requirement_value

        if req_type == "count":
            if achievement.category == AchievementCategory.SALES:
                return profile.total_sales_closed >= req_val
            elif achievement.category == AchievementCategory.GROWTH:
                return profile.total_leads_acquired >= req_val
            elif achievement.category == AchievementCategory.MASTERY:
                if "lead-magnet" in achievement.slug:
                    # Would need actual count from DB
                    return False  # Placeholder
                return False
            elif achievement.category == AchievementCategory.SOCIAL:
                if "review" in achievement.slug:
                    return profile.total_reviews_collected >= req_val
                elif "referral" in achievement.slug:
                    return profile.total_referrals_generated >= req_val
                return False
            elif achievement.category == AchievementCategory.ZEN:
                return profile.total_sales_closed >= req_val  # Simplified
            elif achievement.category == AchievementCategory.MILESTONE:
                # Days since created
                days = (datetime.now(timezone.utc) - profile.created_at).days
                months = days // 30
                return months >= req_val
            elif achievement.category == AchievementCategory.MISSIONS:
                ctx = achievement.requirement_context or {}
                if ctx.get("metric") == "total_platforms_automated":
                    return profile.total_platforms_automated >= req_val
                elif ctx.get("platform") == "computer_use":
                    return profile.total_computer_use_sessions >= req_val
                return profile.total_missions_completed >= req_val

        elif req_type == "streak":
            if "autopilot" in achievement.slug:
                return profile.autopilot_trust_streak >= req_val
            return profile.current_login_streak >= req_val

        elif req_type == "threshold":
            if "big-deal" in achievement.slug:
                return profile.total_revenue_generated >= req_val
            elif "viral" in achievement.slug:
                # Would need referral metrics
                return False
            return False

        return False

    async def record_sale(self, user_id: uuid.UUID, business_id: uuid.UUID, amount: float, was_autopilot: bool = False) -> dict:
        """Record a sale and trigger celebrations/achievements."""
        profile = await self.get_or_create_profile(user_id, business_id)
        profile.total_sales_closed += 1
        profile.total_revenue_generated += amount
        await self.db.commit()

        # XP for sale
        xp = int(amount * 0.1) + 10  # $100 = 20 XP
        await self.add_xp(user_id, business_id, xp, "sale")

        # Celebration
        intensity = "small" if amount < 100 else "medium" if amount < 1000 else "big" if amount < 5000 else "epic"
        companion_msg = await self._generate_companion_sale_message(amount, was_autopilot)

        await self._create_celebration(
            user_id=user_id,
            business_id=business_id,
            event_type="sale",
            event_title="¡Venta cerrada!",
            event_description=f"Venta de ${amount:,.2f}",
            event_value=amount,
            intensity=intensity,
            companion_message=companion_msg,
        )

        # Check achievements
        new_achievements = await self.check_achievements(user_id, business_id)

        return {
            "xp_gained": xp,
            "new_achievements": [{"id": str(a.id), "name": a.name, "tier": a.tier.value} for a in new_achievements],
            "celebration_intensity": intensity,
        }

    async def record_login(self, user_id: uuid.UUID, business_id: uuid.UUID) -> dict:
        """Record user login and update streaks."""
        profile = await self.get_or_create_profile(user_id, business_id)

        today = datetime.now(timezone.utc).date()
        if profile.last_login_date:
            last_date = profile.last_login_date.date() if hasattr(profile.last_login_date, 'date') else profile.last_login_date
            if isinstance(last_date, datetime):
                last_date = last_date.date()

            if last_date == today:
                pass  # Already logged in today
            elif (today - last_date).days == 1:
                profile.current_login_streak += 1
                profile.max_login_streak = max(profile.max_login_streak, profile.current_login_streak)
            else:
                profile.current_login_streak = 1
        else:
            profile.current_login_streak = 1

        profile.last_login_date = datetime.now(timezone.utc)
        await self.db.commit()

        # XP for login
        xp = 5 + min(profile.current_login_streak, 10)  # Bonus for streak
        await self.add_xp(user_id, business_id, xp, "login")

        # Check achievements
        new_achievements = await self.check_achievements(user_id, business_id)

        return {
            "streak": profile.current_login_streak,
            "xp_gained": xp,
            "new_achievements": [{"id": str(a.id), "name": a.name} for a in new_achievements],
        }

    async def record_mission_completed(self, user_id: uuid.UUID, business_id: uuid.UUID, mission_platforms: List[str] = None, used_computer_use: bool = False) -> dict:
        """Record a completed mission and trigger celebrations/achievements."""
        profile = await self.get_or_create_profile(user_id, business_id)
        profile.total_missions_completed += 1
        if used_computer_use:
            profile.total_computer_use_sessions += 1
        if mission_platforms:
            profile.total_platforms_automated = max(profile.total_platforms_automated, len(set(mission_platforms)))
        await self.db.commit()

        # XP for mission completion
        xp = 50 + (10 * (len(mission_platforms) if mission_platforms else 1))
        await self.add_xp(user_id, business_id, xp, "mission_completed")

        # Celebration
        await self._create_celebration(
            user_id=user_id,
            business_id=business_id,
            event_type="mission",
            event_title="¡Misión completada!",
            event_description=f"Misión ejecutada en {len(mission_platforms) if mission_platforms else 1} plataforma(s)",
            intensity="medium",
            companion_message="🚀 ¡Otra misión completada! Tu negocio crece mientras tú descansas.",
        )

        # Check achievements
        new_achievements = await self.check_achievements(user_id, business_id)

        return {
            "xp_gained": xp,
            "new_achievements": [{"id": str(a.id), "name": a.name, "tier": a.tier.value} for a in new_achievements],
            "celebration_intensity": "medium",
        }

    async def record_mission_started(self, user_id: uuid.UUID, business_id: uuid.UUID) -> None:
        """Record that a mission was started."""
        profile = await self.get_or_create_profile(user_id, business_id)
        profile.total_missions_started += 1
        await self.db.commit()

    async def get_pending_celebrations(self, user_id: uuid.UUID) -> List[CelebrationEvent]:
        """Get unshown celebration events for the user."""
        result = await self.db.execute(
            select(CelebrationEvent).where(
                CelebrationEvent.user_id == user_id,
                CelebrationEvent.was_shown == False,
            ).order_by(desc(CelebrationEvent.created_at)).limit(10)
        )
        return list(result.scalars().all())

    async def mark_celebration_shown(self, celebration_id: uuid.UUID):
        """Mark a celebration as shown."""
        event = await self.db.get(CelebrationEvent, celebration_id)
        if event:
            event.was_shown = True
            event.shown_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def update_garden(self, user_id: uuid.UUID, business_id: uuid.UUID, action: str) -> dict:
        """Update the visual 'Business Garden' based on user actions."""
        profile = await self.get_or_create_profile(user_id, business_id)
        garden = profile.garden_state

        if action == "sale":
            garden["flowers"] = garden.get("flowers", 0) + 1
            if garden["flowers"] >= 10 and garden.get("trees", 0) < (garden["flowers"] // 10):
                garden["trees"] = garden.get("trees", 0) + 1
                return {"action": "sale", "grew_tree": True, "garden": garden}
        elif action == "lead":
            garden["seeds"] = garden.get("seeds", 0) + 1
        elif action == "review":
            garden["butterflies"] = garden.get("butterflies", 0) + 1
        elif action == "referral":
            garden["birds"] = garden.get("birds", 0) + 1
        elif action == "milestone":
            garden["fountain"] = True
            garden["lights_on"] = True

        await self.db.commit()
        return {"action": action, "garden": garden}

    async def get_companion_message(self, user_id: uuid.UUID, business_id: uuid.UUID, context: str = "welcome") -> str:
        """Get a personalized message from the companion AI."""
        profile = await self.get_or_create_profile(user_id, business_id)

        messages = {
            "welcome": [
                f"¡Bienvenido de vuelta! Tu jardín tiene {profile.garden_state.get('flowers', 0)} flores hoy. 🌸",
                "¿Listo para hacer crecer tu negocio hoy? Estoy acá para ayudarte.",
                f"¡{profile.level_title}! Ese es tu título ahora. Suena bien, ¿no?",
            ],
            "morning": [
                "Buen día! Mientras dormías, el sistema estuvo trabajando por vos. ¿Querés ver qué pasó?",
                "¡Nuevo día, nuevas oportunidades! Tu negocio está listo para crecer.",
            ],
            "sale": [
                "¡BOOM! Otra venta. Tu jardín acaba de florecer una flor más. 🌺",
                "¿Escuchaste eso? Fue el sonido de otra venta cerrada automáticamente.",
                "Tu sistema no duerme, y los resultados lo demuestran. ¡Felicitaciones!",
            ],
            "streak": [
                f"¡{profile.current_login_streak} días seguidos! Esa constancia es lo que separa a los campeones.",
                "Tu racha sigue viva. No rompas la cadena! 🔥",
            ],
            "zen": [
                "¿Sabés lo mejor? No tuviste que hacer NADA para esta venta. El sistema lo hizo todo.",
                "Esta venta llegó mientras descansabas. Eso es libertad real. ☕",
            ],
            "achievement": [
                "¡Nuevo logro desbloqueado! Estás construyendo algo grande.",
                "Otro trofeo para tu colección. ¿Cuál será el próximo?",
            ],
            "milestone": [
                f"¡{profile.level_title}! Llegaste lejos. Pero esto es solo el comienzo.",
                "Mirá todo lo que construiste. ¿Te acordás cuando empezaste?",
            ],
        }

        import random
        return random.choice(messages.get(context, messages["welcome"]))

    # ========== Private helpers ==========

    async def _create_celebration(
        self,
        user_id: uuid.UUID,
        business_id: uuid.UUID,
        event_type: str,
        event_title: str,
        event_description: str = "",
        event_value: float = None,
        intensity: str = "medium",
        companion_message: str = None,
    ):
        """Create a celebration event."""
        event = CelebrationEvent(
            user_id=user_id,
            business_id=business_id,
            event_type=event_type,
            event_title=event_title,
            event_description=event_description,
            event_value=event_value,
            intensity=intensity,
            companion_message=companion_message or event_title,
        )
        self.db.add(event)
        await self.db.commit()

    async def _generate_companion_sale_message(self, amount: float, was_autopilot: bool) -> str:
        """Generate a companion message for a sale."""
        if was_autopilot:
            messages = [
                f"¡Chin chin! 🥂 ${amount:,.0f} mientras descansabas. El piloto automático no duerme.",
                f"¿Sabés qué estabas haciendo cuando cerraste esta venta? ¡Lo que quisieras! Porque el sistema lo hizo solo. ☕",
                f"¡Ding ding! 💰 ${amount:,.0f} en la cuenta. Y ni siquiera tuviste que levantar un dedo.",
            ]
        else:
            messages = [
                f"¡Excelente trabajo! ${amount:,.0f} en el bolsillo. ¿Vamos por más?",
                f"¡Venta cerrada! ${amount:,.0f}. Tu esfuerzo + el sistema = resultados épicos.",
                f"¡Boom! 💥 ${amount:,.0f}. Cada venta es un ladrillo más en tu imperio.",
            ]
        import random
        return random.choice(messages)

    async def _generate_companion_achievement_message(self, achievement: Achievement) -> str:
        """Generate a companion message for achievement unlock."""
        messages = {
            AchievementTier.BRONZE: [
                f"¡{achievement.name}! Tu primer paso hacia algo grande. 🥉",
                "Empezando con el pie derecho. ¡Seguí así!",
            ],
            AchievementTier.SILVER: [
                f"¡{achievement.name}! Ya no sos un novato. 🥈",
                "Esa plata brilla casi tanto como tu negocio.",
            ],
            AchievementTier.GOLD: [
                f"¡{achievement.name}! Oro puro. 🥇",
                "¡Campeón! Esto ya es en serio.",
            ],
            AchievementTier.PLATINUM: [
                f"¡{achievement.name}! Élite total. 💎",
                "Pocos llegan acá. Vos sos uno de ellos.",
            ],
        }
        import random
        return random.choice(messages.get(achievement.tier, ["¡Logro desbloqueado!"]))


class GamificationSeeder:
    """Seeds default achievements into the database."""

    @staticmethod
    async def seed_achievements(db: AsyncSession):
        """Seed all predefined achievements."""
        for ach_data in ACHIEVEMENT_DEFINITIONS:
            result = await db.execute(
                select(Achievement).where(Achievement.slug == ach_data["slug"])
            )
            if not result.scalar_one_or_none():
                achievement = Achievement(**ach_data)
                db.add(achievement)
        await db.commit()
        logger.info(f"Seeded {len(ACHIEVEMENT_DEFINITIONS)} achievements")
