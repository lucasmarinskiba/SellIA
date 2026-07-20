"""Prompt Registry — Index, lookup, version, and track all 200 prompts."""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptMetadata:
    """Metadata for tracking prompt usage and effectiveness."""
    prompt_id: str
    name: str
    category: str
    tags: List[str]
    industry_variations: Dict[str, str]
    times_used: int = 0
    avg_effectiveness_score: float = 0.0
    last_updated: str = ""
    created_at: str = ""
    version: str = "1.0"


class PromptRegistry:
    """Central registry for all 200 Sellía Brain prompts."""

    def __init__(self):
        """Initialize the prompt registry."""
        self.prompts: Dict[str, any] = {}
        self.metadata: Dict[str, PromptMetadata] = {}
        self.tags_index: Dict[str, Set[str]] = {}
        self.category_index: Dict[str, Set[str]] = {}
        self._load_all_prompts()

    def _load_all_prompts(self) -> None:
        """Load all prompts from modules."""
        from .marketing_prompts import MarketingPrompts
        from .sales_prompts import SalesPrompts
        from .positioning_prompts import PositioningPrompts
        from .retention_prompts import RetentionPrompts
        from .comprehensive_sales_prompts import load_comprehensive_prompts
        from .expert_voices_prompts import load_expert_prompts
        from .affiliate_prompts import load_affiliate_prompts

        # Load marketing prompts (50)
        marketing = MarketingPrompts.get_all_marketing_prompts()
        self.prompts.update(marketing)
        logger.info(f"Loaded {len(marketing)} marketing prompts")

        # Load sales prompts (50)
        sales = SalesPrompts.get_all_sales_prompts()
        self.prompts.update(sales)
        logger.info(f"Loaded {len(sales)} sales prompts")

        # Load positioning prompts (50)
        positioning = PositioningPrompts.get_all_positioning_prompts()
        self.prompts.update(positioning)
        logger.info(f"Loaded {len(positioning)} positioning prompts")

        # Load retention prompts (50)
        retention = RetentionPrompts.get_all_retention_prompts()
        self.prompts.update(retention)
        logger.info(f"Loaded {len(retention)} retention prompts")

        # Load comprehensive sales prompts (200 — niche/positioning/competitive/sales strategies/strengths/weaknesses)
        comprehensive = load_comprehensive_prompts()
        self.prompts.update(comprehensive)
        logger.info(f"Loaded {len(comprehensive)} comprehensive sales prompts")

        # Load expert voices prompts (350 — Trump/Belfort/Buffett/Kiyosaki/Hormozi/Cardone/Robbins/GaryVee/Dalio/Miner/Elliott/Loidi/Ribas/Galperin/Rocca/Galuccio/Naval/Taleb/Graham/Benioff)
        expert = load_expert_prompts()
        self.prompts.update(expert)
        logger.info(f"Loaded {len(expert)} expert voices prompts")

        # Load affiliate prompts (50 — program setup, marketing, partner management, channels, optimization)
        affiliate = load_affiliate_prompts()
        self.prompts.update(affiliate)
        logger.info(f"Loaded {len(affiliate)} affiliate prompts")

        # Build indices
        self._build_indices()
        logger.info(f"Loaded {len(self.prompts)} total prompts (50+50+50+50+200+350+50)")

    def _build_indices(self) -> None:
        """Build lookup indices for fast searching."""
        for prompt_id, prompt in self.prompts.items():
            # Get attributes safely
            name = getattr(prompt, 'name', 'Unknown')
            category = getattr(prompt, 'category', 'Uncategorized')
            tags = getattr(prompt, 'tags', [])

            # Create metadata
            self.metadata[prompt_id] = PromptMetadata(
                prompt_id=prompt_id,
                name=name,
                category=category,
                tags=tags,
                industry_variations=getattr(prompt, 'industry_variations', {}),
                created_at=datetime.utcnow().isoformat()
            )

            # Index by category
            if category not in self.category_index:
                self.category_index[category] = set()
            self.category_index[category].add(prompt_id)

            # Index by tags
            for tag in tags:
                if tag not in self.tags_index:
                    self.tags_index[tag] = set()
                self.tags_index[tag].add(prompt_id)

    def get_prompt(self, prompt_id: str) -> Optional[any]:
        """Retrieve a prompt by ID."""
        prompt = self.prompts.get(prompt_id)
        if prompt and prompt_id in self.metadata:
            # Increment usage counter
            self.metadata[prompt_id].times_used += 1
            logger.info(f"Retrieved prompt: {prompt_id}")
        return prompt

    def search_by_tag(self, tag: str) -> List[str]:
        """Find all prompts with a specific tag."""
        return list(self.tags_index.get(tag.lower(), []))

    def search_by_category(self, category: str) -> List[str]:
        """Find all prompts in a category."""
        return list(self.category_index.get(category, []))

    def search_by_industry(self, industry: str) -> Dict[str, any]:
        """Find all prompts with variations for a specific industry."""
        results = {}
        for prompt_id, prompt in self.prompts.items():
            variations = getattr(prompt, 'industry_variations', {})
            if industry in variations:
                results[prompt_id] = {
                    'prompt': prompt,
                    'industry_variation': variations[industry]
                }
        return results

    def search(self, query: str, search_type: str = 'tag') -> List[str]:
        """Search for prompts by tag, category, or name."""
        query = query.lower()

        if search_type == 'tag':
            return self.search_by_tag(query)
        elif search_type == 'category':
            return self.search_by_category(query)
        elif search_type == 'name':
            return [pid for pid, meta in self.metadata.items()
                    if query in meta.name.lower()]
        else:
            return []

    def get_by_industry_and_category(self, industry: str, category: str) -> List[str]:
        """Find prompts matching industry and category."""
        category_prompts = self.search_by_category(category)
        industry_prompts = set()

        for prompt_id in category_prompts:
            prompt = self.prompts[prompt_id]
            variations = getattr(prompt, 'industry_variations', {})
            if industry in variations:
                industry_prompts.add(prompt_id)

        return list(industry_prompts)

    def get_recommended_prompts(self, use_case: str) -> List[Dict[str, any]]:
        """Get recommended prompts for a specific use case."""
        use_case_tags = {
            'lead_generation': ['content', 'audience-analysis', 'organic-growth'],
            'sales_discovery': ['discovery', 'pain-points', 'questioning'],
            'deal_closing': ['proposal', 'roi', 'value-prop', 'sales'],
            'customer_retention': ['onboarding', 'engagement', 'churn-prevention'],
            'brand_positioning': ['positioning', 'differentiation', 'messaging'],
            'revenue_expansion': ['upsell', 'expansion', 'account-management'],
        }

        tags = use_case_tags.get(use_case, [])
        recommended = []

        for tag in tags:
            for prompt_id in self.search_by_tag(tag):
                if self.prompts[prompt_id] not in [r['prompt'] for r in recommended]:
                    recommended.append({
                        'prompt_id': prompt_id,
                        'prompt': self.prompts[prompt_id],
                        'metadata': self.metadata[prompt_id],
                        'relevance_score': len([t for t in tags if t in self.metadata[prompt_id].tags]) / len(tags)
                    })

        # Sort by relevance
        recommended.sort(key=lambda x: x['relevance_score'], reverse=True)
        return recommended[:5]  # Return top 5

    def get_statistics(self) -> Dict[str, any]:
        """Get registry statistics."""
        total_prompts = len(self.prompts)
        total_usage = sum(m.times_used for m in self.metadata.values())
        avg_effectiveness = sum(m.avg_effectiveness_score for m in self.metadata.values()) / total_prompts if total_prompts > 0 else 0

        return {
            'total_prompts': total_prompts,
            'total_categories': len(self.category_index),
            'total_tags': len(self.tags_index),
            'total_usage': total_usage,
            'average_effectiveness': avg_effectiveness,
            'categories': {cat: len(ids) for cat, ids in self.category_index.items()},
            'most_used': sorted(
                [(m.name, m.times_used) for m in self.metadata.values()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def record_effectiveness(self, prompt_id: str, effectiveness_score: float) -> None:
        """Record the effectiveness score of a prompt usage."""
        if prompt_id in self.metadata:
            meta = self.metadata[prompt_id]
            # Update running average
            current_sum = meta.avg_effectiveness_score * max(meta.times_used - 1, 0)
            new_avg = (current_sum + effectiveness_score) / meta.times_used
            meta.avg_effectiveness_score = new_avg
            meta.last_updated = datetime.utcnow().isoformat()

    def get_top_prompts_by_effectiveness(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get top prompts by effectiveness score."""
        sorted_meta = sorted(
            self.metadata.values(),
            key=lambda m: (m.avg_effectiveness_score, m.times_used),
            reverse=True
        )
        return [
            {
                'prompt_id': m.prompt_id,
                'name': m.name,
                'effectiveness_score': m.avg_effectiveness_score,
                'times_used': m.times_used
            }
            for m in sorted_meta[:limit]
        ]

    def export_prompts(self, filter_category: Optional[str] = None) -> Dict[str, any]:
        """Export prompts for external use."""
        export_data = {}

        for prompt_id, prompt in self.prompts.items():
            if filter_category and getattr(prompt, 'category', None) != filter_category:
                continue

            meta = self.metadata.get(prompt_id, {})
            export_data[prompt_id] = {
                'id': prompt_id,
                'name': getattr(prompt, 'name', ''),
                'category': getattr(prompt, 'category', ''),
                'tags': getattr(prompt, 'tags', []),
                'prompt_text': getattr(prompt, 'prompt_text', ''),
                'variables': getattr(prompt, 'variables', []),
                'example_input': getattr(prompt, 'example_input', {}),
                'example_output': getattr(prompt, 'example_output', ''),
                'metadata': {
                    'times_used': meta.times_used,
                    'effectiveness_score': meta.avg_effectiveness_score,
                    'last_updated': meta.last_updated
                } if meta else {}
            }

        return export_data

    def list_all_prompts(self) -> List[Dict[str, any]]:
        """List all prompts with summary information."""
        return [
            {
                'prompt_id': prompt_id,
                'name': meta.name,
                'category': meta.category,
                'tags': meta.tags,
                'times_used': meta.times_used,
                'effectiveness': meta.avg_effectiveness_score
            }
            for prompt_id, meta in self.metadata.items()
        ]
