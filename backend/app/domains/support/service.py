"""Support system service layer."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc

from app.domains.support.models import (
    SupportTicket, TicketMessage, FAQ, KnowledgeBaseArticle,
    TicketStatus, TicketPriority, TicketCategory, MessageSenderType
)
from app.domains.support.schemas import (
    SupportTicketCreate, SupportTicketUpdate, TicketMessageCreate,
    FAQCreate, FAQUpdate, KnowledgeBaseArticleCreate, KnowledgeBaseArticleUpdate,
    CSATSubmit
)


class SupportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ===== Tickets =====

    async def create_ticket(self, user_id: uuid.UUID, data: SupportTicketCreate) -> SupportTicket:
        ticket = SupportTicket(
            user_id=user_id,
            business_id=data.business_id,
            category=data.category,
            title=data.title,
            description=data.description,
        )
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def get_ticket(self, ticket_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if ticket and user_id and ticket.user_id != user_id:
            return None
        return ticket

    async def list_tickets(
        self,
        user_id: Optional[uuid.UUID] = None,
        business_id: Optional[uuid.UUID] = None,
        status: Optional[TicketStatus] = None,
        priority: Optional[TicketPriority] = None,
        assigned_to: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[SupportTicket], int]:
        query = select(SupportTicket)
        count_query = select(func.count()).select_from(SupportTicket)

        if user_id:
            query = query.where(SupportTicket.user_id == user_id)
            count_query = count_query.where(SupportTicket.user_id == user_id)
        if business_id:
            query = query.where(SupportTicket.business_id == business_id)
            count_query = count_query.where(SupportTicket.business_id == business_id)
        if status:
            query = query.where(SupportTicket.status == status)
            count_query = count_query.where(SupportTicket.status == status)
        if priority:
            query = query.where(SupportTicket.priority == priority)
            count_query = count_query.where(SupportTicket.priority == priority)
        if assigned_to:
            query = query.where(SupportTicket.assigned_to == assigned_to)
            count_query = count_query.where(SupportTicket.assigned_to == assigned_to)

        query = query.order_by(desc(SupportTicket.created_at)).offset(offset).limit(limit)

        result = await self.db.execute(query)
        total_result = await self.db.execute(count_query)
        return list(result.scalars().all()), total_result.scalar() or 0

    async def update_ticket(self, ticket_id: uuid.UUID, data: SupportTicketUpdate) -> Optional[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ticket, field, value)

        if data.status == TicketStatus.RESOLVED and not ticket.resolved_at:
            ticket.resolved_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def escalate_ticket(self, ticket_id: uuid.UUID) -> Optional[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            return None

        ticket.status = TicketStatus.ESCALATED
        ticket.priority = TicketPriority.HIGH
        ticket.escalated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def submit_csat(self, ticket_id: uuid.UUID, data: CSATSubmit) -> Optional[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            return None

        ticket.csat_rating = data.rating
        ticket.csat_comment = data.comment
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    # ===== Messages =====

    async def add_message(
        self,
        ticket_id: uuid.UUID,
        content: str,
        sender_type: MessageSenderType = MessageSenderType.USER,
        sender_id: Optional[uuid.UUID] = None,
        is_internal: bool = False,
    ) -> TicketMessage:
        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            is_internal=is_internal,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)

        # Update ticket updated_at
        result = await self.db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

        return msg

    async def list_messages(self, ticket_id: uuid.UUID, include_internal: bool = False) -> List[TicketMessage]:
        query = select(TicketMessage).where(TicketMessage.ticket_id == ticket_id)
        if not include_internal:
            query = query.where(TicketMessage.is_internal == False)
        query = query.order_by(asc(TicketMessage.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ===== FAQ =====

    async def create_faq(self, data: FAQCreate, business_id: Optional[uuid.UUID] = None) -> FAQ:
        faq = FAQ(
            business_id=business_id,
            question=data.question,
            answer=data.answer,
            tags=data.tags,
        )
        self.db.add(faq)
        await self.db.commit()
        await self.db.refresh(faq)
        return faq

    async def list_faqs(self, business_id: Optional[uuid.UUID] = None, search: Optional[str] = None) -> List[FAQ]:
        query = select(FAQ).where(FAQ.is_active == True)
        if business_id:
            query = query.where(FAQ.business_id == business_id)
        if search:
            query = query.where(
                FAQ.question.ilike(f"%{search}%") | FAQ.answer.ilike(f"%{search}%")
            )
        query = query.order_by(desc(FAQ.usage_count))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_faq(self, faq_id: uuid.UUID) -> Optional[FAQ]:
        result = await self.db.execute(select(FAQ).where(FAQ.id == faq_id))
        return result.scalar_one_or_none()

    async def update_faq(self, faq_id: uuid.UUID, data: FAQUpdate) -> Optional[FAQ]:
        faq = await self.get_faq(faq_id)
        if not faq:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(faq, field, value)
        await self.db.commit()
        await self.db.refresh(faq)
        return faq

    async def delete_faq(self, faq_id: uuid.UUID) -> bool:
        faq = await self.get_faq(faq_id)
        if not faq:
            return False
        await self.db.delete(faq)
        await self.db.commit()
        return True

    async def increment_faq_usage(self, faq_id: uuid.UUID) -> None:
        faq = await self.get_faq(faq_id)
        if faq:
            faq.usage_count += 1
            await self.db.commit()

    # ===== Knowledge Base =====

    async def create_kb_article(self, data: KnowledgeBaseArticleCreate, business_id: Optional[uuid.UUID] = None) -> KnowledgeBaseArticle:
        article = KnowledgeBaseArticle(
            business_id=business_id,
            title=data.title,
            content=data.content,
            category=data.category,
            tags=data.tags,
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def list_kb_articles(self, business_id: Optional[uuid.UUID] = None, search: Optional[str] = None) -> List[KnowledgeBaseArticle]:
        query = select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.is_active == True)
        if business_id:
            query = query.where(KnowledgeBaseArticle.business_id == business_id)
        if search:
            query = query.where(
                KnowledgeBaseArticle.title.ilike(f"%{search}%") |
                KnowledgeBaseArticle.content.ilike(f"%{search}%")
            )
        query = query.order_by(KnowledgeBaseArticle.title)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_kb_article(self, article_id: uuid.UUID) -> Optional[KnowledgeBaseArticle]:
        result = await self.db.execute(select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.id == article_id))
        return result.scalar_one_or_none()

    async def update_kb_article(self, article_id: uuid.UUID, data: KnowledgeBaseArticleUpdate) -> Optional[KnowledgeBaseArticle]:
        article = await self.get_kb_article(article_id)
        if not article:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(article, field, value)
        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def delete_kb_article(self, article_id: uuid.UUID) -> bool:
        article = await self.get_kb_article(article_id)
        if not article:
            return False
        await self.db.delete(article)
        await self.db.commit()
        return True

    # ===== Stats =====

    async def get_stats(self, business_id: Optional[uuid.UUID] = None) -> dict:
        query = select(func.count()).select_from(SupportTicket)
        open_query = select(func.count()).select_from(SupportTicket).where(SupportTicket.status == TicketStatus.OPEN)
        in_progress_query = select(func.count()).select_from(SupportTicket).where(SupportTicket.status == TicketStatus.IN_PROGRESS)
        resolved_today_query = select(func.count()).select_from(SupportTicket).where(
            SupportTicket.status == TicketStatus.RESOLVED,
            SupportTicket.resolved_at >= datetime.now(timezone.utc) - timedelta(days=1)
        )
        csat_query = select(func.avg(SupportTicket.csat_rating)).select_from(SupportTicket).where(
            SupportTicket.csat_rating.isnot(None)
        )

        if business_id:
            query = query.where(SupportTicket.business_id == business_id)
            open_query = open_query.where(SupportTicket.business_id == business_id)
            in_progress_query = in_progress_query.where(SupportTicket.business_id == business_id)
            resolved_today_query = resolved_today_query.where(SupportTicket.business_id == business_id)
            csat_query = csat_query.where(SupportTicket.business_id == business_id)

        total = (await self.db.execute(query)).scalar() or 0
        open_count = (await self.db.execute(open_query)).scalar() or 0
        in_progress = (await self.db.execute(in_progress_query)).scalar() or 0
        resolved_today = (await self.db.execute(resolved_today_query)).scalar() or 0
        csat_avg = (await self.db.execute(csat_query)).scalar()

        return {
            "total_tickets": total,
            "open_tickets": open_count,
            "in_progress_tickets": in_progress,
            "resolved_today": resolved_today,
            "avg_resolution_hours": None,  # TODO: calcular
            "ai_resolution_rate": None,    # TODO: calcular
            "csat_avg": round(csat_avg, 2) if csat_avg else None,
        }
