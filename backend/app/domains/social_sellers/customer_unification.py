"""Customer Identity Unification — reconoce que María de IG es María de WA."""

import uuid
from datetime import datetime, timezone
from typing import Optional, Any, List, Dict
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.social_sellers.models import UnifiedCustomer
from app.core.logger import get_logger

logger = get_logger(__name__)


def _normalize_name(name: Optional[str]) -> str:
    if not name:
        return ''
    return name.strip().lower()


def _name_similarity(a: Optional[str], b: Optional[str]) -> float:
    na = _normalize_name(a)
    nb = _normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


class CustomerIdentityMatcher:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_or_create_unified_customer(
        self,
        business_id: uuid.UUID,
        platform: str,
        external_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> UnifiedCustomer:
        """Busca un cliente unificado por email, teléfono o nombre fuzzy.
        Si encuentra, agrega la plataforma al identity_map.
        Si no, crea uno nuevo.
        """
        platform = platform.lower()

        # 1. Match por email exacto
        if email:
            matched = await self.match_by_email(business_id, email)
            if matched:
                await self._add_platform(matched, platform, external_id, name, email, phone)
                return matched

        # 2. Match por teléfono exacto
        if phone:
            matched = await self.match_by_phone(business_id, phone)
            if matched:
                await self._add_platform(matched, platform, external_id, name, email, phone)
                return matched

        # 3. Match por nombre fuzzy contra clientes del mismo negocio
        if name:
            matched = await self._match_by_fuzzy_name(business_id, name)
            if matched:
                await self._add_platform(matched, platform, external_id, name, email, phone)
                return matched

        # 4. Crear nuevo UnifiedCustomer
        now = datetime.now(timezone.utc)
        identity_map = {platform: external_id}
        if email and platform != 'email':
            identity_map['email'] = email
        if phone and platform != 'phone':
            identity_map['phone'] = phone

        new_customer = UnifiedCustomer(
            business_id=business_id,
            display_name=name,
            master_email=email,
            master_phone=phone,
            identity_map=identity_map,
            first_seen_at=now,
            last_seen_at=now,
            total_lifetime_value=Decimal('0'),
            preferred_platforms=[platform],
            total_purchases=0,
        )
        self.db.add(new_customer)
        await self.db.commit()
        await self.db.refresh(new_customer)
        logger.info(f'Nuevo unified customer creado: {new_customer.id} ({name})')
        return new_customer

    async def _add_platform(
        self,
        customer: UnifiedCustomer,
        platform: str,
        external_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> None:
        """Agrega una plataforma al identity_map y actualiza campos derivados."""
        identity_map = dict(customer.identity_map or {})
        identity_map[platform] = external_id
        customer.identity_map = identity_map

        if name and not customer.display_name:
            customer.display_name = name
        if email and not customer.master_email:
            customer.master_email = email
        if phone and not customer.master_phone:
            customer.master_phone = phone

        preferred = list(customer.preferred_platforms or [])
        if platform not in preferred:
            preferred.append(platform)
            customer.preferred_platforms = preferred

        customer.last_seen_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(customer)
        logger.info(f'Plataforma {platform} agregada a unified customer {customer.id}')

    async def match_by_email(
        self,
        business_id: uuid.UUID,
        email: str,
    ) -> Optional[UnifiedCustomer]:
        """Encuentra un cliente unificado por email exacto."""
        result = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.business_id == business_id,
                    func.lower(UnifiedCustomer.master_email) == email.lower(),
                )
            )
        )
        return result.scalar_one_or_none()

    async def match_by_phone(
        self,
        business_id: uuid.UUID,
        phone: str,
    ) -> Optional[UnifiedCustomer]:
        """Encuentra un cliente unificado por teléfono exacto."""
        normalized = phone.strip().replace(' ', '').replace('-', '')
        result = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.business_id == business_id,
                    func.replace(
                        func.replace(UnifiedCustomer.master_phone, ' ', ''), '-', ''
                    ) == normalized,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _match_by_fuzzy_name(
        self,
        business_id: uuid.UUID,
        name: str,
        threshold: float = 0.85,
    ) -> Optional[UnifiedCustomer]:
        """Busca clientes del mismo negocio con nombre similar."""
        result = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.business_id == business_id,
                    UnifiedCustomer.display_name.isnot(None),
                )
            )
        )
        candidates = result.scalars().all()
        best_match = None
        best_score = 0.0
        for candidate in candidates:
            score = _name_similarity(name, candidate.display_name)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        return best_match

    async def suggest_merge(
        self,
        business_id: uuid.UUID,
        customer_a_id: uuid.UUID,
        customer_b_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Calcula un puntaje de confianza (0-100) para fusionar dos clientes."""
        if customer_a_id == customer_b_id:
            return {"score": 0, "reasons": ['Los IDs son idénticos']}

        result_a = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.id == customer_a_id,
                    UnifiedCustomer.business_id == business_id,
                )
            )
        )
        a = result_a.scalar_one_or_none()
        result_b = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.id == customer_b_id,
                    UnifiedCustomer.business_id == business_id,
                )
            )
        )
        b = result_b.scalar_one_or_none()

        if not a or not b:
            return {"score": 0, "reasons": ['Uno o ambos clientes no existen']}

        score = 0
        reasons = []

        # Email exacto
        if a.master_email and b.master_email and a.master_email.lower() == b.master_email.lower():
            score += 50
            reasons.append('Email idéntico')

        # Teléfono exacto
        if a.master_phone and b.master_phone:
            na = a.master_phone.strip().replace(' ', '').replace('-', '')
            nb = b.master_phone.strip().replace(' ', '').replace('-', '')
            if na == nb:
                score += 50
                reasons.append('Teléfono idéntico')

        # Nombre similar
        name_score = _name_similarity(a.display_name, b.display_name)
        if name_score >= 0.85:
            score += int(name_score * 30)
            reasons.append(f'Nombre muy similar ({int(name_score * 100)}%)')
        elif name_score >= 0.6:
            score += int(name_score * 15)
            reasons.append(f'Nombre parecido ({int(name_score * 100)}%)')

        # Plataformas complementarias (misma persona en distintas plataformas)
        platforms_a = set(a.identity_map.keys()) if a.identity_map else set()
        platforms_b = set(b.identity_map.keys()) if b.identity_map else set()
        if platforms_a and platforms_b and not platforms_a.intersection(platforms_b):
            score += 10
            reasons.append('Plataformas complementarias')

        score = min(100, score)
        return {"score": score, "reasons": reasons}

    async def merge_customers(
        self,
        business_id: uuid.UUID,
        target_id: uuid.UUID,
        source_id: uuid.UUID,
    ) -> Optional[UnifiedCustomer]:
        """Fusiona source en target: combina identity_maps, suma LTV, mantiene first_seen más antiguo."""
        if target_id == source_id:
            return None

        result_t = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.id == target_id,
                    UnifiedCustomer.business_id == business_id,
                )
            )
        )
        target = result_t.scalar_one_or_none()

        result_s = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.id == source_id,
                    UnifiedCustomer.business_id == business_id,
                )
            )
        )
        source = result_s.scalar_one_or_none()

        if not target or not source:
            return None

        # Combinar identity_map
        target_map = dict(target.identity_map or {})
        source_map = dict(source.identity_map or {})
        target_map.update(source_map)
        target.identity_map = target_map

        # Combinar preferred_platforms
        target_platforms = list(target.preferred_platforms or [])
        for p in (source.preferred_platforms or []):
            if p not in target_platforms:
                target_platforms.append(p)
        target.preferred_platforms = target_platforms

        # Sumar LTV y compras
        target.total_lifetime_value = Decimal(target.total_lifetime_value or 0) + Decimal(source.total_lifetime_value or 0)
        target.total_purchases = (target.total_purchases or 0) + (source.total_purchases or 0)

        # Mantener first_seen más antiguo
        if source.first_seen_at and target.first_seen_at:
            if source.first_seen_at < target.first_seen_at:
                target.first_seen_at = source.first_seen_at
        elif source.first_seen_at and not target.first_seen_at:
            target.first_seen_at = source.first_seen_at

        # Mantener display_name si target no tiene
        if not target.display_name and source.display_name:
            target.display_name = source.display_name
        if not target.master_email and source.master_email:
            target.master_email = source.master_email
        if not target.master_phone and source.master_phone:
            target.master_phone = source.master_phone

        # last_purchase_at más reciente
        if source.last_purchase_at and target.last_purchase_at:
            if source.last_purchase_at > target.last_purchase_at:
                target.last_purchase_at = source.last_purchase_at
        elif source.last_purchase_at and not target.last_purchase_at:
            target.last_purchase_at = source.last_purchase_at

        target.updated_at = datetime.now(timezone.utc)

        # Eliminar source
        await self.db.delete(source)
        await self.db.commit()
        await self.db.refresh(target)

        logger.info(f'Clientes fusionados: {source_id} -> {target_id}')
        return target

    async def get_unified_profile(
        self,
        unified_customer_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """Devuelve el perfil completo con todas las plataformas, LTV total, plataforma preferida, etc."""
        result = await self.db.execute(
            select(UnifiedCustomer).where(UnifiedCustomer.id == unified_customer_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            return None

        preferred = list(customer.preferred_platforms or [])
        identity_map = dict(customer.identity_map or {})

        return {
            "id": str(customer.id),
            "business_id": str(customer.business_id),
            "display_name": customer.display_name,
            "master_email": customer.master_email,
            "master_phone": customer.master_phone,
            "identity_map": identity_map,
            "platforms": list(identity_map.keys()),
            "first_seen_at": customer.first_seen_at.isoformat() if customer.first_seen_at else None,
            "last_seen_at": customer.last_seen_at.isoformat() if customer.last_seen_at else None,
            "total_lifetime_value": float(customer.total_lifetime_value or 0),
            "buying_frequency_days": customer.buying_frequency_days,
            "preferred_platforms": preferred,
            "preferred_platform": preferred[0] if preferred else None,
            "rfm_segment": customer.rfm_segment,
            "last_purchase_at": customer.last_purchase_at.isoformat() if customer.last_purchase_at else None,
            "total_purchases": customer.total_purchases or 0,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
        }

    async def list_unified_customers(
        self,
        business_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[UnifiedCustomer]:
        """Lista todos los clientes unificados de un negocio."""
        result = await self.db.execute(
            select(UnifiedCustomer)
            .where(UnifiedCustomer.business_id == business_id)
            .order_by(UnifiedCustomer.last_seen_at.desc().nullslast())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_unified_customer_by_id(
        self,
        business_id: uuid.UUID,
        unified_customer_id: uuid.UUID,
    ) -> Optional[UnifiedCustomer]:
        """Obtiene un cliente unificado por ID y negocio."""
        result = await self.db.execute(
            select(UnifiedCustomer).where(
                and_(
                    UnifiedCustomer.id == unified_customer_id,
                    UnifiedCustomer.business_id == business_id,
                )
            )
        )
        return result.scalar_one_or_none()
