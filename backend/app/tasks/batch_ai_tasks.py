"""
Batch AI Processor

Groups similar content-generation tasks into a single LLM call
instead of N separate requests. Dramatically reduces token overhead
and API call count.

Example: generating 20 product descriptions → 1 structured request.
"""

import json
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.provisioning import service as provisioning_service

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_batch_generation(self, batch_job_id: str):
    """Process a batch of AI generation tasks in a single LLM call."""
    import asyncio
    asyncio.run(_process_batch_async(self, batch_job_id))


async def _process_batch_async(task_self, batch_job_id: str):
    async with AsyncSessionLocal() as db:
        # Fetch the batch job
        from app.domains.provisioning.models import ResourceJob
        result = await db.execute(
            select(ResourceJob).where(ResourceJob.id == batch_job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"Batch job {batch_job_id} not found")
            return

        await provisioning_service.update_job(db, job, "running")

        try:
            items = job.result.get("items", [])
            task_type = job.result.get("task_type", "content_generation")
            business_id = job.result.get("business_id")

            if not items:
                raise ValueError("No items to process in batch")

            # Build a single structured prompt
            structured_prompt = _build_batch_prompt(task_type, items)

            # Call LLM once
            from app.domains.agents.llm_provider import LLMResponse
            from app.domains.agents.llm_router import route_model
            from app.domains.agents.llm_provider import OpenAIProvider, AnthropicProvider, KimiProvider, OllamaProvider
            from langchain_core.messages import HumanMessage, SystemMessage

            provider_name, model, _ = route_model(structured_prompt, ollama_available=False)

            messages = [
                SystemMessage(content="You are a batch content generator. Respond ONLY with a JSON object where keys are item IDs and values are the generated content."),
                HumanMessage(content=structured_prompt),
            ]

            response = None
            if provider_name == "openai":
                from app.core.config import get_settings
                key = get_settings().OPENAI_API_KEY
                response = await OpenAIProvider().generate(messages, key or "", model)
            elif provider_name == "anthropic":
                from app.core.config import get_settings
                key = get_settings().ANTHROPIC_API_KEY
                response = await AnthropicProvider().generate(messages, key or "", model)
            elif provider_name == "kimi":
                from app.core.config import get_settings
                key = get_settings().KIMI_API_KEY
                response = await KimiProvider().generate(messages, key or "", model)
            elif provider_name == "ollama":
                response = await OllamaProvider().generate(messages, "", model)

            if not response:
                raise RuntimeError("LLM batch generation failed")

            # Parse JSON response
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback: wrap raw response
                parsed = {str(i): response.content for i in range(len(items))}

            # Update job result
            await provisioning_service.update_job(
                db, job, "completed",
                result={
                    "task_type": task_type,
                    "items_generated": len(items),
                    "provider": provider_name,
                    "model": model,
                    "outputs": parsed,
                }
            )

            await provisioning_service.add_event(
                db, job.request_id, "step_completed",
                f"Batch generation completed: {len(items)} items via {provider_name}/{model}",
                {"items": len(items), "provider": provider_name, "model": model}
            )

            logger.info(f"Batch job {batch_job_id}: generated {len(items)} items")

        except Exception as exc:
            await provisioning_service.update_job(db, job, "failed", error_message=str(exc))
            raise task_self.retry(exc=exc) from exc


def _build_batch_prompt(task_type: str, items: List[Dict[str, Any]]) -> str:
    """Build a single prompt for batch generation."""
    lines = [
        f"Generate content for the following {len(items)} items.",
        f"Task type: {task_type}",
        "",
        "For each item, use the provided ID as the key in your JSON response.",
        "",
        "Items:",
    ]
    for item in items:
        item_id = item.get("id", str(uuid.uuid4())[:8])
        context = item.get("context", "")
        lines.append(f"  [{item_id}] {context}")

    lines.append("")
    lines.append("Respond with valid JSON only. Example: {\"item-1\": \"Generated text...\", ...}")
    return "\n".join(lines)


@shared_task
def schedule_batch_jobs():
    """Periodic task (Celery Beat) that groups pending batch items and enqueues them."""
    # This is a placeholder for a more sophisticated scheduler that would
    # look at a 'batch_queue' table and group items every 5 minutes.
    logger.info("Batch scheduler tick — implement queue grouping here if needed")
