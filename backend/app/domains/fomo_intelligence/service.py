"""FOMO Intelligence service: registra usos reales + aprende qué convierte."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.fomo_intelligence.models import (
    FOMOStrategyApplication, FOMOStrategyOutcome, FOMOStrategyIntelligence,
    FOMOStrategyType,
)


class FOMOIntelligenceService:
    """Registra aplicaciones de las 4 estrategias FOMO y genera inteligencia agregada."""

    STRATEGY_TEMPLATES = {
        FOMOStrategyType.ESCASEZ_REAL: {
            "requires_fields": ["slots_remaining", "total_slots"],
            "message_template": "Quedan {slots_remaining} de {total_slots} cupos disponibles",
        },
        FOMOStrategyType.PRUEBA_SOCIAL: {
            "requires_fields": ["buyer_name_or_alias", "result_or_quote"],
            "message_template": '"{result_or_quote}" — {buyer_name_or_alias}',
        },
        FOMOStrategyType.EXCLUSIVIDAD: {
            "requires_fields": ["group_size_or_criteria", "access_window"],
            "message_template": "Acceso solo para {group_size_or_criteria}, disponible {access_window}",
        },
        FOMOStrategyType.TRANSPARENCIA: {
            "requires_fields": ["metric_name", "metric_value", "verification_source"],
            "message_template": "{metric_name}: {metric_value} (verificado en {verification_source})",
        },
    }

    @classmethod
    def _validate_and_render(cls, strategy_type: FOMOStrategyType, data_snapshot: dict) -> str:
        """Valida que el snapshot tenga los campos reales requeridos y arma el mensaje."""
        template = cls.STRATEGY_TEMPLATES[strategy_type]
        missing = [f for f in template["requires_fields"] if f not in data_snapshot]
        if missing:
            raise ValueError(
                f"data_snapshot incompleto para {strategy_type.value}: faltan {missing}. "
                f"FOMO sin dato real no se registra (viola integridad de Transparencia)."
            )
        return template["message_template"].format(**data_snapshot)

    @classmethod
    async def register_strategy_application(
        cls,
        db: AsyncSession,
        business_id: str,
        strategy_type: str,
        target_type: str,
        target_id: str,
        real_data_source: str,
        data_snapshot: dict,
        channel: str | None = None,
        personality_target: str | None = None,
    ) -> FOMOStrategyApplication:
        """Registra un uso real de una de las 4 estrategias FOMO."""
        strategy_enum = FOMOStrategyType(strategy_type)
        message = cls._validate_and_render(strategy_enum, data_snapshot)

        application = FOMOStrategyApplication(
            id=str(uuid.uuid4()),
            business_id=business_id,
            strategy_type=strategy_enum,
            target_type=target_type,
            target_id=target_id,
            channel=channel,
            personality_target=personality_target,
            real_data_source=real_data_source,
            data_snapshot=data_snapshot,
            generated_message=message,
        )
        db.add(application)
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def record_outcome(
        db: AsyncSession,
        application_id: str,
        impressions: int,
        clicks: int,
        conversions: int,
        revenue: float = 0.0,
        perceived_as_genuine: bool | None = None,
    ) -> FOMOStrategyOutcome:
        """Registra el resultado medido de una aplicación de estrategia."""
        outcome = FOMOStrategyOutcome(
            id=str(uuid.uuid4()),
            application_id=application_id,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            revenue=revenue,
            perceived_as_genuine=perceived_as_genuine,
        )
        db.add(outcome)
        await db.commit()
        await db.refresh(outcome)
        return outcome

    @staticmethod
    async def generate_intelligence_report(db: AsyncSession) -> dict:
        """Agrega applications + outcomes por estrategia y por personalidad, recalcula intelligence."""
        apps_result = await db.execute(select(FOMOStrategyApplication))
        applications = apps_result.scalars().all()

        outcomes_result = await db.execute(select(FOMOStrategyOutcome))
        outcomes = outcomes_result.scalars().all()

        outcomes_by_app = {}
        for o in outcomes:
            outcomes_by_app.setdefault(o.application_id, []).append(o)

        buckets: dict[tuple, dict] = {}
        for app in applications:
            key = (app.strategy_type, app.personality_target or "general")
            bucket = buckets.setdefault(key, {
                "sample_size": 0, "impressions": 0, "conversions": 0,
                "genuine_votes": 0, "genuine_total": 0,
            })
            bucket["sample_size"] += 1
            for o in outcomes_by_app.get(app.id, []):
                bucket["impressions"] += o.impressions
                bucket["conversions"] += o.conversions
                if o.perceived_as_genuine is not None:
                    bucket["genuine_total"] += 1
                    if o.perceived_as_genuine:
                        bucket["genuine_votes"] += 1

        report = []
        for (strategy_type, personality), b in buckets.items():
            conversion_rate = b["conversions"] / max(b["impressions"], 1)
            trust_score = b["genuine_votes"] / max(b["genuine_total"], 1) if b["genuine_total"] else None
            confidence = "high" if b["sample_size"] >= 30 else "medium" if b["sample_size"] >= 10 else "low"

            # Upsert intelligence row
            existing = await db.execute(
                select(FOMOStrategyIntelligence).where(
                    FOMOStrategyIntelligence.strategy_type == strategy_type,
                    FOMOStrategyIntelligence.personality_type == personality,
                )
            )
            row = existing.scalar_one_or_none()
            if row is None:
                row = FOMOStrategyIntelligence(
                    id=str(uuid.uuid4()),
                    strategy_type=strategy_type,
                    personality_type=personality,
                )
                db.add(row)

            row.sample_size = b["sample_size"]
            row.total_impressions = b["impressions"]
            row.total_conversions = b["conversions"]
            row.avg_conversion_rate = conversion_rate
            row.trust_score = trust_score if trust_score is not None else row.trust_score
            row.confidence_level = confidence
            row.recommendation = (
                f"Escalar {strategy_type.value} para {personality}" if conversion_rate > 0.05
                else f"Ajustar mensaje de {strategy_type.value} para {personality} (conversión baja)"
            )

            report.append({
                "strategy_type": strategy_type.value,
                "personality_type": personality,
                "sample_size": b["sample_size"],
                "conversion_rate": round(conversion_rate, 4),
                "trust_score": round(trust_score, 2) if trust_score is not None else None,
                "confidence_level": confidence,
                "recommendation": row.recommendation,
            })

        await db.commit()
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_applications": len(applications),
            "total_outcomes_measured": len(outcomes),
            "strategy_breakdown": sorted(report, key=lambda r: r["conversion_rate"], reverse=True),
        }

    @staticmethod
    async def recommend_strategy(db: AsyncSession, personality_type: str) -> dict:
        """Recomienda la mejor estrategia para una personalidad, basado en intelligence acumulada."""
        result = await db.execute(
            select(FOMOStrategyIntelligence).where(
                FOMOStrategyIntelligence.personality_type == personality_type
            ).order_by(FOMOStrategyIntelligence.avg_conversion_rate.desc())
        )
        rows = result.scalars().all()

        if not rows:
            # Sin data propia todavía: usar priors basados en literatura de conducta
            defaults = {
                "impulse_buyer": FOMOStrategyType.ESCASEZ_REAL,
                "skeptic": FOMOStrategyType.TRANSPARENCIA,
                "social_proof_seeker": FOMOStrategyType.PRUEBA_SOCIAL,
                "status_conscious": FOMOStrategyType.EXCLUSIVIDAD,
                "pragmatist": FOMOStrategyType.TRANSPARENCIA,
                "analyst": FOMOStrategyType.TRANSPARENCIA,
                "early_adopter": FOMOStrategyType.EXCLUSIVIDAD,
                "value_maximizer": FOMOStrategyType.PRUEBA_SOCIAL,
            }
            fallback = defaults.get(personality_type, FOMOStrategyType.PRUEBA_SOCIAL)
            return {
                "personality_type": personality_type,
                "recommended_strategy": fallback.value,
                "confidence": "prior",
                "reason": "Sin datos propios aún; recomendación basada en heurística inicial",
            }

        best = rows[0]
        return {
            "personality_type": personality_type,
            "recommended_strategy": best.strategy_type.value,
            "confidence": best.confidence_level,
            "conversion_rate": round(best.avg_conversion_rate, 4),
            "trust_score": round(best.trust_score, 2) if best.trust_score else None,
            "reason": best.recommendation,
            "alternatives": [
                {"strategy": r.strategy_type.value, "conversion_rate": round(r.avg_conversion_rate, 4)}
                for r in rows[1:]
            ],
        }

    @staticmethod
    async def get_transparency_dashboard(db: AsyncSession) -> dict:
        """Métricas reales del sistema para usar como contenido de la estrategia Transparencia.

        Estos números deben salir de datos reales del sistema (no inventados) —
        cuando la integración con conversion_engine/loyalty_engine está completa,
        estas queries deben apuntar a esas tablas en vez de a valores fijos.
        """
        apps_count = await db.execute(select(func.count(FOMOStrategyApplication.id)))
        total_applications = apps_count.scalar() or 0

        outcomes_result = await db.execute(
            select(
                func.sum(FOMOStrategyOutcome.conversions),
                func.sum(FOMOStrategyOutcome.impressions),
                func.sum(FOMOStrategyOutcome.revenue),
            )
        )
        total_conversions, total_impressions, total_revenue = outcomes_result.one()

        return {
            "verified_metrics": {
                "fomo_strategies_registered": total_applications,
                "total_conversions_tracked": total_conversions or 0,
                "total_impressions_tracked": total_impressions or 0,
                "total_revenue_attributed": float(total_revenue or 0),
                "overall_conversion_rate": round(
                    (total_conversions or 0) / max(total_impressions or 1, 1), 4
                ),
            },
            "data_integrity_note": (
                "Estos números provienen de aplicaciones y resultados registrados "
                "en el sistema (fomo_strategy_applications/outcomes), no de estimaciones."
            ),
            "usable_as_transparencia_content": True,
        }
