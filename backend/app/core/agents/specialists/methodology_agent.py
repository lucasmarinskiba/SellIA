"""
Methodology Agent — Framework knowledge and business methodology expertise.

Specialties:
- Jobs to be Done (JTBD) framework
- Value Proposition Design
- Lean Startup methodology
- OKRs (Objectives & Key Results)
- Helps users define business methodology
- Recommends frameworks by business type and stage
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class BusinessStage(str, Enum):
    """Business lifecycle stages."""
    IDEA = "idea"
    MVP = "mvp"
    EARLY_TRACTION = "early_traction"
    GROWTH = "growth"
    SCALE = "scale"
    MATURE = "mature"


class BusinessType(str, Enum):
    """Types of businesses."""
    B2B_SaaS = "b2b_saas"
    B2C_SaaS = "b2c_saas"
    MARKETPLACE = "marketplace"
    E_COMMERCE = "e_commerce"
    SERVICES = "services"
    HARDWARE = "hardware"
    CREATOR = "creator"
    NON_PROFIT = "non_profit"


@dataclass
class Framework:
    """Business framework definition."""
    name: str
    description: str
    suitable_for: List[str]  # Business types/stages
    key_concepts: List[str]
    implementation_steps: List[str]
    kpis: List[str]
    time_to_implement: str
    difficulty: str  # easy, medium, hard


class MethodologyAgent:
    """Expert in business frameworks and methodologies."""

    FRAMEWORKS = {
        "jtbd": Framework(
            name="Jobs to be Done",
            description="Understand what customers are trying to accomplish and design solutions around that job.",
            suitable_for=["All stages", "All types"],
            key_concepts=[
                "The job (functional, emotional, social)",
                "Customer circumstances",
                "Competing solutions",
                "Desired outcomes",
                "Obstacles to getting the job done"
            ],
            implementation_steps=[
                "1. Conduct customer interviews with 10-15 target customers",
                "2. Identify the primary job they're trying to get done",
                "3. Map functional, emotional, and social aspects",
                "4. List competing alternatives and workarounds",
                "5. Identify barriers and desired outcomes",
                "6. Prioritize by job importance and satisfaction gap"
            ],
            kpis=[
                "Jobs identified per customer segment",
                "Solution-job fit score",
                "Outcome achievement rate",
                "Customer satisfaction with job accomplishment"
            ],
            time_to_implement="4-8 weeks",
            difficulty="medium"
        ),

        "vpd": Framework(
            name="Value Proposition Design",
            description="Design value propositions that align customer jobs, pains, and gains with your product.",
            suitable_for=["MVP", "Early traction", "Growth"],
            key_concepts=[
                "Value proposition",
                "Customer segments",
                "Customer jobs",
                "Customer pains",
                "Customer gains",
                "Products and services",
                "Pain relievers",
                "Gain creators"
            ],
            implementation_steps=[
                "1. Define your target customer segment",
                "2. Map their jobs (functional, emotional, social)",
                "3. List their pains and associated emotions",
                "4. Identify desired gains and benefits",
                "5. List your products/services and features",
                "6. Identify pain relievers (reduce pains)",
                "7. Identify gain creators (enhance gains)",
                "8. Test fit with customers"
            ],
            kpis=[
                "Jobs coverage (%)",
                "Pains addressed (%)",
                "Gains delivered (%)",
                "Value proposition clarity score",
                "Feature-to-job alignment"
            ],
            time_to_implement="3-6 weeks",
            difficulty="medium"
        ),

        "lean_startup": Framework(
            name="Lean Startup",
            description="Build-Measure-Learn cycles to validate assumptions with minimum resources.",
            suitable_for=["Idea", "MVP", "Early traction"],
            key_concepts=[
                "Build-Measure-Learn loop",
                "Minimum Viable Product (MVP)",
                "Validated learning",
                "Pivot or persevere",
                "Innovation accounting"
            ],
            implementation_steps=[
                "1. Define core hypotheses",
                "2. Design smallest MVP to test",
                "3. Build MVP (minimal feature set)",
                "4. Launch and measure user behavior",
                "5. Collect quantitative and qualitative data",
                "6. Learn: Analyze results",
                "7. Decide: Pivot, persevere, or pivot-and-keep",
                "8. Repeat with next hypothesis"
            ],
            kpis=[
                "Cycle time (days to complete loop)",
                "Validated assumptions (%)",
                "Hypothesis validation rate",
                "MVP feature count",
                "Learning velocity"
            ],
            time_to_implement="1-3 weeks per cycle",
            difficulty="easy"
        ),

        "okrs": Framework(
            name="OKRs (Objectives & Key Results)",
            description="Align organization around ambitious goals and measurable outcomes.",
            suitable_for=["Growth", "Scale"],
            key_concepts=[
                "Objectives (qualitative, inspirational)",
                "Key Results (quantitative, measurable)",
                "Alignment (cascade from company to team)",
                "Stretch goals",
                "Scoring (0-1 confidence)",
                "Reflection cycles"
            ],
            implementation_steps=[
                "1. Define company vision and strategy",
                "2. Set 3-5 company-level objectives",
                "3. For each objective, define 3-4 key results",
                "4. Ensure key results are measurable and ambitious",
                "5. Cascade to team-level OKRs",
                "6. Align cross-functional initiatives",
                "7. Weekly/monthly check-ins on progress",
                "8. Quarterly review and reflection"
            ],
            kpis=[
                "OKR completion rate (%)",
                "Alignment score (cross-team sync)",
                "Team confidence in goals",
                "Strategic initiative completion",
                "Focus (initiatives per goal)"
            ],
            time_to_implement="2-4 weeks setup",
            difficulty="medium"
        ),

        "design_thinking": Framework(
            name="Design Thinking",
            description="Human-centered approach to innovation through empathy and rapid prototyping.",
            suitable_for=["All stages"],
            key_concepts=[
                "Empathy",
                "Problem definition",
                "Ideation",
                "Prototyping",
                "Testing",
                "Iterative refinement"
            ],
            implementation_steps=[
                "1. Empathize: Conduct user research and interviews",
                "2. Define: Synthesize insights into problem statement",
                "3. Ideate: Brainstorm solutions without constraints",
                "4. Prototype: Create low-fidelity mockups/prototypes",
                "5. Test: Get feedback from users",
                "6. Refine: Iterate based on feedback",
                "7. Scale: Build full solution"
            ],
            kpis=[
                "User feedback score",
                "Prototype iterations",
                "Problem clarity score",
                "Solution adoption rate",
                "Innovation index"
            ],
            time_to_implement="4-6 weeks",
            difficulty="medium"
        ),

        "business_model_canvas": Framework(
            name="Business Model Canvas",
            description="Visualize all key business model components on one page.",
            suitable_for=["Idea", "MVP", "Early traction"],
            key_concepts=[
                "Customer segments",
                "Value propositions",
                "Channels",
                "Customer relationships",
                "Revenue streams",
                "Key resources",
                "Key activities",
                "Key partnerships",
                "Cost structure"
            ],
            implementation_steps=[
                "1. Define customer segments",
                "2. Identify value propositions for each segment",
                "3. Map distribution channels",
                "4. Define customer relationship approach",
                "5. List revenue streams and pricing",
                "6. Identify key resources needed",
                "7. Define key activities required",
                "8. Map key partnerships",
                "9. Calculate cost structure"
            ],
            kpis=[
                "Business model clarity",
                "Segment-specific fit",
                "Channel efficiency",
                "Unit economics",
                "Resource utilization"
            ],
            time_to_implement="1-2 weeks",
            difficulty="easy"
        ),

        "north_star_metric": Framework(
            name="North Star Metric",
            description="Define single metric that represents business success.",
            suitable_for=["Growth", "Scale"],
            key_concepts=[
                "Leading indicator",
                "Core value delivery",
                "Measurable",
                "Aligned with strategy",
                "Actionable"
            ],
            implementation_steps=[
                "1. Define what success looks like",
                "2. List potential metrics",
                "3. Evaluate against criteria (leading, aligned, actionable)",
                "4. Select primary North Star",
                "5. Define supporting metrics (inputs)",
                "6. Set targets and baselines",
                "7. Track weekly/monthly",
                "8. Align organization around it"
            ],
            kpis=[
                "North Star metric value",
                "Input metric correlation",
                "Team alignment score",
                "Metric stability",
                "Predictive accuracy"
            ],
            time_to_implement="1-2 weeks",
            difficulty="easy"
        ),
    }

    BUSINESS_TYPE_RECOMMENDATIONS = {
        BusinessType.B2B_SaaS: ["jtbd", "vpd", "okrs", "north_star_metric"],
        BusinessType.B2C_SaaS: ["jtbd", "vpd", "lean_startup", "north_star_metric"],
        BusinessType.MARKETPLACE: ["jtbd", "vpd", "design_thinking", "okrs"],
        BusinessType.E_COMMERCE: ["vpd", "business_model_canvas", "north_star_metric"],
        BusinessType.SERVICES: ["jtbd", "vpd", "design_thinking"],
        BusinessType.HARDWARE: ["lean_startup", "design_thinking", "okrs"],
        BusinessType.CREATOR: ["vpd", "north_star_metric", "lean_startup"],
        BusinessType.NON_PROFIT: ["design_thinking", "okrs", "jtbd"],
    }

    STAGE_RECOMMENDATIONS = {
        BusinessStage.IDEA: ["jtbd", "lean_startup", "business_model_canvas"],
        BusinessStage.MVP: ["vpd", "lean_startup", "business_model_canvas"],
        BusinessStage.EARLY_TRACTION: ["okrs", "vpd", "north_star_metric"],
        BusinessStage.GROWTH: ["okrs", "north_star_metric", "jtbd"],
        BusinessStage.SCALE: ["okrs", "north_star_metric", "design_thinking"],
        BusinessStage.MATURE: ["okrs", "north_star_metric"],
    }

    @staticmethod
    def recommend_framework(
        business_type: Optional[str] = None,
        business_stage: Optional[str] = None,
        specific_problem: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recommend frameworks based on business context.

        Args:
            business_type: Type of business (e.g., 'b2b_saas')
            business_stage: Stage of business (e.g., 'growth')
            specific_problem: Specific challenge to address

        Returns:
            Recommendation with frameworks and implementation guide
        """
        recommendations = {
            "primary_frameworks": [],
            "secondary_frameworks": [],
            "rationale": [],
            "implementation_priority": [],
            "timestamp": datetime.now().isoformat(),
        }

        if business_type and business_stage:
            # Get frameworks for both type and stage
            type_frameworks = set(
                MethodologyAgent.BUSINESS_TYPE_RECOMMENDATIONS.get(business_type, [])
            )
            stage_frameworks = set(
                MethodologyAgent.STAGE_RECOMMENDATIONS.get(business_stage, [])
            )

            # Primary: intersection (recommended for both)
            primary = list(type_frameworks & stage_frameworks)
            # Secondary: union minus primary
            secondary = list((type_frameworks | stage_frameworks) - set(primary))

            for framework_key in primary:
                framework = MethodologyAgent.FRAMEWORKS.get(framework_key)
                if framework:
                    recommendations["primary_frameworks"].append({
                        "key": framework_key,
                        "name": framework.name,
                        "description": framework.description,
                        "difficulty": framework.difficulty,
                        "time": framework.time_to_implement,
                    })

            for framework_key in secondary:
                framework = MethodologyAgent.FRAMEWORKS.get(framework_key)
                if framework:
                    recommendations["secondary_frameworks"].append({
                        "key": framework_key,
                        "name": framework.name,
                        "description": framework.description,
                        "difficulty": framework.difficulty,
                        "time": framework.time_to_implement,
                    })

            recommendations["rationale"].append(
                f"For {business_type.value} at {business_stage.value} stage"
            )

        if specific_problem:
            recommendations["problem_focus"] = MethodologyAgent._match_frameworks_to_problem(
                specific_problem
            )

        return recommendations

    @staticmethod
    def _match_frameworks_to_problem(problem: str) -> List[Dict[str, Any]]:
        """Match frameworks to specific problem."""
        problem_lower = problem.lower()

        problem_framework_map = {
            "customer understanding": ["jtbd", "design_thinking"],
            "product fit": ["vpd", "jtbd"],
            "validate assumptions": ["lean_startup"],
            "define goals": ["okrs"],
            "business model": ["business_model_canvas", "vpd"],
            "measure success": ["north_star_metric"],
            "innovation": ["design_thinking"],
            "alignment": ["okrs"],
            "positioning": ["vpd"],
            "scaling": ["okrs", "north_star_metric"],
        }

        matched = []
        for problem_keyword, framework_keys in problem_framework_map.items():
            if problem_keyword in problem_lower:
                for key in framework_keys:
                    framework = MethodologyAgent.FRAMEWORKS.get(key)
                    if framework:
                        matched.append({
                            "framework": framework.name,
                            "reason": f"Addresses '{problem_keyword}' in your problem",
                            "key_concepts": framework.key_concepts[:3],
                        })

        return matched if matched else []

    @staticmethod
    def get_framework_details(framework_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific framework."""
        framework = MethodologyAgent.FRAMEWORKS.get(framework_key)
        if not framework:
            return None

        return {
            "name": framework.name,
            "description": framework.description,
            "suitable_for": framework.suitable_for,
            "key_concepts": framework.key_concepts,
            "implementation_steps": framework.implementation_steps,
            "kpis": framework.kpis,
            "time_to_implement": framework.time_to_implement,
            "difficulty": framework.difficulty,
        }

    @staticmethod
    def create_implementation_plan(
        framework_key: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed implementation plan for a framework."""
        framework = MethodologyAgent.FRAMEWORKS.get(framework_key)
        if not framework:
            return {"error": "Framework not found"}

        return {
            "framework": framework.name,
            "overview": framework.description,
            "timeline": framework.time_to_implement,
            "difficulty": framework.difficulty,
            "steps": [
                {
                    "step": step,
                    "owner": business_context.get("owner", "Product team"),
                    "dependencies": [],
                    "success_criteria": "Task completion",
                }
                for step in framework.implementation_steps
            ],
            "key_metrics": framework.kpis,
            "resources_needed": MethodologyAgent._get_resources_for_framework(framework_key),
            "common_pitfalls": MethodologyAgent._get_pitfalls_for_framework(framework_key),
            "next_frameworks": MethodologyAgent._get_next_frameworks(framework_key),
        }

    @staticmethod
    def _get_resources_for_framework(framework_key: str) -> List[str]:
        """Get resources needed for framework implementation."""
        resources_map = {
            "jtbd": [
                "Customer interview guide template",
                "Job mapping canvas",
                "Outcome prioritization matrix",
                "Budget: $2-5K for 15 interviews"
            ],
            "vpd": [
                "Value Proposition Canvas template",
                "Customer empathy mapping template",
                "Feature prioritization tool",
                "Design collaboration tool (Figma/Miro)"
            ],
            "lean_startup": [
                "MVP feature list template",
                "Analytics tracking setup",
                "A/B testing framework",
                "Customer feedback loop system"
            ],
            "okrs": [
                "OKR template and tracking tool",
                "Team alignment workshop materials",
                "Weekly check-in cadence",
                "Scoring methodology documentation"
            ],
            "design_thinking": [
                "Empathy mapping template",
                "Ideation facilitation materials",
                "Prototyping tools",
                "User testing framework"
            ],
            "business_model_canvas": [
                "Canvas template (physical or digital)",
                "Marker pens and sticky notes",
                "Customer/partner interview guides",
                "1-2 hours for workshop"
            ],
            "north_star_metric": [
                "Metrics definition template",
                "Analytics platform access",
                "Dashboard setup tools",
                "Historical data (if available)"
            ],
        }
        return resources_map.get(framework_key, [])

    @staticmethod
    def _get_pitfalls_for_framework(framework_key: str) -> List[str]:
        """Get common pitfalls to avoid."""
        pitfalls_map = {
            "jtbd": [
                "Interviewing only existing customers",
                "Confusing job with solution",
                "Not exploring emotional/social jobs",
                "Over-generalizing from small sample"
            ],
            "vpd": [
                "Designing for ideal customer instead of real one",
                "Assuming features = gains",
                "Missing competitive alternatives",
                "Not testing value proposition"
            ],
            "lean_startup": [
                "Building too much before testing",
                "Ignoring negative feedback",
                "Not pivoting when data says to",
                "Optimizing wrong metrics"
            ],
            "okrs": [
                "Setting too many objectives (should be 3-5)",
                "Confusing OKRs with task lists",
                "Not aligning across teams",
                "Setting unambitious key results"
            ],
            "design_thinking": [
                "Skipping empathy phase",
                "Settling on first idea",
                "Insufficient user testing",
                "Prototype becomes real product"
            ],
            "business_model_canvas": [
                "Treating as one-time exercise",
                "Not involving cross-functional teams",
                "Ignoring competitive positioning",
                "Not testing with customers"
            ],
            "north_star_metric": [
                "Choosing vanity metric",
                "Metric too disconnected from value",
                "Not having leading indicators",
                "Too many competing metrics"
            ],
        }
        return pitfalls_map.get(framework_key, [])

    @staticmethod
    def _get_next_frameworks(framework_key: str) -> List[str]:
        """Get recommended next frameworks after this one."""
        progression_map = {
            "jtbd": ["vpd", "design_thinking"],
            "vpd": ["business_model_canvas", "okrs"],
            "lean_startup": ["okrs", "north_star_metric"],
            "okrs": ["north_star_metric"],
            "design_thinking": ["vpd", "lean_startup"],
            "business_model_canvas": ["vpd", "okrs"],
            "north_star_metric": [],
        }
        return progression_map.get(framework_key, [])

    @staticmethod
    def assess_framework_readiness(
        business_context: Dict[str, Any],
        framework_key: str
    ) -> Dict[str, Any]:
        """Assess if business is ready for a framework."""
        readiness = {
            "ready": True,
            "score": 0,
            "gaps": [],
            "recommendations": [],
        }

        # Check resources
        budget = business_context.get("budget", 0)
        team_size = business_context.get("team_size", 1)

        if framework_key == "jtbd" and budget < 2000:
            readiness["gaps"].append("Insufficient budget for proper customer research")
            readiness["score"] -= 30

        if framework_key == "okrs" and team_size < 5:
            readiness["gaps"].append("Small team size (OKRs work better with 5+ people)")
            readiness["score"] -= 20

        readiness["score"] = max(0, min(100, 100 + readiness["score"]))
        readiness["ready"] = readiness["score"] >= 60

        return readiness
