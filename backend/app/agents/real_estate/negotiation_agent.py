"""Negotiation Agent — Offer strategy, terms, closing tactics."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OfferStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTER = "countered"
    WITHDRAWN = "withdrawn"


@dataclass
class OfferTerms:
    """Offer terms and conditions."""

    offer_price: float
    earnest_money: float
    contingencies: List[str] = field(default_factory=list)
    inspection_period_days: int = 10
    appraisal_contingency: bool = True
    financing_contingency: bool = True
    close_date: Optional[datetime] = None
    title_commitment_days: int = 10
    final_walkthrough_allowed: bool = True
    repair_escrow: Optional[float] = None  # For known issues
    possession_date: Optional[datetime] = None
    seller_concessions: float = 0.0  # Amount seller will contribute


@dataclass
class NegotiationStrategy:
    """Negotiation strategy for offer."""

    strategy_type: str  # aggressive, balanced, collaborative
    opening_offer_pct_below: float  # How much below asking to start
    walk_away_price: float  # Minimum acceptable price
    priority_terms: List[str]  # Most important terms
    contingencies_to_include: List[str]
    expected_counter_rounds: int  # Expected negotiations
    time_pressure: bool  # Urgency to close


class NegotiationAgent:
    """Manage offer negotiations and closing strategy."""

    def __init__(self):
        self.offers: Dict[str, Dict[str, Any]] = {}
        self.negotiations: Dict[str, List[Dict[str, Any]]] = {}

    def create_offer(
        self, property_id: str, lead_id: str, strategy: NegotiationStrategy, property_value: float
    ) -> Dict[str, Any]:
        """Create initial offer based on strategy."""
        # Calculate opening offer
        opening_offer_price = property_value * (1 - strategy.opening_offer_pct_below)

        # Determine earnest money (typically 1-3% of offer)
        earnest_money = opening_offer_price * 0.02

        # Build offer terms
        offer = OfferTerms(
            offer_price=opening_offer_price,
            earnest_money=earnest_money,
            contingencies=strategy.contingencies_to_include,
            close_date=datetime.utcnow() + timedelta(days=45),
            possession_date=datetime.utcnow() + timedelta(days=45),
        )

        # Store offer
        self.offers[f"{property_id}_{lead_id}"] = {
            "property_id": property_id,
            "lead_id": lead_id,
            "status": OfferStatus.DRAFT,
            "offer_terms": offer,
            "strategy": strategy,
            "created_at": datetime.utcnow(),
            "rounds": 0,
        }

        logger.info(f"Created offer for {property_id}: ${opening_offer_price:,.0f}")

        return {
            "offer_id": f"{property_id}_{lead_id}",
            "offer_price": opening_offer_price,
            "earnest_money": earnest_money,
            "suggested_contingencies": strategy.contingencies_to_include,
            "expected_close": (datetime.utcnow() + timedelta(days=45)).isoformat(),
        }

    def submit_offer(self, offer_id: str, additional_terms: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Submit offer to seller."""
        if offer_id not in self.offers:
            return {"error": "Offer not found"}

        offer_record = self.offers[offer_id]
        offer_record["status"] = OfferStatus.SUBMITTED

        if offer_id not in self.negotiations:
            self.negotiations[offer_id] = []

        self.negotiations[offer_id].append({
            "round": 1,
            "timestamp": datetime.utcnow(),
            "action": "submitted",
            "terms": offer_record["offer_terms"].__dict__,
        })

        logger.info(f"Submitted offer: {offer_id}")

        return {
            "offer_id": offer_id,
            "status": "submitted",
            "submission_time": datetime.utcnow().isoformat(),
        }

    def process_counter_offer(self, offer_id: str, counter_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Process seller's counter offer."""
        if offer_id not in self.offers:
            return {"error": "Offer not found"}

        offer_record = self.offers[offer_id]
        strategy = offer_record["strategy"]
        offer_record["rounds"] += 1

        # Extract counter terms
        counter_price = counter_terms.get("counter_price", offer_record["offer_terms"].offer_price)
        counter_terms_list = counter_terms.get("terms", [])

        # Evaluate counter
        evaluation = self._evaluate_counter_offer(
            counter_price, strategy.walk_away_price, offer_record["offer_terms"].offer_price, strategy
        )

        # Store negotiation round
        self.negotiations[offer_id].append({
            "round": offer_record["rounds"],
            "timestamp": datetime.utcnow(),
            "action": "counter_received",
            "counter_price": counter_price,
            "counter_terms": counter_terms_list,
        })

        logger.info(f"Counter offer received for {offer_id}: ${counter_price:,.0f}")

        return {
            "offer_id": offer_id,
            "counter_price": counter_price,
            "evaluation": evaluation,
            "recommendation": self._generate_counter_recommendation(counter_price, strategy),
            "suggested_response": self._suggest_response_to_counter(counter_price, strategy),
        }

    def _evaluate_counter_offer(self, counter_price: float, walk_away: float, original_offer: float, strategy: NegotiationStrategy) -> Dict[str, Any]:
        """Evaluate acceptability of counter offer."""
        spread = original_offer - counter_price
        spread_pct = (spread / original_offer) * 100

        accept = counter_price >= walk_away
        move_toward_us = spread < (original_offer - walk_away) / 2

        return {
            "price_spread": spread,
            "spread_percentage": spread_pct,
            "is_acceptable": accept,
            "moving_toward_our_target": move_toward_us,
            "distance_to_walk_away": counter_price - walk_away,
        }

    def _generate_counter_recommendation(self, counter_price: float, strategy: NegotiationStrategy) -> str:
        """Generate recommendation on counter offer."""
        if counter_price >= strategy.walk_away_price * 1.02:
            return "ACCEPT - Price within acceptable range"
        elif counter_price >= strategy.walk_away_price:
            return "CONSIDER ACCEPTING - At walk-away price"
        elif counter_price > strategy.walk_away_price * 0.95:
            return "COUNTER AGAIN - Close to target, room for negotiation"
        else:
            return "REJECT - Below acceptable minimum"

    def _suggest_response_to_counter(self, counter_price: float, strategy: NegotiationStrategy) -> Dict[str, Any]:
        """Suggest response to counter offer."""
        midpoint = (strategy.walk_away_price + counter_price) / 2

        return {
            "counter_offer_option": {
                "price": midpoint,
                "rationale": "Meet seller halfway",
            },
            "accept_option": {
                "price": counter_price,
                "rationale": "Accept to close quickly",
            },
            "reject_and_walkaway_option": {
                "price": None,
                "rationale": "Exceeds acceptable limits",
            },
        }

    def finalize_terms(self, offer_id: str) -> Dict[str, Any]:
        """Finalize accepted offer terms."""
        if offer_id not in self.offers:
            return {"error": "Offer not found"}

        offer_record = self.offers[offer_id]
        offer_record["status"] = OfferStatus.ACCEPTED

        self.negotiations[offer_id].append({
            "round": "final",
            "timestamp": datetime.utcnow(),
            "action": "accepted",
        })

        offer_terms = offer_record["offer_terms"]

        return {
            "offer_id": offer_id,
            "status": "accepted",
            "final_price": offer_terms.offer_price,
            "earnest_money": offer_terms.earnest_money,
            "inspection_period": f"{offer_terms.inspection_period_days} days",
            "close_date": offer_terms.close_date.isoformat(),
            "next_steps": [
                "Sign purchase agreement",
                "Deposit earnest money",
                "Schedule inspection",
                "Finalize financing",
                "Get title insurance",
                "Final walkthrough",
                "Close sale",
            ],
        }

    def get_negotiation_history(self, offer_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get full negotiation history."""
        return self.negotiations.get(offer_id)

    def estimate_final_price(self, offer_id: str) -> Optional[float]:
        """Estimate likely final price based on negotiation pattern."""
        if offer_id not in self.negotiations:
            return None

        history = self.negotiations[offer_id]
        prices = [round_data.get("counter_price") or round_data.get("terms", {}).get("price")
                  for round_data in history if "counter_price" in round_data or "price" in round_data.get("terms", {})]

        if len(prices) >= 2:
            # Calculate average move
            avg_move = (prices[-1] - prices[0]) / len(prices)
            estimated = prices[-1] + avg_move
            return estimated

        return None
