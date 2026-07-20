"""Market Context Injector — Customize agent instructions per market."""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MarketContextInjector:
    """Inject market context into LLM prompts & agent instructions."""

    @staticmethod
    def inject_market_context(
        prompt: str,
        market_profile: "MarketProfile",
        rules: Dict[str, Any],
    ) -> str:
        """Inject market-specific context into prompt."""

        context_blocks = []

        # Add industry context
        industry_context = MarketContextInjector._get_industry_context(market_profile.industry)
        if industry_context:
            context_blocks.append(industry_context)

        # Add market type context
        market_context = MarketContextInjector._get_market_type_context(market_profile.market_type)
        if market_context:
            context_blocks.append(market_context)

        # Add business model context
        model_context = MarketContextInjector._get_business_model_context(market_profile.business_model)
        if model_context:
            context_blocks.append(model_context)

        # Add sales cycle context
        phases = rules.get("sales_phases", [])
        timeline = rules.get("sales_cycle", {})
        cycle_context = f"Expected sales cycle: {timeline.get('min')}-{timeline.get('max')} days via phases: {', '.join(phases)}"
        context_blocks.append(cycle_context)

        # Add buyer motivation context
        motivation_context = f"Buyer motivation profile: {market_profile.buyer_motivation.value}"
        context_blocks.append(motivation_context)

        # Combine with original prompt
        full_prompt = "\n".join([
            "### MARKET CONTEXT ###",
            "\n".join(context_blocks),
            "\n### ORIGINAL PROMPT ###",
            prompt,
        ])

        return full_prompt

    @staticmethod
    def customize_agent_system_prompt(
        agent_id: str,
        market_profile: "MarketProfile",
        rules: Dict[str, Any],
    ) -> str:
        """Generate market-customized system prompt for agent."""

        base_prompt = MarketContextInjector._get_agent_base_prompt(agent_id)

        # Customize based on market
        customizations = {
            "sales_phases": rules.get("sales_phases", []),
            "sales_cycle": rules.get("sales_cycle", {}),
            "pricing": rules.get("pricing_rules", {}),
            "payment": rules.get("payment_rules", {}),
            "industry": market_profile.industry.value,
            "market_type": market_profile.market_type,
            "business_model": market_profile.business_model.value,
        }

        # Add customization section
        customization_section = "\n## MARKET CUSTOMIZATION ##\n"
        for key, value in customizations.items():
            customization_section += f"- {key}: {value}\n"

        return base_prompt + "\n" + customization_section

    @staticmethod
    def _get_industry_context(industry: "Industry") -> str:
        """Get industry-specific context."""
        contexts = {
            "real_estate": "Real estate market: Focus on property value, buyer financial capability, market conditions, legal requirements.",
            "commerce": "Commerce market: Focus on product-market fit, competitive pricing, platform optimization, inventory.",
            "services": "Services market: Focus on scope definition, delivery timeline, quality assurance, client satisfaction.",
            "finance": "Financial services market: Focus on regulatory compliance, risk assessment, client suitability, audit trails.",
            "labor": "Labor market: Focus on skill match, contract terms, employment law, compensation.",
            "manufacturing": "Manufacturing market: Focus on quality, delivery time, order volume, supply chain.",
            "digital_products": "Digital products market: Focus on conversion, user experience, retention, upsell.",
        }
        return contexts.get(industry.value, "")

    @staticmethod
    def _get_market_type_context(market_type: str) -> str:
        """Get B2B/B2C/D2C context."""
        contexts = {
            "B2B": "B2B selling: Focus on ROI, decision committees, longer sales cycles, contract negotiations.",
            "B2C": "B2C selling: Focus on emotional drivers, quick decisions, trust building, social proof.",
            "D2C": "D2C selling: Focus on direct relationships, brand loyalty, customer data, lifetime value.",
        }
        return contexts.get(market_type, "")

    @staticmethod
    def _get_business_model_context(model: "BusinessModel") -> str:
        """Get business model context."""
        contexts = {
            "physical": "Physical products: Handle shipping, inventory, returns, product quality concerns.",
            "digital": "Digital products: Emphasize instant delivery, access, scalability, automation.",
            "service": "Services: Focus on expertise, delivery quality, timeline, client communication.",
            "hybrid": "Hybrid model: Combine physical and digital value propositions.",
            "subscription": "Subscription model: Focus on retention, recurring value, churn prevention.",
            "marketplace": "Marketplace model: Focus on network effects, seller quality, buyer protection.",
        }
        return contexts.get(model.value, "")

    @staticmethod
    def _get_agent_base_prompt(agent_id: str) -> str:
        """Get base system prompt for agent."""
        base_prompts = {
            "sellIA_base": "You are SellIA, an autonomous sales agent. Your goal is to identify qualified buyers and close sales.",
            "realEstate_leadScorer": "You are a real estate lead scoring specialist. Evaluate buyer profiles and property fit.",
            "realEstate_negotiator": "You are a real estate negotiator. Structure offers and terms favorable to the seller.",
            "commerce_prospector": "You are a commerce prospector. Identify market opportunities and competitive advantages.",
            "commerce_advisor": "You are a commercial advisor. Provide strategy and positioning recommendations.",
            "services_qualifier": "You are a services qualifier. Understand client needs and scope projects accurately.",
            "finance_advisor": "You are a financial advisor. Provide investment recommendations within regulatory guidelines.",
        }
        return base_prompts.get(agent_id, "You are a specialized sales agent.")

    @staticmethod
    def inject_guardrails(prompt: str, market_profile: "MarketProfile", rules: Dict[str, Any]) -> str:
        """Inject market-specific guardrails."""

        guardrails = []

        # Finance guardrails
        if market_profile.industry.value == "finance":
            guardrails.extend([
                "⚠️ REGULATORY: Always verify AML/KYC compliance before proceeding.",
                "⚠️ SUITABILITY: Ensure recommendations match client risk profile.",
                "⚠️ DISCLOSURE: Always disclose fees and potential conflicts.",
            ])

        # Real estate guardrails
        if market_profile.industry.value == "real_estate":
            guardrails.extend([
                "⚠️ LEGAL: Verify property title and liens before marketing.",
                "⚠️ INSPECTION: Always schedule professional inspection.",
                "⚠️ DISCLOSURE: Full disclosure of property condition required.",
            ])

        if guardrails:
            guardrail_section = "\n## GUARDRAILS ##\n" + "\n".join(guardrails)
            return prompt + "\n" + guardrail_section

        return prompt
