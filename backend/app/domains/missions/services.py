"""SellIA Missions — Services

Servicios para crear, ejecutar y monitorear misiones cross-plataforma.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from .models import Mission, MissionStep, BusinessDiagnostic
from .schemas import (
    MissionCreate, MissionRead, MissionUpdate,
    MissionStepUpdate, BusinessDiagnosticCreate, BusinessDiagnosticRead,
    PlaybookRead,
)
from .playbook_library import get_playbook, list_playbooks, get_recommended_playbooks
from .diagnostic_engine import run_diagnostic


class MissionService:
    """Servicio principal de gestión de misiones."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── CRUD Misiones ─────────────────────────────────────────────────────────

    async def create_from_playbook(
        self,
        user_id: uuid.UUID,
        playbook_slug: str,
        business_id: Optional[uuid.UUID] = None,
        auto_approve_low_impact: bool = True,
    ) -> MissionRead:
        """Crear una misión a partir de un playbook."""
        playbook = get_playbook(playbook_slug)
        if not playbook:
            raise ValueError(f"Playbook '{playbook_slug}' no encontrado")

        mission = Mission(
            id=uuid.uuid4(),
            user_id=user_id,
            business_id=business_id,
            title=playbook.name,
            description=playbook.description,
            category=playbook.category,
            playbook_slug=playbook_slug,
            target_platforms=playbook.platforms,
            status="proposed",
            created_by="ai",
            expected_impact={
                "estimated_duration_minutes": playbook.estimated_duration_minutes,
                "platforms": playbook.platforms,
                "steps_count": len(playbook.steps),
            },
        )
        self.db.add(mission)

        # Crear pasos desde el playbook
        for i, step in enumerate(playbook.steps):
            mission_step = MissionStep(
                id=uuid.uuid4(),
                mission_id=mission.id,
                step_number=i + 1,
                title=step.title,
                description=step.description,
                platform=step.platform,
                action_type=step.action_type,
                action_params={
                    **step.params,
                    "url_template": step.url_template,
                },
                requires_approval=step.requires_approval,
                status="pending",
            )
            self.db.add(mission_step)

        await self.db.commit()
        await self.db.refresh(mission)
        return MissionRead.model_validate(mission)

    async def create_custom(
        self,
        user_id: uuid.UUID,
        data: MissionCreate,
    ) -> MissionRead:
        """Crear una misión personalizada."""
        mission = Mission(
            id=uuid.uuid4(),
            user_id=user_id,
            business_id=data.business_id,
            title=data.title,
            description=data.description,
            category=data.category,
            playbook_slug=data.playbook_slug,
            target_platforms=data.target_platforms,
            expected_impact=data.expected_impact,
            status="draft" if data.created_by == "user" else "proposed",
            created_by=data.created_by,
        )
        self.db.add(mission)

        for step_data in data.steps:
            step = MissionStep(
                id=uuid.uuid4(),
                mission_id=mission.id,
                step_number=step_data.step_number,
                title=step_data.title,
                description=step_data.description,
                platform=step_data.platform,
                action_type=step_data.action_type,
                action_params=step_data.action_params,
                requires_approval=step_data.requires_approval,
                status="pending",
            )
            self.db.add(step)

        await self.db.commit()
        await self.db.refresh(mission)
        return MissionRead.model_validate(mission)

    async def get(self, mission_id: uuid.UUID, user_id: uuid.UUID) -> Optional[MissionRead]:
        """Obtener una misión por ID (con verificación de ownership)."""
        result = await self.db.execute(
            select(Mission).where(Mission.id == mission_id, Mission.user_id == user_id)
        )
        mission = result.scalar_one_or_none()
        if mission:
            return MissionRead.model_validate(mission)
        return None

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[MissionRead]:
        """Listar misiones de un usuario."""
        query = select(Mission).where(Mission.user_id == user_id).order_by(desc(Mission.created_at))
        if status:
            query = query.where(Mission.status == status)
        if category:
            query = query.where(Mission.category == category)
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        missions = result.scalars().all()
        return [MissionRead.model_validate(m) for m in missions]

    async def update(self, mission_id: uuid.UUID, user_id: uuid.UUID, data: MissionUpdate) -> Optional[MissionRead]:
        """Actualizar una misión."""
        result = await self.db.execute(
            select(Mission).where(Mission.id == mission_id, Mission.user_id == user_id)
        )
        mission = result.scalar_one_or_none()
        if not mission:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mission, key, value)

        await self.db.commit()
        await self.db.refresh(mission)
        return MissionRead.model_validate(mission)

    async def approve(self, mission_id: uuid.UUID, user_id: uuid.UUID, approve_all_steps: bool = False) -> Optional[MissionRead]:
        """Aprobar una misión propuesta."""
        result = await self.db.execute(
            select(Mission).where(Mission.id == mission_id, Mission.user_id == user_id)
        )
        mission = result.scalar_one_or_none()
        if not mission:
            return None

        mission.status = "approved"
        mission.approved_at = datetime.utcnow()

        if approve_all_steps:
            for step in mission.steps:
                step.approved_by_user = True

        await self.db.commit()
        await self.db.refresh(mission)
        return MissionRead.model_validate(mission)

    async def start(self, mission_id: uuid.UUID, user_id: uuid.UUID) -> Optional[MissionRead]:
        """Iniciar una misión aprobada."""
        result = await self.db.execute(
            select(Mission).where(Mission.id == mission_id, Mission.user_id == user_id, Mission.status == "approved")
        )
        mission = result.scalar_one_or_none()
        if not mission:
            return None

        mission.status = "running"
        mission.started_at = datetime.utcnow()

        # Marcar primer paso ejecutable como running
        for step in mission.steps:
            if step.status == "pending" and (not step.requires_approval or step.approved_by_user):
                step.status = "running"
                step.started_at = datetime.utcnow()
                break

        await self.db.commit()
        await self.db.refresh(mission)
        return MissionRead.model_validate(mission)

    async def update_step(
        self,
        mission_id: uuid.UUID,
        step_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MissionStepUpdate,
    ) -> Optional[MissionRead]:
        """Actualizar el estado de un paso y avanzar al siguiente si corresponde."""
        result = await self.db.execute(
            select(MissionStep)
            .join(Mission)
            .where(MissionStep.id == step_id, Mission.id == mission_id, Mission.user_id == user_id)
        )
        step = result.scalar_one_or_none()
        if not step:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(step, key, value)

        # Si el paso se completó, avanzar al siguiente
        if data.status == "completed":
            step.completed_at = datetime.utcnow()
            await self._advance_to_next_step(step.mission)

        # Si el paso falló, marcar misión como failed
        if data.status == "failed":
            step.mission.status = "failed"

        await self.db.commit()
        await self.db.refresh(step.mission)
        return MissionRead.model_validate(step.mission)

    async def _advance_to_next_step(self, mission: Mission):
        """Avanzar a la siguiente acción de la misión."""
        # Verificar si todos los pasos están completos
        all_completed = all(s.status in ("completed", "skipped") for s in mission.steps)
        if all_completed:
            mission.status = "completed"
            mission.completed_at = datetime.utcnow()
            return

        # Buscar siguiente paso pendiente
        for step in mission.steps:
            if step.status == "pending":
                if step.requires_approval and not step.approved_by_user:
                    step.status = "waiting_approval"
                else:
                    step.status = "running"
                    step.started_at = datetime.utcnow()
                break

    # ─── Diagnósticos ──────────────────────────────────────────────────────────

    async def run_diagnostic(
        self,
        user_id: uuid.UUID,
        business_id: Optional[uuid.UUID],
        business_metrics: Dict[str, Any],
    ) -> List[BusinessDiagnosticRead]:
        """Ejecutar diagnóstico completo y guardar resultados."""
        # Load business context for context-aware diagnostics
        context = {}
        try:
            from app.domains.business_context.models import BusinessContext as BCModel
            result = await self.db.execute(
                select(BCModel).where(BCModel.user_id == user_id, BCModel.business_id == business_id)
            )
            bc = result.scalar_one_or_none()
            if bc:
                context = {
                    "business_type": bc.business_type.value if bc.business_type else None,
                    "geographic_reach": bc.geographic_reach.value if bc.geographic_reach else None,
                    "presence_type": bc.presence_type.value if bc.presence_type else None,
                    "channels_configured": bc.channels_configured or {},
                    "ads_configured": bc.ads_configured or {},
                    "shipping_configured": bc.shipping_configured or {},
                    "website_configured": bc.website_configured,
                    "seo_configured": bc.seo_configured,
                    "does_delivery": bc.does_delivery,
                    "has_physical_location": bc.has_physical_location,
                }
        except Exception:
            pass

        diagnostics_data = run_diagnostic(business_metrics, context)

        created = []
        for diag_data in diagnostics_data:
            diag = BusinessDiagnostic(
                id=uuid.uuid4(),
                user_id=user_id,
                business_id=business_id,
                diagnostic_date=datetime.utcnow(),
                category=diag_data.category,
                severity=diag_data.severity,
                finding=diag_data.finding,
                metric_value=diag_data.metric_value,
                benchmark_value=diag_data.benchmark_value,
                recommended_mission_slug=diag_data.recommended_mission_slug,
                context_data=diag_data.context_data,
            )
            self.db.add(diag)
            created.append(diag)

        await self.db.commit()
        return [BusinessDiagnosticRead.model_validate(d) for d in created]

    async def list_diagnostics(
        self,
        user_id: uuid.UUID,
        business_id: Optional[uuid.UUID] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[BusinessDiagnosticRead]:
        """Listar diagnósticos de un usuario/negocio."""
        query = select(BusinessDiagnostic).where(BusinessDiagnostic.user_id == user_id)
        if business_id:
            query = query.where(BusinessDiagnostic.business_id == business_id)
        if is_resolved is not None:
            query = query.where(BusinessDiagnostic.is_resolved == is_resolved)
        query = query.order_by(desc(BusinessDiagnostic.created_at)).limit(limit)

        result = await self.db.execute(query)
        diagnostics = result.scalars().all()
        return [BusinessDiagnosticRead.model_validate(d) for d in diagnostics]

    async def resolve_diagnostic(self, diagnostic_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Marcar un diagnóstico como resuelto."""
        result = await self.db.execute(
            select(BusinessDiagnostic).where(
                BusinessDiagnostic.id == diagnostic_id,
                BusinessDiagnostic.user_id == user_id,
            )
        )
        diag = result.scalar_one_or_none()
        if not diag:
            return False
        diag.is_resolved = True
        diag.resolved_at = datetime.utcnow()
        await self.db.commit()
        return True

    # ─── Playbooks ─────────────────────────────────────────────────────────────

    async def list_playbooks(self, category: Optional[str] = None) -> List[PlaybookRead]:
        """Listar playbooks disponibles."""
        return list_playbooks(category)

    async def get_playbook(self, slug: str) -> Optional[PlaybookRead]:
        """Obtener un playbook por slug."""
        return get_playbook(slug)
