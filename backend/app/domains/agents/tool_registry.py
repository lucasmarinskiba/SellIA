"""Tool Registry for ReAct Orchestrator.

Defines all available tools as Pydantic-schema + async execute classes,
plus a central ToolRegistry for lookup and execution.
"""

import inspect
import uuid
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_

from app.core.logger import get_logger
from app.domains.catalogs.models import CatalogItem
from app.domains.crm.models import Deal, LeadActivity
from app.domains.channels.models import Conversation, Message
from app.core.knowledge.knowledge_engine import get_knowledge_engine
from app.domains.documents.processor import document_processor
from app.domains.memory.service import MemoryEngine

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------

class SearchProductsToolInput(BaseModel):
    query: str
    category: Optional[str] = None
    max_price: Optional[float] = None


class GetCustomerHistoryToolInput(BaseModel):
    customer_id: str


class CheckInventoryToolInput(BaseModel):
    product_id: str


class RetrieveKnowledgeToolInput(BaseModel):
    topic: str
    k: int = Field(default=3, ge=1, le=10)


class RetrieveDocumentsToolInput(BaseModel):
    query: str
    business_id: str
    k: int = Field(default=3, ge=1, le=10)


class SearchMemoryToolInput(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None
    k: int = Field(default=5, ge=1, le=20)


class ScheduleMeetingToolInput(BaseModel):
    customer_id: str
    proposed_time: str
    duration_minutes: int = Field(default=30, ge=15, le=240)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

class SearchProductsTool:
    name = "search_products"
    description = (
        "Search the business product catalog by name, description, or tags. "
        "Use this when the user asks about products, prices, or availability. "
        "Input: query (str), category (optional str), max_price (optional float)."
    )
    input_schema = SearchProductsToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: uuid.UUID,
        query: str,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        stmt = select(CatalogItem).where(
            CatalogItem.business_id == business_id,
            CatalogItem.is_active == True,
        )
        if category:
            cat_lower = category.lower()
            stmt = stmt.where(
                or_(
                    CatalogItem.type == cat_lower,
                    CatalogItem.tags.contains([cat_lower]),
                )
            )
        if max_price is not None:
            stmt = stmt.where(CatalogItem.price <= max_price)

        result = await db.execute(stmt)
        items = result.scalars().all()

        query_lower = query.lower()
        filtered = []
        for item in items:
            text = f"{item.name} {item.description or ''} {' '.join(item.tags or [])}"
            if query_lower in text.lower():
                filtered.append(item)

        filtered = filtered[:10]

        return {
            "count": len(filtered),
            "products": [
                {
                    "id": str(item.id),
                    "name": item.name,
                    "price": float(item.price) if item.price is not None else None,
                    "currency": item.currency,
                    "stock": item.stock,
                    "category": str(item.type) if item.type else None,
                    "description": item.description,
                }
                for item in filtered
            ],
        }


class GetCustomerHistoryTool:
    name = "get_customer_history"
    description = (
        "Get CRM history for a customer including deals, lead activities, and recent conversations. "
        "Use this when the user asks about a specific customer, lead, or prospect. "
        "Input: customer_id (str) — can be a conversation UUID, email, phone, or external identifier."
    )
    input_schema = GetCustomerHistoryToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: uuid.UUID,
        customer_id: str,
    ) -> Dict[str, Any]:
        conversation_uuid = None
        try:
            conversation_uuid = uuid.UUID(customer_id)
        except ValueError:
            pass

        deals = []
        activities = []
        messages = []
        conversation_info = None

        if conversation_uuid:
            result = await db.execute(
                select(Deal).where(
                    Deal.business_id == business_id,
                    Deal.conversation_id == conversation_uuid,
                )
            )
            deals = result.scalars().all()

            result = await db.execute(
                select(LeadActivity)
                .where(
                    LeadActivity.business_id == business_id,
                    LeadActivity.conversation_id == conversation_uuid,
                )
                .order_by(desc(LeadActivity.created_at))
                .limit(20)
            )
            activities = result.scalars().all()

            result = await db.execute(
                select(Conversation).where(
                    Conversation.business_id == business_id,
                    Conversation.id == conversation_uuid,
                )
            )
            conv = result.scalar_one_or_none()
            if conv:
                conversation_info = {
                    "id": str(conv.id),
                    "lead_name": conv.lead_name,
                    "lead_email": conv.lead_email,
                    "lead_phone": conv.lead_phone,
                    "lead_source": conv.lead_source,
                    "status": conv.status.value if conv.status else None,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                }
                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conv.id)
                    .order_by(desc(Message.created_at))
                    .limit(10)
                )
                messages = result.scalars().all()
        else:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.business_id == business_id,
                    or_(
                        Conversation.external_id == customer_id,
                        Conversation.lead_email.ilike(f"%{customer_id}%"),
                        Conversation.lead_phone.ilike(f"%{customer_id}%"),
                    ),
                )
            )
            conv = result.scalar_one_or_none()
            if conv:
                conversation_uuid = conv.id
                conversation_info = {
                    "id": str(conv.id),
                    "lead_name": conv.lead_name,
                    "lead_email": conv.lead_email,
                    "lead_phone": conv.lead_phone,
                    "lead_source": conv.lead_source,
                    "status": conv.status.value if conv.status else None,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                }
                result = await db.execute(
                    select(Deal).where(
                        Deal.business_id == business_id,
                        Deal.conversation_id == conv.id,
                    )
                )
                deals = result.scalars().all()

                result = await db.execute(
                    select(LeadActivity)
                    .where(
                        LeadActivity.business_id == business_id,
                        LeadActivity.conversation_id == conv.id,
                    )
                    .order_by(desc(LeadActivity.created_at))
                    .limit(20)
                )
                activities = result.scalars().all()

                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conv.id)
                    .order_by(desc(Message.created_at))
                    .limit(10)
                )
                messages = result.scalars().all()

        return {
            "customer_id": customer_id,
            "conversation": conversation_info,
            "deals": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "stage": d.stage.value if d.stage else None,
                    "value": float(d.value) if d.value else None,
                    "probability": d.probability,
                    "contact_name": d.contact_name,
                    "contact_email": d.contact_email,
                }
                for d in deals
            ],
            "activities": [
                {
                    "type": a.activity_type,
                    "points": a.points,
                    "description": a.description,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in activities
            ],
            "recent_messages": [
                {
                    "direction": m.direction.value if m.direction else None,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        }


class CheckInventoryTool:
    name = "check_inventory"
    description = (
        "Check the stock/inventory level for a specific product. "
        "Use this when the user asks if a product is available or how many units are in stock. "
        "Input: product_id (str) — the UUID of the product."
    )
    input_schema = CheckInventoryToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: uuid.UUID,
        product_id: str,
    ) -> Dict[str, Any]:
        try:
            pid = uuid.UUID(product_id)
        except ValueError:
            return {"error": "Invalid product_id format"}

        result = await db.execute(
            select(CatalogItem).where(
                CatalogItem.id == pid,
                CatalogItem.business_id == business_id,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return {"error": "Product not found", "product_id": product_id}

        return {
            "product_id": str(item.id),
            "name": item.name,
            "stock": item.stock,
            "is_available": item.is_available,
            "price": float(item.price) if item.price is not None else None,
            "currency": item.currency,
        }


class RetrieveKnowledgeTool:
    name = "retrieve_knowledge"
    description = (
        "Search the internal knowledge library for sales tactics, frameworks, and principles, "
        "plus business models, crypto, stock-market investing, financial-market analysis and "
        "real-estate valuation. Use this when the user asks for sales advice, negotiation tactics, "
        "business strategy, or guidance on investing, crypto, trading analysis or real estate. "
        "Input: topic (str), k (int, default 3) — number of results."
    )
    input_schema = RetrieveKnowledgeToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: Optional[uuid.UUID],
        topic: str,
        k: int = 3,
    ) -> Dict[str, Any]:
        engine = get_knowledge_engine()
        items = await engine.semantic_query(context=topic, top_k=k)
        return {
            "topic": topic,
            "results": [
                {
                    "id": item.id,
                    "category": item.category,
                    "principle": item.principle,
                    "tactic": item.tactic,
                    "framework": item.framework,
                    "script_template": item.script_template,
                }
                for item in items
            ],
        }


class RetrieveDocumentsTool:
    name = "retrieve_documents"
    description = (
        "RAG search over uploaded business documents (PDFs, manuals, SOPs, etc.). "
        "Use this when the user asks about company policies, procedures, or document content. "
        "Input: query (str), business_id (str), k (int, default 3)."
    )
    input_schema = RetrieveDocumentsToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: uuid.UUID,
        query: str,
        k: int = 3,
    ) -> Dict[str, Any]:
        try:
            results = await document_processor.search_documents(db, business_id, query, k)
        except Exception as exc:
            logger.warning(f"Document search failed: {exc}")
            return {"error": "Document search failed", "details": str(exc)}

        return {
            "query": query,
            "results": results,
        }


class SearchMemoryTool:
    name = "search_memory"
    description = (
        "Semantic search over conversation memory and customer facts. "
        "Use this when the user asks about past conversations, customer preferences, or remembered facts. "
        "Input: query (str), conversation_id (optional str), customer_id (optional str), k (int, default 5)."
    )
    input_schema = SearchMemoryToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: Optional[uuid.UUID],
        query: str,
        conversation_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        k: int = 5,
    ) -> Dict[str, Any]:
        conv_uuid = None
        cust_uuid = None
        try:
            if conversation_id:
                conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            pass
        try:
            if customer_id:
                cust_uuid = uuid.UUID(customer_id)
        except ValueError:
            pass

        engine = MemoryEngine(db)
        try:
            chunks = await engine.retrieve_relevant(
                query=query,
                conversation_id=conv_uuid,
                customer_id=cust_uuid,
                k=k,
            )
        except Exception as exc:
            logger.warning(f"Memory search failed: {exc}")
            return {"error": "Memory search failed", "details": str(exc)}

        return {
            "query": query,
            "results": [
                {
                    "id": str(c.id),
                    "role": c.role,
                    "content": c.content,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in chunks
            ],
        }


class ScheduleMeetingTool:
    name = "schedule_meeting"
    description = (
        "Schedule a meeting with a customer. "
        "Use this when the user wants to book an appointment, demo, or call. "
        "Input: customer_id (str), proposed_time (str, ISO format or natural language), duration_minutes (int, default 30)."
    )
    input_schema = ScheduleMeetingToolInput

    async def execute(
        self,
        db: AsyncSession,
        business_id: Optional[uuid.UUID],
        customer_id: str,
        proposed_time: str,
        duration_minutes: int = 30,
    ) -> Dict[str, Any]:
        return {
            "status": "not_implemented",
            "message": "Meeting scheduling is not implemented yet.",
            "customer_id": customer_id,
            "proposed_time": proposed_time,
            "duration_minutes": duration_minutes,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """Registry of all available tools for the ReAct agent."""

    def __init__(self):
        self._tools: Dict[str, Any] = {
            SearchProductsTool.name: SearchProductsTool(),
            GetCustomerHistoryTool.name: GetCustomerHistoryTool(),
            CheckInventoryTool.name: CheckInventoryTool(),
            RetrieveKnowledgeTool.name: RetrieveKnowledgeTool(),
            RetrieveDocumentsTool.name: RetrieveDocumentsTool(),
            SearchMemoryTool.name: SearchMemoryTool(),
            ScheduleMeetingTool.name: ScheduleMeetingTool(),
        }

    def get_tool(self, name: str) -> Optional[Any]:
        return self._tools.get(name)

    def list_tools(self) -> list:
        return list(self._tools.values())

    def get_tool_descriptions(self, allowed_names: Optional[list] = None) -> str:
        lines = []
        for tool in self._tools.values():
            if allowed_names is not None and tool.name not in allowed_names:
                continue
            lines.append(f"- {tool.name}: {tool.description}")
            schema = tool.input_schema.model_json_schema()
            props = schema.get("properties", {})
            if props:
                lines.append("  Parameters:")
                for prop_name, prop_info in props.items():
                    prop_type = prop_info.get("type", "any")
                    prop_desc = prop_info.get("description", "")
                    lines.append(f"    - {prop_name} ({prop_type}): {prop_desc}")
        return "\n".join(lines)

    def get_filtered_registry(self, allowed_names: list) -> "ToolRegistry":
        """Return a new registry containing only the allowed tools."""
        new_reg = ToolRegistry.__new__(ToolRegistry)
        new_reg._tools = {k: v for k, v in self._tools.items() if k in allowed_names}
        new_reg._total_tokens = 0
        new_reg._tool_calls = []
        return new_reg

    async def execute_tool(
        self,
        name: str,
        db: AsyncSession,
        business_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found"}

        sig = inspect.signature(tool.execute)
        call_kwargs: Dict[str, Any] = {}

        if "db" in sig.parameters:
            call_kwargs["db"] = db
        if "business_id" in sig.parameters:
            call_kwargs["business_id"] = business_id
        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v

        try:
            return await tool.execute(**call_kwargs)
        except Exception as exc:
            logger.exception(f"Tool {name} execution failed: {exc}")
            return {"error": f"Tool execution failed: {str(exc)}"}
