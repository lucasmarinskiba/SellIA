"""Negotiation Engine

Handles price negotiation with customers using a structured concession strategy.
"""

import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.agents.models_negotiation import NegotiationState
from app.domains.agents.schemas_intelligence import NegotiationResponse

logger = get_logger(__name__)


class NegotiationEngine:
    """Handles price negotiation with customers.

    Adapts negotiation strategy based on business type:
    - Products: percentage discounts, bundles, free shipping
    - Services: value-added services, packages, payment terms
    - Software: annual discounts, upgrades, extended trials
    - Food: combos, free delivery, loyalty rewards
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_business_type(self, business_id: Optional[uuid.UUID]) -> Optional[str]:
        """Load specific business type from BusinessContext."""
        if not business_id:
            return None
        try:
            from sqlalchemy import select
            from app.domains.business_context.models import BusinessContext
            result = await self.db.execute(
                select(BusinessContext.business_type).where(
                    BusinessContext.business_id == business_id,
                    BusinessContext.is_active == True,
                )
            )
            btype = result.scalar_one_or_none()
            return btype.value if btype else None
        except Exception as exc:
            logger.debug(f"Could not load business_type for negotiation: {exc}")
            return None

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    async def detect_negotiation_intent(
        self,
        message: str,
        business_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Detect if the customer is trying to negotiate.
        Uses keyword matching first, then LLM for ambiguous cases.
        """
        text = message.lower()
        keywords = [
            "descuento",
            "más barato",
            "oferta",
            "negociar",
            "precio",
            "caro",
            "presupuesto",
            "rebaja",
            "promo",
            "cuesta mucho",
            "me lo dejas",
            "mejor precio",
            "cuánto sale",
            "barato",
            "económico",
            "barat",
            "rebajar",
            "ajustar",
        ]
        keyword_match = any(kw in text for kw in keywords)

        # If strong keyword match, short-circuit
        if keyword_match:
            # Check if it's obviously not a negotiation
            negation_phrases = [
                "está bien",
                "me parece bien",
                "ok con el precio",
                "perfecto",
                "precio justo",
            ]
            if any(p in text for p in negation_phrases):
                return False
            return True

        # Ambiguous case: use quick LLM check if we have business context
        if business_id and self.db:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                from app.domains.agents.llm_provider import generate_with_fallback

                prompt = (
                    "¿Este mensaje expresa intención de negociar el precio "
                    "o pedir descuento? Responde solo 'SI' o 'NO'.\n\n"
                    f"Mensaje: {message}"
                )
                response = await generate_with_fallback(
                    db=self.db,
                    business_id=business_id,
                    messages=[
                        SystemMessage(
                            content="Eres un clasificador de intenciones de venta."
                        ),
                        HumanMessage(content=prompt),
                    ],
                    model="gpt-4o-mini",
                    temperature=0.1,
                    max_tokens=10,
                )
                if response and "si" in response.content.lower():
                    return True
            except Exception as e:
                logger.warning(f"LLM negotiation intent check failed: {e}")

        return False

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    async def create_negotiation_state(
        self,
        conversation_id: uuid.UUID,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        product_id: Optional[uuid.UUID],
        original_price: float,
        max_discount_percent: Optional[float] = None,
    ) -> NegotiationState:
        """Initialize a new negotiation session with business rules."""
        # Resolve max_discount from business config if not provided
        if max_discount_percent is None:
            from app.domains.businesses.models import Business

            result = await self.db.execute(
                select(Business).where(Business.id == business_id)
            )
            business = result.scalar_one_or_none()
            if business and business.config:
                max_discount_percent = float(
                    business.config.get("max_discount_percent", 15.0)
                )
            else:
                max_discount_percent = 15.0

        min_acceptable = original_price * (1 - max_discount_percent / 100)

        state = NegotiationState(
            conversation_id=conversation_id,
            business_id=business_id,
            customer_id=customer_id,
            product_id=product_id,
            original_price=original_price,
            current_offer=original_price,
            minimum_acceptable=min_acceptable,
            max_discount_percent=max_discount_percent,
            round=0,
            concessions_made=[],
            status="active",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self.db.add(state)
        await self.db.commit()
        await self.db.refresh(state)
        return state

    async def get_active_state(
        self,
        conversation_id: uuid.UUID,
    ) -> Optional[NegotiationState]:
        """Get the active negotiation state for a conversation."""
        result = await self.db.execute(
            select(NegotiationState)
            .where(
                NegotiationState.conversation_id == conversation_id,
                NegotiationState.status == "active",
            )
            .order_by(desc(NegotiationState.created_at))
        )
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Strategy
    # ------------------------------------------------------------------

    def should_accept(
        self,
        customer_offer: float,
        state: NegotiationState,
    ) -> bool:
        """Determine if the customer's offer should be accepted."""
        if customer_offer >= float(state.minimum_acceptable):
            return True
        if state.round >= 4 and customer_offer >= float(state.minimum_acceptable) * 0.95:
            return True
        return False

    async def process_offer(
        self,
        conversation_id: uuid.UUID,
        customer_offer: float,
    ) -> NegotiationResponse:
        """
        Process a customer offer and return the next negotiation move.
        """
        state = await self.get_active_state(conversation_id)
        if not state:
            return NegotiationResponse(
                accepted=False,
                counter_offer=None,
                discount_percent=0.0,
                round=0,
                status="not_found",
                message=(
                    "No hay una negociación activa. "
                    "¿Te gustaría que revisemos opciones de precio?"
                ),
            )

        # Check expiration
        if state.expires_at and state.expires_at < datetime.now(timezone.utc):
            state.status = "expired"
            await self.db.commit()
            return NegotiationResponse(
                accepted=False,
                counter_offer=None,
                discount_percent=0.0,
                round=state.round,
                status="expired",
                message="La negociación ha expirado. ¿Te gustaría iniciar una nueva?",
            )

        # Update round
        state.round += 1
        current_round = state.round

        # Check acceptance
        if self.should_accept(customer_offer, state):
            state.status = "accepted"
            state.current_offer = customer_offer
            concessions = list(state.concessions_made or [])
            concessions.append(
                {
                    "round": current_round,
                    "type": "acceptance",
                    "customer_offer": customer_offer,
                }
            )
            state.concessions_made = concessions
            await self.db.commit()
            return NegotiationResponse(
                accepted=True,
                counter_offer=customer_offer,
                discount_percent=self._calc_discount(state),
                round=current_round,
                status="accepted",
                message="¡Oferta aceptada! Preparo los detalles de tu compra.",
                urgency=False,
            )

        # Load business type for adaptive strategy
        business_type = await self._get_business_type(state.business_id)

        # Rejection / counter-offer strategy
        counter, discount, urgency, concession_type = self._calculate_counter(
            state, customer_offer, business_type
        )

        # Persist concession
        concessions = list(state.concessions_made or [])
        concessions.append(
            {
                "round": current_round,
                "type": concession_type,
                "customer_offer": customer_offer,
                "counter_offer": counter,
                "discount_percent": discount,
            }
        )
        state.concessions_made = concessions
        state.current_offer = counter
        await self.db.commit()

        return NegotiationResponse(
            accepted=False,
            counter_offer=counter,
            discount_percent=discount,
            round=current_round,
            status="active",
            message="",
            urgency=urgency,
        )

    def _calc_discount(self, state: NegotiationState) -> float:
        """Calculate current discount percentage."""
        orig = float(state.original_price)
        if orig == 0:
            return 0.0
        return round((1 - float(state.current_offer) / orig) * 100, 2)

    def _calculate_counter(
        self,
        state: NegotiationState,
        customer_offer: float,
        business_type: Optional[str] = None,
    ) -> tuple:
        """
        Return (counter_offer, discount_percent, urgency, concession_type)
        based on round, strategy, and business type.
        """
        original = float(state.original_price)
        max_discount = float(state.max_discount_percent)

        # Business-type-specific strategies
        if business_type in ("services", "consulting"):
            return self._calculate_service_counter(state, original, max_discount)
        if business_type == "software":
            return self._calculate_software_counter(state, original, max_discount)
        if business_type == "food_beverage":
            return self._calculate_food_counter(state, original, max_discount)

        # Default: product-based percentage discount
        return self._calculate_product_counter(state, original, max_discount)

    def _calculate_product_counter(
        self, state: NegotiationState, original: float, max_discount: float
    ) -> tuple:
        """Standard product discount strategy."""
        if state.round == 1:
            discount = min(2.0, max_discount)
            return original * (1 - discount / 100), discount, False, "minimal_concession"
        if state.round == 2:
            discount = min(max_discount * 0.25, 5.0)
            return original * (1 - discount / 100), discount, False, "small_concession_bundle"
        if state.round == 3:
            discount = min(max_discount * 0.60, max_discount - 2.0)
            return original * (1 - discount / 100), discount, True, "moderate_discount_free_shipping"
        discount = max_discount
        return original * (1 - discount / 100), discount, True, "max_discount_final_offer"

    def _calculate_service_counter(
        self, state: NegotiationState, original: float, max_discount: float
    ) -> tuple:
        """Service negotiation: value-adds, packages, payment terms."""
        if state.round == 1:
            discount = min(2.0, max_discount)
            return original * (1 - discount / 100), discount, False, "minimal_concession"
        if state.round == 2:
            discount = min(max_discount * 0.20, 5.0)
            return original * (1 - discount / 100), discount, False, "small_discount_extra_service"
        if state.round == 3:
            discount = min(max_discount * 0.50, max_discount - 3.0)
            return original * (1 - discount / 100), discount, True, "moderate_discount_payment_plan"
        discount = max_discount
        return original * (1 - discount / 100), discount, True, "max_discount_guarantee"

    def _calculate_software_counter(
        self, state: NegotiationState, original: float, max_discount: float
    ) -> tuple:
        """Software/SaaS negotiation: annual plans, upgrades, trials."""
        if state.round == 1:
            discount = min(2.0, max_discount)
            return original * (1 - discount / 100), discount, False, "minimal_concession"
        if state.round == 2:
            discount = min(max_discount * 0.30, 8.0)
            return original * (1 - discount / 100), discount, False, "annual_discount_upgrade"
        if state.round == 3:
            discount = min(max_discount * 0.65, max_discount - 2.0)
            return original * (1 - discount / 100), discount, True, "significant_discount_extended_trial"
        discount = max_discount
        return original * (1 - discount / 100), discount, True, "max_discount_annual_commitment"

    def _calculate_food_counter(
        self, state: NegotiationState, original: float, max_discount: float
    ) -> tuple:
        """Food & beverage negotiation: combos, free delivery, loyalty."""
        if state.round == 1:
            discount = min(2.0, max_discount)
            return original * (1 - discount / 100), discount, False, "minimal_concession"
        if state.round == 2:
            discount = min(max_discount * 0.25, 5.0)
            return original * (1 - discount / 100), discount, False, "combo_offer_free_drink"
        if state.round == 3:
            discount = min(max_discount * 0.55, max_discount - 3.0)
            return original * (1 - discount / 100), discount, True, "moderate_discount_free_delivery"
        discount = max_discount
        return original * (1 - discount / 100), discount, True, "max_discount_loyalty_reward"

    async def generate_negotiation_reply(
        self,
        business_id: uuid.UUID,
        negotiation_response: NegotiationResponse,
        state: NegotiationState,
    ) -> str:
        """Generate a natural-language negotiation reply using LLM."""
        try:
            # Late import to avoid circular dependency
            from app.domains.agents.ai_reply import generate_raw_ai_response
        except ImportError:
            logger.error("Failed to import generate_raw_ai_response")
            return negotiation_response.message or "Gracias por tu oferta."

        # Load business type for adaptive messaging
        business_type = await self._get_business_type(business_id)
        type_hint = ""
        if business_type == "services":
            type_hint = " Estás negociando SERVICIOS profesionales. Ofrece valor agregado o flexibilidad de horarios."
        elif business_type == "consulting":
            type_hint = " Estás negociando CONSULTORÍA. Enfatiza resultados garantizados y milestones."
        elif business_type == "software":
            type_hint = " Estás negociando SOFTWARE/SaaS. Menciona onboarding, soporte o funcionalidades extra."
        elif business_type == "food_beverage":
            type_hint = " Estás negociando COMIDA/BEBIDA. Ofrece combos, delivery gratis o descuentos en próxima compra."
        elif business_type in ("physical_products", "fashion_beauty", "home_decor", "handcraft"):
            type_hint = " Estás negociando PRODUCTOS FÍSICOS. Menciona envío gratis, garantía o bundles."

        if negotiation_response.status == "accepted":
            system = (
                "Eres un vendedor experto. El cliente ha aceptado la oferta final. "
                "Confirma con entusiasmo y pasa al cierre de la venta."
                f"{type_hint}"
            )
            user = (
                f"Oferta aceptada: ${negotiation_response.counter_offer:.2f}. "
                f"Descuento aplicado: {negotiation_response.discount_percent:.1f}%. "
                "Genera un mensaje de confirmación breve y profesional."
            )
        elif negotiation_response.status in ("expired", "not_found"):
            return negotiation_response.message
        else:
            urgency_text = ""
            if negotiation_response.urgency:
                urgency_text = (
                    "Añade urgencia realista: 'esta oferta es válida solo por hoy' o "
                    "'quedan pocas unidades'."
                )
            system = (
                "Eres un negociador experto en ventas. Responde al cliente de forma "
                "natural, profesional y persuasiva. Nunca suenes desesperado. "
                f"{urgency_text}{type_hint}"
            )
            user = (
                f"Precio original: ${float(state.original_price):.2f}. "
                f"Oferta del cliente: ${float(state.current_offer):.2f}. "
                f"Nuestra contraoferta: ${negotiation_response.counter_offer:.2f} "
                f"({negotiation_response.discount_percent:.1f}% descuento). "
                f"Tipo de concesión: {negotiation_response.status}. "
                f"Ronda {negotiation_response.round}/4. "
                "Genera un mensaje corto y natural en español para presentar esta contraoferta."
            )

        reply = await generate_raw_ai_response(
            db=self.db,
            business_id=business_id,
            system_prompt=system,
            user_prompt=user,
            max_tokens=400,
            temperature=0.6,
        )
        return reply or negotiation_response.message or "Gracias por tu oferta."

    @staticmethod
    def extract_offer_amount(message: str) -> Optional[float]:
        """Extract a monetary offer from free-text message."""
        text = message.lower()

        # Common patterns: $500, 500 pesos, 500 usd, 500.00, 1.234,56
        patterns = [
            r"[\$€£]\s*([\d.,]+)",
            r"([\d.,]+)\s*[\$€£]",
            r"(?:ofrezco|oferta|presupuesto|máximo|hasta|por)\s*[\$€£]?\s*([\d.,]+)",
            r"([\d.,]+)\s*(?:pesos|usd|dólares|euros)",
        ]
        for pat in patterns:
            matches = re.findall(pat, text)
            for m in matches:
                val = NegotiationEngine._parse_number(m)
                if val and val > 0:
                    return val

        # Fallback: any standalone number that looks like a price (> 10)
        nums = re.findall(r"[\d.,]+", text)
        for n in nums:
            val = NegotiationEngine._parse_number(n)
            if val and val > 10:
                return val

        return None

    @staticmethod
    def _parse_number(num_str: str) -> Optional[float]:
        """Parse a numeric string handling comma/dot formats."""
        s = num_str.strip()
        if not s:
            return None
        try:
            # Handle both 1.234,56 and 1,234.56
            if "," in s and "." in s:
                if s.rfind(",") > s.rfind("."):
                    # European: 1.234,56
                    s = s.replace(".", "").replace(",", ".")
                else:
                    # US: 1,234.56
                    s = s.replace(",", "")
            elif "," in s:
                # Could be decimal separator or thousands
                parts = s.split(",")
                if len(parts) == 2 and len(parts[1]) <= 2:
                    s = s.replace(",", ".")
                else:
                    s = s.replace(",", "")
            return float(s)
        except ValueError:
            return None
