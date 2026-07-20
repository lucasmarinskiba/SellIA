"""
Loop Engineering — Iteración controlada hasta objetivo logrado.

Loop = Objetivo + Acción + Evaluación + Corrección + Condición salida + Límite

Aplicado a: lead capture → negotiation → closing → payment → delivery → retention.
"""

import logging
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class LoopStatus(str, Enum):
    """Estados loop."""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    EXHAUSTED = "exhausted"  # Max retries/time/resources


class LoopPhase(str, Enum):
    """Fases venta."""
    LEAD_CAPTURE = "lead_capture"
    LEAD_QUALIFICATION = "lead_qualification"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    PAYMENT = "payment"
    DELIVERY = "delivery"
    RETENTION = "retention"


class LoopEngineering:
    """Ejecuta loops iterativos con control completo."""

    def __init__(self):
        self.loops_history: List[Dict[str, Any]] = []
        self.active_loops: Dict[str, Any] = {}

    async def run_loop(
        self,
        objective: str,
        action_fn: Callable,
        evaluate_fn: Callable,
        correct_fn: Callable,
        max_iterations: int = 5,
        max_time_seconds: int = 300,
        exit_condition_fn: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta loop controlado.

        Loop formula:
        1. Objetivo: qué queremos lograr
        2. Acción: ejecuta (action_fn)
        3. Evaluación: chequea éxito (evaluate_fn)
        4. Corrección: si falla, ajusta (correct_fn)
        5. Condición salida: exit_condition_fn() → True = stop
        6. Límite: max_iterations + max_time_seconds
        """

        logger.info(f"Starting loop: {objective}")

        loop_id = f"{objective}_{int(asyncio.get_event_loop().time())}"
        loop_log = {
            "id": loop_id,
            "objective": objective,
            "status": LoopStatus.RUNNING.value,
            "iterations": 0,
            "start_time": asyncio.get_event_loop().time(),
            "actions": [],
            "evaluations": [],
            "corrections": [],
        }

        iteration = 0
        start_time = asyncio.get_event_loop().time()

        while iteration < max_iterations:
            iteration += 1
            elapsed = asyncio.get_event_loop().time() - start_time

            # Chequear límite tiempo
            if elapsed > max_time_seconds:
                logger.warning(f"Loop {objective} exhausted by time ({elapsed}s > {max_time_seconds}s)")
                loop_log["status"] = LoopStatus.EXHAUSTED.value
                break

            logger.info(f"Loop {objective} - iteration {iteration}/{max_iterations}")

            try:
                # 1. ACCIÓN
                action_result = await action_fn()
                loop_log["actions"].append(action_result)

                # 2. EVALUACIÓN
                eval_result = await evaluate_fn(action_result)
                loop_log["evaluations"].append(eval_result)

                # 3. CONDICIÓN SALIDA
                if exit_condition_fn and exit_condition_fn(eval_result):
                    logger.info(f"Loop {objective} - exit condition met")
                    loop_log["status"] = LoopStatus.SUCCESS.value
                    break

                # Si success
                if eval_result.get("success"):
                    logger.info(f"Loop {objective} - success on iteration {iteration}")
                    loop_log["status"] = LoopStatus.SUCCESS.value
                    break

                # 4. CORRECCIÓN (si falla)
                correction = await correct_fn(eval_result)
                loop_log["corrections"].append(correction)

                logger.info(f"Applied correction: {correction.get('adjustment')}")

            except Exception as e:
                logger.error(f"Loop {objective} error on iteration {iteration}: {str(e)}")
                loop_log["corrections"].append({"error": str(e)})

        # Final status
        if loop_log["status"] == LoopStatus.RUNNING.value:
            if iteration >= max_iterations:
                loop_log["status"] = LoopStatus.EXHAUSTED.value
            else:
                loop_log["status"] = LoopStatus.FAILED.value

        loop_log["iterations"] = iteration
        loop_log["elapsed_time"] = asyncio.get_event_loop().time() - start_time

        self.loops_history.append(loop_log)
        logger.info(f"Loop {objective} completed: {loop_log['status']} ({iteration} iterations)")

        return loop_log

    async def run_sales_cycle_with_loops(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ciclo venta completo con Loop Engineering.

        Fases: capture → qualify → negotiate → close → pay → deliver → retain.
        """

        logger.info(f"Starting sales cycle with loops for {product.get('name')}")

        cycle_result = {
            "product": product.get("name"),
            "buyer": buyer.get("email"),
            "phases": {},
            "overall_status": "in_progress",
        }

        # FASE 1: LEAD CAPTURE
        cycle_result["phases"]["capture"] = await self.run_loop(
            objective="capture_lead",
            action_fn=lambda: self._action_capture(product, buyer),
            evaluate_fn=lambda r: self._eval_capture(r),
            correct_fn=lambda e: self._correct_capture(e),
            max_iterations=3,
            exit_condition_fn=lambda e: e.get("contact_verified"),
        )

        # FASE 2: LEAD QUALIFICATION
        cycle_result["phases"]["qualification"] = await self.run_loop(
            objective="qualify_lead",
            action_fn=lambda: self._action_qualify(buyer),
            evaluate_fn=lambda r: self._eval_qualify(r),
            correct_fn=lambda e: self._correct_qualify(e),
            max_iterations=2,
            exit_condition_fn=lambda e: e.get("qualified"),
        )

        # FASE 3: NEGOTIATION
        cycle_result["phases"]["negotiation"] = await self.run_loop(
            objective="negotiate",
            action_fn=lambda: self._action_negotiate(product, buyer),
            evaluate_fn=lambda r: self._eval_negotiate(r),
            correct_fn=lambda e: self._correct_negotiate(e),
            max_iterations=5,
            max_time_seconds=600,
            exit_condition_fn=lambda e: e.get("deal_agreed"),
        )

        # FASE 4: CLOSING
        cycle_result["phases"]["closing"] = await self.run_loop(
            objective="close_sale",
            action_fn=lambda: self._action_close(product, buyer),
            evaluate_fn=lambda r: self._eval_close(r),
            correct_fn=lambda e: self._correct_close(e),
            max_iterations=3,
            exit_condition_fn=lambda e: e.get("signed"),
        )

        # FASE 5: PAYMENT
        cycle_result["phases"]["payment"] = await self.run_loop(
            objective="process_payment",
            action_fn=lambda: self._action_payment(product, buyer),
            evaluate_fn=lambda r: self._eval_payment(r),
            correct_fn=lambda e: self._correct_payment(e),
            max_iterations=2,
            exit_condition_fn=lambda e: e.get("payment_confirmed"),
        )

        # FASE 6: DELIVERY
        cycle_result["phases"]["delivery"] = await self.run_loop(
            objective="deliver_product",
            action_fn=lambda: self._action_delivery(product, buyer),
            evaluate_fn=lambda r: self._eval_delivery(r),
            correct_fn=lambda e: self._correct_delivery(e),
            max_iterations=2,
            exit_condition_fn=lambda e: e.get("delivered"),
        )

        # FASE 7: RETENTION
        cycle_result["phases"]["retention"] = await self.run_loop(
            objective="retain_customer",
            action_fn=lambda: self._action_retention(product, buyer),
            evaluate_fn=lambda r: self._eval_retention(r),
            correct_fn=lambda e: self._correct_retention(e),
            max_iterations=10,
            max_time_seconds=2592000,  # 30 días
            exit_condition_fn=lambda e: e.get("nps_score", 0) > 50,
        )

        # Overall status
        all_success = all(
            p.get("status") == LoopStatus.SUCCESS.value
            for p in cycle_result["phases"].values()
        )
        cycle_result["overall_status"] = "success" if all_success else "partial"

        logger.info(f"Sales cycle completed: {cycle_result['overall_status']}")

        return cycle_result

    # ========== FASE 1: CAPTURE ==========
    async def _action_capture(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Captura lead vía múltiples canales."""
        return {"status": "capturing", "channels": ["whatsapp", "email", "instagram"]}

    async def _eval_capture(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: contact verificado?"""
        return {"success": True, "contact_verified": True}

    async def _correct_capture(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: retry otro canal si falla."""
        return {"adjustment": "try_next_channel"}

    # ========== FASE 2: QUALIFY ==========
    async def _action_qualify(self, buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Califica lead (budget, timeline, authority)."""
        return {"score": 85, "authority": True, "budget": 50000}

    async def _eval_qualify(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: score > 70?"""
        return {"success": result.get("score", 0) > 70, "qualified": True}

    async def _correct_qualify(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: send more info si score bajo."""
        return {"adjustment": "nurture_sequence"}

    # ========== FASE 3: NEGOTIATE ==========
    async def _action_negotiate(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Negocia deal (price, terms, payment plan)."""
        return {"price_offered": product.get("price"), "terms": "Net 30"}

    async def _eval_negotiate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: buyer aceptó deal?"""
        return {"success": True, "deal_agreed": True, "price": result.get("price_offered")}

    async def _correct_negotiate(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: offer payment plan si rechaza price."""
        return {"adjustment": "offer_installments"}

    # ========== FASE 4: CLOSING ==========
    async def _action_close(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Cierra: firma contrato."""
        return {"contract_sent": True, "signature_requested": True}

    async def _eval_close(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: firmó?"""
        return {"success": True, "signed": True}

    async def _correct_close(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: reminder si no firmó."""
        return {"adjustment": "send_reminder"}

    # ========== FASE 5: PAYMENT ==========
    async def _action_payment(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa pago vía Stripe."""
        return {"payment_initiated": True, "intent_id": "pi_12345"}

    async def _eval_payment(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: pago confirmado?"""
        return {"success": True, "payment_confirmed": True}

    async def _correct_payment(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: retry payment si falla."""
        return {"adjustment": "retry_payment"}

    # ========== FASE 6: DELIVERY ==========
    async def _action_delivery(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Entrega producto/acceso."""
        return {"access_granted": True, "onboarding_started": True}

    async def _eval_delivery(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: cliente accedió?"""
        return {"success": True, "delivered": True}

    async def _correct_delivery(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: send access email si no accede."""
        return {"adjustment": "resend_access"}

    # ========== FASE 7: RETENTION ==========
    async def _action_retention(self, product: Dict[str, Any], buyer: Dict[str, Any]) -> Dict[str, Any]:
        """Retiene: engagement, upsell, referral."""
        return {"engagement_email_sent": True, "nps_survey_sent": True}

    async def _eval_retention(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluá: NPS score alto?"""
        return {"success": True, "nps_score": 65}

    async def _correct_retention(self, eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige: support call si NPS bajo."""
        return {"adjustment": "schedule_support_call"}
